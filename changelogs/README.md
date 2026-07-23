# 💻 IT Asistent — RAG Chatbot

Modularni RAG (Retrieval-Augmented Generation) chatbot sistem za IT hardversku tehničku podršku i prodaju. Korisnici se prijavljuju, postavljaju pitanja, a sistem odgovara isključivo na osnovu dokumentacione baze znanja, uz poštovanje pristupnih prava po ulozi (RBAC) i prikaz izvora odgovora.

---

##   Sadržaj

1. [Tehnologije]
2. [Arhitektura sistema]
3. [Chunkovanje, Parsiranje, LLM i Embedding]
4. [Backend – Uputstvo za pokretanje]
5. [Frontend – Uputstvo za pokretanje]
6. [Kako testirati sistem]
7. [Autentifikacija, RBAC i role_id]
8. [Bezbednosne funkcije (status implementacije)]
9. [Citiranje izvora (citations) – status]
10. [Buduća unapređenja]
11. [Struktura projekta]

---

##  Tehnologije

### Backend (Python 3.12)

| Tehnologija | Svrha |
|---|---|
| **FastAPI** | Web framework za REST API – brz, asinhron, sa automatskom OpenAPI/Swagger dokumentacijom |
| **Uvicorn** | ASGI server za pokretanje FastAPI aplikacije |
| **LlamaIndex Core** | RAG framework – hibridni retriever (vektor + BM25), chat engine sa memorijom |
| **OpenAI** | LLM (`gpt-4o-mini`) i embedding model (`text-embedding-3-small`, dim=1536) |
| **LlamaParse** | Parsiranje strukturiranih dokumenata (PDF, DOCX, PPTX) – čuva tabele i strukturu |
| **Qdrant Cloud** | Vektorska baza podataka – čuva embeddovane chunkove dokumenata |
| **PostgreSQL 18 + SQLModel** | Relaciona baza – korisnici, uloge i istorija razgovora |
| **bcrypt** | Bezbedno hashiranje lozinki |
| **PyJWT** | JSON Web Token autentifikacija (HS256, istek 60 min) |
| **pydantic-settings** | Centralizovano učitavanje `.env` konfiguracije |
| **python-multipart** | Podrška za OAuth2 form data login i upload fajlova |

### Frontend (JavaScript)

| Tehnologija | Svrha |
|---|---|
| **Vite** | Build tool i dev server – izuzetno brz HMR (Hot Module Replacement), moderna zamena za Webpack |
| **React 18** | UI biblioteka – komponentna arhitektura, deklarativno renderovanje, useState/useEffect hook-ovi |
| **Tailwind CSS** | Utility-first CSS framework – brzo dizajniranje UI-ja bez pisanja custom CSS-a, konzistentan dizajn sistem |
| **Axios** | HTTP klijent – automatsko dodavanje JWT tokena, centralizovana obrada grešaka (401, 429) |

#### Zašto baš ove frontend tehnologije?

- **Vite** – Donosi brže vreme pokretanja i reload u odnosu na starije alate. Koristi ES module direktno u browser-u tokom development-a.
- **React** – Standard izbora za moderne SPA aplikacije. Veliki ekosistem, lako održavanje kroz komponente, i odlična podrška za asinhrone tokove (SSE streaming chat odgovora).
- **Tailwind CSS** – Ubrzava UI development kroz predefinisane utility klase. PurgeCSS automatski uklanja neiskorišćene stilove pri build-u.

---

##  Arhitektura sistema

