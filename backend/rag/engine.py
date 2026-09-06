import json
import logging
import re
from typing import Dict, List, Optional

from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.chat_engine.types import BaseChatEngine
from llama_index.core.base.llms.types import ChatMessage, MessageRole

# Uvozimo funkciju za sistemski prompt iz odvojenog fajla
from rag.system_prompt import get_system_prompt, SYSTEM_PROMPT as SYSTEM_PROMPT_DETAILED
from rag.configurator import get_components_catalog, is_config_query
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.vector_stores.types import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from qdrant_client import QdrantClient
from sqlmodel import Session

from core.config import settings
from rag.chat_history import load_chat_history

logger = logging.getLogger(__name__)

# ==========================================
# 0. Globalna konfiguracija LlamaIndex
# ==========================================
# HuggingFace embedding model (besplatan, radi lokalno)
# BAAI/bge-small-en-v1.5 → 384 dimenzije
Settings.embed_model = HuggingFaceEmbedding(
    model_name=settings.HF_EMBEDDING_MODEL,
)
# Groq LLM (besplatan, brz)
Settings.llm = Groq(
    model=settings.GROQ_MODEL,
    temperature=0.1,
    max_tokens=300,
    api_key=settings.GROQ_API_KEY or None,
)
# Settings.num_output koristi LlamaIndex default (512)
# max_tokens=150 se postavlja samo na chitchat LLM instanci

# ==========================================
# 1. Lazy inicijalizacija Qdrant veze i indeksa
# ==========================================
# Ove promenljive se inicijalizuju na zahtev (lazy), tek kada ih
# get_chat_engine() prvi put pozove. To omogucava auto-start Qdrant-a
# iz main.py lifespan-a pre nego sto se engine importuje.

_QDRANT_INITIALIZED: bool = False
_client: QdrantClient | None = None
_vector_store: QdrantVectorStore | None = None
_storage_context: StorageContext | None = None
_index: VectorStoreIndex | None = None
_bm25_docstore: SimpleDocumentStore | None = None


def invalidate_bm25_cache() -> None:
    """
    Invalidira BM25 docstore cache.

    Pozvati nakon što se novi dokumenti indeksiraju u Qdrant
    (npr. iz admin upload endpoint-a) kako bi se BM25 docstore
    rebuild-ovao pri sledećem pozivu get_chat_engine().
    """
    global _QDRANT_INITIALIZED, _bm25_docstore
    _QDRANT_INITIALIZED = False
    _bm25_docstore = None
    logger.info(
        "BM25 docstore cache invalidiran. Biće rebuild-ovan pri sledećem zahtevu."
    )


def _ensure_initialized() -> None:
    """Lazy inicijalizacija Qdrant klijenta, indeksa i BM25 docstore-a."""
    global \
        _QDRANT_INITIALIZED, \
        _client, \
        _vector_store, \
        _storage_context, \
        _index, \
        _bm25_docstore

    if _QDRANT_INITIALIZED:
        return

    logger.info("Lazy inicijalizacija Qdrant veze...")

    _client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY or None,
    )
    _vector_store = QdrantVectorStore(
        client=_client, collection_name=settings.QDRANT_COLLECTION
    )
    _storage_context = StorageContext.from_defaults(vector_store=_vector_store)

    _index = VectorStoreIndex.from_vector_store(
        vector_store=_vector_store,
        storage_context=_storage_context,
    )

    # BM25 docstore
    _bm25_docstore = _build_bm25_docstore()

    if _bm25_docstore is None:
        logger.warning(
            "Qdrant kolekcija '%s' je prazna ili nedostupna. "
            "Koristicu LLM-only rezim.",
            settings.QDRANT_COLLECTION,
        )
        _QDRANT_INITIALIZED = True  # Kesiraj da smo proverili
        _index = None               # Forsiraj LLM-only
    else:
        _QDRANT_INITIALIZED = True
        logger.info("Qdrant inicijalizacija zavrsena.")


