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
 * Slanje poruke chatbot-u.
 * @param {string} message - Korisnička poruka
 */
export async function sendMessage(message) {
  const response = await api.post('/api/chat', { message })
  return response.data
}

export default api