```
Korisnik (Browser)
    │
    ├── Login → POST /api/auth/login ────────────► JWT token (username, role_id, is_admin)
    │                                                  │
    │                                                  ▼
    └── Chat  → POST /api/chat/stream (SSE) ──────► FastAPI
                (Bearer token)                              │
                                                       ┌──────┴──────┐
                                                       │  Auth Check  │
                                                       │ get_current_ │
                                                       │    user()    │
                                                       └──────┬──────┘
                                                              │
                                                       ┌──────▼──────┐
                                                       │ LlamaIndex  │
                                                       │ Hybrid RAG  │
                                                       │   Engine    │
                                                       └──────┬──────┘
                                                              │
                                    ┌─────────────┬───────────┼───────────┬─────────────┐
                                    ▼             ▼           ▼           ▼             ▼
                              ┌─────────┐  ┌───────────┐┌─────────┐┌───────────┐ ┌───────────┐
                              │ OpenAI  │  │  Qdrant   ││  BM25   ││PostgreSQL │ │  Admin    │
                              │gpt-4o-  │  │  Cloud    ││Keyword  ││(users +   │ │  Panel    │
                              │  mini   │  │ (vektor,  ││Retriever││ istorija) │ │ (upload,  │
                              │         │  │dim=1536)  ││         ││           │ │ RBAC role)│
                              └─────────┘  └───────────┘└─────────┘└───────────┘ └───────────┘
```

### Tok podataka:

1. Korisnik se prijavljuje → backend proverava bcrypt hash lozinke u PostgreSQL, kreira JWT token sa `username`, `role_id` i `is_admin`
2. Frontend čuva token u `localStorage` i šalje ga u `Authorization: Bearer` header-u
3. Pri svakoj poruci, FastAPI proverava token preko `get_current_user()` dependency-ja
4. Poruka ide u LlamaIndex hybrid chat engine koji:
   - Pretvara pitanje u vektor (OpenAI `text-embedding-3-small`)
   - Paralelno pretražuje Qdrant (semantički) i BM25 (ključne reči), sa RBAC filterom `required_role_id <= role_id`
   - Kombinuje rezultate kroz Reciprocal Rank Fusion (RRF) i deduplikuje
   - Prosleđuje kontekst + istoriju razgovora + pitanje OpenAI `gpt-4o-mini` modelu
   - LLM generiše odgovor **isključivo** na osnovu priloženog konteksta
5. Odgovor se strimuje frontendu token-po-token (SSE), a na kraju se šalje i najbolji izvor (naziv, sadržaj, skor relevantnosti)

---

##  Chunkovanje, Parsiranje, LLM i Embedding Model

### Parsiranje dokumenata

Dokumenti se dodaju **isključivo kroz admin panel** (`POST /api/admin/documents/upload`), ne više automatskim učitavanjem foldera pri startu.

- **Strukturirani formati (`.pdf`, `.docx`, `.doc`, `.pptx`):** `LlamaParse` (`result_type="markdown"`) + `MarkdownNodeParser` – čuva tabele i strukturu dokumenta netaknutom
- **Ravni tekst (`.txt`, `.md`, `.csv`):** `SimpleDirectoryReader` + `SentenceSplitter`
- **Ograničenje veličine fajla:** 50 MB
- **Privremeno čuvanje:** fajl se snima na disk sa UUID prefiksom, indeksira, pa se briše – trajni zapis je isključivo u Qdrant-u

### Chunkovanje

- **Parser (za .txt/.md/.csv):** `SentenceSplitter`
- **Veličina chunka (chunk_size):** 1024 karaktera
- **Preklapanje (chunk_overlap):** 200 karaktera
- **Za PDF/DOCX/PPTX:** `MarkdownNodeParser` deli po markdown strukturi (naslovi, tabele) umesto po fiksnoj dužini

### LLM (Large Language Model)

- **Provajder:** OpenAI
- **Model:** `gpt-4o-mini`
- **Temperatura:** 0.1 (visoka preciznost, minimalna kreativnost)
- **Max tokena:** 300 (`Settings.num_output` dodatno duplira ovo ograničenje)
- **API ključ:** `.env` → `OPENAI_API_KEY`
- **Konfiguracija:** `backend/rag/engine.py` → `Settings.llm = OpenAI(...)`

### Embedding model

- **Model:** `text-embedding-3-small` (OpenAI)
- **Dimenzija:** 1536
- **API ključ:** `.env` → `OPENAI_API_KEY`
- **Konfiguracija:** `backend/rag/engine.py` → `Settings.embed_model = OpenAIEmbedding(...)`
- **Auto-migracija:** Ako Qdrant kolekcija postoji sa pogrešnom dimenzijom (npr. stara 384 od prethodnog lokalnog modela), backend je automatski briše i ponovo kreira pri startu (`main.py` lifespan)

