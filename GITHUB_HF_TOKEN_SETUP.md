# 🔑 Podešavanje HF_TOKEN u GitHub Secrets

Kompletno uputstvo — kako povezati GitHub Action sa Hugging Face Space-om
tako da se cene automatski ažuriraju svaki dan.

---

## 📋 Šta ćemo da uradimo

```
GitHub Action (Daily Orion Scrape)
    ↓  (koristi HF_TOKEN)
HF Space → komponente.json se ažurira sa svežim cenama
    ↓
Chatbot čita najnovije cene → korisnik dobija tačne konfiguracije
```

---

## 🧾 Korak 1: Kreiraj HF Access Token

Idi na https://huggingface.co/settings/tokens

![1] Otvori HF Settings → Access Tokens

```
1. Uloguj se na huggingface.co
2. Klikni na profil → Settings
3. Sa leve strane klikni na "Access Tokens"
```

### Klikni "New token"

![2] Kreiraj novi token

Podesi sledeće:

| Polje | Vrednost |
|-------|----------|
| **Token name** | `github-action` |
| **Token type** | **Write** (ili `Fine-grained` sa `repo` scope-om) |

> ⚠️ **VAŽNO:** Mora biti **Write**, ne Read! Akcija treba da push-uje fajlove.

### Kopiraj token

![3] Kopiraj token

**Odmah ga kopiraj!** Posle zatvaranja prozora, više nećeš moći da ga vidiš.

Token izgleda ovako:
```
hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🔐 Korak 2: Dodaj token u GitHub Secrets

Idi na svoj GitHub repozitorijum.

### Otvori Settings → Secrets

```
1. Otvori GitHub → tvoj repozitorijum
2. Klikni na "Settings" tab (desno gore)
3. Sa leve strane klikni "Secrets and variables"
4. Klikni "Actions"
```

### Klikni "New repository secret"

![4] Novi secret

Popuni:

| Polje | Vrednost |
|-------|----------|
| **Name** | `HF_TOKEN` |
| **Secret** | `hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (tvoj token) |

![5] Polja za unos

### Klikni "Add secret"

Gotovo! Sad izgleda ovako:

```
Repository secrets
──────────────────────────────────────
  HF_TOKEN    ████████████████████████   ← Updated just now
```

---

## ✅ Korak 3: Proveri da li radi

### Opcija A: Pokreni Action ručno

```
1. Idi na GitHub → tvoj repo → "Actions" tab
2. Sa leve strane klikni "Daily Orion Scrape"
3. Klikni "Run workflow" (desna strana)
4. Klikni "Run workflow" (padajući meni)
```

Sačekaj 1-2 minuta i proveri da li je workflow prošao (zeleni ✅).

### Opcija B: Proveri da li je token ispravan

Pokreni ovo u terminalu (ako imaš `curl`):

```bash
# Zameni TOKEN sa tvojim stvarnim tokenom
curl -s -H "Authorization: Bearer hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  https://huggingface.co/api/whoami
```

**Ako je token ispravan** — dobićeš odgovor sa tvojim korisničkim imenom:
```json
{"type":"user","id":"...","name":"dexilio","fullname":"Dexilio",...}
```

**Ako nije** — dobićeš:
```json
{"error":"Unauthorized"}
```

---

## 📝 Kako izgleda u GitHub Action fajlu

Tvoj `daily_scrape.yml` već ima ovo:

```yaml
jobs:
  scrape-and-push:
    steps:
      # ... scraping steps ...

    - name: Guranje fajla na Hugging Face Space
      env:
        HF_TOKEN: ${{ secrets.HF_TOKEN }}    # ← Ovo koristi Secret
      run: |
        git config --global user.email "action@github.com"
        git config --global user.name "GitHub Action"
        git clone https://user:$HF_TOKEN@huggingface.co/spaces/dexilio/orion-chatbot hf_space
        cp komponente.json hf_space/komponente.json
        cd hf_space
        git add komponente.json
        git commit -m "Auto update cena $(date '+%Y-%m-%d')" || echo "Nema promena"
        git push
```

**Šta se dešava:**
1. `${{ secrets.HF_TOKEN }}` uzima vrednost iz GitHub Secrets
2. `$HF_TOKEN` se koristi u URL-u za autentifikaciju: `https://user:$HF_TOKEN@huggingface.co/...`
3. Git klonira HF Space, kopira fajl, commit-uje i push-uje

---

## ❗ Rešavanje problema

| Problem | Verovatni uzrok | Rešenje |
|---------|----------------|---------|
| Action fails sa "Authentication failed" | Token nema **write** dozvolu | Kreiraj novi token sa **Write** tipom |
| Action fails sa "Repository not found" | Pogrešan naziv Space-a | Proveri da li se Space zove `dexilio/orion-chatbot` |
| Action fails sa "Permission denied" | Token je **Read** umesto Write | Obriši stari token i kreiraj novi sa **Write** |
| Action prošao ali komponente.json nema | Push nije uspeo (stari token) | Proveri Action logove za greške |
| Ne mogu da nađem "Secrets" na GitHub-u | Pogrešan tab | GitHub → Settings (repo) → Secrets and variables → Actions |

### Kako da obrišeš i ponovo kreiraš token

Ako si napravio grešku sa tipom tokena:

```
HF (huggingface.co):
  1. Settings → Access Tokens
  2. Nađi "github-action" token
  3. Klikni "Delete" (🟥)
  4. Klikni "Create new token"
  5. Ovaj put izaberi "Write"

GitHub:
  1. Repo → Settings → Secrets and variables → Actions
  2. Nađi HF_TOKEN → klikni "Delete" (🟥)
  3. "Add new secret" → nalepi novi token
```

---

## 🎯 Kratka verzija (cheat sheet)

```
┌─────────────────────────────────────────────────────────┐
│  1. HF:   huggingface.co/settings/tokens                │
│           → New token → Write → kopiraj                │
│                                                         │
│  2. GitHub: Repo → Settings → Secrets → Actions         │
│             → New repository secret                     │
│             → Name: HF_TOKEN                            │
│             → Secret: hf_... (tvoj token)               │
│                                                         │
│  3. Test: GitHub → Actions → Run workflow               │
└─────────────────────────────────────────────────────────┘
```

---

*Ažurirano: Jul 2026*
