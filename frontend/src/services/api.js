import axios from 'axios'

/**
 * Axios instanca konfigurisana za komunikaciju sa FastAPI backend-om.
 * Automatski dodaje JWT token iz localStorage u svaki zahtev.
 *
 * URL se učitava iz .env fajla (VITE_API_URL) sa fallback-om na localhost:8000.
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ----------------------------------------------------------------
// REQUEST INTERCEPTOR
// Automatski dodaje Authorization: Bearer <token> na svaki zahtev
// ----------------------------------------------------------------
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ----------------------------------------------------------------
// RESPONSE INTERCEPTOR
// Centralizovana obrada grešaka (401 - token istekao, 429 - rate limit)
// ----------------------------------------------------------------
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // Token je istekao ili je nevalidan -> očisti sesiju
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          // Emitujemo događaj da AuthContext detektuje i prebaci na login
          window.dispatchEvent(new CustomEvent('auth:unauthorized'))
          break

        case 429:
          // Rate limiting - možemo proveriti captcha_required flag
          if (data?.captcha_required) {
            // Backend signalizira da je potrebna captcha verifikacija
            console.warn('Rate limit dostignut. Captcha verifikacija zahtevana.')
          }
          break
      }
    }

    return Promise.reject(error)
  }
)

/**
 * Pomoćna funkcija za login (application/x-www-form-urlencoded format).
 * FastAPI koristi OAuth2PasswordRequestForm koji očekuje form data.
 */
export async function loginUser(username, password) {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)

  const response = await api.post('/api/auth/login', formData.toString(), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })

  return response.data
}

/**
 * Slanje poruke chatbot-u (sinhroni JSON odgovor).
 * @param {string} message - Korisnička poruka
 */
export async function sendMessage(message) {
  const response = await api.post('/api/chat', { message })
  return response.data
}

/**
 * Slanje poruke chatbot-u sa SSE strimovanjem.
 *
 * Tokom strima poziva:
 *   onToken(token)   - svaki pojedinačni token
 *   onSources(sources) - izvori (citations) na kraju
 *   onDone()         - signal da je strim završen
 *
 * @param {string} message - Korisnička poruka
 * @param {(token: string) => void} onToken
 * @param {(sources: Array) => void} onSources
 * @param {() => void} onDone
 */
export async function sendMessageStream(message, onToken, onSources, onDone) {
  const token = localStorage.getItem('access_token')

  // Timeout od 60 sekundi - ako backend ne odgovori za to vreme
  // (npr. Groq rate limit sa retry-jem od 120s), prekidamo zahtev
  // da se ne zaglavimo beskonacno u "sending" stanju
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 60000)

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      signal: controller.signal,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ message }),
    })

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    throw new Error(errData.detail || `HTTP ${response.status}`)
  }

  } finally {
    clearTimeout(timeoutId)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ') && line.length > 6) {
        try {
          const data = JSON.parse(line.slice(6))
          switch (data.type) {
            case 'token':
              onToken(data.content)
              break
            case 'sources':
              onSources(data.content || [])
              break
            case 'done':
              onDone()
              return
            case 'error':
              console.error('SSE error:', data.content)
              break
          }
        } catch (e) {
          console.warn('SSE parse error:', e)
        }
      }
    }
  }

  // Ako stream zavrsi bez "done" eventa (npr. backend error),
  // ipak signaliziramo da je obrada gotova da se ne bi
  // zaglavili u "sending" stanju:
  onDone()
}

// ────────────────────────────────────────────────────────────────
// ADMIN API funkcije
// ────────────────────────────────────────────────────────────────

/**
 * Upload dokumenta na backend (admin only).
 * @param {File} file - Fajl za upload (.pdf, .docx, .txt, .md, .csv)
 * @param {number} requiredRoleId - 1=Kupac, 2=Prodavac, 3=Serviser
 * @param {string|null} sourceName - Opcioni naziv izvora
 * @param {(progress: number) => void} onProgress - Callback za praćenje napretka
 */
export async function uploadDocument(file, requiredRoleId = 1, sourceName = null, onProgress = null) {
  const formData = new FormData()
  formData.append('file', file)

  if (requiredRoleId) {
    formData.append('required_role_id', String(requiredRoleId))
  }

  if (sourceName) {
    formData.append('source_name', sourceName)
  }

  const response = await api.post('/api/admin/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: onProgress
      ? (e) => onProgress(Math.round((e.loaded * 100) / (e.total || 1)))
      : undefined,
  })

  return response.data
}

/**
 * Dohvatanje liste indeksiranih dokumenata iz Qdrant-a (admin only).
 */
export async function listDocuments() {
  const response = await api.get('/api/admin/documents')
  return response.data
}

/**
 * Brisanje point-a iz Qdrant kolekcije (admin only).
 * @param {string} pointId - ID point-a za brisanje
 */
export async function deleteDocument(pointId) {
  const response = await api.delete(`/api/admin/documents/${pointId}`)
  return response.data
}

/**
 * Brisanje svih chunkova za dati source (admin only).
 * @param {string} sourceName - Naziv izvora za brisanje
 */
export async function deleteDocumentBySource(sourceName) {
  const response = await api.delete(`/api/admin/documents/source/${encodeURIComponent(sourceName)}`)
  return response.data
}

/**
 * Dohvatanje liste korisnika (admin only).
 */
export async function listUsers() {
  const response = await api.get('/api/admin/users')
  return response.data
}

export default api