### Hibridna pretraga (Hybrid Retrieval)

- **Vektorska pretraga:** Qdrant, semantička sličnost, RBAC filter (`required_role_id <= role_id`)
- **BM25 pretraga:** ključne reči, RBAC se primenjuje naknadnim filtriranjem (BM25 ne podržava MetadataFilters direktno)
- **Spajanje rezultata:** Reciprocal Rank Fusion (RRF, k=60) – koristi se isključivo za rangiranje
- **Prikaz relevantnosti:** originalni cosine similarity skor iz vektorskog retrievera (0–100%), dodatno ograničen (`_clamp_score`) da nikad ne pređe 100%
- **Deduplikacija:** po normalizovanom tekstu chunka

### Memorija

- **Tip:** `ChatMemoryBuffer` (in-memory po username-u) ili istorija iz PostgreSQL, ako je dostupna sesija
- **Mod rada:** `condense_plus_context` – sažima istoriju razgovora i dodaje je kontekstu
- **Perzistencija:** poslednjih 50 poruka po korisniku čuva se u PostgreSQL (`ChatHistory` tabela)
- **Sistemski prompt:** `backend/rag/system_prompt.py` – definiše pravila ponašanja bota (odgovara isključivo iz konteksta, ne izmišlja podatke)

### Vektorska baza (Qdrant Cloud)

- **Kolekcija:** konfigurisano preko `QDRANT_COLLECTION` (npr. `it_support_kb`)
- **Payload indeksi:** `source` (keyword) i `required_role_id` (integer) – kreiraju se automatski pri startu
- **Upravljanje:** kroz admin panel (upload, brisanje po source-u ili po ID-ju)

---

##  Backend – Uputstvo za pokretanje

### Preduslovi

- Python 3.12+
- UV package manager (`pip install uv` ili `pipx install uv`)
- PostgreSQL 18 (lokalno, port 5433 preporučeno) ili drugi PostgreSQL server
- OpenAI API ključ
- LlamaCloud API ključ (za LlamaParse)
- Qdrant Cloud instanca (ili lokalni Qdrant kontejner)

### Koraci

```bash
# 1. Klonirati repozitorijum
git clone <repo-url>
cd chatbot_app/backend

# 2. Kreirati .env fajl
cat <<EOF > .env
DATABASE_URL=postgresql://postgres:admin123@localhost:5433/postgres
JWT_SECRET_KEY=tvoja-super-tajna-sifra-za-jwt-32bita
OPENAI_API_KEY=tvoj-openai-api-kljuc
LLAMA_CLOUD_API_KEY=tvoj-llamacloud-api-kljuc
QDRANT_URL=https://tvoj-qdrant-cluster.cloud.qdrant.io
QDRANT_API_KEY=tvoj-qdrant-api-kljuc
QDRANT_COLLECTION=it_support_kb
EOF

# 3. Instalirati zavisnosti
uv sync

# 4. Pokrenuti server (kolekcija u Qdrant-u se kreira/migrira automatski)
uv run fastapi dev main.py --port 8000
             ili
uv run uvicorn main:app --reload

# 5. Dodati dokumente kroz admin panel (Swagger UI ili frontend)
# POST /api/admin/documents/upload (potreban admin token)
```

Backend je dostupan na: **http://localhost:8000**

### API Endpointi

| Metod | Ruta | Opis |
|---|---|---|
| `POST` | `/api/auth/login` | Prijava (username + password) → vraća JWT token |
| `POST` | `/api/chat` | Slanje poruke, sinhroni odgovor (zahteva Bearer token) |
| `POST` | `/api/chat/stream` | Slanje poruke, SSE streaming odgovor (zahteva Bearer token) |
| `GET`  | `/api/admin/users` | Lista svih korisnika (samo admin) |
| `GET`  | `/api/admin/documents` | Lista indeksiranih dokumenata iz Qdrant-a (samo admin) |
| `POST` | `/api/admin/documents/upload` | Upload i indeksiranje novog dokumenta (samo admin) |
| `DELETE` | `/api/admin/documents/source/{source_name}` | Brisanje svih chunkova za dati dokument (samo admin) |
| `DELETE` | `/api/admin/documents/{point_id}` | Brisanje jednog chunka (samo admin) |
| `GET`  | `/` | Health check |
| `GET`  | `/docs` | Swagger UI dokumentacija |

