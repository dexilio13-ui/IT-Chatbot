"""
Hugging Face Space — Chatbot sa RAG engine-om.

Ovo je Gradio aplikacija koja koristi isti RAG engine kao i
originalni FastAPI backend, ali bez PostgreSQL (in-memory istorija).

Podesi sledece env varijable u HF Space Settings -> Repository Secrets:
  - OPENAI_API_KEY: tvoj OpenAI API kljuc
  - QDRANT_URL: URL QdrantCloud instance
  - QDRANT_API_KEY: API kljuc za Qdrant (ako je potreban)
  - QDRANT_COLLECTION: ime kolekcije (default: it_support_kb)
  - ENABLE_CHITCHAT: True (podrazumevano)
  - CHITCHAT_TEMPERATURE: 0.4 (podrazumevano)
"""

import os
import logging
import sys
import traceback

# Dodajemo backend folder u PATH da mozemo da importujemo rag modul.
# Na HF Space-u, app.py i backend/ folder su u istom korenom direktorijumu.
_BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import gradio as gr

# spaces je potreban za ZeroGPU kompatibilnost na HF.
# Iako nas app ne koristi GPU (samo OpenAI API), HF zahteva
# ovaj import da bi Space mogao da se pokrene na ZeroGPU hardveru.
import spaces  # noqa: F401

from rag.engine import get_chat_engine
from rag.classifier import is_chitchat_query
from rag.configurator import is_config_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hf_app")

# ── Inicijalizacija chat engine-a ─────────────────────────────────
# Koristimo in-memory memoriju (nema PostgreSQL)
# Svi korisnici su gosti sa role_id=1

_USERNAME = "hf_user"
_ROLE_ID = 1
_IS_ADMIN = False

_NO_DATA_PHRASE = "Nemam taj podatak u bazi znanja"

# Proveravamo na startu da li su bitne env varijable postavljene
_MISSING_ENV = []
if not os.environ.get("OPENAI_API_KEY"):
    _MISSING_ENV.append("OPENAI_API_KEY")
if not os.environ.get("QDRANT_URL"):
    _MISSING_ENV.append("QDRANT_URL")

if _MISSING_ENV:
    logger.warning(
        "Nedostaju env varijable: %s. App radi u DEMO rezimu.",
        ", ".join(_MISSING_ENV),
    )


def _clamp_score(score: float | None) -> float | None:
    """Ogranicava skor na opseg [0.0, 1.0] za korektan prikaz."""
    if score is None:
        return None
    return round(min(max(score, 0.0), 1.0), 3)


def _format_sources(source_nodes) -> str:
    """Formatira izvore iz source_nodes u tekst koji se dodaje uz odgovor."""
    if not source_nodes:
        return ""

    parts = []
    for ns in source_nodes[:1]:  # Samo 1 najbolji izvor
        source = ns.node.metadata.get("source", "Nepoznat")
        score = _clamp_score(ns.score)
        score_str = f"{min(round((score or 0) * 100), 100)}%" if score is not None else "?"
        role = ns.node.metadata.get("required_role_id", "?")
        parts.append(f"\n\n📄 **Izvor:** {source}  \n🎯 Relevatnost: {score_str}  \n👤 Role >= {role}")

    return "".join(parts)


def _get_chat_engine(message: str):
    """
    Kreira chat engine za HF Space.
    Detektuje da li je poruka caskanje ili zahteva konfiguraciju.
    """
    use_chitchat = os.environ.get("ENABLE_CHITCHAT", "True").lower() == "true"
    chitchat = use_chitchat and is_chitchat_query(message)
    config = use_chitchat and is_config_query(message)

    logger.debug("Chitchat=%s Config=%s Poruka=%.50s", chitchat, config, message)

    return get_chat_engine(
        username=_USERNAME,
        role_id=_ROLE_ID,
        is_admin=_IS_ADMIN,
        chitchat_enabled=chitchat,
        config_mode=config,
    )


# ── Gradio chat funkcija sa strimovanjem ──────────────────────────

def respond_stream(message: str, history: list):
    """
    Gradio chat funkcija sa strimovanjem tokena u realnom vremenu.
    Na kraju dodaje i izvore (citate) ako postoje.

    Ako OpenAI ili Qdrant nisu dostupni, vraca prijateljsku poruku
    umesto da crash-uje.
    """
    # Ako nedostaju env varijable, odmah vrati poruku
    if _MISSING_ENV:
        yield (
            "❌ **Baza znanja nije povezana.**\n\n"
            "Da bi chatbot radio potrebno je podesiti:\n"
            f"- `{_MISSING_ENV[0]}` u HF Secrets\n"
            + (f"- `{_MISSING_ENV[1]}` u HF Secrets\n" if len(_MISSING_ENV) > 1 else "")
            + "\nPogledaj README.md za uputstvo."
        )
        return

    try:
        engine = _get_chat_engine(message)
    except Exception as e:
        logger.error("Greska pri kreiranju engine-a: %s", traceback.format_exc())
        yield (
            "❌ **Doslo je do greske prilikom obrade zahteva.**\n\n"
            "Proveri da li su sledece usluge dostupne:\n"
            "- Qdrant baza podataka (QDRANT_URL)\n"
            "- OpenAI API kljuc (OPENAI_API_KEY)\n"
            "- OpenAI API nalog ima sredstava\n\n"
            f"{type(e).__name__}: {e}"
        )
        return

    try:
        streaming_response = engine.stream_chat(message)
    except Exception as e:
        logger.error("Greska pri strimovanju: %s", traceback.format_exc())
        yield f"❌ **Greska:** {type(e).__name__}: {e}"
        return

    partial = ""
    for token in streaming_response.response_gen:
        partial += token
        yield partial

    # Dodaj izvore na kraju odgovora (ako LLM nije rekao da nema podataka)
    if _NO_DATA_PHRASE not in partial:
        sources_text = _format_sources(streaming_response.source_nodes)
        if sources_text:
            yield partial + sources_text


# ── CSS za lepsi izgled ──────────────────────────────────────────

CUSTOM_CSS = """
footer {display: none !important;}
#chat-container {
    height: calc(100vh - 120px) !important;
}
.message {
    border-radius: 16px !important;
    padding: 12px 18px !important;
    font-size: 15px !important;
    line-height: 1.5 !important;
}
.user-message {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
}
.bot-message {
    background: #1f2937 !important;
    color: #e5e7eb !important;
    border: 1px solid #374151 !important;
}
"""


# ── Kreiranje Gradio interfejsa ──────────────────────────────────

with gr.Blocks(
    css=CUSTOM_CSS,
    title="IT Asistent — Konfigurator",
    theme=gr.themes.Soft(
        primary_hue="violet",
        neutral_hue="zinc",
        font=gr.themes.GoogleFont("Inter"),
    ),
) as demo:
    gr.Markdown(
        """
    # IT Asistent
    ### Tehnicka podrska i konfiguracija racunara
    """
    )

    chatbot = gr.ChatInterface(
        fn=respond_stream,
        title=None,
        description=None,
        type="messages",
        examples=[
            "Cao, kako si?",
            "Napravi mi konfiguraciju za gaming PC do 800e",
            "Koji CPU preporucujes za AMD platformu?",
            "Sastavi mi radnu stanicu za editing do 1500e",
            "Kako da instaliram Windows drajvere?",
        ],
        cache_examples=False,
    )

    gr.Markdown(
        """
    ---
    Powered by **GPT-4o-mini** + **Qdrant** + **LlamaIndex**
    """
    )

# ── Pokretanje ───────────────────────────────────────────────────

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
