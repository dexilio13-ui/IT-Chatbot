# 💻 RAG Chatbot

Modularni RAG (Retrieval-Augmented Generation) chatbot sistem za IT hardversku tehničku podršku i prodaju. Korisnici se prijavljuju, postavljaju pitanja, a sistem odgovara isključivo na osnovu dokumentacione baze znanja.

---

##   Sadržaj

1. [Tehnologije] 
2. [Arhitektura sistema] 
3. [Chunkovanje, Parsiranje, LLM i Embedding] 
4. [Backend – Uputstvo za pokretanje] 
5. [Frontend – Uputstvo za pokretanje] 
6. [Kako testirati sistem] 
7. [Autentifikacija i role_id] 
8. [Bezbednosne funkcije (status implementacije)] 
9. [Citiranje izvora (citations) – status] 
10. [Buduća unapređenja] 

---

##  Tehnologije

### Backend (Python 3.12)

| Tehnologija | Svrha |
|---|---|
| **FastAPI** | Web framework za REST API – brz, asinhron, sa automatskom OpenAPI/Swagger dokumentacijom |
| **Uvicorn** | ASGI server za pokretanje FastAPI aplikacije |
| **LlamaIndex Core** | RAG framework – povezuje LLM sa vektorskom bazom za kontekstualne odgovore |
| **Groq** | LLM provajder – pokreće `llama-3.3-70b-versatile` model, izuzetno brz inference |
| **ChromaDB** | Vektorska baza podataka – čuva embeddovane chunkove dokumenata |
| **SentenceTransformers (BAAI/bge-small-en-v1.5)** | Lokalni embedding model – pretvara tekst u vektore |
| **PyJWT** | JSON Web Token autentifikacija |
| **python-dotenv** | Učitavanje `.env` konfiguracije |
| **python-multipart** | Podrška za OAuth2 form data login |

### Frontend (JavaScript)

| Tehnologija | Svrha |
|---|---|
| **Vite** | Build tool i dev server – izuzetno brz HMR (Hot Module Replacement), moderna zamena za Webpack |
| **React 18** | UI biblioteka – komponentna arhitektura, deklarativno renderovanje, useState/useEffect hook-ovi |
| **Tailwind CSS** | Utility-first CSS framework – brzo dizajniranje UI-ja bez pisanja custom CSS-a, konzistentan dizajn sistem |
| **Axios** | HTTP klijent – automatsko dodavanje JWT tokena, centralizovana obrada grešaka (401, 429) |

#### Zašto baš ove frontend tehnologije?

- **Vite** – Donosi brže vreme pokretanja i reload u odnosu na starije alate. Koristi ES module direktno u browser-u tokom development-a.
- **React** – Standard izbora za moderne SPA aplikacije. Veliki ekosistem, lako održavanje kroz komponente, i odlična podrška za asinhrone tokove u ovom slučaju (chatbot).
- **Tailwind CSS** – Ubrzava UI development kroz predefinisane utility klase. PurgeCSS automatski uklanja neiskorišćene stilove pri build-u.

---

##  Arhitektura sistema

```
Korisnik (Browser)
    │
    ├── Login → POST /api/auth/login ────────────► JWT token
    │                                                  │
    │                                                  ▼
    └── Chat  → POST /api/chat (sa Bearer token) ──► FastAPI
                                                            │
                                                     ┌──────┴──────┐
                                                     │  Auth Check  │
                                                     │ get_current_ │
                                                     │    user()    │
                                                     └──────┬──────┘
                                                            │
                                                     ┌──────▼──────┐
                                                     │ LlamaIndex  │
                                                     │ Chat Engine │
                                                     └──────┬──────┘
                                                            │
                                              ┌─────────────┼─────────────┐
                                              ▼             ▼             ▼
                                        ┌─────────┐  ┌─────────┐  ┌─────────┐
                                        │ Groq    │  │ChromaDB │  │Uploads  │
                                        │  LLM    │  │Vector   │  │Folder   │
                                        └─────────┘  │  Store  │  │(.md)    │
                                                     └─────────┘  └─────────┘
```

### Tok podataka:

1. Korisnik se prijavljuje → backend kreira JWT token sa `username` i `role_id`
2. Frontend čuva token u `localStorage` i šalje ga u `Authorization: Bearer` header-u
3. Pri svakoj poruci, FastAPI proverava token preko `get_current_user()` dependency-ja
4. Poruka ide u LlamaIndex chat engine koji:
   - Pretvara pitanje u vektor (embedding)
   - Pretražuje ChromaDB za najsličnije chunkove
   - Prosleđuje kontekst + pitanje Groq LLM-u
   - LLM generiše odgovor **isključivo** na osnovu priloženog konteksta
5. Odgovor se vraća frontendu kao JSON

---

##  Chunkovanje, Parsiranje, LLM i Embedding Model