### Test nalozi

| Username | Password | role_id | Uloga | is_admin |
|---|---|---|---|---|
| `admin`     | `admin123` | 3 | Admin | ✅ |
| `serviser` | `123` | 3 | Technician | ❌ |
| `prodavac` | `123` | 2 | Sales | ❌ |
| `kupac`    | `123` | 1 | Customer | ❌ |

### Konfiguracija (fajlovi)

- `backend/core/config.py` – Sve `.env` promenljive (JWT, PostgreSQL, Qdrant, OpenAI, LlamaCloud)
- `backend/core/security.py` – JWT podešavanja (kreiranje tokena)
- `backend/rag/engine.py` – RAG engine (LLM, embedding, hibridni retriever, RRF)
- `backend/rag/system_prompt.py` – Sistemski prompt sa pravilima ponašanja
- `backend/api/auth.py` – Login ruta sa bcrypt proverom naspram PostgreSQL baze
- `backend/api/chat.py` – Chat rute (sync + SSE) sa JWT verifikacijom
- `backend/api/admin.py` – Admin rute (upload, brisanje, listanje dokumenata)

---

##   Frontend – Uputstvo za pokretanje

### Preduslovi

- Node.js 18+
- npm ili pnpm

### Koraci

```bash
# 1. Navigirati do frontend foldera
cd frontend

# 2. Instalirati zavisnosti
npm install

# 3. (Opcijalno) Podesiti API URL u .env fajlu
echo "VITE_API_URL=http://localhost:8000" > .env

# 4. Pokrenuti dev server
npm run dev
```

Frontend je dostupan na: **http://localhost:5173**

### Build za produkciju

```bash
npm run build
```

Statički fajlovi se generišu u `frontend/dist/` folderu.

### Struktura frontend koda

| Fajl | Opis |
|---|---|
| `src/App.jsx` | Glavna komponenta – uslovno prikazuje LoginForm ili ChatBox |
| `src/components/LoginForm.jsx` | Forma za prijavu (username + password), prikazuje test naloge |
| `src/components/ChatBox.jsx` | Chat interfejs – poruke, SSE streaming, prikaz izvora i skora relevantnosti |
| `src/context/AuthContext.jsx` | Auth provider – upravlja JWT tokenom, login/logout logika |
| `src/services/api.js` | Axios instanca – automatski dodat token, centralizovana obrada grešaka |

---

##   Kako testirati sistem

### 1. Pokrenuti oba servera

```bash
# Terminal 1 - Backend
cd backend
uv run fastapi dev main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Testiranje preko Swagger UI (preporučeno)

1. Otvoriti: **http://localhost:8000/docs**
2. Kliknuti na `/api/auth/login` → "Try it out"
3. Uneti: `username = serviser`, `password = 123`
4. Kopirati dobijeni `access_token`
5. Kliknuti na "Authorize" dugme (gore desno) i uneti: `Bearer <token>`
6. Testirati `/api/chat` sa porukom npr. "Šta piše u servisnom priručniku?"

### 3. Testiranje RBAC filtriranja

1. Ulogovati se kao `kupac` (role_id=1) → postaviti pitanje o cenama → bot ne sme da vidi Interni cenovnik
2. Ulogovati se kao `prodavac` (role_id=2) → isto pitanje → bot treba da vidi i cenovnik
3. Ulogovati se kao `admin` → treba da vidi sve dokumente bez obzira na `required_role_id`

### 4. Testiranje preko frontenda

1. Otvoriti: **http://localhost:5173**
2. Prijaviti se sa `serviser` / `123`
3. Postaviti pitanje u chat polju i pratiti streaming odgovor uživo
4. Kliknuti na prikazani izvor da vidiš ceo tekst chunka i skor relevantnosti

### 5. Testiranje admin panela

1. Ulogovati se kao `admin` / `admin123`
2. Upload-ovati novi dokument (PDF, DOCX, TXT, MD ili CSV) sa izabranim `required_role_id`
3. Proveriti listu dokumenata (`GET /api/admin/documents`)
4. Obrisati dokument po source-u ili pojedinačnom chunku

### 6. Unit testovi

```bash
cd backend
uv run pytest tests/ -v
```

### 7. Type checking

```bash
cd backend
uv run mypy .
```

### 8. Lint

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
```

