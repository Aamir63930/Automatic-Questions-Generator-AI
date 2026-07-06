import os

# ══════════════════════════════════════════
# FIX 1: Dark/Light mode - Navbar fix
# ══════════════════════════════════════════
os.makedirs("../frontend/components/student", exist_ok=True)
with open("../frontend/components/student/StudentNavbar.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useEffect, useState } from 'react'
import { useSession, signOut } from 'next-auth/react'
import Link from 'next/link'

export default function StudentNavbar() {
  const { data: session } = useSession()
  const [dark, setDark] = useState(true)
  const [notifCount, setNotifCount] = useState(0)

  useEffect(() => {
    const saved = localStorage.getItem('theme') || 'dark'
    setDark(saved === 'dark')
    applyTheme(saved === 'dark')
  }, [])

  useEffect(() => {
    const token = session?.user?.backendToken
    if (!token) return
    fetch((process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1') + '/notifications', {
      headers: { Authorization: 'Bearer ' + token }
    }).then(r => r.json()).then(d => {
      if (d.success) setNotifCount(d.data.filter((n: any) => !n.isRead).length)
    }).catch(() => {})
  }, [session])

  const applyTheme = (isDark: boolean) => {
    if (isDark) {
      document.documentElement.classList.add('dark')
      document.documentElement.style.colorScheme = 'dark'
    } else {
      document.documentElement.classList.remove('dark')
      document.documentElement.style.colorScheme = 'light'
      document.documentElement.style.background = '#f8fafc'
    }
  }

  const toggleTheme = () => {
    const newDark = !dark
    setDark(newDark)
    localStorage.setItem('theme', newDark ? 'dark' : 'light')
    applyTheme(newDark)
    // Force page bg
    document.body.style.background = newDark ? '#020617' : '#f1f5f9'
  }

  return (
    <header className="h-14 border-b border-white/5 bg-slate-900/80 backdrop-blur flex items-center justify-between px-6 flex-shrink-0">
      <p className="text-sm font-medium text-slate-400">Student Dashboard</p>
      <div className="flex items-center gap-3">
        {/* Dark/Light toggle */}
        <button onClick={toggleTheme}
          className="w-9 h-9 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center hover:border-white/20 transition-all text-lg"
          title={dark ? 'Switch to Light' : 'Switch to Dark'}>
          {dark ? '🌙' : '☀️'}
        </button>

        {/* Notifications */}
        <Link href="/student/notifications">
          <button className="relative w-9 h-9 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center hover:border-white/20 transition-all">
            <span className="text-lg">🔔</span>
            {notifCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-blue-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold">
                {notifCount > 9 ? '9+' : notifCount}
              </span>
            )}
          </button>
        </Link>

        {/* Profile */}
        <button onClick={() => signOut({ callbackUrl: '/login' })}
          className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-xl bg-slate-800 border border-white/10 hover:border-white/20 transition-all">
          {session?.user?.image ? (
            <img src={session.user.image} className="w-7 h-7 rounded-full object-cover" alt="" />
          ) : (
            <div className="w-7 h-7 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 text-xs font-bold">
              {session?.user?.name?.charAt(0) || 'S'}
            </div>
          )}
          <div className="text-left hidden sm:block">
            <p className="text-xs font-medium text-white leading-none">{session?.user?.name?.split(' ')[0] || 'Student'}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Sign out</p>
          </div>
        </button>
      </div>
    </header>
  )
}
""")
print("StudentNavbar done!")

# Teacher Navbar dark/light fix
os.makedirs("../frontend/components/ui", exist_ok=True)
with open("../frontend/components/ui/Navbar.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useEffect, useState } from 'react'
import { useSession, signOut } from 'next-auth/react'
import Link from 'next/link'

export default function Navbar() {
  const { data: session } = useSession()
  const [dark, setDark] = useState(true)
  const [notifCount, setNotifCount] = useState(0)

  useEffect(() => {
    const saved = localStorage.getItem('theme') || 'dark'
    setDark(saved === 'dark')
    applyTheme(saved === 'dark')
  }, [])

  useEffect(() => {
    const token = session?.user?.backendToken
    if (!token) return
    fetch((process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1') + '/notifications', {
      headers: { Authorization: 'Bearer ' + token }
    }).then(r => r.json()).then(d => {
      if (d.success) setNotifCount(d.data.filter((n: any) => !n.isRead).length)
    }).catch(() => {})
  }, [session])

  const applyTheme = (isDark: boolean) => {
    document.documentElement.classList.toggle('dark', isDark)
    document.body.style.background = isDark ? '#020617' : '#f1f5f9'
    document.documentElement.style.colorScheme = isDark ? 'dark' : 'light'
  }

  const toggleTheme = () => {
    const newDark = !dark
    setDark(newDark)
    localStorage.setItem('theme', newDark ? 'dark' : 'light')
    applyTheme(newDark)
  }

  return (
    <header className="h-14 border-b border-white/5 bg-slate-900/80 backdrop-blur flex items-center justify-between px-6 flex-shrink-0">
      <p className="text-sm font-medium text-slate-400">Dashboard</p>
      <div className="flex items-center gap-3">
        <button onClick={toggleTheme}
          className="w-9 h-9 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center hover:border-white/20 transition-all text-lg"
          title={dark ? 'Light Mode' : 'Dark Mode'}>
          {dark ? '🌙' : '☀️'}
        </button>

        <Link href="/teacher/notifications">
          <button className="relative w-9 h-9 rounded-xl bg-slate-800 border border-white/10 flex items-center justify-center hover:border-white/20 transition-all">
            <span className="text-lg">🔔</span>
            {notifCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-blue-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold">
                {notifCount > 9 ? '9+' : notifCount}
              </span>
            )}
          </button>
        </Link>

        <div className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-xl bg-slate-800 border border-white/10">
          {session?.user?.image ? (
            <img src={session.user.image} className="w-7 h-7 rounded-full object-cover" alt="" />
          ) : (
            <div className="w-7 h-7 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold">
              {session?.user?.name?.charAt(0) || 'T'}
            </div>
          )}
          <div className="hidden sm:block">
            <p className="text-xs font-medium text-white leading-none">{session?.user?.name?.split(' ')[0] || 'Teacher'}</p>
            <button onClick={() => signOut({ callbackUrl: '/login' })} className="text-[10px] text-red-400 hover:text-red-300 mt-0.5">Sign out</button>
          </div>
        </div>
      </div>
    </header>
  )
}
""")
print("Navbar done!")

