# -*- coding: utf-8 -*-
"""Skript za kreiranje objasnjenje_frontend.txt dokumentacije."""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPORT_DIR = Path("D:/OneDrive/Desktop/Potraga za sreckom/MI Systems Co/RAG/Chatbot/export")
CHATBOT_DIR = Path("E:/chatbot")
ENCODING = "utf-8"

CONTENT = """\
==============================================================================
OBJAŠNJENJE FRONTEND ARHITEKTURE - RAG CHATBOT
==============================================================================
React 18 + Vite + Tailwind CSS + Axios
Poslednja izmena: Jul 2026

==============================================================================
1. TEHNOLOŠKI STEK
==============================================================================

| Komponenta       | Tehnologija                          |
|------------------|--------------------------------------|
| UI framework     | React 18 (JSX)                       |
| Build tool       | Vite 5                               |
| Stilizovanje     | Tailwind CSS 3 (custom accent boje)  |
| HTTP klijent     | Axios (interceptor pattern)          |
| Autentifikacija  | JWT (lokalno skladištenje)           |
| Streaming        | SSE preko ReadableStream API         |
| CSS animacije    | Custom keyframes (fadeInUp, bounce)  |

==============================================================================
2. STRUKTURA FRONTEND FOLDERA
==============================================================================

frontend/
  ├── index.html                  # HTML ulazna tačka
  ├── package.json                # npm zavisnosti
  ├── vite.config.js              # Vite konfiguracija (port 5173)
  ├── postcss.config.js           # PostCSS (Tailwind + Autoprefixer)
  ├── tailwind.config.js          # Tailwind tema (accent boje)
  ├── .env                        # API URL (VITE_API_URL)
  └── src/
      ├── main.jsx                # React entry point
      ├── index.css               # Globalni CSS + animacije
      ├── App.jsx                 # Root komponenta (uslovno renderovanje)
      ├── context/
      │   └── AuthContext.jsx     # Auth stanje (login/logout/token)
      ├── services/
      │   └── api.js              # Axios instanca + svi API pozivi
      └── components/
          ├── LoginForm.jsx       # Login forma
          ├── ChatBox.jsx         # Glavni chat interfejs
          └── AdminPanel.jsx      # Admin panel (upload/brisanje dokumenata)

==============================================================================
3. DETALJNO OBJAŠNJENJE KOMPONENTI
==============================================================================

--- index.html ---
- Standardni HTML5 boilerplate.
- Postavlja <html lang="sr"> (srpski jezik).
- Uključuje <div id="root"> za React mount.
- Font: system UI (antialiased).
- Favicon: 💻 emoji kao SVG data URI.

--- package.json ---
- Zavisnosti: react, react-dom, axios.
- Dev zavisnosti: vite, @vitejs/plugin-react, tailwindcss,
  postcss, autoprefixer.
- Skripte: dev (vite), build (vite build), preview (vite preview).

--- vite.config.js ---
- Minimalna konfiguracija.
- Plugin: @vitejs/plugin-react (React Fast Refresh).
- Server port: 5173, ne otvara browser automatski (open: false).

--- tailwind.config.js ---
- Content: index.html + svi fajlovi u src/.
- Custom accent boje: indigo/ljubičasta paleta (50-950).
  Koristi se za primarne akcije, linkove, hover stanja.
- Ostatak: default Tailwind paleta.

--- .env ---
- VITE_API_URL: URL backend servera (http://localhost:8000).
- Frontend koristi VITE_ prefiks (Vite standard) za izlaganje
  env varijabli browseru.

--- src/main.jsx ---
- React 18 createRoot API.
- Omotava celu aplikaciju u AuthProvider (context za auth).
- Učitava index.css (Tailwind + animacije).
- StrictMode je uključen (detektuje potencijalne probleme).

--- src/index.css ---
- Tailwind direktive: @tailwind base/components/utilities.
- Custom scrollbar (tanak, indigo boja).
- Animacije:
  - fadeInUp: poruke ulaze odozdo sa blagim scale (0.35s, cubic-bezier).
  - sourceReveal: citati se pojavljuju sa fade + translate.
  - iconPulse: pulsirajući shadow na bot ikoni tokom strima.
  - loadingBounce: 3 tačkice koje odskaču (staggered delay).
- Staggered delay: .source-item, .loading-dot:nth-child(2/3).
- Klase: .message-enter, .source-item, .icon-streaming, .loading-dot.

--- src/App.jsx ---
- Root komponenta, samo 10 linija koda.
- Logika: ako user nije ulogovan → LoginForm.
  Ako jeste → ChatBox u full-screen layoutu.
- Layout: h-screen, bg-gray-950, max-w-4xl centered sa border-x.

--- src/context/AuthContext.jsx ---
- React Context + Provider pattern.
- Stanje: user (objekat), token (string), loading (bool), error (string).
- Inicijalizacija iz localStorage (persistent login).
- login(username, password):
  1. Poziva api.loginUser().
  2. Dekodira JWT payload (base64url → JSON) da izvuče
     is_admin, role_id.
  3. Čuva token i user u localStorage.
  4. Ažurira state.
  5. Obrada grešaka: 401 (pogrešni kredencijali),
     429 (rate limiting, captcha_required flag).
- logout(): briše localStorage, resetuje state.
- Sluša 'auth:unauthorized' event iz api.js interceptora
  (automatski logout kad token istekne).

--- src/services/api.js ---
- Axios instanca sa baseURL = VITE_API_URL.
- REQUEST INTERCEPTOR: automatski dodaje Authorization: Bearer
  header iz localStorage.access_token na svaki zahtev.
- RESPONSE INTERCEPTOR:
  - 401: briše token/user iz localStorage, emituje
    'auth:unauthorized' događaj.
  - 429: loguje captcha_required flag ako postoji.
- API funkcije:
  - loginUser(username, password) → POST /api/auth/login
    (application/x-www-form-urlencoded za OAuth2PasswordRequestForm).
  - sendMessage(message) → POST /api/chat (JSON response).
  - sendMessageStream(message, onToken, onSources, onDone):
    → POST /api/chat/stream (SSE).
    - Fetch API (ne Axios) za stream podršku.
    - AbortController sa 60s timeout-om.
    - Parsira SSE linije (data: {...}), poziva callback-ove.
    - Fallback: ako stream završi bez 'done' eventa, ipak
      poziva onDone() da se ne zaglavi u "sending" stanju.
  - uploadDocument(file, requiredRoleId, sourceName, onProgress)
    → POST /api/admin/documents/upload (multipart, sa progress).
  - listDocuments() → GET /api/admin/documents.
  - deleteDocument(pointId) → DELETE /api/admin/documents/{id}.
  - deleteDocumentBySource(sourceName) → DELETE .../source/{name}.
  - listUsers() → GET /api/admin/users.

--- src/components/LoginForm.jsx ---
- Jednostavna forma: username input, password input, submit dugme.
- Inputi sa placeholder-ovima (serviser, ••••••).
- Prikazuje test kredencijale u info kutiji (serviser/123, itd.).
- Error poruka (crvena kutija) ako login ne uspe.
- Loading stanje: spinner + "Prijavljivanje..." tekst.
- Disabled stanje: inputi i dugme zaključani tokom slanja.
- Footer: "RAG Chatbot © 2026".

--- src/components/ChatBox.jsx ---
- GLAVNA KOMPONENTA - najsloženija.
- Stanje: messages[], input, sending, showAdmin, selectedSource.
- Inicijalna poruka: "Zdravo, {username}! Kako vam mogu pomoći?"
- Header:
  - Logo + naziv "IT Asistent" + "Powered by FastAPI".
  - Admin dugme (samo za is_admin=true) → otvara AdminPanel modal.
  - Status: zeleni indikator + "Prijavljen: {username}".
  - Logout dugme (crveno na hover).
  - Responzivan: flex-wrap na mobilnom.
- Messages area:
  - User poruke: desno, indigo pozadina, rounded-br-md.
  - Bot poruke: levo, tamno siva pozadina, rounded-bl-md.
  - Hover efekat: blago podizanje (-translate-y-0.5).
  - Sources/Citations: klikabilna kartica sa:
    - Naziv izvora (📄 ikonica).
    - Relevatnost u %.
    - Role ≥ X.
    - Klik → otvara modal sa celim sadržajem izvora.
  - Loading indikator: 3 animirane tačkice + "Razmišljam...".
  - Auto-scroll na dno pri novoj poruci.
- Input area:
  - Text input sa placeholder-om.
  - Submit dugme sa ikonicom (strelica gore).
  - Disabled tokom slanja.
- SSE streaming:
  - Unikatan ID (Date.now()) za svaku bot poruku.
  - onToken: immutable update (map + spread) na messages.
  - onSources: postavlja sources na bot poruku.
  - onDone: setSending(false).
  - Error handling: fallback poruka ako stream padne.
- Source Content Modal:
  - Header: naziv izvora, relevatnost, role.
  - Content: pre-wrap tekst u font-sans.
  - Klik na pozadinu ili X zatvara modal.
- Admin Panel Modal:
  - Uslovno renderovanje AdminPanel komponente.

--- src/components/AdminPanel.jsx ---
- Modal sa 2 taba: Upload dokumenta i Indeksirani dokumenti.
- Upload tab:
  - Drag-and-drop zona (klik za file picker).
  - Prihvaćeni formati: PDF, DOCX, DOC, TXT, MD, CSV.
  - Prikaz imena i veličine fajla nakon izbora.
  - Opcioni naziv izvora (text input).
  - Radio dugmad za required_role_id (Kupac/Prodavac/Serviser).
  - Progress bar tokom uploada (gradient indigo).
  - Success/Error poruke.
  - Rezultat: broj chunkova, role, vreme indeksiranja.
- Documents tab:
  - Lista indeksiranih dokumenata iz Qdrant-a.
  - Svaki dokument: naziv, broj chunkova, role_id.
  - Preview teksta (line-clamp-2).
  - Delete dugme (crvena hover) → confirmation dialog.
  - Refresh dugme.
  - Loading/Error/Empty stanja.
- Confirmation dialog za brisanje:
  - Warning ikonica, pitanje "Obriši dokument?".
  - Otkaži / Obriši dugmad.
- Staggered animacija: source-item sa animationDelay.

==============================================================================
4. SSE (SERVER-SENT EVENTS) STREAMING PROTOKOL
==============================================================================

Frontend → Backend:
  POST /api/chat/stream
  Authorization: Bearer <token>
  Content-Type: application/json
  Body: {"message": "Korisničko pitanje"}

Backend → Frontend (SSE format):
  data: {"type": "token", "content": "deo odgovora..."}
  data: {"type": "token", "content": "još teksta..."}
  data: {"type": "sources", "content": [{"source": "...", ...}]}
  data: {"type": "done"}

Frontend parsiranje:
  1. Čita stream kroz ReadableStream.getReader().
  2. Akumulira buffer, deli po \n\n (SSE delimiter).
  3. Parsira JSON iz svake 'data: ' linije.
  4. dispatch: token → onToken(), sources → onSources(),
     done → onDone().
  5. Timeout: 60s (AbortController) - ako backend ne odgovori,
     prekida se zahtev.
  6. Fallback: ako stream završi bez 'done' eventa,
     poziva onDone() da oslobodi UI.

==============================================================================
5. AUTENTIFIKACIJA (JWT FLOW)
==============================================================================

1. Login forma → POST /api/auth/login (form-urlencoded).
2. Backend vraća {access_token: "eyJ...", token_type: "bearer"}.
3. Frontend dekodira JWT payload (base64url):
   {
     "sub": "serviser",
     "role_id": 3,
     "is_admin": false,
     "exp": 1712345678
   }
4. Čuva token u localStorage (persistent).
5. Svaki API zahtev automatski dobija Authorization header
   preko Axios request interceptora.
6. Ako backend vrati 401 → response interceptor briše
   localStorage i emituje 'auth:unauthorized' događaj.
7. AuthContext sluša događaj i resetuje stanje → prikazuje
   LoginForm.
8. Logout dugme ručno briše localStorage i resetuje stanje.

==============================================================================
6. RBAC (ROLE-BASED ACCESS CONTROL) - FRONTEND PERSPEKTIVA
==============================================================================

Frontend ima ograničenu RBAC logiku - glavni filter je na backendu.
- JWT payload sadrži role_id (1-3) i is_admin (bool).
- Admin Panel dugme je vidljivo SAMO ako je is_admin = true
  (uslovno renderovanje u ChatBox.jsx).
- ChatBox prikazuje "role ≥ X" na svakom citatu (samo info).
- Sve ostalo filtriranje radi backend (Qdrant MetadataFilters).
- Frontend NIKADA ne odlučuje koji dokumenti su vidljivi -
  to je isključivo backend odgovornost.

==============================================================================
7. STANJA KORISNIČKOG INTERFEJSA
==============================================================================

Za svaku komponentu definisana su sledeća stanja:

LoginForm:
  - Idle: prikaz forme, inputi prazni.
  - Loading: spinner, inputi disabled, "Prijavljivanje...".
  - Error: crvena poruka ispod inputa (pogrešna lozinka,
    server nedostupan, rate limit).
  - Uspeh: redirect na ChatBox (ne prikazuje se u LoginForm).

ChatBox:
  - Prazan: samo pozdravna poruka od bota.
  - Normal: korisnik i bot poruke.
  - Sending: loading indikator, input disabled.
  - Stream: bot poruka se popunjava token po token.
  - Error: "❌ Došlo je do greške..." poruka.
  - Source modal otvoren: prikaz celog teksta izvora.

AdminPanel:
  - Upload tab:
    - Idle: drag-drop zona.
    - File selected: prikaz imena i veličine.
    - Uploading: progress bar.
    - Success: zelena poruka + detalji (chunks, role, time).
    - Error: crvena poruka.
  - Documents tab:
    - Loading: spinner + "Učitavanje dokumenata...".
    - Empty: "Nema indeksiranih dokumenata".
    - Error: crvena poruka.
    - Normal: lista dokumenata sa delete opcijom.
    - Deleting: confirmation dialog.
    - Delete success/error: obaveštenje na vrhu liste.

==============================================================================
8. ANIMACIJE I MIKROINTERAKCIJE
==============================================================================

- fadeInUp (0.35s): svaka nova poruka, sa stagger delay-om.
- sourceReveal (0.3s): citati se pojavljuju posle poruke.
- loadingBounce (1.2s): tri tačkice dok čeka odgovor.
- iconPulse (1.5s): bot ikonica pulsira tokom strima.
- Hover: poruke se blago podižu (-translate-y-0.5).
- Hover: source kartice menjaju boju i podižu se.
- Hover: admin panel dugmad menjaju boju.
- Transition: sve interakcije imaju duration-200.

==============================================================================
9. RESPONZIVNOST
==============================================================================

- Header: flex-wrap na mobilnom (prelama u redove).
- Poruke: max-w-[75%] na širokom, full-width na uskom.
- Modali: max-w-lg (login), max-w-2xl (source), sa mx-4 margin.
- Input: full-width.
- Admin panel: max-h-[90vh] sa overflow-y-auto.
- Sve u: sm: prefiksi za veće ekrane (padding, breakpoints).
- Testirano na: desktop (1920x1080), tablet, mobile.

==============================================================================
10. INSTALACIJA I POKRETANJE
==============================================================================

  cd frontend
  npm install
  # Podesi .env:
  #   VITE_API_URL=http://localhost:8000
  npm run dev          # Development server na portu 5173
  npm run build        # Produkcioni build u dist/

==============================================================================
11. ISTORIJA IZMENA
==============================================================================

2026-07-20 - Inicijalna struktura fajla
- Kompletan opis frontend arhitekture.

==============================================================================
KRAJ DOKUMENTACIJE
==============================================================================
"""


def write_frontend_doc():
    # U export folder
    export_path = EXPORT_DIR / "objasnjenje_frontend.txt"
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    export_path.write_text(CONTENT, encoding=ENCODING)
    print(f"objasnjenje_frontend.txt kreiran ({export_path})")

    # Kopiraj na E:\\chatbot
    chatbot_path = CHATBOT_DIR / "objasnjenje_frontend.txt"
    CHATBOT_DIR.mkdir(parents=True, exist_ok=True)
    chatbot_path.write_text(CONTENT, encoding=ENCODING)
    print(f"Kopiran na {chatbot_path}")

    print(f"\nVeličina: {export_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    print("=" * 60)
    print("Kreiranje objasnjenje_frontend.txt...")
    print("=" * 60)
    write_frontend_doc()
    print("=" * 60)
    print("Gotovo!")
    print("=" * 60)