---

## 🔐 Autentifikacija, RBAC i role_id

### ✅ Implementirano

- **JWT autentifikacija** kompletno radi, lozinke se čuvaju kao **bcrypt hash** (ne plain-text)
- **role_id i is_admin se čuvaju u tokenu:** `backend/api/auth.py`
- **role_id se izvlači iz tokena:** `backend/api/chat.py` u `get_current_user()` dependency-ju
- **Token expiration:** 60 minuta od kreiranja (podesivo u `.env`)
- **Četiri test naloga** sa različitim `role_id` i `is_admin` vrednostima (1=Kupac, 2=Prodavac, 3=Serviser, + admin)
- **Filtriranje dokumenata po role_id JE implementirano** – `required_role_id <= role_id` filter se primenjuje i na vektorskoj (MetadataFilters) i na BM25 pretrazi (naknadno filtriranje)
- **Admin nalozi (`is_admin=true`) preskaču RBAC filter u potpunosti** i vide sve dokumente

---

## 🔒 Bezbednosne funkcije – Status implementacije

### 1. Rate limit (ograničenje broja pokušaja)

| Status | Detalji |
|---|---|
| ❌ **Nije implementirano na backend-u** | FastAPI nema rate limiting middleware |
| ⏳ **Frontend ima pripremu** | `api.js` i `AuthContext.jsx` već obrađuju HTTP 429 (Too Many Requests) status, ali backend ga nikad ne šalje |

**Šta je potrebno za implementaciju:**
- Dodati `slowapi` ili `fastapi-limiter` paket
- Konfigurisati rate limit na `/api/auth/login` ruti (npr. maksimalno 5 pokušaja u minuti)
- Vratiti `429 Too Many Requests` sa opcionim `captcha_required` flag-om

### 2. CAPTCHA posle 3 neuspešna pokušaja

| Status | Detalji |
|---|---|
| ❌ **Nije implementirano** | Nema CAPTCHA integracije |

**Šta je potrebno za implementaciju:**
- Integrisati Google reCAPTCHA ili Cloudflare Turnstile
- Pratiti broj neuspešnih login pokušaja po IP adresi (u memoriji ili Redis-u)
- Nakon 3 neuspešna pokušaja, zahtevati CAPTCHA verifikaciju
- Frontend već ima pripremljenu logiku za prikaz CAPTCHA poruke (`captcha_required` flag)

### 3. Logovanje svih neuspešnih pokušaja

| Status | Detalji |
|---|---|
| ❌ **Nije implementirano** | Nema evidencije neuspešnih login pokušaja (postoji samo opšte logovanje kroz `core/logger.py`) |

**Šta je potrebno za implementaciju:**
- Logovati: IP adresu, username, vreme, razlog neuspeha kroz postojeći `logger` iz `core/logger.py`
- Opciono: čuvati u fajlu (`failed_logins.log`) ili posebnoj PostgreSQL tabeli

---

## 📚 Citiranje izvora (Citations) – Status

| Status | Detalji |
|---|---|
| ✅ **Implementirano** | Svaki chat odgovor (sync i SSE) sadrži referencu na izvorni dokument |

