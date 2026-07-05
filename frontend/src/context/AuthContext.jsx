import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { loginUser } from '../services/api'

const AuthContext = createContext(null)

/**
 * AuthProvider obmotava celu aplikaciju i upravlja stanjem
 * autentifikacije (JWT token, korisničko ime).
 */
export function AuthProvider({ children }) {
  // Inicijalizujemo stanje iz localStorage (ako je korisnik već ulogovan)
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('user')
    return storedUser ? JSON.parse(storedUser) : null
  })

  const [token, setToken] = useState(() => {
    return localStorage.getItem('access_token') || null
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  /**
   * Login funkcija - šalje POST zahtev na /api/auth/login.
   *
   * FastAPI koristi OAuth2PasswordRequestForm koji očekuje
   * application/x-www-form-urlencoded format (username & password).
   *
   * @param {string} username
   * @param {string} password
   */
  const login = useCallback(async (username, password) => {
    setLoading(true)
    setError(null)

    try {
      const data = await loginUser(username, password)

      // Uspešan login - čuvamo token i korisnika
      const accessToken = data.access_token
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('user', JSON.stringify({ username }))

      setToken(accessToken)
      setUser({ username })
    } catch (err) {
      // Obrada grešaka
      if (err.response) {
        const { status, data } = err.response

        if (status === 429) {
          // Rate limiting
          const message = data?.captcha_required
            ? 'Previše neuspešnih pokušaja. Captcha verifikacija je zahtevana.'
            : 'Previše zahteva. Molimo sačekajte pre sledećeg pokušaja.'
          setError(message)
        } else if (status === 401) {
          setError(data?.detail || 'Pogrešan username ili lozinka.')
        } else {
          setError(data?.detail || 'Došlo je do greške prilikom prijave.')
        }
      } else {
        setError('Ne mogu da se povežem sa serverom. Proverite da li je backend pokrenut.')
      }

      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * Logout - čisti token i korisnika iz state-a i localStorage-a.
   */
  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
    setError(null)
  }, [])

  // Sluša custom 'auth:unauthorized' događaj iz api.js interceptor-a
  // i automatski odjavljuje korisnika kada backend vrati 401
  useEffect(() => {
    function handleUnauthorized() {
      setToken(null)
      setUser(null)
      setError(null)
    }

    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Custom hook za pristup AuthContext-u.
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth mora da se koristi unutar AuthProvider-a')
  }
  return context
}

export default AuthContext
