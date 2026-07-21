import { useState, useRef, useEffect } from 'react'
import { uploadDocument, listDocuments, deleteDocumentBySource } from '../services/api'

const ACCEPTED_FORMATS = '.pdf,.docx,.doc,.txt,.md,.csv'

export default function AdminPanel({ onClose }) {
  const [activeTab, setActiveTab] = useState('upload')
  const [file, setFile] = useState(null)
  const [requiredRoleId, setRequiredRoleId] = useState(1)
  const [sourceName, setSourceName] = useState('')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState(null)
  const [message, setMessage] = useState('')
  const [uploadResult, setUploadResult] = useState(null)
  const [documents, setDocuments] = useState([])
  const [loadingDocs, setLoadingDocs] = useState(false)
  const [docError, setDocError] = useState(null)
  const [deletingSource, setDeletingSource] = useState(null)
  const [deleteMsg, setDeleteMsg] = useState(null)
  const [deleteStatus, setDeleteStatus] = useState(null)
  const fileInputRef = useRef(null)

  const roles = [
    { id: 1, label: 'Kupac (javni dokumenti)', description: 'Vidljivo svim korisnicima' },
    { id: 2, label: 'Prodavac', description: 'Vidljivo prodavcima i serviserima' },
    { id: 3, label: 'Serviser', description: 'Vidljivo samo serviserima i adminu' },
  ]

  // Učitavanje dokumenata pri montiranju i kad se tab promeni na 'documents'
  useEffect(() => {
    if (activeTab === 'documents') {
      fetchDocuments()
    }
  }, [activeTab])

  async function fetchDocuments() {
    setLoadingDocs(true)
    setDocError(null)
    try {
      const data = await listDocuments()
      setDocuments(data.documents || [])
    } catch (err) {
      setDocError(err.response?.data?.detail || err.message || 'Greška pri učitavanju dokumenata.')
      setDocuments([])
    } finally {
      setLoadingDocs(false)
    }
  }

  async function handleUpload(e) {
    e.preventDefault()
    if (!file) return
    setUploading(true)
    setProgress(0)
    setStatus(null)
    setMessage('')
    setUploadResult(null)
    const startTime = performance.now()
    try {
      const result = await uploadDocument(file, requiredRoleId, sourceName.trim() || null, setProgress)
      const elapsed = ((performance.now() - startTime) / 1000).toFixed(1)
      const source = result.source || sourceName.trim() || file.name
      const chunks = result.chunks || 0
      const roleNames = { 1: 'Kupac', 2: 'Prodavac', 3: 'Serviser' }
      const roleName = roleNames[result.required_role_id] || `role ${result.required_role_id}`
      setUploadResult({ source, chunks, roleName, required_role_id: result.required_role_id, elapsed })
      setStatus('success')
      setMessage(`Dokument "${source}" je uspešno indeksiran.`)
      setFile(null)
      setSourceName('')
      if (fileInputRef.current) fileInputRef.current.value = ''
      // Unapred učitavamo listu dokumenata da bude spremna kad korisnik pređe
      fetchDocuments()
    } catch (err) {
      setStatus('error')
      setMessage(err.response?.data?.detail || err.message || 'Došlo je do greške.')
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  async function handleDelete(sourceName) {
    setDeleteMsg(null)
    setDeleteStatus(null)
    try {
      const result = await deleteDocumentBySource(sourceName)
      setDeleteStatus('success')
      setDeleteMsg(result.message || `Dokument '${sourceName}' obrisan.`)
      setDeletingSource(null)
      fetchDocuments()
    } catch (err) {
      setDeleteStatus('error')
      setDeleteMsg(err.response?.data?.detail || err.message || 'Greška pri brisanju.')
      setDeletingSource(null)
    }
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent-500 to-accent-700 flex items-center justify-center text-base shadow-lg shadow-accent-500/20">
              📄
            </div>
            <div>
              <h2 className="text-white font-semibold text-sm">Admin Panel</h2>
              <p className="text-gray-500 text-xs">Upravljanje bazom znanja</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 transition-colors p-1 rounded-lg hover:bg-gray-800">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tab navigacija */}
        <div className="flex border-b border-gray-700 flex-shrink-0">
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex-1 py-3 text-sm font-medium transition-all duration-200 relative ${
              activeTab === 'upload'
                ? 'text-accent-400'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            Upload dokumenta
            {activeTab === 'upload' && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-500 rounded-full" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`flex-1 py-3 text-sm font-medium transition-all duration-200 relative ${
              activeTab === 'documents'
                ? 'text-accent-400'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            Indeksirani dokumenti
            {activeTab === 'documents' && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-500 rounded-full" />
            )}
          </button>
        </div>

        {/* Sadržaj tabova */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'upload' ? (
            <form onSubmit={handleUpload} className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Dokument za upload</label>
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${
                    file ? 'border-accent-500/50 bg-accent-500/5' : 'border-gray-600 hover:border-gray-500 bg-gray-800/50 hover:bg-gray-800'
                  }`}
                >
                  <input ref={fileInputRef} type="file" accept={ACCEPTED_FORMATS} onChange={(e) => setFile(e.target.files[0])} className="hidden" />
                  {file ? (
                    <div className="space-y-2">
                      <div className="text-3xl">📎</div>
                      <p className="text-white font-medium text-sm">{file.name}</p>
                      <p className="text-gray-500 text-xs">{formatFileSize(file.size)}</p>
                      <button type="button" onClick={(e) => { e.stopPropagation(); setFile(null); if (fileInputRef.current) fileInputRef.current.value = '' }} className="text-xs text-red-400 hover:text-red-300">Ukloni fajl</button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="text-3xl">📂</div>
                      <p className="text-gray-400 text-sm font-medium">Klikni za upload dokumenta</p>
                      <p className="text-gray-600 text-xs">PDF, Word, TXT, Markdown, CSV</p>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label htmlFor="sourceName" className="block text-sm font-medium text-gray-400 mb-1.5">
                  Naziv izvora <span className="text-gray-600">(opciono)</span>
                </label>
                <input id="sourceName" type="text" value={sourceName} onChange={(e) => setSourceName(e.target.value)} placeholder="npr. Interni cenovnik" disabled={uploading}
                  className="w-full bg-gray-800 text-white placeholder-gray-600 rounded-xl px-4 py-2.5 border border-gray-700 focus:border-accent-500 focus:ring-1 focus:ring-accent-500/50 outline-none transition-all duration-200 text-sm disabled:opacity-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Dozvola za pregled (uloga)</label>
                <div className="space-y-2">
                  {roles.map((role) => (
                    <label key={role.id} className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-200 ${
                      requiredRoleId === role.id ? 'border-accent-500/50 bg-accent-500/10 text-white' : 'border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600'
                    } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                      <input type="radio" name="role" value={role.id} checked={requiredRoleId === role.id} onChange={() => setRequiredRoleId(role.id)} disabled={uploading} className="accent-accent-500" />
                      <div>
                        <p className="text-sm font-medium">{role.label}</p>
                        <p className="text-xs text-gray-500">{role.description}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {uploading && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>Uploadovanje...</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-accent-500 to-accent-600 rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
                  </div>
                </div>
              )}

              {message && status === 'error' && (
                <div className="rounded-xl px-4 py-3 text-sm message-enter bg-red-900/30 border border-red-800/50 text-red-400">
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5">❌</span>
                    <p>{message}</p>
                  </div>
                </div>
              )}

              {uploadResult && status === 'success' && (
                <div className="rounded-xl p-4 text-sm message-enter bg-green-900/30 border border-green-800/50">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center text-sm">✅</span>
                    <div>
                      <p className="text-green-400 font-medium text-sm">{uploadResult.source}</p>
                      <p className="text-green-600/80 text-[10px]">Uspešno indeksiran</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className="px-2 py-1 rounded-md bg-green-500/10 border border-green-500/20 text-green-400 text-[10px]">
                      📦 {uploadResult.chunks} chunk{uploadResult.chunks > 1 ? 'ova' : ''}
                    </span>
                    <span className="px-2 py-1 rounded-md bg-green-500/10 border border-green-500/20 text-green-400 text-[10px]">
                      🔒 {uploadResult.roleName}
                    </span>
                    <span className="px-2 py-1 rounded-md bg-green-500/10 border border-green-500/20 text-green-400 text-[10px]">
                      ⏱ {uploadResult.elapsed}s
                    </span>
                  </div>
                  <button
                    onClick={() => setActiveTab('documents')}
                    className="w-full py-2 rounded-lg bg-green-500/10 hover:bg-green-500/20 border border-green-500/30 text-green-400 text-xs font-medium transition-all duration-200"
                  >
                    Pogledaj u indeksiranim dokumentima →
                  </button>
                </div>
              )}

              <button type="submit" disabled={!file || uploading}
                className="w-full bg-accent-600 hover:bg-accent-500 disabled:bg-gray-800 disabled:text-gray-600 text-white rounded-xl px-4 py-3 font-medium text-sm transition-all duration-200 shadow-lg shadow-accent-600/20 hover:shadow-accent-500/30 disabled:shadow-none flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Uploadovanje...
                  </>
                ) : (
                  "Upload"
                )}
              </button>
            </form>
          ) : (
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-400">
                  {documents.length > 0
                    ? `${documents.length} indeksiranih dokumenata`
                    : 'Indeksirani dokumenti'}
                </p>
                <button
                  onClick={fetchDocuments}
                  disabled={loadingDocs}
                  className="text-xs text-accent-400 hover:text-accent-300 transition-colors disabled:opacity-50 flex items-center gap-1"
                >
                  <svg className={`w-3.5 h-3.5 ${loadingDocs ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Osveži
                </button>
              </div>

              {loadingDocs ? (
                <div className="flex items-center justify-center py-12">
                  <div className="flex flex-col items-center gap-3">
                    <svg className="animate-spin h-8 w-8 text-accent-500" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <p className="text-sm text-gray-500">Učitavanje dokumenata...</p>
                  </div>
                </div>
              ) : docError ? (
                <div className="rounded-xl px-4 py-3 text-sm bg-red-900/30 border border-red-800/50 text-red-400">
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5">❌</span>
                    <p>{docError}</p>
                  </div>
                </div>
              ) : documents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                  <span className="text-4xl mb-3">📭</span>
                  <p className="text-sm font-medium">Nema indeksiranih dokumenata</p>
                  <p className="text-xs mt-1">Upload-ujte dokument putem Upload tab-a</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {deleteMsg && (
                    <div className={`rounded-xl px-4 py-3 text-sm message-enter ${
                      deleteStatus === 'success' ? 'bg-green-900/30 border border-green-800/50 text-green-400' : 'bg-red-900/30 border border-red-800/50 text-red-400'
                    }`}>
                      <div className="flex items-start gap-2">
                        <span className="mt-0.5">{deleteStatus === 'success' ? '✅' : '❌'}</span>
                        <p>{deleteMsg}</p>
                      </div>
                    </div>
                  )}

                  {documents.map((doc, idx) => (
                    <div
                      key={doc.id || idx}
                      className="p-4 rounded-xl border border-gray-700/50 bg-gray-800/30 hover:bg-gray-800/50 transition-all duration-200 hover:border-gray-600 source-item"
                      style={{ animationDelay: `${idx * 0.05}s` }}
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-lg bg-accent-500/10 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                          📄
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-medium text-white truncate">
                              {doc.source}
                            </span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-accent-500/10 text-accent-400 border border-accent-500/20 whitespace-nowrap">
                              {doc.chunks} chunk{doc.chunks > 1 ? 'ova' : ''}
                            </span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-gray-800 text-gray-500 border border-gray-700 whitespace-nowrap">
                              role ≥ {doc.required_role_id}
                            </span>
                          </div>
                          {doc.text_preview && (
                            <p className="text-xs text-gray-500 mt-1.5 line-clamp-2">
                              {doc.text_preview}...
                            </p>
                          )}
                        </div>

                        {/* Delete dugme */}
                        <button
                          onClick={() => setDeletingSource(doc.source)}
                          title="Obriši dokument"
                          className="
                            flex-shrink-0 p-2 rounded-lg
                            text-gray-600 hover:text-red-400 hover:bg-red-900/20
                            transition-all duration-200
                          "
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Confirmation dialog za brisanje */}
      {deletingSource && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setDeletingSource(null)}
        >
          <div
            className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-red-900/30 flex items-center justify-center">
                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div>
                <h3 className="text-white font-semibold text-sm">Obriši dokument?</h3>
                <p className="text-gray-400 text-xs mt-1">
                  Ova akcija će trajno obrisati <span className="text-gray-200 font-medium">{deletingSource}</span>
                  {' '}i sve njegove chunk-ove iz baze znanja.
                </p>
              </div>
              <div className="flex gap-3 w-full">
                <button
                  onClick={() => setDeletingSource(null)}
                  className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl py-2.5 text-sm font-medium transition-all duration-200 border border-gray-700"
                >
                  Otkaži
                </button>
                <button
                  onClick={() => handleDelete(deletingSource)}
                  className="flex-1 bg-red-600 hover:bg-red-500 text-white rounded-xl py-2.5 text-sm font-medium transition-all duration-200 shadow-lg shadow-red-600/20"
                >
                  Obriši
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