# ==========================================
# 2. BM25 docstore (iz Qdrant payload-a)
# ==========================================
def _build_bm25_docstore() -> SimpleDocumentStore | None:
    """
    Dohvata sve dokumente iz Qdrant-a i gradi SimpleDocumentStore
    za BM25 keyword pretragu.

    Returns:
        SimpleDocumentStore ako ima dokumenata, None ako je kolekcija prazna.
    """
    assert _client is not None  # _ensure_initialized() mora biti pozvan pre
    logger.info(
        "Pravim BM25 docstore iz Qdrant kolekcije '%s'...", settings.QDRANT_COLLECTION
    )

    try:
        points, _ = _client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            limit=10000,
            with_payload=True,
            with_vectors=False,
        )
    except Exception as e:
        logger.warning("Ne mogu da dohvatim dokumente iz Qdrant-a: %s", e)
        return None

    nodes: list[TextNode] = []
    for point in points:
        payload = point.payload
        if not payload:
            continue

        # LlamaIndex QdrantVectorStore cuva text unutar _node_content JSON polja
        text = ""
        node_content_str = payload.get("_node_content", "")
        if node_content_str:
            try:
                node_data = json.loads(node_content_str)
                text = node_data.get("text", "") or ""
            except Exception:
                pass

        # Fallback: direktno text polje (stariji format ili custom upload)
        if not text:
            text = payload.get("text", "") or ""

        if not text:
            continue

        # Kopiramo sve metapodatke iz payload-a (source, required_role_id, itd.)
        # Ove metapodatke LlamaIndex cuva direktno u payload-u, ne u _node_content
        metadata = {
            k: v for k, v in payload.items() if k not in ("text", "_node_content")
        }
        node_id = str(point.id) if point.id else None

        node = TextNode(text=text, metadata=metadata, id_=node_id)
        nodes.append(node)

    logger.info("BM25 docstore: %d nodova učitano iz Qdrant-a.", len(nodes))

    if not nodes:
        logger.warning(
            "Qdrant kolekcija '%s' je prazna. BM25 neće biti dostupan.",
            settings.QDRANT_COLLECTION,
        )
        return None

    docstore = SimpleDocumentStore()
    docstore.add_documents(nodes)
    return docstore