### Parsiranje dokumenata

- **Alat:** `SimpleDirectoryReader` iz LlamaIndex-a
- **Podržani formati:** `.txt`, `.md`, `.pdf`, `.csv`, `.docx` i drugi (automatski detektuje)
- **Lokacija:** `backend/uploads/`
- **Proces:** Pri prvom pokretanju, svi fajlovi iz `uploads/` foldera se učitavaju, chunkuju i embedduju u ChromaDB

### Chunkovanje

- **Parser:** `SentenceSplitter`
- **Veličina chunka (chunk_size):** 1024 karaktera
- **Preklapanje (chunk_overlap):** 200 karaktera
- **Zašto:** Manji chunkovi su precizniji za IT hardverska pitanja nego LlamaIndex-ove podrazumevane vrednosti (1024/200). Preklapanje osigurava da kontekst nije izgubljen na granicama chunkova.

### LLM (Large Language Model)

- **Provajder:** Groq
- **Model:** `llama-3.3-70b-versatile`
- **Temperatura:** 0.5 (balans između kreativnosti i preciznosti)
- **Max tokena:** 1024
- **API ključ:** Postavlja se u `.env` fajl kao `GROQ_API_KEY`
- **Konfiguracija:** `backend/rag/engine.py` → `Settings.llm = Groq(...)`

### Embedding model

- **Model:** `local:BAAI/bge-small-en-v1.5`
- **Tip:** Lokalni (ne zahteva API ključ)
- **Veličina:** Mali i brz model (~30MB), odličan za semantičko pretraživanje
- **Konfiguracija:** `backend/rag/engine.py` → `Settings.embed_model = "local:BAAI/bge-small-en-v1.5"`

### Memorija

- **Tip:** `ChatMemoryBuffer`
- **Limit:** 3000 tokena
- **Mod rada:** `condense_plus_context` – sažima istoriju razgovora i dodaje je kontekstu
- **Sistemski prompt:** `backend/rag/system_prompt.py` – definiše pravila ponašanja bota

### Vektorska baza (ChromaDB)

- **Lokacija:** `backend/chroma_db/`
- **Kolekcija:** `it_hardver_baza`
- **Perzistencija:** Automatska – podaci ostaju sačuvani između restartovanja
- **Duplikacija:** **Sprečena** – pre ponovnog indeksiranja proverava se broj postojećih vektora

---

##  Backend – Uputstvo za pokretanje

### Preduslovi

- Python 3.12+
- UV package manager (`pip install uv` ili `pipx install uv`)

### Koraci

```bash
# 1. Klonirati repozitorijum
git clone <repo-url>
cd chatbot_app/backend

# 2. Kreirati .env fajl
echo "GROQ_API_KEY=tvoj-groq-api-kljuc" > .env

# 3. Instalirati zavisnosti
uv sync

# 4. Dodati dokumente u uploads folder
# Stavi .md, .txt, .pdf fajlove u: backend/uploads/

# 5. Pokrenuti server
uv run uvicorn main:app --reload
             ili
uv run fastapi dev backend/main.py
```

Backend je dostupan na: **http://localhost:8000**

### API Endpointi

| Metod | Ruta | Opis |
|---|---|---|
| `POST` | `/api/auth/login` | Prijava (username + password) → vraća JWT token |
| `POST` | `/api/chat` | Slanje poruke (zahteva Bearer token) |
| `GET`  | `/` | Health check |
| `GET`  | `/docs` | Swagger UI dokumentacija |

### Test nalozi

| Username | Password | role_id | Uloga |
|---|---|---|---|
| `serviser` | `123` | 3 | Technician |
| `prodavac` | `123` | 2 | Sales |
| `kupac`    | `123` | 1 | Customer |

### Konfiguracija (fajlovi)

- `backend/core/security.py` – JWT podešavanja (SECRET_KEY, ALGORITHM, token expiration)
- `backend/rag/engine.py` – RAG engine (LLM, embedding, chunking, ChromaDB)
- `backend/rag/system_prompt.py` – Sistemski prompt sa pravilima ponašanja
- `backend/api/auth.py` – Auth ruta sa dummy bazom korisnika
- `backend/api/chat.py` – Chat ruta sa JWT verifikacijom

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

Staticki fajlovi se generisu u `frontend/dist/` folderu.

### Struktura frontend koda

| Fajl | Opis |
|---|---|
| `src/App.jsx` | Glavna komponenta – uslovno prikazuje LoginForm ili ChatBox |
| `src/components/LoginForm.jsx` | Forma za prijavu (username + password) |
| `src/components/ChatBox.jsx` | Chat interfejs – poruke, input, slanje |
| `src/context/AuthContext.jsx` | Auth provider – upravlja JWT tokenom, login/logout logika |
| `src/services/api.js` | Axios instanca – automatski dodat token, centralizovana obrada grešaka |

