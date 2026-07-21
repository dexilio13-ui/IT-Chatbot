import { useState, useRef, useEffect } from 'react'
import { sendMessageStream } from '../services/api'
import { useAuth } from '../context/AuthContext'
import AdminPanel from './AdminPanel'


/**
 * ChatBox - glavni interfejs za razgovor sa RAG chatbot-om.
 *
 * Prikazuje listu poruka (korisnik / bot), input polje i dugme za slanje.
 * Koristi SSE strimovanje preko ReadableStream API-ja.
 */
export default function ChatBox() {
  const { user, logout } = useAuth()
  const [showAdmin, setShowAdmin] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      text: `Zdravo, ${user?.username || 'korisniče'}! Kako vam mogu pomoći?`,
    },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [selectedSource, setSelectedSource] = useState(null)
  const messagesEndRef = useRef(null)

  // Automatsko skrolovanje na dno kada stigne nova poruka
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  /**
   * Slanje poruke na backend putem SSE strima.
   *
   * Tokeni se dodaju u realnom vremenu u poslednju bot poruku,
   * a izvori (citations) se prikažu na kraju.
   */
  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    // Dodajemo korisničku poruku u listu
    const userMessage = { role: 'user', text }
    setMessages((prev) => [...prev, userMessage])

    // Pravimo unikatan ID za bot poruku da bismo je našli kasnije
    const botMessageId = Date.now()
    setMessages((prev) => [
      ...prev,
      { id: botMessageId, role: 'bot', text: '', sources: [] },
    ])

    setInput('')
    setSending(true)

    try {
      await sendMessageStream(
        text,
        // onToken - dodaje token u poslednju bot poruku (Immutable nacin)
        (token) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMessageId
                ? { ...msg, text: msg.text + token }
                : msg
            )
          )
        },
        // onSources - postavlja izvore na bot poruku (Immutable nacin)
        (sources) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMessageId
                ? { ...msg, sources: sources }
                : msg
            )
          )
        },
        // onDone
        () => setSending(false)
      )
    } catch (err) {
      console.error('Greška pri slanju poruke:', err)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === botMessageId && !msg.text
            ? { ...msg, text: '❌ Došlo je do greške. Molimo vas pokušajte ponovo.' }
            : msg
        )
      )
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header - responzivan: flex-wrap prelama u redove na mobilnom, manji padding na malim ekranima */}
      <div className="flex items-center justify-between px-4 py-3 sm:px-6 sm:py-4 border-b border-gray-800 flex-wrap gap-y-2">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br from-accent-500 to-accent-700 flex items-center justify-center text-lg shadow-lg shadow-accent-500/20 ${sending ? 'icon-streaming' : ''}`}>
            💻
          </div>
          <div>
            <h2 className="text-white font-semibold text-sm">IT Asistent</h2>
            <p className="text-gray-500 text-xs">Powered by FastAPI</p>
          </div>

          {/* Admin dugme - dostupno samo adminima */}
          {user?.is_admin && (
            <button
              onClick={() => setShowAdmin(true)}
              title="Admin Panel - Upload dokumenata"
              className="
                ml-4 bg-gray-800 hover:bg-accent-600 hover:text-white
                text-accent-400 rounded-lg px-3 py-1.5 text-xs font-medium
                transition-all duration-200 border border-gray-700 hover:border-accent-500/50
                shadow-lg flex items-center gap-1.5
              "
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Admin Panel
            </button>
          )}
        </div>
        {/* Desna strana: status korisnika + logout dugme - bez preklapanja */}
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-2 text-xs text-gray-500 whitespace-nowrap">
            <span className="w-2 h-2 rounded-full bg-green-500 shadow-lg shadow-green-500/50"></span>
            Prijavljen: <span className="text-gray-300 font-medium">{user?.username}</span>
          </span>
          <button
            onClick={logout}
            title="Odjavi se"
            className="
              bg-gray-800 hover:bg-red-900/50 hover:text-red-400
              text-gray-400 rounded-lg p-2.5 text-sm
              transition-all duration-200 border border-gray-700 hover:border-red-800/50
              shadow-lg
            "
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} message-enter group`}
            style={{ animationDelay: `${idx * 0.04}s` }}
          >
            <div
              className={`
                max-w-[75%] rounded-2xl px-5 py-3 text-sm leading-relaxed
                transition-all duration-200 hover:-translate-y-0.5
                ${
                  msg.role === 'user'
                    ? 'bg-accent-600 text-white rounded-br-md shadow-lg shadow-accent-600/20 hover:shadow-xl hover:shadow-accent-600/30'
                    : 'bg-gray-800 text-gray-200 rounded-bl-md border border-gray-700/50 hover:border-gray-600 hover:shadow-xl hover:shadow-black/20'
                }
              `}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>

              {/* Sources / Citations - klikabilna kartica */}
              {msg.sources?.length > 0 && msg.sources.map((s, i) => (
                <div
                  key={i}
                  onClick={() => setSelectedSource(s)}
                  className="
                    mt-3 p-3 rounded-xl border border-accent-500/20
                    bg-accent-500/5 hover:bg-accent-500/10
                    cursor-pointer transition-all duration-200
                    hover:border-accent-500/40 hover:-translate-y-0.5
                    hover:shadow-lg hover:shadow-accent-500/10
                    source-item group/source
                  "
                  style={{ animationDelay: `${i * 0.08}s` }}
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    <div className="w-6 h-6 rounded-lg bg-accent-500/20 flex items-center justify-center text-xs">
                      📄
                    </div>
                    <span className="text-xs font-medium text-accent-400 group-hover/source:text-accent-300 transition-colors">
                      {s.source || 'Izvor'}
                    </span>
                    <span className="text-[10px] text-gray-600 ml-auto">
                      klikni za prikaz
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] text-gray-500">
                    {s.score != null && (
                      <span className="px-1.5 py-0.5 rounded-md bg-gray-800 border border-gray-700">
                        relevatnost: {Math.min(Math.round(s.score * 100), 100)}%
                      </span>
                    )}
                    <span className="px-1.5 py-0.5 rounded-md bg-gray-800 border border-gray-700">
                      role ≥ {s.required_role_id}
                    </span>
                    <span className="ml-auto text-accent-500/60 group-hover/source:text-accent-400 transition-colors">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {sending && (
          <div className="flex justify-start message-enter">
            <div className="bg-gray-800 text-gray-400 rounded-2xl rounded-bl-md px-5 py-3 border border-gray-700/50">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 bg-gray-500 rounded-full loading-dot"></span>
                  <span className="w-2 h-2 bg-gray-500 rounded-full loading-dot"></span>
                  <span className="w-2 h-2 bg-gray-500 rounded-full loading-dot"></span>
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

      {/* Admin Panel modal */}
      {showAdmin && <AdminPanel onClose={() => setShowAdmin(false)} />}

      {/* Source Content Modal */}
      {selectedSource && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setSelectedSource(null)}
        >
          <div
            className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[80vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700 flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-accent-500/20 flex items-center justify-center text-base">
                  📄
                </div>
                <div>
                  <h3 className="text-white font-semibold text-sm">{selectedSource.source || 'Izvor'}</h3>
                  <p className="text-gray-500 text-xs">
                    Relevatnost: {selectedSource.score != null ? `${Math.min(Math.round(selectedSource.score * 100), 100)}%` : 'Nepoznata'}
                    {' · '}Role ≥ {selectedSource.required_role_id}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedSource(null)}
                className="text-gray-500 hover:text-gray-300 transition-colors p-1 rounded-lg hover:bg-gray-800"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <pre className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap font-sans">
                {selectedSource.content || 'Sadržaj nije dostupan'}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}