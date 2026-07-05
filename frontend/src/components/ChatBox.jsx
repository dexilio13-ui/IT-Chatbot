import { useState, useRef, useEffect } from 'react'
import { sendMessage } from '../services/api'
import { useAuth } from '../context/AuthContext'

/**
 * ChatBox - glavni interfejs za razgovor sa RAG chatbot-om.
 *
 * Prikazuje listu poruka (korisnik / bot), input polje i dugme za slanje.
 * Dizajniran sa Tailwind CSS u profesionalnom IT/Tech stilu.
 *
 * Lako se proširuje za SSE strimovanje - dovoljno je zameniti
 * fetch logiku u handleSend sa EventSource/ReadableStream.
 */
export default function ChatBox() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      text: `Zdravo, ${user?.username || 'korisniče'}! Kako vam mogu pomoći?`,
    },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef(null)

  // Automatsko skrolovanje na dno kada stigne nova poruka
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  /**
   * Slanje poruke na backend.
   *
   * Trenutno: POST /api/chat -> JSON { response: "tekst" }
   * Buduće: lako se zamenjuje sa SSE strimovanjem (EventSource).
   */
  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    // Dodajemo korisničku poruku u listu
    const userMessage = { role: 'user', text }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setSending(true)

    try {
      // Trenutno: klasičan POST zahtev koji vraća JSON
      // Buduće: ovde ide SSE strimovanje:
      //   const eventSource = new EventSource(`/api/chat/stream?message=${encodeURIComponent(text)}`)
      const data = await sendMessage(text)

      setMessages((prev) => [
        ...prev,
        { role: 'bot', text: data.response },
      ])
    } catch (err) {
      console.error('Greška pri slanju poruke:', err)
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          text: '❌ Došlo je do greške. Molimo vas pokušajte ponovo.',
        },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-500 to-accent-700 flex items-center justify-center text-lg shadow-lg shadow-accent-500/20">
            💻
          </div>
          <div>
            <h2 className="text-white font-semibold text-sm">RAG Chatbot</h2>
            <p className="text-gray-500 text-xs">Powered by FastAPI</p>
          </div>
        </div>
        <span className="flex items-center gap-2 text-xs text-gray-500">
          <span className="w-2 h-2 rounded-full bg-green-500 shadow-lg shadow-green-500/50"></span>
          Prijavljen: {user?.username}
        </span>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} message-enter`}
          >
            <div
              className={`
                max-w-[75%] rounded-2xl px-5 py-3 text-sm leading-relaxed
                ${
                  msg.role === 'user'
                    ? 'bg-accent-600 text-white rounded-br-md shadow-lg shadow-accent-600/20'
                    : 'bg-gray-800 text-gray-200 rounded-bl-md border border-gray-700/50'
                }
              `}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {sending && (
          <div className="flex justify-start message-enter">
            <div className="bg-gray-800 text-gray-400 rounded-2xl rounded-bl-md px-5 py-3 border border-gray-700/50">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
                <span className="text-xs">Razmišljam...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-800 px-6 py-4">
        <form onSubmit={handleSend} className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Unesite poruku..."
            disabled={sending}
            className="
              flex-1 bg-gray-800 text-white placeholder-gray-500 rounded-xl px-5 py-3
              border border-gray-700 focus:border-accent-500 focus:ring-1 focus:ring-accent-500/50
              outline-none transition-all duration-200 text-sm
              disabled:opacity-50 disabled:cursor-not-allowed
            "
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="
              bg-accent-600 hover:bg-accent-500 disabled:bg-gray-800 disabled:text-gray-600
              text-white rounded-xl px-5 py-3 font-medium text-sm
              transition-all duration-200 shadow-lg shadow-accent-600/20
              hover:shadow-accent-500/30 disabled:shadow-none
              flex items-center gap-2
            "
          >
            {sending ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Slanje...
              </>
            ) : (
              <>
                Pošalji
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
                </svg>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
