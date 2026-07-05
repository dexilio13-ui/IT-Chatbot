import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

/**
 * LoginForm - forma za prijavu sa JWT autentifikacijom.
 *
 * Šalje username/password na /api/auth/login u
 * application/x-www-form-urlencoded formatu (OAuth2PasswordRequestForm).
 */
export default function LoginForm() {
  const { login, loading, error } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!username.trim() || !password.trim()) return

    try {
      await login(username.trim(), password)
    } catch {
      // Greška je već postavljena u AuthContext-u
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-sm">
        {/* Logo / Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-accent-500 to-accent-700 flex items-center justify-center text-3xl shadow-2xl shadow-accent-500/20">
            💻
          </div>
          <h1 className="text-2xl font-bold text-white">RAG Chatbot</h1>
          <p className="text-gray-500 text-sm mt-1">Prijavite se za nastavak</p>
        </div>

        {/* Login form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-400 mb-1.5">
              Korisničko ime
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="serviser"
              autoFocus
              disabled={loading}
              className="
                w-full bg-gray-800 text-white placeholder-gray-500 rounded-xl px-4 py-3
                border border-gray-700 focus:border-accent-500 focus:ring-1 focus:ring-accent-500/50
                outline-none transition-all duration-200 text-sm
                disabled:opacity-50 disabled:cursor-not-allowed
              "
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-400 mb-1.5">
              Lozinka
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••"
              disabled={loading}
              className="
                w-full bg-gray-800 text-white placeholder-gray-500 rounded-xl px-4 py-3
                border border-gray-700 focus:border-accent-500 focus:ring-1 focus:ring-accent-500/50
                outline-none transition-all duration-200 text-sm
                disabled:opacity-50 disabled:cursor-not-allowed
              "
            />
          </div>

          {/* Error message */}
          {error && (
            <div className="bg-red-900/30 border border-red-800/50 text-red-400 text-sm rounded-xl px-4 py-3 message-enter">
              {error}
            </div>
          )}

          {/* Test credentials hint */}
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl px-4 py-3 text-xs text-gray-500 space-y-0.5">
            <p className="font-medium text-gray-400 mb-1">Test nalozi:</p>
            <p>serviser / 123</p>
            <p>prodavac / 123</p>
            <p>kupac / 123</p>
          </div>

          <button
            type="submit"
            disabled={loading || !username.trim() || !password.trim()}
            className="
              w-full bg-accent-600 hover:bg-accent-500 disabled:bg-gray-800 disabled:text-gray-600
              text-white rounded-xl px-4 py-3 font-medium text-sm
              transition-all duration-200
              shadow-lg shadow-accent-600/20 hover:shadow-accent-500/30 disabled:shadow-none
              flex items-center justify-center gap-2
            "
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Prijavljivanje...
              </>
            ) : (
              'Prijavi se'
            )}
          </button>
        </form>

        {/* Footer */}
        <p className="text-center text-xs text-gray-600 mt-8">
          RAG Chatbot &copy; 2026
        </p>
      </div>
    </div>
  )
}
