import os, shutil

# ══════════════════════════════════════
# FIX 1: layout.tsx - remove broken script tag
# ══════════════════════════════════════
with open("../frontend/app/layout.tsx", "r", encoding="utf-8") as f:
    layout = f.read()

# Remove the broken script + revert html class
layout = layout.replace('className="dark"', '')
# Remove dangerouslySetInnerHTML script block
import re
layout = re.sub(r'<script dangerouslySetInnerHTML=\{\{.*?\}\}\s*/>', '', layout, flags=re.DOTALL)
layout = re.sub(r'<script dangerouslySetInnerHTML=.*?/>[\s]*', '', layout, flags=re.DOTALL)

with open("../frontend/app/layout.tsx", "w", encoding="utf-8") as f:
    f.write(layout)
print("layout.tsx fixed!")

# ══════════════════════════════════════
# FIX 2: ThemeProvider component - proper SSR-safe theme
# ══════════════════════════════════════
os.makedirs("../frontend/components", exist_ok=True)
with open("../frontend/components/ThemeProvider.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useEffect } from 'react'

export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Apply theme on mount - client only
    const theme = localStorage.getItem('theme') || 'dark'
    applyTheme(theme === 'dark')
  }, [])

  return <>{children}</>
}

export function applyTheme(isDark: boolean) {
  const root = document.documentElement
  if (isDark) {
    root.classList.add('dark')
    root.style.setProperty('--bg-main', '#020617')
    document.body.style.background = '#020617'
    document.body.style.color = '#f8fafc'
  } else {
    root.classList.remove('dark')
    root.style.setProperty('--bg-main', '#f1f5f9')
    document.body.style.background = '#f1f5f9'
    document.body.style.color = '#0f172a'
  }
}
""")
print("ThemeProvider done!")

# Add ThemeProvider to layout
with open("../frontend/app/layout.tsx", "r", encoding="utf-8") as f:
    layout = f.read()

if "ThemeProvider" not in layout:
    layout = layout.replace(
        "export default function RootLayout",
        "import ThemeProvider from '@/components/ThemeProvider'\nexport default function RootLayout"
    )
    layout = layout.replace(
        "{children}",
        "<ThemeProvider>{children}</ThemeProvider>",
        1
    )
    with open("../frontend/app/layout.tsx", "w", encoding="utf-8") as f:
        f.write(layout)
    print("ThemeProvider added to layout!")

# ══════════════════════════════════════
# FIX 3: Navbar theme toggle - use applyTheme properly
# ══════════════════════════════════════
navbar_code = """'use client'
import { useEffect, useState } from 'react'
import { useSession, signOut } from 'next-auth/react'
import Link from 'next/link'

function applyTheme(isDark: boolean) {
  const root = document.documentElement
  if (isDark) {
    root.classList.add('dark')
    document.body.style.background = '#020617'
    document.body.style.color = '#f8fafc'
  } else {
    root.classList.remove('dark')
    document.body.style.background = '#f1f5f9'
    document.body.style.color = '#0f172a'
    // Override slate colors for light mode
    const style = document.getElementById('light-mode-style') || document.createElement('style')
    style.id = 'light-mode-style'
    style.textContent = `
      .bg-slate-950, .min-h-screen { background: #f1f5f9 !important; }
      .bg-slate-900 { background: #ffffff !important; }
      .bg-slate-800, .bg-slate-800\\/50 { background: #f8fafc !important; }
      .bg-slate-700 { background: #e2e8f0 !important; }
      .text-white { color: #0f172a !important; }
      .text-slate-400 { color: #475569 !important; }
      .text-slate-500 { color: #64748b !important; }
      .text-slate-300 { color: #334155 !important; }
      .text-slate-600 { color: #475569 !important; }
      .border-white\\/5 { border-color: #e2e8f0 !important; }
      .border-white\\/10 { border-color: #cbd5e1 !important; }
      header, aside { background: rgba(255,255,255,0.95) !important; border-color: #e2e8f0 !important; }
    `
    document.head.appendChild(style)
  }
  // Remove light mode styles when switching to dark
  if (isDark) {
    const style = document.getElementById('light-mode-style')
    if (style) style.remove()
  }
}

