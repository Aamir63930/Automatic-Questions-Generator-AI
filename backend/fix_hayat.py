import os

# ══════════════════════════════════════
# FIX 1: Dark/Light mode - full page
# ══════════════════════════════════════
# Add to globals.css
with open("../frontend/app/globals.css", "r", encoding="utf-8") as f:
    css = f.read()

if "light-mode" not in css:
    css += """
/* Light mode overrides */
html:not(.dark) {
  background: #f1f5f9 !important;
}
html:not(.dark) body {
  background: #f1f5f9 !important;
  color: #0f172a !important;
}
html:not(.dark) .bg-slate-950 { background-color: #f1f5f9 !important; }
html:not(.dark) .bg-slate-900 { background-color: #ffffff !important; border-color: #e2e8f0 !important; }
html:not(.dark) .bg-slate-800 { background-color: #f8fafc !important; }
html:not(.dark) .bg-slate-800\\/50 { background-color: #f1f5f9 !important; }
html:not(.dark) .bg-slate-700 { background-color: #e2e8f0 !important; }
html:not(.dark) .text-white { color: #0f172a !important; }
html:not(.dark) .text-slate-400 { color: #475569 !important; }
html:not(.dark) .text-slate-500 { color: #64748b !important; }
html:not(.dark) .text-slate-300 { color: #334155 !important; }
html:not(.dark) .text-slate-200 { color: #1e293b !important; }
html:not(.dark) .border-white\\/5 { border-color: #e2e8f0 !important; }
html:not(.dark) .border-white\\/10 { border-color: #cbd5e1 !important; }
html:not(.dark) header { background-color: rgba(255,255,255,0.9) !important; border-color: #e2e8f0 !important; }
html:not(.dark) aside { background-color: #ffffff !important; border-color: #e2e8f0 !important; }
html:not(.dark) .min-h-screen { background: #f1f5f9 !important; }
"""
    with open("../frontend/app/globals.css", "w", encoding="utf-8") as f:
        f.write(css)
    print("globals.css updated!")
else:
    print("Already updated")

# Fix theme init in layout - apply on load
with open("../frontend/app/layout.tsx", "r", encoding="utf-8") as f:
    layout_content = f.read()

if "themeScript" not in layout_content:
    theme_script = """      <script dangerouslySetInnerHTML={{ __html: `
        (function() {
          var theme = localStorage.getItem('theme') || 'dark';
          if (theme === 'dark') {
            document.documentElement.classList.add('dark');
            document.body.style.background = '#020617';
          } else {
            document.documentElement.classList.remove('dark');
            document.body.style.background = '#f1f5f9';
          }
        })();
      `}} />"""

    layout_content = layout_content.replace(
        "<html lang=\"en\">",
        "<html lang=\"en\" className=\"dark\">"
    )
    layout_content = layout_content.replace(
        "<body",
        theme_script + "\n      <body"
    )
    with open("../frontend/app/layout.tsx", "w", encoding="utf-8") as f:
        f.write(layout_content)
    print("Layout theme script added!")
else:
    print("Theme script already added")

