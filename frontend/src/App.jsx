import { useAuth } from './context/AuthContext'
import LoginForm from './components/LoginForm'
import ChatBox from './components/ChatBox'

/**
 * App - glavna komponenta aplikacije.
 *
 * Uslovno renderovanje:
 * - Ako korisnik NIJE ulogovan NI gost -> LoginForm
 * - Ako korisnik JESTE ulogovan ILI je gost -> ChatBox
 */
export default function App() {
  const { user, isGuest, isActive } = useAuth()

  // Prikazi LoginForm samo ako nema aktivnog korisnika (ni gost ni ulogovan)
  if (!isActive) {
    return <LoginForm />
  }

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      <div className="flex-1 flex flex-col max-w-4xl w-full mx-auto border-x border-gray-800 relative">
        <ChatBox />
      </div>
    </div>
  )
}