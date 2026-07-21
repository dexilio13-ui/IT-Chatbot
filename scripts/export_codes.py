# -*- coding: utf-8 -*-
"""Skript za eksportovanje backend i frontend kodova u tekstualne fajlove."""
import sys
# Postavljamo stdout enkodiranje da izbegnemo UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import sys
from pathlib import Path

# Putanje
PROJECT_DIR = Path("E:/Chatbot/chatbot_app")
EXPORT_DIR = Path("D:/OneDrive/Desktop/Potraga za sreckom/MI Systems Co/RAG/Chatbot/export")

ENCODING = "utf-8"

def write_file_safe(path: Path, content: str) -> None:
    """Upisuje fajl sa UTF-8 enkodiranjem, bez BOM."""
    path.write_text(content, encoding=ENCODING)


def read_file_safe(path: Path) -> str:
    """Čita fajl sa UTF-8 enkodiranjem."""
    return path.read_text(encoding=ENCODING)


SEPARATOR = "#" * 60 + "\n\n"

# ──────────────────────────────────────────────
# 1. BACKEND FAJLOVI
# ──────────────────────────────────────────────
BACKEND_FILES = [
    "backend/api/__init__.py",
    "backend/api/auth.py",
    "backend/api/chat.py",
    "backend/api/admin.py",
    "backend/core/__init__.py",
    "backend/core/config.py",
    "backend/core/db.py",
    "backend/core/logger.py",
    "backend/core/security.py",
    "backend/main.py",
    "backend/models/__init__.py",
    "backend/models/user.py",
    "backend/models/chat_history.py",
    "backend/rag/__init__.py",
    "backend/rag/engine.py",
    "backend/rag/chat_history.py",
    "backend/rag/system_prompt.py",
]

OUTPUT_BACKEND = EXPORT_DIR / "backend_kodovi.txt"


def write_backend_export():
    with open(OUTPUT_BACKEND, "w", encoding=ENCODING, errors="replace") as out:
        for rel_path in BACKEND_FILES:
            abs_path = PROJECT_DIR / rel_path
            out.write(f"--- POCETAK FAJLA: ..\\chatbot_local\\{rel_path.replace('/', '\\\\')} ---\n")
            if abs_path.exists():
                content = abs_path.read_text(encoding=ENCODING, errors="replace")
                out.write(content)
                if not content.endswith("\n"):
                    out.write("\n")
            else:
                out.write(f"# FAJL NE POSTOJI: {abs_path}")
            out.write("\n--- KRAJ FAJLA ---\n\n")
            out.write(SEPARATOR)
    print(f"backend_kodovi.txt kreiran ({OUTPUT_BACKEND})")


# ──────────────────────────────────────────────
# 2. FRONTEND FAJLOVI
# ──────────────────────────────────────────────
FRONTEND_FILES = [
    "frontend/index.html",
    "frontend/package.json",
    "frontend/postcss.config.js",
    "frontend/tailwind.config.js",
    "frontend/vite.config.js",
    # .env je namerno izostavljen - sadrzi osetljive API kljuceve
    "frontend/src/main.jsx",
    "frontend/src/index.css",
    "frontend/src/App.jsx",
    "frontend/src/services/api.js",
    "frontend/src/context/AuthContext.jsx",
    "frontend/src/components/LoginForm.jsx",
    "frontend/src/components/ChatBox.jsx",
    "frontend/src/components/AdminPanel.jsx",
]

OUTPUT_FRONTEND = EXPORT_DIR / "frontend_kodovi.txt"


def write_frontend_export():
    with open(OUTPUT_FRONTEND, "w", encoding=ENCODING, errors="replace") as out:
        for rel_path in FRONTEND_FILES:
            abs_path = PROJECT_DIR / rel_path
            out.write(f"--- POCETAK FAJLA: ..\\chatbot_local\\{rel_path.replace('/', '\\\\')} ---\n")
            if abs_path.exists():
                content = abs_path.read_text(encoding=ENCODING, errors="replace")
                out.write(content)
                if not content.endswith("\n"):
                    out.write("\n")
            else:
                out.write(f"# FAJL NE POSTOJI: {abs_path}")
            out.write("\n--- KRAJ FAJLA ---\n\n")
            out.write(SEPARATOR)
    print(f"frontend_kodovi.txt kreiran ({OUTPUT_FRONTEND})")