# ══════════════════════════════════════
# FIX 2: Floating Chatbot - HAYAT branding
# ══════════════════════════════════════
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
      const reply = d.success ? d.data.reply : 'Sorry, HAYAT is unavailable right now. Check backend GROQ_API_KEY.'
      setMsgs(p => [...p, { id: uid + '_b', role: 'assistant', text: reply }])
      setHistory([...newHist, { role: 'assistant', content: reply }])
    } catch {
      setMsgs(p => [...p, { id: uid + '_e', role: 'assistant', text: '❌ Cannot connect. Is backend running on port 5000?' }])
    }
    setLoading(false)
  }

  const fmt = (t: string) => t
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code style="background:#1e293b;padding:1px 5px;border-radius:4px;font-size:11px;color:#4ade80">$1</code>')
    .replace(/^• (.+)$/gm, '<div style="display:flex;gap:6px;margin-top:4px"><span style="color:#60a5fa">•</span><span>$1</span></div>')
    .replace(/\\n/g, '<br/>')

  const QUICK = ['Explain with example', 'Practice questions', 'Key exam topics']

  return (
    <>
      {/* Floating button with label */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
        {!open && (
          <div className="flex items-center gap-2 bg-white rounded-full shadow-xl px-3 py-1.5 border border-blue-100">
            <span className="text-xs font-bold text-blue-600">Ask HAYAT !!!</span>
          </div>
        )}
        <button
          onClick={() => setOpen(!open)}
          className="w-14 h-14 rounded-full flex items-center justify-center transition-all hover:scale-110 active:scale-95 relative"
          style={{
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%)',
            boxShadow: '0 8px 32px rgba(59,130,246,0.5), 0 0 0 4px rgba(59,130,246,0.15)'
          }}>
          {open ? (
            <span className="text-white text-xl font-bold">✕</span>
          ) : (
            <span className="text-2xl">🤖</span>
          )}
          {!open && msgs.length > 1 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-green-400 rounded-full flex items-center justify-center text-[10px] font-bold text-white">
              {Math.min(msgs.filter(m => m.role === 'assistant').length - 1, 9)}
            </span>
          )}
        </button>
      </div>

      {/* Chat window */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 rounded-2xl overflow-hidden shadow-2xl flex flex-col"
          style={{
            width: 'min(380px, calc(100vw - 24px))',
            maxHeight: '70vh',
            background: '#0f172a',
            border: '1px solid rgba(255,255,255,0.1)',
          }}>

          {/* Header */}
          <div className="px-4 py-3 flex items-center gap-3 flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
            <div className="w-10 h-10 rounded-full bg-white/20 border-2 border-white/30 flex items-center justify-center text-xl flex-shrink-0">
              🤖
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-white">HAYAT</p>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                <p className="text-xs text-white/70">AI Study Assistant • Online</p>
              </div>
            </div>
            {/* Subject */}
            <div className="relative flex-shrink-0">
              <button onClick={() => setShowSubjects(!showSubjects)}
                className="text-xs bg-white/20 hover:bg-white/30 text-white px-2 py-1 rounded-lg transition-all max-w-[80px] truncate">
                {subject} ▾
              </button>
              {showSubjects && (
                <div className="absolute right-0 top-full mt-1 w-44 rounded-xl overflow-hidden z-20"
                  style={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 20px 40px rgba(0,0,0,0.5)' }}>
                  {SUBJECTS.map(s => (
                    <button key={s} onClick={() => { setSubject(s); setShowSubjects(false) }}
                      className="w-full text-left px-3 py-2 text-xs transition-all"
                      style={{ color: subject === s ? '#fff' : '#94a3b8', background: subject === s ? '#3b82f6' : 'transparent' }}>
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3" style={{ minHeight: 0 }}>
            {msgs.map(m => (
              <div key={m.id} className={'flex gap-2 ' + (m.role === 'user' ? 'justify-end' : 'justify-start')}>
                {m.role === 'assistant' && (
                  <div className="w-6 h-6 rounded-full flex-shrink-0 mt-0.5 flex items-center justify-center text-sm"
                    style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>🤖</div>
                )}
                <div className="max-w-[80%] px-3 py-2 rounded-2xl text-xs leading-relaxed"
                  style={{
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
              <div className="flex gap-2 justify-start">
                <div className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-sm"
                  style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>🤖</div>
                <div className="px-3 py-2 rounded-2xl flex gap-1 items-center"
                  style={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <span className="text-xs text-slate-400 mr-1">HAYAT is thinking</span>
                  {[0,1,2].map(i => (
                    <div key={i} className="w-1.5 h-1.5 rounded-full animate-bounce"
                      style={{ background: '#60a5fa', animationDelay: i*150+'ms' }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick prompts */}
          {msgs.length <= 2 && (
            <div className="px-3 py-2 flex gap-2 flex-wrap flex-shrink-0">
              {QUICK.map(q => (
                <button key={q} onClick={() => send(q)}
                  className="text-[10px] px-2 py-1 rounded-full transition-all"
                  style={{ color: '#60a5fa', border: '1px solid rgba(96,165,250,0.3)', background: 'rgba(96,165,250,0.05)' }}>
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="p-3 flex gap-2 flex-shrink-0"
            style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              placeholder="Ask HAYAT anything..."
              disabled={loading}
              className="flex-1 rounded-xl px-3 py-2 text-xs text-white outline-none placeholder-slate-500"
              style={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)' }}
            />
            <button onClick={() => send()} disabled={!input.trim() || loading}
              className="w-9 h-9 rounded-xl flex items-center justify-center text-white text-sm transition-all"
              style={{ background: input.trim() && !loading ? 'linear-gradient(135deg, #3b82f6, #8b5cf6)' : '#334155' }}>
              ➤
            </button>
          </div>

          {/* Footer */}
          <div className="px-3 pb-2 text-center flex-shrink-0">
            <p className="text-[10px]" style={{ color: '#475569' }}>HAYAT AI • Powered by Groq Llama 3</p>
          </div>
        </div>
      )}
    </>
  )
}
""")
print("HAYAT Chatbot done!")

# ══════════════════════════════════════
# FIX 3: TeacherResultsPage key prop fix
# ══════════════════════════════════════
with open("../frontend/app/(dashboard)/teacher/results/page.tsx", "r", encoding="utf-8") as f:
    results = f.read()

# Fix all list items without proper keys
import re

# Fix expanded student rows
results = results.replace(
    "s.tasks.map((t: any, ti: number) => (",
    "s.tasks.map((t: any, ti: number) => { const taskKey = (s.id || '') + '_task_' + ti + '_' + (t.taskId || ti); return ("
)
results = results.replace(
    "))}  {/* end tasks */}",
    ")})}  {/* end tasks */}"
)

# Simpler approach - just rewrite the key assignments
results = re.sub(
    r'key=\{s\.id \+ \'_task_\' \+ ti\}',
    "key={s.id + '_task_' + ti + '_' + (t.taskId || '')}",
    results
)

# Fix any duplicate key patterns
results = results.replace(
    'key={s.id + \'_row\'}',
    'key={\'row_\' + s.id}'
)
results = results.replace(
    'key={s.id + \'_expanded\'}',
    'key={\'exp_\' + s.id}'
)
results = results.replace(
    'key={cls.classId + \'_\' + s.id}',
    'key={\'cls_\' + cls.classId + \'_stu_\' + s.id}'
)
results = results.replace(
    'key={\'sub_\' + sub.id}',
    'key={\'submission_\' + sub.id}'
)
results = results.replace(
    'key={t.taskId}',
    'key={\'task_pending_\' + t.taskId}'
)
results = results.replace(
    "key={t.taskId + '_ns_' + s.id}",
    "key={'notsubmit_' + t.taskId + '_' + s.id}"
)

with open("../frontend/app/(dashboard)/teacher/results/page.tsx", "w", encoding="utf-8") as f:
    f.write(results)
print("Results key props fixed!")

print("\n=== ALL DONE! ===")