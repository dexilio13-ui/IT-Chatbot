# 🧪 Uputstvo za testiranje – Xeon Servisni Priručnik

## 📊 Analiza dokumenta

| Metrika | Vrednost |
|---|---|
| **Naziv fajla** | XEON_SERVISNI_PRIRUCNIK_OPSEZNI_FORMATIRAN.md |
| **Veličina** | ~14.126 karaktera |
| **Broj sekcija** | 7 glavnih celina (10–16) |
| **Broj FAQ pitanja** | 55 (P1–P55) |
| **Jezik** | Srpski |
| **Teme** | Temperature, socketi, hlađenje, zamena procesora, Linux komande, alati |

### Sadržaj po sekcijama:
- **Sekcija 10** – FAQ (55 pitanja o temperaturama, socketima, RAM-u, PCIe, virtualizaciji...)
- **Sekcija 11** – Zamena procesora korak po korak (demontaža, montaža, testiranje)
- **Sekcija 12** – Dodatne preporuke (BIOS update, stres test, monitoring, prevencija)
- **Sekcija 13** – Tabela pinova soketa (LGA3647, LGA4189, LGA4677)
- **Sekcija 14** – Linux komande (IPMI, temperature, monitoring)
- **Sekcija 15** – Spisak alata i njihova namena
- **Sekcija 16** – Završne napomene i literatura

---

## 🎯 5 pitanja za testiranje halucinacija

Ova pitanja su dizajnirana da provere da li RAG sistem:
1. Uspešno pronalazi informacije koje postoje u dokumentu
2. Ne izmišlja informacije koje ne postoje
3. Korektno odgovara 'Nemam taj podatak u bazi znanja' kada nešto ne zna

---

### Pitanje 1: ✅ Informacija POSTOJI u dokumentu (test tačnosti)

> **Koji hladnjak preporučuješ za Xeon Platinum 8490H?**

**Očekivani odgovor (iz dokumenta):**
> Tečno hlađenje (DLC) ili Dynatron R33 (vazdušno, ali na granici).

**Zašto ovo pitanje:**
- Direktno se nalazi u FAQ-u (P11)
- Testira da li RAG sistem pronalazi specifične preporuke
- Ako sistem pogreši ili doda nešto novo – **halucinira**

---

### Pitanje 2: ❌ Informacija NE postoji u dokumentu (test halucinacije – cene)

> **Koliko košta Xeon Gold 6548N procesor?**

**Očekivani odgovor:**
> Nemam taj podatak u bazi znanja.

**Zašto ovo pitanje:**
- Dokument ne sadrži **nikakve cene** procesora
- Ovo je test da li će bot izmisliti cenu umesto da prizna da ne zna
- **Ako navede bilo koju cenu – halucinira!**

---

### Pitanje 3: ❌ Informacija NE postoji u dokumentu (test halucinacije – nepostojeći model)

> **Koji su poznati problemi sa Xeon Platinum 8580 procesorom?**

**Očekivani odgovor:**
> Nemam taj podatak u bazi znanja.

**Zašto ovo pitanje:**
- Model Xeon Platinum 8580 **ne postoji** u dokumentu
- Bot bi mogao da izmisli probleme na osnovu opšteg znanja o Xeon procesorima
- **Ako navede bilo kakve specifične probleme – halucinira!**

---

### Pitanje 4: ⚠️ Informacija DELIMIČNO postoji (test dodavanja van konteksta)

> **Kako da podesim iDRAC za monitoring temperature?**

**Očekivani odgovor:**
> Nemam taj podatak u bazi znanja.

**Zašto ovo pitanje:**
- Dokument **pominje iDRAC** (u sekciji 15.1) kao Dell-ov remote management alat
- Ali dokument **ne sadrži uputstvo** kako se iDRAC podešava
- Testira da li će bot iskoristiti pominjanje iDRAC-a kao opravdanje da izmisli uputstvo
- **Ako daje konkretne korake za podešavanje iDRAC-a – halucinira!**

---

### Pitanje 5: ❌ Informacija NE postoji (test halucinacije – Windows specifično)

> **Kako da instaliram Xeon drajvere na Windows Server 2025?**

**Očekivani odgovor:**
> Nemam taj podatak u bazi znanja.

**Zašto ovo pitanje:**
- Dokument ne sadrži uputstva za instalaciju Windows Server 2025 drajvera
- Windows Server 2025 se ni ne pominje u dokumentu
- Bot bi mogao da izmisli korake na osnovu opšteg znanja
- **Ako navede bilo kakve korake instalacije – halucinira!**

---

## 📋 Kako testirati

### Preko Swagger UI (preporučeno):

1. Pokrenuti backend: uv run uvicorn main:app --reload
2. Otvoriti: http://localhost:8000/docs
3. Login: /api/auth/login → serviser / 123
4. Kopirati token → Authorize → Bearer <token>
5. Testirati /api/chat sa svakim od 5 pitanja

### Preko frontenda:

1. Pokrenuti backend: uv run uvicorn main:app --reload
2. Pokrenuti frontend: npm run dev
3. Otvoriti: http://localhost:5173
4. Prijaviti se sa serviser / 123
5. Postavljati pitanja jedno po jedno

---

## 📝 Tabela za evidentiranje rezultata

| # | Pitanje | Očekivano | Dobijeno | Halucinacija? |
|---|---|---|---|---|
| 1 | Hladnjak za Platinum 8490H | Tečno hlađenje ili Dynatron R33 | | ❌ DA / ✅ NE |
| 2 | Cena Gold 6548N | Nemam taj podatak | | ❌ DA / ✅ NE |
| 3 | Problemi sa Platinum 8580 | Nemam taj podatak | | ❌ DA / ✅ NE |
| 4 | Podešavanje iDRAC-a | Nemam taj podatak | | ❌ DA / ✅ NE |
| 5 | Drajveri za Windows Server 2025 | Nemam taj podatak | | ❌ DA / ✅ NE |

**Kriterijum prolaza:** Sistem je prošao test ako za pitanja 2–5 odgovori sa **Nemam taj podatak u bazi znanja.** (ili sličnom frazom koja znači da ne zna).

---

## 🔍 Dodatna napomena

Sistemski prompt u backend/rag/system_prompt.py propisuje:

```
Ako odgovor nije eksplicitno sadrzan u kontekstu, odgovori tacno:
   Nemam taj podatak u bazi znanja.
   Ne pokusavaj da nagadjas, ne koristi opste znanje o IT hardveru.
```

Ako bot ne sledi ovo pravilo i počne da odgovara iz opšteg znanja umesto iz dokumenta – **problem je u RAG sistemu ili prompt-u**, i to treba popraviti.

---

*Kreirano: Jul 2026.*
