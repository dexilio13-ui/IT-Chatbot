---
title: IT Asistent
emoji: 💻
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.25.0
app_file: app.py
pinned: false
license: mit
python_version: "3.10"
---

# 💻 IT Asistent — Konfigurator Racunara

RAG chatbot za tehnicku podrsku i konfiguraciju PC komponenti sa cenama.

---

## 📋 Sadrzaj

1. [Sta sve ume da radi](#-sta-sve-ume-da-radi)
2. [Kako pokrenuti na Hugging Face](#-kako-pokrenuti-na-hugging-face)
3. [Automatsko azuriranje cena (GitHub Action)](#-automatsko-azuriranje-cena-github-action)
4. [Sta je uradjeno do sada](#-sta-je-uradjeno-do-sada)
5. [Resavanje problema](#-resavanje-problema)
6. [Struktura projekta](#-struktura-projekta)

---

## 🎯 Sta sve ume da radi

| Funkcija | Sta mu kazes | Sta dobijes |
|----------|-------------|-------------|
| **Caskanje** | "Cao kako si?" | Prijateljski odgovor (temperatura 0.4) |
| **Tehnicka pitanja** | "Kako da instaliram Windows?" | Odgovor iz Qdrant baze znanja |
| **Konfiguracija** | "Napravi mi gaming PC do 800e" | Spisak komponenti sa cenama iz kataloga |
| **Cene** | "Koliko kosta RTX 4060?" | Trenutna cena iz komponente.json |
| **Kompatibilnost** | "Da li Ryzen 5 radi sa B550 plocom?" | Provera socket-a i DDR tipa |
| **Izvori (citations)** | Bilo koje pitanje | Prikazuje source dokument sa relevatnoscu |

### Pametna detekcija po poruci

Svaka poruka se klasifikuje **pojedinacno**:

| Poruka | Classified as | Temperatura | System prompt |
|--------|:------------:|:----------:|:-------------:|
| "Cao kako si?" | Caskanje | 0.4 | Relaksiran + chitchat |
| "Napravi mi PC do 800e" | Konfiguracija | 0.4 | Relaksiran + chitchat + katalog |
| "Kako da instaliram Windows?" | Tehnicko | 0.1 | Strogi RAG (samo iz baze) |
| "Koja je cena laptopa?" | Tehnicko | 0.1 | Strogi RAG (samo iz baze) |

---

## 🚀 Kako pokrenuti na Hugging Face

### Korak 1: Kreiraj Space

1. Idi na https://huggingface.co/new-space
2. Ime: `orion-chatbot` (ili sta zelis)
3. SDK: **Gradio**
4. Space Hardware: **ZeroGPU** (besplatno — Nvidia RTX Pro 6000 Blackwell)
   > ⚠️ **Vazno:** Besplatni HF nalozi ne mogu da koriste Gradio na CPU basic.
   > ZeroGPU je jedina besplatna opcija koja podrzava Gradio.
5. Klikni **Create Space**

### Korak 1b: Podesi ZeroGPU (ako si vec kreirao Space)

Ako si vec kreirao Space, uradi sledece:

1. Otvori Space → **Settings** tab
2. Na dnu, u sekciji **Hardware**, klikni **Configure Hardware**
3. Izaberi **ZeroGPU** (besplatno, NVIDIA RTX Pro 6000 Blackwell)
4. Klikni **Save** i sacekaj restart Space-a

### Korak 2: Upload fajlove

Upload-uj sledece fajlove i foldere u Space:

```
📁 backend/                    ← CEO backend folder iz projekta
   ├── __init__.py
   ├── rag/
   │   ├── __init__.py
   │   ├── engine.py
   │   ├── system_prompt.py
   │   ├── classifier.py
   │   ├── configurator.py
   │   └── chat_history.py
   ├── core/
   │   ├── __init__.py
   │   ├── config.py
   │   ├── db.py
   │   ├── logger.py
   │   └── security.py
   ├── api/
   │   ├── __init__.py
   │   ├── chat.py
   │   ├── auth.py
   │   └── admin.py
   ├── models/
   │   ├── __init__.py
   │   ├── user.py
   │   └── chat_history.py
   └── data/
       └── components.json     ← Sample katalog (dok ne stigne pravi sa Action)
📄 app.py                      ← Gradio aplikacija (iz hf/ foldera)
📄 requirements.txt            ← Python zavisnosti (iz hf/ foldera)
📄 README.md                   ← Ovaj fajl
```

### Korak 3: Podesi Secret varijable na HF

U **Settings → Repository Secrets** dodaj:

| Secret | Vrednost | Obavezno |
|--------|----------|:--------:|
| `OPENAI_API_KEY` | `sk-...` tvoj OpenAI API kljuc | ✅ DA |
| `QDRANT_URL` | URL QdrantCloud (npr. https://xyz.us-east-1-0.aws.cloud.qdrant.io:6333) | ✅ DA |
| `QDRANT_API_KEY` | API kljuc za Qdrant | ❌ Ne |
| `QDRANT_COLLECTION` | Ime kolekcije (default: `it_support_kb`) | ❌ Ne |
| `ENABLE_CHITCHAT` | `True` ili `False` (default: True) | ❌ Ne |
| `CHITCHAT_TEMPERATURE` | 0.3 do 0.5 (default: 0.4) | ❌ Ne |

### Korak 4: Pokreni

Space ce se automatski build-ovati.
- Prvi build traje ~5-10 minuta
- Sledeci buildovi ~1 minut
- URL: `https://tvoje-ime-orion-chatbot.hf.space`

### Lokalno testiranje (pre deploy-a)

Ako zelis da testiras pre nego sto upload-ujes na HF:

```bash
# Iz korena projekta
cd /e/Chatbot/chatbot_app

# Instaliraj gradio (ako nije)
uv add "gradio>=5.0,<6.0"

# Pokreni Gradio app
PYTHONPATH=backend .venv/Scripts/python hf/app.py

# Otvori u browser-u: http://localhost:7860
```

**Napomena:** Lokalno ce se prikazati poruka o nedostajucim API kljucevima
(OPENAI_API_KEY, QDRANT_URL) — to je ocekivano. Na HF-u ces ih podesiti
kroz Secrets.

---

## 🤖 Automatsko azuriranje cena (GitHub Action)

### Kako radi

Tvoj GitHub Action (`daily_scrape.yml`) svakodnevno u 3h:

1. Pokrece `scraper_cene.py` koji skrejpuje sajt sa cenama
2. Generise `komponente.json` sa najnovijim cenama
3. Push-uje ga **direktno na HF Space** pomocu `HF_TOKEN`

Chatbot automatski koristi najnoviji `komponente.json` — ne moras nista da radis.

```
GitHub Action (svaki dan u 3h)
    ↓
scraper_cene.py → generise komponente.json
    ↓
git push na huggingface.co/spaces/dexilio/orion-chatbot
    ↓
komponente.json zavrsava u korenu HF Space-a
    ↓
Kada korisnik pita za konfiguraciju:
    configurator.py → cita komponente.json → LLM dobija sveze cene
```

### Sta treba da podesis na GitHub-u

U **GitHub repozitorijum → Settings → Secrets and variables → Actions** dodaj:

| Secret | Vrednost |
|--------|----------|
| `HF_TOKEN` | Hugging Face token sa **write** dozvolom |

**Kako da dobijes HF_TOKEN:**
1. Idi na https://huggingface.co/settings/tokens
2. Klikni **New token**
3. Ime: `github-action`
4. Permissions: **write** (ili `repo` scope)
5. Kopiraj token i dodaj ga u GitHub Secrets

### Sta ako Action jos nije pokrenut?

Ako tek postavljas Space i GitHub Action se jos nije pokrenuo (prvi put u 3h),
`komponente.json` nece postojati na HF-u. U tom slucaju chatbot automatski
koristi **`backend/data/components.json`** kao privremeni katalog.

Cim se Action pokrene prvi put, `komponente.json` se push-uje na HF i chatbot
ga odmah koristi (bez restart-a, zahvaljujuci kesiranju).

### Akcija ne radi? Proveri:

1. Da li je `HF_TOKEN` dodat u GitHub Secrets?
2. Da li HF token ima `write` dozvolu?
3. Da li se HF Space zove `orion-chatbot`? (Action push-uje na `dexilio/orion-chatbot`)
4. Pokreni Action rucno: GitHub → Actions → Daily Orion Scrape → Run workflow

---

## 📝 Sta je uradjeno do sada

### Guest chat (bez login-a)

- Dodata opcija "Nastavi kao gost" na login formu
- Guest korisnici mogu odmah da postavljaju pitanja
- Guest vidi samo javne dokumente (role_id=1)
- Na HF-u su svi korisnici automatski "gosti" (nema login-a)

### Pametna detekcija caskanja

- Svaka poruka se klasifikuje: caskanje, konfiguracija ili tehnicko pitanje
- Caskanje → visa temperatura (0.4), prirodniji odgovori
- Tehnicko → niska temperatura (0.1), strogo iz baze znanja
- Konfiguracija → visa temperatura + katalog komponenti u context-u

### Konfigurator PC komponenti

- `backend/data/components.json` — katalog sa cenama (CPU, GPU, RAM, itd.)
- `komponente.json` na HF-u — azurira se dnevno kroz GitHub Action
- Configurator prvo cita `komponente.json` sa HF-a, pa pada na `components.json`
- LLM dobija kompletne specifikacije i proverava kompatibilnost

### Error handling

- Ako OpenAI ili Qdrant nisu dostupni, prikazuje se lepa poruka umesto crash-a
- Startup provera nedostajucih env varijabli
- try/except na svim kritickim mestima

### HF Space fajlovi (u `hf/` folderu)

| Fajl | Sta radi |
|------|----------|
| `hf/app.py` | Gradio chat aplikacija sa strimovanjem |
| `hf/requirements.txt` | Python zavisnosti za HF |
| `hf/README.md` | Ovo uputstvo |

### Izmene u postojecem kodu

| Fajl | Promena |
|------|---------|
| `backend/core/config.py` | DATABASE_URL postao opcioni (warning umesto error) |
| `backend/rag/configurator.py` | Prvo cita `komponente.json` sa HF root-a, pa lokalni fajl |
| `backend/rag/system_prompt.py` | Dodat configurator system prompt |
| `backend/rag/engine.py` | Podrska za config_mode, povecan max_tokens za konfiguracije |
| `backend/rag/classifier.py` | Dodata detekcija konfiguracija |
| `backend/api/chat.py` | Dodati guest endpointi + config detekcija |
| `frontend/...` | Guest mod, "Nastavi kao gost" dugme, prilagodjen ChatBox |

---

## ❗ Resavanje problema

### Space se ne pali / build ne prolazi

**Proveri Logs tab** za tacnu gresku. Najcesce:

| Problem | Resenje |
|---------|---------|
| ModuleNotFoundError: No module named 'rag' | Nisi upload-ovao `backend/` folder |
| ModuleNotFoundError: No module named 'sqlmodel' | Dodaj `sqlmodel>=0.0.39` u requirements.txt |
| ModuleNotFoundError: No module named 'llama_index' | Fali `requirements.txt` ili pogresan SDK (mora Gradio) |
| App radi ali pise "❌ Baza znanja nije povezana" | Nisi podesio `OPENAI_API_KEY` i `QDRANT_URL` u Secrets |

### API kljucevi ne rade

- Proveri da li si dodao Secrets u **Settings → Repository Secrets** (NE u .env fajl)
- Secrets se automatski ucitavaju kao env varijable (ne treba .env na HF-u)
- OpenAI kljuc mora da ima sredstava (check billing)
- Qdrant URL mora da bude tacan (ukljuci `:6333` port ako je potrebno)

### GitHub Action ne push-uje komponente.json

- Proveri da li je `HF_TOKEN` dodat u GitHub Secrets
- Pokreni Action rucno: Actions → Daily Orion Scrape → Run workflow
- Proveri da li se HF Space tacno zove: `dexilio/orion-chatbot`
- Action logovi ce pokazati tacnu gresku ako nesto fali

### Cene nisu azurne

- `komponente.json` se azurira samo jednom dnevno (u 3h)
- Ako si tek postavio Space, sacekaj prvi Action run
- Dok ne stigne pravi fajl, chatbot koristi `backend/data/components.json`

---

## 📁 Struktura projekta

```
chatbot_app/                    ← Glavni projekat
├── backend/                    ← Python backend (RAG engine, API)
│   ├── rag/                   ←    RAG engine, klasifikator, konfigurator
│   │   ├── engine.py          ←       Glavni RAG engine
│   │   ├── system_prompt.py   ←       System prompt-ovi
│   │   ├── classifier.py      ←       Detekcija caskanja
│   │   ├── configurator.py    ←       Konfigurator + citanje cena
│   │   └── chat_history.py    ←       Cuvanje istorije
│   ├── core/                  ←    Konfiguracija, bezbednost
│   │   ├── config.py          ←       .env varijable
│   │   ├── db.py              ←       PostgreSQL konekcija
│   │   └── security.py        ←       JWT tokeni
│   ├── api/                   ←    API rute
│   │   ├── chat.py            ←       Chat + guest endpointi
│   │   ├── auth.py            ←       Login
│   │   └── admin.py           ←       Admin panel
│   ├── models/                ←    SQLModel modeli
│   └── data/
│       └── components.json    ←    Sample katalog komponenti
│
├── frontend/                  ← React frontend (opciono)
│
├── hf/                        ← HF Space fajlovi
│   ├── app.py                 ←    Gradio app za HF
│   ├── requirements.txt       ←    Zavisnosti za HF
│   └── README.md              ←    Ovo uputstvo
│
├── .github/workflows/         ← GitHub Action skripte
│   └── daily_scrape.yml       ←    Dnevno skrejpovanje cena
│
└── README.md                  ← README glavnog projekta
```
