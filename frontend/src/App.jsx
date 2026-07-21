import { useAuth } from './context/AuthContext'
import LoginForm from './components/LoginForm'
import ChatBox from './components/ChatBox'

/**
 * App - glavna komponenta aplikacije.
 *
 * Uslovno renderovanje:
 * - Ako korisnik NIJE ulogovan -> prikazuje LoginForm
 * - Ako korisnik JESTE ulogovan -> prikazuje ChatBox
 */
export default function App() {
  const { user } = useAuth()

  if (!user) {
    return <LoginForm />
  }

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* ChatBox zauzima ceo ekran, a sve kontrole su sada čisto integrisane unutar njega */}
      <div className="flex-1 flex flex-col max-w-4xl w-full mx-auto border-x border-gray-800 relative">
        <ChatBox />
      </div>
    </div>
  )
}