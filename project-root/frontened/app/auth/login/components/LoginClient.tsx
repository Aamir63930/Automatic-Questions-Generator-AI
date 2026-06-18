'use client'

import { useState } from 'react'
import { signIn } from 'next-auth/react'

const COLLEGES = [
  { id: 'nit', name: 'NIT Kurukshetra' },
  { id: 'dtu', name: 'DTU Delhi' },
  { id: 'bits', name: 'BITS Pilani' },
  { id: 'iit', name: 'IIT Delhi' },
  { id: 'mdu', name: 'MDU Rohtak' },
]

export default function LoginClient() {
  const [selectedId, setSelectedId] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const selected = COLLEGES.find((c) => c.id === selectedId)

  const handleLogin = async () => {
    if (!selectedId) {
      setError('Please select your institution first')
      return
    }
    setIsLoading(true)
    setError('')
    await signIn('microsoft-entra-id', { callbackUrl: '/teacher' })
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="flex w-full max-w-[860px] min-h-[520px] rounded-2xl border border-white/5 bg-slate-900 overflow-hidden shadow-2xl">

        <div className="hidden md:flex w-[320px] flex-shrink-0 bg-slate-900 border-r border-white/5 p-10 flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 mb-10">
              <div className="w-9 h-9 rounded-xl bg-blue-500 flex items-center justify-center text-white font-bold text-lg">✦</div>
              <div>
                <p className="text-sm font-semibold text-white leading-tight">AI Question Paper Generator</p>
                <p className="text-xs text-slate-500">Academic Management System</p>
              </div>
            </div>
            <h2 className="text-xl font-semibold text-white leading-snug mb-8">
              Smarter exams,<br />
              <span className="text-blue-400">powered by AI</span>
            </h2>
            <ul className="space-y-5">
              {[
                { icon: '🤖', title: 'AI Question Generation', desc: '2, 5, 10 marks — difficulty controlled' },
                { icon: '📄', title: 'Branded PDF Export', desc: 'Professional papers with college branding' },
                { icon: '💬', title: 'RAG Chatbot', desc: 'Subject-wise AI from uploaded materials' },
                { icon: '🏫', title: 'Multi-Tenant', desc: 'Isolated data per institution' },
              ].map((f) => (
                <li key={f.title} className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">{f.icon}</div>
                  <div>
                    <p className="text-sm font-medium text-white">{f.title}</p>
                    <p className="text-xs text-slate-500 leading-snug">{f.desc}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <div className="border-t border-white/5 pt-4 mt-6">
            <p className="text-xs text-slate-600">Secured with Azure AD · JWT Auth · RBAC</p>
          </div>
        </div>

        <div className="flex-1 p-10 flex flex-col justify-center bg-slate-800/30">
          <h1 className="text-2xl font-semibold text-white mb-1">Welcome back 👋</h1>
          <p className="text-sm text-slate-400 mb-8 leading-relaxed">
            Select your institution and sign in with your Microsoft Outlook account.
          </p>
          <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">
            Select Institution
          </label>
          <select
            value={selectedId}
            onChange={(e) => { setSelectedId(e.target.value); setError('') }}
            className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none mb-2"
          >
            <option value="">— Choose your college —</option>
            {COLLEGES.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          {error && <p className="text-xs text-red-400 mb-3">{error}</p>}
          {selected && (
            <div className="mb-5">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-slate-400">{selected.name}</span>
                <span className="text-xs text-green-400 bg-green-400/10 px-2 py-0.5 rounded border border-green-400/20">✓ Active Tenant</span>
              </div>
              <div className="h-0.5 bg-white/5 rounded-full">
                <div className="h-full w-full bg-blue-500 rounded-full transition-all duration-500" />
              </div>
            </div>
          )}
          <div className="flex gap-2 flex-wrap mb-5">
            {['👤 Admin', '🎓 HOD', '📚 Teacher', '🧑‍🎓 Student'].map((r) => (
              <span key={r} className="text-xs text-slate-500 border border-white/10 px-2.5 py-1 rounded-md">{r}</span>
            ))}
          </div>
          <div className="flex gap-2 bg-blue-500/5 border border-blue-500/15 rounded-xl p-3 mb-5">
            <span className="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0 mt-0.5">i</span>
            <p className="text-xs text-slate-400 leading-relaxed">
              Your role will be automatically determined from your Outlook account. Please use your institutional email.
            </p>
          </div>
          <div className="flex items-center gap-3 mb-5 text-xs text-slate-600">
            <div className="flex-1 h-px bg-white/5" />
            Sign in with
            <div className="flex-1 h-px bg-white/5" />
          </div>
          <button
            onClick={handleLogin}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 py-3 bg-white text-slate-800 font-medium text-sm rounded-xl hover:bg-slate-100 transition-all disabled:opacity-60"
          >
            <div className="grid grid-cols-2 gap-0.5 w-4 h-4 flex-shrink-0">
              <div className="bg-[#f25022] rounded-[1px]" />
              <div className="bg-[#7fba00] rounded-[1px]" />
              <div className="bg-[#00a4ef] rounded-[1px]" />
              <div className="bg-[#ffb900] rounded-[1px]" />
            </div>
            {isLoading ? 'Redirecting to Microsoft...' : 'Continue with Microsoft'}
          </button>
          <p className="mt-5 text-xs text-slate-600 text-center">
            By signing in, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>

      </div>
    </div>
  )
}