# ══════════════════════════════════════════
# FIX 2: Floating AI Chatbot Widget
# ══════════════════════════════════════════
with open("../frontend/components/student/FloatingChatbot.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useRef, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Msg = { id: string; role: 'user' | 'assistant'; text: string }

const SUBJECTS = [
  'Data Structures', 'Operating Systems', 'Computer Networks',
  'DBMS', 'Software Engineering', 'AI & ML', 'Web Technologies', 'Mathematics',
]

export default function FloatingChatbot() {
  const { data: session } = useSession()
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([
    { id: 'w', role: 'assistant', text: 'Hi! 👋 I am your AI Study Assistant. Ask me anything about your subjects!' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [subject, setSubject] = useState('General')
  const [showSubjects, setShowSubjects] = useState(false)
  const [history, setHistory] = useState<{role:string;content:string}[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const token = session?.user?.backendToken

  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [msgs, open])

  const send = async (text?: string) => {
    const msg = text || input.trim()
    if (!msg || loading || !token) return
    const uid = Date.now().toString()
    const userMsg: Msg = { id: uid, role: 'user', text: msg }
    const newHist = [...history, { role: 'user', content: msg }]
    setMsgs(p => [...p, userMsg])
    setHistory(newHist)
    if (!text) setInput('')
    setLoading(true)

    try {
      const res = await fetch(API + '/ai/chat', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, subject, history: history.slice(-4) })
      })
      const d = await res.json()
      const reply = d.success ? d.data.reply : 'Sorry, AI unavailable right now.'
      const botMsg: Msg = { id: uid + '_b', role: 'assistant', text: reply }
      setMsgs(p => [...p, botMsg])
      setHistory([...newHist, { role: 'assistant', content: reply }])
    } catch {
      setMsgs(p => [...p, { id: uid + '_e', role: 'assistant', text: '❌ Cannot connect to AI. Is backend running?' }])
    }
    setLoading(false)
  }

  const fmt = (t: string) => t
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code style="background:#1e293b;padding:1px 4px;border-radius:4px;font-size:11px">$1</code>')
    .replace(/\\n/g, '<br/>')

  const QUICK = ['Explain with example', 'Practice questions', 'Key topics for exam']

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-2xl flex items-center justify-center transition-all hover:scale-110 active:scale-95"
        style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', boxShadow: '0 8px 32px rgba(59,130,246,0.4)' }}
      >
        {open ? (
          <span className="text-white text-2xl font-bold">✕</span>
        ) : (
          <span className="text-2xl">🤖</span>
        )}
        {!open && msgs.length > 1 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-green-400 rounded-full flex items-center justify-center text-[10px] font-bold text-white">
            {msgs.filter(m => m.role === 'assistant').length - 1 || ''}
          </span>
        )}
      </button>

      {/* Chat window */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-80 sm:w-96 rounded-2xl overflow-hidden shadow-2xl"
          style={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', maxHeight: '70vh', display: 'flex', flexDirection: 'column' }}>

          {/* Header */}
          <div className="p-4 flex items-center gap-3 flex-shrink-0" style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
            <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-xl">🤖</div>
            <div className="flex-1">
              <p className="text-sm font-bold text-white">AI Study Assistant</p>
              <p className="text-xs text-white/70">Always here to help!</p>
            </div>
            {/* Subject picker */}
            <div className="relative">
              <button onClick={() => setShowSubjects(!showSubjects)}
                className="text-xs bg-white/20 text-white px-2 py-1 rounded-lg hover:bg-white/30 max-w-[80px] truncate">
                {subject} ▼
              </button>
              {showSubjects && (
                <div className="absolute right-0 top-full mt-1 w-44 rounded-xl overflow-hidden shadow-2xl z-10"
                  style={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)' }}>
                  {['General', ...SUBJECTS].map(s => (
                    <button key={s} onClick={() => { setSubject(s); setShowSubjects(false) }}
                      className={'w-full text-left px-3 py-2 text-xs transition-all ' + (subject === s ? 'bg-blue-500 text-white' : 'text-slate-300 hover:bg-slate-700')}>
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ minHeight: 0 }}>
            {msgs.map(m => (
              <div key={m.id} className={'flex ' + (m.role === 'user' ? 'justify-end' : 'justify-start')}>
                <div className={'max-w-[85%] px-3 py-2 rounded-2xl text-xs leading-relaxed ' +
                  (m.role === 'user'
                    ? 'text-white rounded-br-sm'
                    : 'text-slate-200 rounded-bl-sm')}
                  style={{ background: m.role === 'user' ? '#3b82f6' : '#1e293b', border: m.role === 'assistant' ? '1px solid rgba(255,255,255,0.05)' : 'none' }}
                  dangerouslySetInnerHTML={{ __html: fmt(m.text) }}
                />
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="px-3 py-2 rounded-2xl rounded-bl-sm flex gap-1"
                  style={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.05)' }}>
                  {[0,1,2].map(i => <div key={i} className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: i*150+'ms' }} />)}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick prompts */}
          {msgs.length <= 2 && (
            <div className="px-4 flex gap-2 flex-wrap flex-shrink-0">
              {QUICK.map(q => (
                <button key={q} onClick={() => send(q)}
                  className="text-[10px] px-2 py-1 rounded-full text-blue-400 hover:bg-blue-500/10 transition-all"
                  style={{ border: '1px solid rgba(59,130,246,0.3)' }}>
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="p-3 flex gap-2 flex-shrink-0" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') send() }}
              placeholder="Ask anything..."
              disabled={loading}
              className="flex-1 rounded-xl px-3 py-2 text-xs text-white outline-none"
              style={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)' }}
            />
            <button onClick={() => send()} disabled={!input.trim() || loading}
              className="w-9 h-9 rounded-xl flex items-center justify-center text-white transition-all"
              style={{ background: input.trim() && !loading ? '#3b82f6' : '#334155' }}>
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  )
}
""")
print("FloatingChatbot done!")

# Add FloatingChatbot to student layout
with open("../frontend/app/(student)/layout.tsx", "r", encoding="utf-8") as f:
    layout = f.read()

if "FloatingChatbot" not in layout:
    layout = layout.replace(
        "import StudentNavbar from '@/components/student/StudentNavbar'",
        "import StudentNavbar from '@/components/student/StudentNavbar'\nimport FloatingChatbot from '@/components/student/FloatingChatbot'"
    )
    layout = layout.replace(
        "<main className=\"flex-1 p-6 overflow-auto\">{children}</main>",
        "<main className=\"flex-1 p-6 overflow-auto\">{children}</main>\n        <FloatingChatbot />"
    )
    with open("../frontend/app/(student)/layout.tsx", "w", encoding="utf-8") as f:
        f.write(layout)
    print("FloatingChatbot added to layout!")
else:
    print("Already added")

print("\n=== ALL UI FIXES DONE ===")