# ==========================================
# 3. HybridRetriever — Vector + BM25 + RBAC
# ==========================================
class HybridRetriever(BaseRetriever):
    """
    Kombinuje Qdrant vektorski retriever (sa ugrađenim RBAC filterom)
    i BM25 keyword retriever.

    BM25 ne podržava MetadataFilters direktno, pa se RBAC primenjuje
    naknadno filtriranjem rezultata. Oba skupa se spajaju kroz
    Reciprocal Rank Fusion (RRF) sa deduplikacijom po tekstu.
    """

    def __init__(
        self,
        vector_retriever,
        bm25_retriever,
        role_id: int,
        similarity_top_k: int = 3,
        is_admin: bool = False,
    ) -> None:
        super().__init__()
        self._vector_retriever = vector_retriever
        self._bm25_retriever = bm25_retriever
        self._role_id = role_id
        self._similarity_top_k = similarity_top_k
        self._is_admin = is_admin

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        # 1. Vektorska pretraga (RBAC filter ugrađen u retriever)
        vector_nodes = self._vector_retriever.retrieve(query_bundle)

        # 2. BM25 pretraga (bez RBAC — filtriramo odmah, osim za admina)
        bm25_nodes = self._bm25_retriever.retrieve(query_bundle)
        if self._is_admin:
            filtered_bm25 = bm25_nodes
        else:
            filtered_bm25 = [
                n
                for n in bm25_nodes
                if n.node.metadata.get("required_role_id", 999) <= self._role_id
            ]

        # 3. RRF kombinacija sa deduplikacijom po tekstu
        return self._reciprocal_rank_fusion(
            [vector_nodes, filtered_bm25],
            top_k=self._similarity_top_k,
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalizuje tekst za poređenje (lowercase, strip, uklanja višestruke razmake)."""
        return re.sub(r"\s+", " ", text.strip().lower())

    @staticmethod
    def _reciprocal_rank_fusion(
        results: list[list[NodeWithScore]],
        top_k: int,
    ) -> List[NodeWithScore]:
        """
        Reciprocal Rank Fusion (RRF) sa standardnom konstantom k=60.

        Formula: score(d) = Σ 1 / (rank(d) + 60)  za svaku listu rangiranja.

        RRF se koristi ISKLJUČIVO za rangiranje/sortiranje.
        Za prikaz skora (relevatnost u %) koristimo cosine similarity
        iz vektorskog retrivera (opseg 0-1 → 0-100%), jer je RRF skor
        suviše mali (max ~0.033 → 3%) i ne pruža korisnu informaciju.

        Dodatna deduplikacija: ako dva noda imaju isti tekst (ignorišući
        velika/mala slova i višestruke razmake), zadržava se samo onaj
        sa višim RRF skorom. Ovo rešava problem duplih citata kada:
          - Isti sadržaj vrate i vektorski i BM25 retriver sa različitim ID-jevima
          - Postoje dupli point-ovi u Qdrant-u (npr. višestruki upload istog fajla)
        """
        rrf_scores: dict[str, float] = {}
        node_map: dict[str, NodeWithScore] = {}
        # Cosine similarity skorovi iz vektorskog retrivera (results[0])
        vector_scores: dict[str, float] = {}

        for list_idx, rank_list in enumerate(results):
            for rank, node_with_score in enumerate(rank_list, start=1):
                node_id = node_with_score.node.node_id
                rrf_scores[node_id] = rrf_scores.get(node_id, 0.0) + 1.0 / (rank + 60)
                node_map[node_id] = node_with_score
                # Sačuvaj cosine similarity skor iz vektorskog retrivera
                if list_idx == 0 and node_with_score.score is not None:
                    vector_scores[node_id] = node_with_score.score

        # Sortiramo po RRF skoru (opadajuće)
        sorted_ids = sorted(
            rrf_scores, key=lambda k: rrf_scores.get(k, 0.0), reverse=True
        )

        # Deduplikacija po tekstualnom sadržaju
        seen_texts: set[str] = set()
        deduplicated: list[NodeWithScore] = []
        for nid in sorted_ids:
            nws = node_map[nid]
            text_key = HybridRetriever._normalize_text(nws.node.get_content())
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                # Koristimo cosine similarity skor za prikaz (0-1 → 0-100%)
                # Ako nema vektorskog skora (npr. nod je došao samo iz BM25),
                # koristimo RRF skor kao fallback.
                display_score = vector_scores.get(nid, rrf_scores.get(nid, 0.0))
                deduplicated.append(NodeWithScore(node=nws.node, score=display_score))

        return deduplicated[:top_k]


# ==========================================
# 4. Upravljanje memorijom
# ==========================================
# Rečnik za čuvanje istorije razgovora po korisniku (fallback ako nema DB).
_chat_memories: Dict[str, ChatMemoryBuffer] = {}

# Podrazumevani sistemski prompt (caskanje ukljuceno)
# Koristi se globalno u Settings.llm / inicijalizaciji ako nije drugacije navedeno
SYSTEM_PROMPT = SYSTEM_PROMPT_DETAILED


# ==========================================
# 5. Glavna funkcija za kreiranje engine-a
# ==========================================
def get_chat_engine(
    username: str,
    role_id: int,
    is_admin: bool = False,
    session: Optional[Session] = None,
    chitchat_enabled: bool = True,
    config_mode: bool = False,
) -> BaseChatEngine:
    """
    Kreira CondensePlusContextChatEngine sa hybridnim retriever-om
    (vektor + BM25) i RBAC filtriranjem.

    Retriever kombinuje:
      - Qdrant vektorsku pretragu (sa MetadataFilters na required_role_id)
      - BM25 keyword pretragu (sa naknadnim RBAC filtriranjem)
    Rezultati se spajaju kroz Reciprocal Rank Fusion (RRF) sa deduplikacijom.

    Istorija razgovora:
      - Ako je prosleđen `session`, učitava istoriju iz PostgreSQL.
      - Ako nije prosleđen `session`, koristi in-memory `_chat_memories` dict
        (fallback za testove i stare pozive).

    Args:
        username: Korisničko ime (za odvajanje memorije po korisniku).
        role_id: Role ID korisnika:
            1 = Kupac (vidi samo javne dokumente, tj. required_role_id <= 1)
            2 = Prodavac (vidi javne i prodavačke, tj. required_role_id <= 2)
            3 = Serviser (vidi sve, tj. required_role_id <= 3)
        is_admin: Ako je True, preskače RBAC filter (vidi sve dokumente).
        session: Opcioni SQLModel Session. Ako je prosleđen, učitava istoriju
            iz PostgreSQL umesto iz in-memory dict-a.
        chitchat_enabled: Ako je True, model odgovara i na pozdrave/caskanje.
            Ako je False, strogo samo iz baze znanja.
        config_mode: Ako je True, ukljucuje konfigurator PC komponenti
            i ubacuje katalog sa cenama u system prompt.

    Returns:
        BaseChatEngine instanca konfigurisana za specifičnog korisnika.
    """
    # Odaberi odgovarajuci sistemski prompt na osnovu podesavanja
    system_prompt = get_system_prompt(
        chitchat_enabled=chitchat_enabled,
        config_mode=config_mode,
    )

    # Ako je config_mode aktivan, dodaj katalog komponenti direktno u system prompt
    if config_mode:
        catalog = get_components_catalog()
        if catalog:
            system_prompt += "\n\n" + catalog
        logger.info("Konfigurator mod: ucitano %d karaktera kataloga.", len(catalog))

    # ── LLM setup (radi i bez Qdrant-a) ──────────────────────
    if chitchat_enabled:
        llm = Groq(
            model=settings.GROQ_MODEL,
            temperature=settings.CHITCHAT_TEMPERATURE,
            max_tokens=150,
            api_key=settings.GROQ_API_KEY or None,
        )
        logger.debug(
            "Chitchat mod: temperatura LLM = %.1f", settings.CHITCHAT_TEMPERATURE
        )
    else:
        llm = Settings.llm
        logger.debug("Strogi RAG mod: temperatura LLM = 0.1")

    # ── Učitavanje istorije ────────────────────────────────────
    if session is not None:
        history_entries = load_chat_history(session, username)
        chat_messages: list[ChatMessage] = [
            ChatMessage(
                role=MessageRole.USER
                if entry.role == "user"
                else MessageRole.ASSISTANT,
                content=entry.content,
            )
            for entry in history_entries
        ]
        memory = ChatMemoryBuffer.from_defaults(
            token_limit=3000,
            chat_history=chat_messages,
        )
        logger.debug(
            "Učitano %d poruka istorije za '%s' iz PostgreSQL.",
            len(chat_messages),
            username,
        )
    else:
        if username not in _chat_memories:
            _chat_memories[username] = ChatMemoryBuffer.from_defaults(token_limit=1500)
        memory = _chat_memories[username]

    # ── Pokušaj inicijalizacije Qdrant-a ──────────────────────
    # Stara Qdrant kolekcija ima 1536-dim vektore (OpenAI),
    # novi HuggingFace model proizvodi 384-dim. Ako dodje do
    # dimenzijske neusaglašenosti, padamo na LLM-only rezim.
    try:
        _ensure_initialized()
    except Exception as e:
        logger.warning(
            "Qdrant inicijalizacija nije uspela: %s. Radim u LLM-only rezimu.", e
        )

    # ── Kreiranje chat engine-a ────────────────────────────────
    if _index is not None and _QDRANT_INITIALIZED:
        # Qdrant je dostupan — koristimo hibridni retriver
        if not is_admin:
            filters = MetadataFilters(
                filters=[
                    MetadataFilter(
                        key="required_role_id",
                        value=role_id,
                        operator=FilterOperator.LTE,
                    )
                ]
            )
        else:
            filters = None

        vector_retriever = _index.as_retriever(filters=filters, similarity_top_k=3)

        if _bm25_docstore is not None:
            bm25_retriever = BM25Retriever.from_defaults(
                docstore=_bm25_docstore,
                similarity_top_k=3,
            )
            hybrid_retriever: BaseRetriever = HybridRetriever(
                vector_retriever=vector_retriever,
                bm25_retriever=bm25_retriever,
                role_id=role_id,
                similarity_top_k=3,
                is_admin=is_admin,
            )
        else:
            hybrid_retriever = vector_retriever

        return CondensePlusContextChatEngine.from_defaults(
            retriever=hybrid_retriever,
            memory=memory,
            system_prompt=system_prompt,
            llm=llm,
        )
    else:
        # Qdrant nije dostupan — LLM-only rezim (chitchat radi, RAG ne)
        from llama_index.core.chat_engine import SimpleChatEngine

        logger.info(
            "Qdrant nije dostupan. Koristim SimpleChatEngine (LLM-only) za '%s'.",
            username,
        )
        return SimpleChatEngine.from_defaults(
            llm=llm,
            memory=memory,
            system_prompt=system_prompt,
        )
