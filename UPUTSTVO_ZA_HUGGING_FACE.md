# Kompletno uputstvo za prebacivanje na Hugging Face (Besplatno)

## 📋 Sta je uradjeno

Da bi chatbot mogao da radi na **besplatnom Hugging Face** tier-u,
uradio sam sledece izmene i kreirao potrebne fajlove:

---

## 1. IZMENJENI FAJLOVI

### `backend/core/config.py`
**Sta je menjano:** DATABASE_URL vise nije obavezan.

Pre:
```python
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL nije postavljen.")
```

Posle:
```python
if not settings.DATABASE_URL:
    logger.warning("DATABASE_URL nije postavljen. "
                   "Koristi se in-memory cuvanje.")
```

**Zasto:** Na HF nemamo PostgreSQL bazu, pa je ovo moralo da se
ukloni da aplikacija ne bi pukla na startu. Istorija razgovora
se cuva u memoriji (traje dok je Space aktivan).

---

## 2. NOVI FAJLOVI (u `hf/` folderu)

### `hf/app.py`
Gradio aplikacija koja zamenjuje React frontend + FastAPI backend.

**Karakteristike:**
- Radi na besplatnom Gradio Space-u (nema Docker PRO)
- Koristi isti RAG engine iz `backend/` foldera
- Ima **caskanje** (pozdravi, "cao kako si")
- Ima **konfigurator** ("napravi mi PC do 800e")
- Strimuje odgovore u realnom vremenu
- Moderan ljubicasti UI

**Tehnicka arhitektura:**
```
korisnik -> Gradio UI -> _get_chat_engine() -> get_chat_engine()
                                              (iz rag/engine.py)
                            -> is_chitchat_query() (detektuje caskanje)
                            -> is_config_query()   (detektuje konfiguraciju)
                            -> OpenAI GPT-4o-mini
                            -> Qdrant vektorska baza
                            -> odgovor nazad kroz stream
```

**Detekcija po poruci (pametna):**
- "Cao kako si?" -> chitchat: True,  config: False  -> temp 0.4, relaksiran prompt
- "Napravi mi PC do 800e" -> chitchat: True, config: True -> temp 0.4 + katalog komponenti
- "Koja je cena laptopa?" -> chitchat: False, config: False -> temp 0.1, strogi RAG

### `hf/requirements.txt`
Spisak svih Python biblioteka potrebnih za HF.

### `hf/README.md`
Kratko uputstvo za HF (ovaj fajl je detaljniji).

---

## 3. KORAK PO KORAK — PRENOS NA HUGGING FACE

### Korak 1: Kreiraj nalog na Hugging Face

Ako vec nemas:
1. Idi na https://huggingface.co/join
2. Registruj se (besplatno)
3. Potvrdi email

### Korak 2: Kreiraj novi Space

1. Klikni na profil (gore desno) → **New Space**
2. Ispuni formu:
   - **Space Name**: `it-asistent` (ili sta zelis)
   - **License**: MIT
   - **SDK**: `Gradio`
   - **Hardware**: `CPU basic` (besplatno, 2 vCPU, 16GB RAM)
3. Klikni **Create Space**

### Korak 3: Upload fajlova

Posle kreiranja Space-a, videces prazan folder.
Upload-uj sledece fajlove i foldere:

**Metod A — Preko browser-a (najlakse):**
1. Otvori Space
2. Idi na **Files** tab
3. Klikni **Add file** → **Upload files**
4. Upload-uj OVE fajlove:

```
📁 backend/               ← CELA STRUKTURA backend foldera
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
       └── components.json
📄 app.py                  ← iz hf/ foldera (Gradio app)
📄 requirements.txt        ← iz hf/ foldera
📄 README.md               ← iz hf/ foldera
```

5. Klikni **Commit changes**

**Metod B — Preko Git-a (ako znas):**
```bash
# Kloniraj Space
git clone https://huggingface.co/spaces/TVOJE_IME/it-asistent
cd it-asistent

# Kopiraj fajlove
cp /putanja/do/projekta/hf/app.py .
cp /putanja/do/projekta/hf/requirements.txt .
cp /putanja/do/projekta/hf/README.md .
cp -r /putanja/do/projekta/backend .

# Push-uj
git add .
git commit -m "Prvi deployment"
git push
```