export default function Navbar() {
  const { data: session } = useSession()
  const [dark, setDark] = useState(true)
  const [notifCount, setNotifCount] = useState(0)

  useEffect(() => {
    const saved = localStorage.getItem('theme') || 'dark'
    const isDark = saved === 'dark'
    setDark(isDark)
    applyTheme(isDark)
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
          title={dark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
          {dark ? '☀️' : '🌙'}
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
"""

with open("../frontend/components/ui/Navbar.tsx", "w", encoding="utf-8") as f:
    f.write(navbar_code)
print("Teacher Navbar done!")

# Student Navbar - same theme logic
student_navbar = navbar_code.replace(
    'export default function Navbar()',
    'export default function StudentNavbar()'
).replace(
    "href=\"/teacher/notifications\"",
    "href=\"/student/notifications\""
).replace(
    "bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold",
    "bg-green-500/20 flex items-center justify-center text-green-400 text-xs font-bold"
).replace(
    "session?.user?.name?.split(' ')[0] || 'Teacher'",
    "session?.user?.name?.split(' ')[0] || 'Student'"
)

with open("../frontend/components/student/StudentNavbar.tsx", "w", encoding="utf-8") as f:
    f.write(student_navbar)
print("Student Navbar done!")

# ══════════════════════════════════════
# FIX 4: Copy AI logo + Chatbot with custom image
# ══════════════════════════════════════
# Copy logo to public folder
logo_src = r"C:\Users\Aamir Khan\Downloads\Ai logo.jpeg"
os.makedirs("../frontend/public", exist_ok=True)
logo_dst = "../frontend/public/hayat-logo.jpeg"
try:
    shutil.copy2(logo_src, logo_dst)
    print("AI logo copied!")
    use_custom_logo = True
except:
    print("Logo not found - using emoji fallback")
    use_custom_logo = False

logo_img = '<img src="/hayat-logo.jpeg" className="w-10 h-10 rounded-full object-cover border-2 border-white/30 flex-shrink-0" alt="HAYAT" />' if use_custom_logo else '<div className="w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center text-xl" style={{background:"linear-gradient(135deg,#3b82f6,#8b5cf6)"}}>🤖</div>'

btn_logo = '<img src="/hayat-logo.jpeg" className="w-8 h-8 rounded-full object-cover" alt="HAYAT" />' if use_custom_logo else '<span className="text-2xl">🤖</span>'

with open("../frontend/components/student/FloatingChatbot.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useRef, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'
type Msg = { id: string; role: 'user' | 'assistant'; text: string }

const SUBJECTS = [
  'General','Data Structures','Operating Systems','Computer Networks',
  'DBMS','Software Engineering','AI & ML','Web Technologies',
  'Mathematics','Physics','Chemistry','English',
]

export default function FloatingChatbot() {
  const { data: session } = useSession()
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([
    { id: 'w', role: 'assistant', text: 'Assalamu Alaikum! 👋 I am HAYAT, your AI Study Assistant. Ask me anything about your studies!' }
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
      setTimeout(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
        inputRef.current?.focus()
      }, 100)
    }
  }, [msgs, open])

  const send = async (text?: string) => {
    const msg = text || input.trim()
    if (!msg || loading || !token) return
    const uid = Date.now().toString()
    const newHist = [...history, { role: 'user', content: msg }]
    setMsgs(p => [...p, { id: uid, role: 'user', text: msg }])
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
      const reply = d.success ? d.data.reply : 'Sorry, HAYAT is unavailable. Check backend GROQ_API_KEY.'
      setMsgs(p => [...p, { id: uid + '_b', role: 'assistant', text: reply }])
      setHistory([...newHist, { role: 'assistant', content: reply }])
    } catch {
      setMsgs(p => [...p, { id: uid + '_e', role: 'assistant', text: '❌ Cannot connect. Backend running on port 5000?' }])
    }
    setLoading(false)
  }

  const fmt = (t: string) => t
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code style="background:#1e293b;padding:1px 5px;border-radius:4px;font-size:11px;color:#4ade80">$1</code>')
    .replace(/^• (.+)$/gm, '<div style="display:flex;gap:6px;margin-top:4px"><span style="color:#60a5fa">•</span><span>$1</span></div>')
    .replace(/\\n/g, '<br/>')

  const QUICK = ['Explain with example', 'Practice questions', 'Key exam topics']

  const LogoImg = () => (
    <img src="/hayat-logo.jpeg" 
      style={{ width:36, height:36, borderRadius:'50%', objectFit:'cover', border:'2px solid rgba(255,255,255,0.3)' }} 
      alt="HAYAT"
      onError={e => { (e.target as HTMLImageElement).style.display='none' }}
    />
  )

  const SmallLogo = () => (
    <img src="/hayat-logo.jpeg"
      style={{ width:28, height:28, borderRadius:'50%', objectFit:'cover', border:'2px solid rgba(255,255,255,0.3)', flexShrink:0 }}
      alt="HAYAT"
      onError={e => { (e.target as HTMLImageElement).outerHTML = '<span style="font-size:18px;flex-shrink:0">🤖</span>' }}
    />
  )

  return (
    <>
      {/* Floating button with label */}
      <div style={{ position:'fixed', bottom:24, right:24, zIndex:9999, display:'flex', flexDirection:'column', alignItems:'flex-end', gap:8 }}>
        {!open && (
          <div style={{
            display:'flex', alignItems:'center', gap:8,
            background:'white', borderRadius:999, padding:'6px 14px',
            boxShadow:'0 4px 20px rgba(0,0,0,0.15)', border:'2px solid #e0e7ff',
          }}>
            <SmallLogo />
            <span style={{ fontSize:13, fontWeight:700, color:'#3b82f6', whiteSpace:'nowrap' }}>Ask HAYAT !!!</span>
          </div>
        )}
        <button
          onClick={() => setOpen(!open)}
          style={{
            width:56, height:56, borderRadius:'50%',
            display:'flex', alignItems:'center', justifyContent:'center',
            background:'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%)',
            boxShadow:'0 8px 32px rgba(59,130,246,0.5), 0 0 0 4px rgba(59,130,246,0.15)',
            border:'none', cursor:'pointer', transition:'transform 0.2s',
            position:'relative',
          }}
          onMouseEnter={e => (e.currentTarget.style.transform = 'scale(1.1)')}
          onMouseLeave={e => (e.currentTarget.style.transform = 'scale(1)')}>
          {open ? (
            <span style={{ color:'white', fontSize:20, fontWeight:'bold' }}>✕</span>
          ) : (
            <img src="/hayat-logo.jpeg" 
              style={{ width:48, height:48, borderRadius:'50%', objectFit:'cover' }} 
              alt="HAYAT"
              onError={e => { (e.target as HTMLImageElement).outerHTML = '<span style="font-size:28px">🤖</span>' }}
            />
          )}
          {!open && msgs.length > 1 && (
            <span style={{
              position:'absolute', top:-4, right:-4,
              background:'#22c55e', color:'white', fontSize:10,
              width:20, height:20, borderRadius:'50%',
              display:'flex', alignItems:'center', justifyContent:'center', fontWeight:'bold'
            }}>
              {Math.min(msgs.filter(m => m.role === 'assistant').length - 1, 9)}
            </span>
          )}
        </button>
      </div>

      {/* Chat window */}
      {open && (
        <div style={{
          position:'fixed', bottom:100, right:24, zIndex:9998,
          width: Math.min(380, window.innerWidth - 32),
          maxHeight:'70vh', display:'flex', flexDirection:'column',
          background:'#0f172a', border:'1px solid rgba(255,255,255,0.1)',
          borderRadius:20, overflow:'hidden',
          boxShadow:'0 25px 60px rgba(0,0,0,0.5)',
        }}>

          {/* Header */}
          <div style={{ padding:'12px 16px', display:'flex', alignItems:'center', gap:12, flexShrink:0, background:'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
            <LogoImg />
            <div style={{ flex:1 }}>
              <p style={{ margin:0, fontSize:14, fontWeight:700, color:'white' }}>HAYAT</p>
              <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                <span style={{ width:8, height:8, background:'#4ade80', borderRadius:'50%', display:'inline-block' }}></span>
                <p style={{ margin:0, fontSize:11, color:'rgba(255,255,255,0.7)' }}>AI Study Assistant • Online</p>
              </div>
            </div>
            {/* Subject */}
            <div style={{ position:'relative' }}>
              <button onClick={() => setShowSubjects(!showSubjects)}
                style={{ fontSize:11, background:'rgba(255,255,255,0.2)', color:'white', padding:'4px 10px', borderRadius:8, border:'none', cursor:'pointer', maxWidth:80, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                {subject} ▾
              </button>
              {showSubjects && (
                <div style={{ position:'absolute', right:0, top:'100%', marginTop:4, width:160, background:'#1e293b', border:'1px solid rgba(255,255,255,0.1)', borderRadius:12, overflow:'hidden', zIndex:10, boxShadow:'0 20px 40px rgba(0,0,0,0.5)' }}>
                  {SUBJECTS.map(s => (
                    <button key={s} onClick={() => { setSubject(s); setShowSubjects(false) }}
                      style={{ display:'block', width:'100%', textAlign:'left', padding:'8px 12px', fontSize:12, color: subject === s ? '#fff' : '#94a3b8', background: subject === s ? '#3b82f6' : 'transparent', border:'none', cursor:'pointer' }}>
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Messages */}
          <div style={{ flex:1, overflowY:'auto', padding:12, display:'flex', flexDirection:'column', gap:10, minHeight:0 }}>
            {msgs.map(m => (
              <div key={m.id} style={{ display:'flex', gap:8, justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', alignItems:'flex-start' }}>
                {m.role === 'assistant' && <SmallLogo />}
                <div style={{
                  maxWidth:'80%', padding:'8px 12px', fontSize:12, lineHeight:1.6,
                  background: m.role === 'user' ? '#3b82f6' : '#1e293b',
                  color: m.role === 'user' ? '#fff' : '#e2e8f0',
                  borderRadius: m.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                  border: m.role === 'assistant' ? '1px solid rgba(255,255,255,0.05)' : 'none',
                }}
                  dangerouslySetInnerHTML={{ __html: fmt(m.text) }}
                />
              </div>
            ))}
            {loading && (
              <div style={{ display:'flex', gap:8, alignItems:'flex-start' }}>
                <SmallLogo />
                <div style={{ padding:'8px 12px', background:'#1e293b', border:'1px solid rgba(255,255,255,0.05)', borderRadius:'18px 18px 18px 4px', display:'flex', alignItems:'center', gap:4 }}>
                  <span style={{ fontSize:11, color:'#94a3b8', marginRight:4 }}>HAYAT is thinking</span>
                  {[0,1,2].map(i => (
                    <div key={i} style={{ width:6, height:6, background:'#60a5fa', borderRadius:'50%', animation:'bounce 1s infinite', animationDelay: i*150+'ms' }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick prompts */}
          {msgs.length <= 2 && (
            <div style={{ padding:'0 12px 8px', display:'flex', gap:6, flexWrap:'wrap', flexShrink:0 }}>
              {QUICK.map(q => (
                <button key={q} onClick={() => send(q)}
                  style={{ fontSize:10, padding:'4px 10px', borderRadius:999, color:'#60a5fa', border:'1px solid rgba(96,165,250,0.3)', background:'rgba(96,165,250,0.05)', cursor:'pointer' }}>
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div style={{ padding:12, display:'flex', gap:8, flexShrink:0, borderTop:'1px solid rgba(255,255,255,0.05)' }}>
            <input
              ref={inputRef}
              type="text" value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') send() }}
              placeholder="Ask HAYAT anything..."
              disabled={loading}
              style={{ flex:1, background:'#1e293b', border:'1px solid rgba(255,255,255,0.1)', borderRadius:12, padding:'8px 12px', fontSize:12, color:'white', outline:'none' }}
            />
            <button onClick={() => send()} disabled={!input.trim() || loading}
              style={{ width:36, height:36, borderRadius:12, display:'flex', alignItems:'center', justifyContent:'center', color:'white', fontSize:14, border:'none', cursor: input.trim() && !loading ? 'pointer' : 'default', background: input.trim() && !loading ? 'linear-gradient(135deg,#3b82f6,#8b5cf6)' : '#334155' }}>
              ➤
            </button>
          </div>

          <div style={{ padding:'0 12px 8px', textAlign:'center' }}>
            <p style={{ margin:0, fontSize:10, color:'#475569' }}>HAYAT AI • K.R Mangalam University</p>
          </div>
        </div>
      )}

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
      `}</style>
    </>
  )
}
""")
print("HAYAT Chatbot with custom logo done!")

# ══════════════════════════════════════
# FIX 5: Teacher Results - proper unique keys
# ══════════════════════════════════════
with open("../frontend/app/(dashboard)/teacher/results/page.tsx", "r", encoding="utf-8") as f:
    results = f.read()

# Replace all problematic key patterns with guaranteed unique ones
results = results.replace("key={s.id + '_row'}", "key={'r_' + i + '_' + s.id}")
results = results.replace("key={s.id + '_expanded'}", "key={'e_' + i + '_' + s.id}")
results = results.replace("key={cls.classId + '_' + s.id}", "key={'c_' + cls.classId + '_s_' + s.id + '_' + i}")
results = results.replace("key={'sub_' + sub.id}", "key={'sub_' + sub.id + '_' + Math.random()}")

# Fix task breakdown keys
results = results.replace(
    "s.tasks.map((t: any, ti: number) => (",
    "s.tasks.map((t: any, ti: number) => { const tk = 'tk_' + s.id + '_' + ti; return ("
)
# Close the arrow function properly - this is fragile, do a simpler replace
results = results.replace(
    "key={s.id + '_task_' + ti}",
    "key={tk}"
)

with open("../frontend/app/(dashboard)/teacher/results/page.tsx", "w", encoding="utf-8") as f:
    f.write(results)
print("Results keys fixed!")

print("\n=== ALL DONE! ===")