import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { loginUser } from '../services/api'

const AuthContext = createContext(null)

/**
 * Dekodira JWT token i vraća payload (bez validacije potpisa).
 * @param {string} token - JWT token
 * @returns {object|null} Dekodirani payload ili null ako je nevalidan
 */
function decodeJwt(token) {
  try {
    const payload = token.split('.')[1]
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64))
  } catch {
    return null
  }
}

/**
 * AuthProvider obmotava celu aplikaciju i upravlja stanjem
 * autentifikacije (JWT token, korisničko ime, admin status, gost mod).
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('user')
    return storedUser ? JSON.parse(storedUser) : null
  })

  const [token, setToken] = useState(() => {
    return localStorage.getItem('access_token') || null
  })

  const [isGuest, setIsGuest] = useState(() => {
    return localStorage.getItem('guest_id') ? true : false
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  /**
   * Login funkcija - šalje POST zahtev na /api/auth/login.
   */
  const login = useCallback(async (username, password) => {
    setLoading(true)
    setError(null)

    try {
      const data = await loginUser(username, password)
      const accessToken = data.access_token
      const payload = decodeJwt(accessToken)
      const isAdmin = payload?.is_admin || false
      const roleId = payload?.role_id || 1

      // Ako je bio gost, cistimo gost sesiju
      localStorage.removeItem('guest_id')

      localStorage.setItem('access_token', accessToken)
      localStorage.setItem(
        'user',
        JSON.stringify({ username, is_admin: isAdmin, role_id: roleId })
      )

      setToken(accessToken)
      setUser({ username, is_admin: isAdmin, role_id: roleId })
      setIsGuest(false)
    } catch (err) {
      if (err.response) {
        const { status, data } = err.response
        if (status === 429) {
          setError(
            data?.captcha_required
              ? 'Previše neuspešnih pokušaja. Captcha verifikacija je zahtevana.'
              : 'Previše zahteva. Molimo sačekajte pre sledećeg pokušaja.'
          )
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
   * Guest login - kreira gost sesiju bez JWT autentifikacije.
   */
  const loginAsGuest = useCallback(() => {
    const guestId = crypto.randomUUID().slice(0, 8)
    localStorage.setItem('guest_id', guestId)
    setIsGuest(true)
    setUser({ username: 'gost', is_admin: false, role_id: 1, isGuest: true })
    setError(null)
  }, [])

  /**
   * Logout - čisti i gost i regular sesiju.
   */
  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    localStorage.removeItem('guest_id')
    setToken(null)
    setUser(null)
    setIsGuest(false)
    setError(null)
  }, [])

  // Sluša custom 'auth:unauthorized' događaj
  useEffect(() => {
    function handleUnauthorized() {
      if (!isGuest) {
        setToken(null)
        setUser(null)
        setError(null)
      }
    }
    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [isGuest])

  /**
   * Dohvata guest ID iz localStorage.
   */
  const getGuestId = useCallback(() => {
    return localStorage.getItem('guest_id')
  }, [])

  // Korisnik je aktivan ako je ulogovan ili je gost
  const isActive = !!(user || isGuest)

  return (
    <AuthContext.Provider value={{ user, token, loading, error, login, logout, loginAsGuest, isGuest, getGuestId, isActive }}>
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