### Korak 4: Podesi Secret varijable (obavezno!)

1. Idi u **Settings** tab Space-a
2. Pronadji **Repository Secrets** (donji deo strane)
3. Dodaj sledece varijable:

| Secret | Sta staviti | Obavezno |
|--------|------------|----------|
| `OPENAI_API_KEY` | Tvoj OpenAI kljuc (sk-...) | **DA** |
| `QDRANT_URL` | URL tvoje QdrantCloud baze (npr. https://xyz.us-east-1-0.aws.cloud.qdrant.io:6333) | **DA** |
| `QDRANT_API_KEY` | API kljuc za Qdrant | Ne, samo ako ga Qdrant zahteva |
| `QDRANT_COLLECTION` | Ime kolekcije (default: `it_support_kb`) | Ne |
| `ENABLE_CHITCHAT` | `True` za caskanje, `False` bez | Ne |
| `CHITCHAT_TEMPERATURE` | 0.4 (ili 0.3-0.5 za prirodnije) | Ne |

**Kako da dodas:**
1. Klikni **New secret**
2. U polje **Name** upisi: `OPENAI_API_KEY`
3. U polje **Value** upisi tvoj OpenAI kljuc
4. Klikni **Add secret**
5. Ponovi za ostale varijable

### Korak 5: Pokreni Space

1. Idi na **App** tab
2. Space ce automatski poceti da se build-uje
   (prvi build traje 5-10 minuta, sledeci su brzi)
3. Kada build zavrsi, videces chat interfejs
4. URL ce biti: `https://tvoje-ime-it-asistent.hf.space`

### Korak 6: Testiraj

Kad se Space pokrene, probaj:

1. **Caskanje**: "Cao kako si?"
2. **Konfiguracija**: "Napravi mi gaming PC do 800e"
3. **Tehnicko pitanje**: "Kako da instaliram Windows?"
   (odgovor zavisi od toga sta imas u Qdrant bazi)

---

## 4. RESAVANJE PROBLEMA

### "ModuleNotFoundError: No module named 'rag'"
**Uzrok:** Nisi upload-ovao `backend/` folder ili je pogresna struktura.
**Resenje:** Proveri da li `backend/rag/` folder postoji u Space fajlovima.

### "Application is building..."
**Uzrok:** Prvi build uvek traje duze.
**Resenje:** Sacekaj 5-10 minuta. Osvezi stranicu.

### "OpenAI API key not found"
**Uzrok:** Nisi podesio `OPENAI_API_KEY` u Secrets.
**Resenje:** Idi u Settings → Repository Secrets i dodaj ga.

### "Cannot connect to Qdrant"
**Uzrok:** Pogresan QDRANT_URL ili QDRANT_API_KEY.
**Resenje:** Proveri da li QdrantCloud radi i da li su podaci tacni.

### Crni ekran / "Something went wrong"
**Uzrok:** Najcesce greska u kodu ili nedostajuca biblioteka.
**Resenje:**
1. Idi u **Settings** → **Change hardware** → izaberi veci (CPU Upgrade)
2. Ili pogledaj **Logs** tab za detaljnu gresku

---

## 5. STA RADI A STA NE RADI NA HF

| Funkcija | Status | Zasto |
|----------|--------|-------|
| RAG pitanja iz baze | ✅ Radi | Qdrant je eksterni (Cloud) |
| Caskanje ("cao kako si") | ✅ Radi | GPT-4o-mini preko API-ja |
| Konfigurator racunara | ✅ Radi | components.json se ucitava |
| Strimovanje odgovora | ✅ Radi | Gradio podrzava streaming |
| Guest pristup | ✅ Uvek | Nema login-a na HF verziji |
| **Cuvanje istorije** | ⚠️ Privremeno | Samo dok je Space aktivan |
| **Admin panel** | ❌ Ne radi | Zahteva FastAPI + JWT |
| **Login korisnika** | ❌ Ne radi | Nema PostgreSQL baze |
| **Upload dokumenata** | ❌ Ne radi | Samo preko admin API-ja |

---

## 6. KORISNI LINKOVI

- Hugging Face Spaces: https://huggingface.co/spaces
- Qdrant Cloud: https://cloud.qdrant.io
- OpenAI API keys: https://platform.openai.com/api-keys
- Gradio dokumentacija: https://gradio.app/docs