**Kako radi:**
- Backend prosleđuje `source_nodes` iz LlamaIndex odgovora
- Prikazuje se **1 najbolji izvor** po odgovoru: naziv (`source`), potreban nivo pristupa (`required_role_id`), skor relevantnosti (`score`, ograničen na 0–100%) i sadržaj (prvih 2000 karaktera)
- Frontend (`ChatBox.jsx`) prikazuje izvor kao klikabilnu karticu – klikom se vidi ceo tekst chunka

**Istorija popravki skora relevantnosti:**
- Skor relevantnosti je prošao kroz tri iteracije popravki (RRF normalizacija → clamping kao safety net → konačno korišćenje cosine similarity skora za smislen prikaz po upitu). Detalji u internoj dokumentaciji `objasnjenje_backend.txt`.

**Moguća buduća proširenja:**
- Prikaz više od 1 izvora po odgovoru
- Highlight tačnog dela teksta iz kog je odgovor izveden

---

## 🚀 Šta su moguća unapređenja

- **Rate limiting** – zaštita od brute-force napada
- **CAPTCHA** – posle više neuspešnih pokušaja
- **Logging neuspešnih prijava** – evidencija svih neuspešnih login pokušaja
- **Prikaz više izvora** – trenutno se prikazuje samo 1 najbolji izvor po odgovoru
- **Docker** – kontejnerizacija celog sistema (backend + frontend + PostgreSQL)
- **Async obrada upload-a** – asinhrono indeksiranje velikih fajlova (npr. Celery + Redis)


---

## ✅ Implementirano

- **Role-based filtriranje dokumenata** (RBAC) po `role_id`
- **Citations** – prikazivanje izvora uz svaki odgovor, sa skorom relevantnosti
- **SSE streaming** – postepeno prikazivanje odgovora (kao ChatGPT)
- **PostgreSQL + SQLModel** – zamenjena dummy baza pravom relacionom bazom
- **bcrypt hashing lozinki** – zamenjen plain-text
- **`.env` konfiguracija** – svi tajni ključevi i parametri su u `.env`, ne u kodu
- **Admin panel** – upravljanje dokumentima (upload, listanje, brisanje) i korisnicima
- **Hibridna pretraga** (vektor + BM25 + RRF) umesto samo vektorske
- **LlamaParse** – strukturirano parsiranje PDF/DOCX/PPTX dokumenata (čuva tabele)

---

## 📁 Struktura projekta

```
chatbot_app/
├── backend/
│   ├── api/
│   │   ├── auth.py           # Auth ruta (login, JWT + bcrypt)
│   │   ├── chat.py           # Chat rute (sync + SSE, clamp skora)
│   │   ├── admin.py          # Admin rute (upload, brisanje, listanje)
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py         # Pydantic Settings (.env varijable)
│   │   ├── db.py             # PostgreSQL konekcija (SQLModel)
│   │   ├── security.py       # JWT kreiranje
│   │   ├── logger.py         # Centralizovano logovanje
│   │   └── __init__.py
│   ├── rag/
│   │   ├── engine.py         # RAG engine (hibridni retriever, RBAC, RRF)
│   │   ├── chat_history.py   # Učitavanje/čuvanje istorije iz PostgreSQL
│   │   ├── system_prompt.py  # Sistemski prompt
│   │   └── __init__.py
│   ├── models/
│   │   ├── user.py           # SQLModel: User tabela
│   │   ├── chat_history.py   # SQLModel: ChatHistory tabela
│   │   └── __init__.py
│   ├── uploads/               # Privremeni fajlovi za indeksiranje (brišu se posle)
│   ├── tests/                 # pytest testovi
│   ├── main.py                # FastAPI app, lifespan, Qdrant auto-migracija
│   └── pyproject.toml         # Python zavisnosti
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatBox.jsx      # Chat interfejs (streaming, izvori, skor)
│   │   │   └── LoginForm.jsx    # Login forma
│   │   ├── context/
│   │   │   └── AuthContext.jsx  # Auth state
│   │   ├── services/
│   │   │   └── api.js           # Axios konfiguracija
│   │   ├── App.jsx              # Glavna komponenta
│   │   ├── main.jsx             # React entry point
│   │   └── index.css            # Tailwind + custom stilovi
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
└── README.md
```