---

##   Kako testirati sistem

### 1. Pokrenuti oba servera

```bash
# Terminal 1 - Backend
cd backend
uv run uvicorn main:app --reload

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

### 3. Testiranje preko frontenda

1. Otvoriti: **http://localhost:5173**
2. Prijaviti se sa `serviser` / `123`
3. Postaviti pitanje u chat polju

### 4. Unit testovi (ako su implementirani)

```bash
cd backend
uv run pytest
```

### 5. Type checking

```bash
cd backend
uv run mypy .
```

### 6. Lint

```bash
cd backend
uv run ruff check .
```

---

## 🔐 Autentifikacija i role_id

### ✅ Implementirano

- **JWT autentifikacija** kompletno radi
- **role_id se čuva u tokenu:** `backend/api/auth.py` linija 31
- **role_id se izvlači iz tokena:** `backend/api/chat.py` u `get_current_user()` dependency-ju
- **Token expiration:** 60 minuta od kreiranja
- **Tri test naloga** sa različitim `role_id` vrednostima (1 = Kupac, 2 = Prodavac, 3 = Serviser)

### ❌ Nije implementirano (planirano)

- **Filtriranje dokumenata po role_id** – Trenutno svi ulogovani korisnici imaju pristup **svim dokumentima** u `uploads/` folderu
- U `chat.py` postoji komentar:
  ```python
  # Kasnije cemo current_user['role_id'] prosledjivati LlamaIndexu za filtriranje!
  ```
- **Plan:** Potrebno je označiti dokumente sa dozvoljenim `role_id` (metadata) i proslediti filter u ChromaDB query

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
- Pratiti broj neuspešnih login pokušaja po IP adresi (npr. u memoriji ili Redis-u)
- Nakon 3 neuspešna pokušaja, zahtevati CAPTCHA verifikaciju
- Frontend već ima pripremljenu logiku za prikaz CAPTCHA poruke (`captcha_required` flag)

### 3. Logovanje svih neuspešnih pokušaja

| Status | Detalji |
|---|---|
| ❌ **Nije implementirano** | Nema evidencije neuspešnih login pokušaja |

**Šta je potrebno za implementaciju:**
- Dodati `loguru` ili koristiti Python `logging` modul
- Logovati: IP adresu, username, vreme, razlog neuspeha
- Opciono: čuvati u fajlu (`failed_logins.log`) ili bazi podataka

---

## 📚 Citiranje izvora (Citations) – Status

| Status | Detalji |
|---|---|
| ❌ **Nije implementirano** | Chat odgovori ne sadrže reference na izvorne dokumente |

**Šta je planirano:**
- Prikazati iz kog dokumenta i iz kog chunka je preuzet odgovor
- Dodati metapodatke uz svaki odgovor (naziv fajla, strana, pozicija u dokumentu)
- Omogućiti korisniku da klikne na izvor i vidi originalni kontekst

**Kako će biti implementirano (ubuduće):**
- U `engine.py`, prilikom query-ja, sačuvati `source_nodes` iz LlamaIndex odgovora
- Proslediti metapodatke uz `response` u chat endpointu
- Prikazati ih na frontendu kao linkove ili hover kartice

---

## 🚀 Šta su moguća unapređenja

**Role-based filtriranje dokumenata** – ograničiti pristup dokumentima po `role_id`
**Rate limiting** – zaštita od brute-force napada
**CAPTCHA** – posle više neuspešnih pokušaja
**Logging** – evidencija svih neuspešnih prijava
**Citations** – prikazivanje izvora uz svaki odgovor
**SSE striming** – postepeno prikazivanje odgovora (kao ChatGPT)
**PostgreSQL + SQLModel** – zameniti dummy bazu pravom bazom
**.env konfiguracija** – prebaciti SECRET_KEY i ostale parametre u `.env`
**Docker** – kontejnerizacija celog sistema
**Admin panel** – upravljanje dokumentima i korisnicima

---

## 📁 Struktura projekta

```
chatbot_app/
├── backend/
│   ├── api/
│   │   ├── auth.py          # Auth ruta (login, JWT)
│   │   ├── chat.py          # Chat ruta (RAG)
│   │   └── __init__.py
│   ├── chroma_db/           # Vektorska baza (perzistentna)
│   ├── core/
│   │   ├── security.py      # JWT konfiguracija
│   │   └── __init__.py
│   ├── rag/
│   │   ├── engine.py        # RAG engine (LlamaIndex)
│   │   ├── system_prompt.py # Sistemski prompt
│   │   └── __init__.py
│   ├── uploads/             # Dokumenti za indeksiranje
│   ├── main.py              # FastAPI app
│   └── pyproject.toml       # Python zavisnosti
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatBox.jsx      # Chat interfejs
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