# ──────────────────────────────────────────────
# 3. OBJASNJENJE BACKEND (ažurirano)
# ──────────────────────────────────────────────
def write_objasnjenje():
    content = """\
==============================================================================
OBJAŠNJENJE BACKEND ARHITEKTURE - RAG CHATBOT
==============================================================================
FastAPI + LlamaIndex + Qdrant + PostgreSQL + Groq LLM
Poslednja izmena: Jul 2026

==============================================================================
1. TEHNOLOŠKI STEK
==============================================================================

| Komponenta      | Tehnologija                                |
|-----------------|--------------------------------------------|
| Web framework   | FastAPI (Python 3.12+)                     |
| RAG framework   | LlamaIndex (hibridna pretraga)             |
| Vektorska baza  | Qdrant (Cloud, dim=1536)                   |
| Relaciona baza  | PostgreSQL 18 (lokalni EDB)                |
| LLM             | OpenAI - gpt-4o-mini (max_tokens=300)      |
| Embedding model | OpenAI - text-embedding-3-small (dim=1536) |
| Dokument parser | LlamaParse + MarkdownNodeParser            |
| Autentifikacija | JWT (HS256, istek 60min)                  |
| ORM             | SQLModel (SQLAlchemy + Pydantic)           |
| Lozinke         | bcrypt hash                                |

==============================================================================
2. STRUKTURA FOLDERA (backend/)
==============================================================================

backend/
  ├── main.py                 # Ulazna tačka, lifespan, seed korisnici
  ├── api/
  │   ├── auth.py             # POST /api/auth/login (JWT + bcrypt)
  │   ├── chat.py             # POST /api/chat, POST /api/chat/stream (SSE)
  │   └── admin.py            # Admin rute (upload, brisanje, listanje)
  ├── core/
  │   ├── config.py           # Pydantic Settings (env varijable)
  │   ├── db.py               # PostgreSQL konekcija (SQLModel)
  │   ├── security.py         # JWT kreiranje
  │   └── logger.py           # Centralizovano logovanje
  ├── rag/
  │   ├── engine.py           # RAG engine (hybrid retriever, RBAC, RRF)
  │   ├── chat_history.py     # Učitavanje/čuvanje istorije iz PostgreSQL
  │   └── system_prompt.py    # Sistemski prompt za LLM
  ├── models/
  │   ├── user.py             # SQLModel: User tabela
  │   └── chat_history.py     # SQLModel: ChatHistory tabela
  ├── uploads/                # Privremeni fajlovi za indeksiranje
  └── tests/                  # pytest testovi (ako postoje)

==============================================================================
3. DETALJNO OBJAŠNJENJE MODULA
==============================================================================

--- main.py ---
- FastAPI aplikacija sa lifespan funkcijom (zamenjuje stari startup/shutdown).
- Startup: inicijalizacija logera, PostgreSQL tabele (create_all),
  seedovanje testnih korisnika (admin, serviser, prodavac, kupac) sa
  bcrypt hash-ovanim lozinkama, automatsko kreiranje Qdrant kolekcije
  ako ne postoji, kreiranje payload indeksa za filtriranje.
- Lozinke se hashiraju preko _hash_password() (bcrypt.hashpw + gensalt).
- CORS podešen dozvoljava sve (*) - za produkciju suziti.
- Shutdown: loguje gašenje aplikacije.

--- api/auth.py ---
- Jedan endpoint: POST /api/auth/login.
- Prima username/password preko OAuth2PasswordRequestForm.
- Proverava bcrypt hash preko bcrypt.checkpw().
- Vraća JWT token sa sub (username), role_id (1-3), is_admin (bool).
- Token ističe za 60 minuta (podesivo u .env).

--- api/chat.py ---
- Dva endpointa: POST /api/chat (JSON) i POST /api/chat/stream (SSE).
- get_current_user() dependency dekodira JWT i izvlači username, role_id,
  is_admin. Vraća 401 za istekao/nevalidan token.
- Chat: kreira get_chat_engine() sa korisničkim podacima, prosleđuje
  role_id za RBAC filtriranje.
- SSE streaming šalje tokene u realnom vremenu, zatim sources (citati),
  pa done signal. Fallback za kraj strima bez done eventa.
- Prikazuje samo 1 najbolji izvor (source) po odgovoru.

--- api/admin.py ---
- require_admin dependency: proverava is_admin flag, 403 ako nije admin.
- GET /api/admin/users - lista svih korisnika iz PostgreSQL.
- GET /api/admin/documents - lista indeksiranih dokumenata iz Qdrant-a,
  grupisana po source-u.
- DELETE /api/admin/documents/source/{source_name} - briše sve chunkove
  za dati source iz Qdrant-a. Invalidira BM25 cache.
- DELETE /api/admin/documents/{point_id} - briše jedan point.
- POST /api/admin/documents/upload - upload fajla (PDF, DOCX, TXT, MD,
  CSV) sa izborom required_role_id (1-3).
  * Za PDF/ DOCX/PPTX: LlamaParse (result_type=markdown) + MarkdownNodeParser
    (čuva tabele i strukturu)
  * Za TXT/MD/CSV: SimpleDirectoryReader + SentenceSplitter (chunk_size=1024)
  Fajl se indeksira u Qdrant, zatim briše sa diska. Ograničenje: 50MB.

--- core/config.py ---
- Pydantic Settings klasa, učitava .env fajl.
- Ključne varijable:
  - DATABASE_URL: PostgreSQL konekcioni string
  - JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
  - QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_EMBEDDING_DIM
  - OPENAI_API_KEY, LLAMA_CLOUD_API_KEY
  - CORS_ORIGINS, UPLOAD_DIR
- Baca ValueError ako DATABASE_URL nije postavljen.

--- core/db.py ---
- create_engine(SQLAlchemy) sa DATABASE_URL i echo=True (SQL logovanje).
- get_session() generator funkcija za FastAPI Depends().

--- core/security.py ---
- Učitava JWT parametre iz settings.
- create_access_token(data): kreira JWT sa exp (vreme isteka).
- oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login").

--- core/logger.py ---
- setup_logging(): konfiguriše root logger sa konzolnim handlerom.
- Format: vreme | ime_logera | nivo | poruka.
- Zaštićen od duplog pozivanja.

--- rag/engine.py ---
- GLOBALNA KONFIGURACIJA: OpenAI embedding model (text-embedding-3-small,
  dim=1536) i OpenAI LLM (gpt-4o-mini) sa temperature=0.1,
  max_tokens=300. API ključ se prosleđuje eksplicitno.
- LAZY INICIJALIZACIJA: Qdrant klijent i indeks se inicijalizuju
  tek pri prvom pozivu get_chat_engine() (omogućava main.py da
  startuje Qdrant pre importa engine modula).
- BM25 docstore: Gradi SimpleDocumentStore iz Qdrant payload-a.
  Parsira _node_content JSON da izvuče tekst i metapodatke.
- HybridRetriever klasa:
  - Kombinuje vektorski retriever (Qdrant, sa MetadataFilters za RBAC)
    i BM25 retriever (keyword pretraga).
  - RBAC: BM25 ne podržava MetadataFilters direktno, pa se RBAC
    primenjuje naknadnim filtriranjem (required_role_id).
  - Admin (is_admin=True) preskače RBAC filter.
  - RRF (Reciprocal Rank Fusion) spaja rezultate sa k=60.
  - Deduplikacija po normalizovanom tekstu (case-insensitive, bez
    višestrukih razmaka).
- Chat memorija:
  - Ako je prosleđen SQLModel Session: učitava istoriju iz PostgreSQL.
  - Ako nije: in-memory ChatMemoryBuffer po username-u.
- get_chat_engine() vraća CondensePlusContextChatEngine sa system_prompt,
  hybrid retrieverom i memorijom.

--- rag/chat_history.py ---
- load_chat_history(): učitava poslednjih 50 poruka iz PostgreSQL.
- save_chat_messages(): čuva user i assistant poruke u bazu.

--- rag/system_prompt.py ---
- Detaljan sistemski prompt na srpskom jeziku.
- Ključna pravila: odgovarati ISKLJUČIVO na osnovu konteksta.
- Ako odgovor nije u kontekstu: "Nemam taj podatak u bazi znanja."
- Zabranjeno izmišljanje modela, cena, specifikacija.

--- models/user.py ---
- SQLModel tabela: id, username (unique), hashed_password, role_id,
  role_name, is_admin.
- role_id: 1=Kupac, 2=Prodavac, 3=Serviser.
- is_admin: ortogonalno na role_id (admin može biti bilo koja rola).

--- models/chat_history.py ---
- SQLModel tabela: id, username, role (user/assistant), content, created_at.

--- main.py (Qdrant auto-migracija) ---
- Kolekcija se kreira automatski pri startu ako ne postoji (size=1536).
- Ako postoji sa pogrešnom dimenzijom (npr. starih 384), briše se i
  kreira nova (auto-migracija pri promeni embedding modela).

==============================================================================
4. RBAC (ROLE-BASED ACCESS CONTROL) SISTEM
==============================================================================

- required_role_id na svakom dokumentu/chunku definiše minimalnu ulogu.
- Filter: required_role_id <= user_role_id (LTE operator).
- Kupac (role_id=1): vidi samo Javne specifikacije.
- Prodavac (role_id=2): vidi Javne specifikacije + Interni cenovnik.
- Serviser (role_id=3): vidi sva 3 dokumenta.
- Admin (is_admin=true): vidi SVE bez obzira na role_id.

==============================================================================
5. INSTALACIJA I POKRETANJE
==============================================================================

PostgreSQL (lokalni):
- Port: 5433 (EDB installer default)
- Korisnik: postgres
- Lozinka: admin123
- Baza: postgres

Backend:
  cd backend
  uv sync
  # podesi .env sa DATABASE_URL, OPENAI_API_KEY, LLAMA_CLOUD_API_KEY,
  #   JWT_SECRET_KEY, QDRANT_URL, QDRANT_API_KEY
  uv run fastapi dev main.py --port 8000

Qdrant kolekcija se kreira automatski pri prvom pokretanju.
Dokumenti se upload-uju kroz admin panel (POST /api/admin/documents/upload).

Frontend:
  cd frontend
  npm install
  npm run dev

Test korisnici (bcrypt hash-ovane lozinke):
  admin / admin123 (role_id=3, is_admin=true)
  serviser / 123 (role_id=3, Technician)
  prodavac / 123 (role_id=2, Sales)
  kupac / 123 (role_id=1, Customer)

==============================================================================
6. ISTORIJA IZMENA
==============================================================================

2026-07-20 - Inicijalna struktura fajla
- Opisana kompletna backend arhitektura.

2026-07-20 (Migracija: Supabase -> Lokalni PostgreSQL):
- Zamenjen DATABASE_URL iz Supabase u lokalni PostgreSQL (port 5433).
- Ažuriran .env.example sa svim ključevima.
- Seed korisnici prebačeni na lokalnu bazu.

2026-07-20 (Dodat bcrypt hashing):
- Lozinke se hashiraju pre čuvanja (bcrypt.hashpw + gensalt).
- Login proverava sa bcrypt.checkpw().
- Stari plain-text korisnici obrisani i ponovo kreirani sa hash-ovima.

2026-07-20 (Popravljen linting i formatiranje):
- Fix E402 u main.py (importi rutera premešteni na vrh fajla).
- Pokrenut ruff format na svim fajlovima.
- Svi linting/format checkovi prolaze (ruff check, ruff format --check, mypy).

==============================================================================
KRAJ DOKUMENTACIJE
==============================================================================
"""

    # 1. Sačuvaj u export folderu
    output_path = EXPORT_DIR / "objasnjenje_backend.txt"
    output_path.write_text(content, encoding="utf-8")
    print(f"✅ objasnjenje_backend.txt kreiran ({output_path})")

    # 2. Kopiraj na E:\\chatbot
    dest_path = Path("E:/chatbot/objasnjenje_backend.txt")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(content, encoding="utf-8")
    print(f"✅ Kopiran na {dest_path}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Generisanje export fajlova...")
    print("=" * 60)

    # Kreiraj export folder ako ne postoji
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    write_backend_export()
    write_frontend_export()
    write_objasnjenje()

    # Velicine fajlova
    print("\n" + "=" * 60)
    print("Pregled generisanih fajlova:")
    for f in ["backend_kodovi.txt", "frontend_kodovi.txt", "objasnjenje_backend.txt"]:
        fp = EXPORT_DIR / f
        if fp.exists():
            kb = fp.stat().st_size / 1024
            print(f"  {f}: {kb:.1f} KB")
    print("=" * 60)
