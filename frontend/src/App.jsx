import { useAuth } from './context/AuthContext'
import LoginForm from './components/LoginForm'
import ChatBox from './components/ChatBox'

/**
 * App - glavna komponenta aplikacije.
 *
 * Uslovno renderovanje:
 * - Ako korisnik NIJE ulogovan -> prikazuje LoginForm
 * - Ako korisnik JESTE ulogovan -> prikazuje ChatBox + Logout dugme
 */
export default function App() {
  const { user, logout } = useAuth()

  if (!user) {
    return <LoginForm />
  }

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* ChatBox zauzima ceo ekran */}
      <div className="flex-1 flex flex-col max-w-4xl w-full mx-auto border-x border-gray-800 relative">
        <ChatBox />

        {/* Logout dugme - fiksirano u donjem desnom uglu van ChatBox inputa */}
        <button
          onClick={logout}
          title="Odjavi se"
          className="
            absolute top-4 right-4 z-10
            bg-gray-800 hover:bg-red-900/50 hover:text-red-400
            text-gray-400 rounded-lg p-2.5 text-sm
            transition-all duration-200 border border-gray-700 hover:border-red-800/50
            shadow-lg
          "
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
          </svg>
        </button>
      </div>
    </div>
  )
}
