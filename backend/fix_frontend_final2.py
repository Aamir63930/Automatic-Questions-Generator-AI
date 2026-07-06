import os

# AI Chatbot - Subject add option
os.makedirs("../frontend/app/(student)/student/chatbot", exist_ok=True)
with open("../frontend/app/(student)/student/chatbot/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useRef, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Msg = { id: string; role: 'user'|'assistant'; text: string; time: string }

const DEFAULT_SUBJECTS = [
  { n: 'Data Structures and Algorithms', i: '🌳' },
  { n: 'Operating Systems', i: '💻' },
  { n: 'Computer Networks', i: '🌐' },
  { n: 'Database Management Systems', i: '🗄️' },
  { n: 'Software Engineering', i: '⚙️' },
  { n: 'Artificial Intelligence', i: '🤖' },
  { n: 'Machine Learning', i: '📊' },
  { n: 'Web Technologies', i: '🌍' },
  { n: 'Object Oriented Programming', i: '📦' },
  { n: 'Discrete Mathematics', i: '📐' },
  { n: 'Mathematics', i: '🔢' },
  { n: 'Physics', i: '⚡' },
  { n: 'Chemistry', i: '🧪' },
  { n: 'English', i: '📝' },
  { n: 'Management', i: '📈' },
]

export default function ChatbotPage() {
  const { data: session } = useSession()
  const [subject, setSubject] = useState('')
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<{role:string;content:string}[]>([])
  const [customSubjects, setCustomSubjects] = useState<{n:string;i:string}[]>(() => {
    if (typeof window !== 'undefined') {
      try { return JSON.parse(localStorage.getItem('chatbotSubjects') || '[]') } catch { return [] }
    }
    return []
  })
  const [showAddSubject, setShowAddSubject] = useState(false)
  const [newSubjectName, setNewSubjectName] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const token = session?.user?.backendToken

  const allSubjects = [...DEFAULT_SUBJECTS, ...customSubjects]

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs, loading])

  const addSubject = () => {
    const name = newSubjectName.trim()
    if (!name || allSubjects.some(s => s.n === name)) return
    const updated = [...customSubjects, { n: name, i: '📖' }]
    setCustomSubjects(updated)
    localStorage.setItem('chatbotSubjects', JSON.stringify(updated))
    setNewSubjectName('')
    setShowAddSubject(false)
  }

  const removeCustomSubject = (name: string) => {
    const updated = customSubjects.filter(s => s.n !== name)
    setCustomSubjects(updated)
    localStorage.setItem('chatbotSubjects', JSON.stringify(updated))
    if (subject === name) { setSubject(''); setMsgs([]); setHistory([]) }
  }

  const start = (s: string) => {
    setSubject(s)
    const welcome = `Hello! I am your AI Study Assistant. I am here to help you with **${s}**.

I can:
- Explain concepts clearly with examples
- Generate practice questions
- Help with exam preparation
- Clear your doubts instantly

What would you like to learn today?`
    const m: Msg = { id: 'welcome', role: 'assistant', text: welcome, time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }) }
    setMsgs([m]); setHistory([{ role: 'assistant', content: welcome }])
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  const send = async (text?: string) => {
    const msg = text || input.trim()
    if (!msg || !subject || loading || !token) return
    const uid = Date.now().toString()
    const userMsg: Msg = { id: uid, role: 'user', text: msg, time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }) }
    const newHist = [...history, { role: 'user', content: msg }]
    setMsgs(p => [...p, userMsg]); setHistory(newHist)
    if (!text) setInput('')
    setLoading(true)
    try {
      const res = await fetch(API + '/ai/chat', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, subject, history: history.slice(-6) })
      })
      const d = await res.json()
      const reply = d.success ? d.data.reply : 'Sorry, AI unavailable. Make sure GROQ_API_KEY is set in backend .env'
      const botMsg: Msg = { id: uid + '_bot', role: 'assistant', text: reply, time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }) }
      setMsgs(p => [...p, botMsg]); setHistory([...newHist, { role: 'assistant', content: reply }])
    } catch {
      setMsgs(p => [...p, { id: uid + '_err', role: 'assistant', text: '❌ Connection error. Is backend running?', time: 'Now' }])
    }
    setLoading(false)
  }

  const fmt = (t: string) => t
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong class="text-white">$1</strong>')
    .replace(/`(.+?)`/g, '<code class="bg-slate-700 px-1.5 py-0.5 rounded text-green-400 text-xs font-mono">$1</code>')
    .replace(/^• (.+)$/gm, '<div class="flex gap-2 mt-1"><span class="text-blue-400">•</span><span>$1</span></div>')
    .replace(/\\n/g, '<br/>')

  const QUICK = ['Explain with example', 'Give 5 practice questions', 'Key exam topics', 'Common mistakes to avoid']

  return (
    <div className="max-w-4xl mx-auto flex flex-col" style={{ height: 'calc(100vh - 120px)' }}>
      <div className="mb-4 flex-shrink-0 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xl">🤖</div>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-white">AI Study Assistant</h1>
          <p className="text-slate-400 text-xs">Powered by Groq AI (Free) — Instant doubt solving</p>
        </div>
        {subject && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-blue-400 bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded-full">{subject.length > 25 ? subject.slice(0,25)+'...' : subject}</span>
            <button onClick={() => { setSubject(''); setMsgs([]); setHistory([]) }} className="text-xs text-slate-500 hover:text-white px-2 py-1 bg-slate-800 rounded-lg border border-white/5">Change</button>
          </div>
        )}
      </div>

      {!subject ? (
        <div className="flex-1 overflow-y-auto">
          <div className="text-center py-6 mb-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 flex items-center justify-center text-3xl mx-auto mb-3">🤖</div>
            <h2 className="text-lg font-bold text-white mb-1">Choose a Subject</h2>
            <p className="text-slate-400 text-sm">AI will answer all your questions instantly</p>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            {allSubjects.map(s => (
              <button key={s.n} onClick={() => start(s.n)}
                className="p-4 bg-slate-900 rounded-2xl border border-white/5 hover:border-blue-500/30 hover:bg-blue-500/5 transition-all text-left group">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{s.i}</span>
                  <p className="text-sm font-medium text-white">{s.n}</p>
                </div>
                {customSubjects.some(cs => cs.n === s.n) && (
                  <button onClick={e => { e.stopPropagation(); removeCustomSubject(s.n) }}
                    className="mt-2 text-[10px] text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity">
                    ✕ Remove
                  </button>
                )}
              </button>
            ))}
          </div>

          {/* Add custom subject */}
          {showAddSubject ? (
            <div className="flex gap-2 mb-4">
              <input type="text" value={newSubjectName} onChange={e => setNewSubjectName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addSubject()}
                placeholder="Enter subject name e.g. Compiler Design"
                autoFocus
                className="flex-1 bg-slate-900 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
              <button onClick={addSubject} disabled={!newSubjectName.trim()} className="px-4 py-2.5 bg-blue-500 text-white text-sm rounded-xl disabled:opacity-40">Add</button>
              <button onClick={() => setShowAddSubject(false)} className="px-3 py-2.5 bg-slate-800 text-slate-400 text-sm rounded-xl border border-white/5">✕</button>
            </div>
          ) : (
            <button onClick={() => setShowAddSubject(true)}
              className="w-full py-3 text-sm text-blue-400 border border-dashed border-blue-500/30 rounded-2xl hover:border-blue-500/60 hover:bg-blue-500/5 transition-all">
              + Add Custom Subject
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto bg-slate-900/50 rounded-2xl border border-white/5 p-4 mb-3 space-y-4">
            {msgs.map(m => (
              <div key={m.id} className={'flex ' + (m.role === 'user' ? 'justify-end' : 'justify-start')}>
                <div className={'max-w-[85%] flex flex-col gap-1 ' + (m.role === 'user' ? 'items-end' : 'items-start')}>
                  {m.role === 'assistant' && (
                    <div className="flex items-center gap-1.5 mb-1">
                      <div className="w-5 h-5 rounded-md bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-[10px]">🤖</div>
                      <span className="text-[10px] text-slate-500">AI Assistant</span>
                    </div>
                  )}
                  <div className={'px-4 py-3 rounded-2xl text-sm leading-relaxed ' +
                    (m.role === 'user' ? 'bg-blue-500 text-white rounded-br-sm' : 'bg-slate-800 text-slate-200 border border-white/5 rounded-bl-sm')}
                    dangerouslySetInnerHTML={{ __html: fmt(m.text) }} />
                  <p className="text-[10px] text-slate-600 px-1">{m.time}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-800 border border-white/5 rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1">
                  <span className="text-xs text-slate-500 mr-2">Thinking</span>
                  {[0,1,2].map(i => <div key={i} className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: i*150+'ms' }} />)}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          {msgs.length <= 1 && (
            <div className="flex gap-2 flex-wrap mb-3 flex-shrink-0">
              {QUICK.map(q => (
                <button key={q} onClick={() => send(q)}
                  className="text-xs px-3 py-1.5 bg-slate-900 text-slate-400 border border-white/5 rounded-full hover:border-blue-500/30 hover:text-blue-400 transition-all">
                  {q}
                </button>
              ))}
            </div>
          )}
          <div className="flex gap-2 flex-shrink-0">
            <input ref={inputRef} type="text" value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              placeholder={'Ask about ' + (subject.length > 30 ? subject.slice(0,30)+'...' : subject) + '...'}
              disabled={loading}
              className="flex-1 bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 disabled:opacity-50" />
            <button onClick={() => send()} disabled={!input.trim() || loading}
              className="px-5 py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600 disabled:opacity-40">
              Send
            </button>
          </div>
        </>
      )}
    </div>
  )
}
""")
print("AI Chatbot done!")

# Teacher Classes - show students per class
os.makedirs("../frontend/app/(dashboard)/teacher/classes", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/classes/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Student = { id: string; name: string; email: string; rollNumber?: string | null; avatarUrl?: string | null }
type ClassSection = {
  id: string; name: string; section: string; branch: string
  semester: number; year: number; uniqueCode: string
  _count: { students: number }
}

export default function ClassesPage() {
  const { data: session } = useSession()
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [allUsers, setAllUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [expandedClass, setExpandedClass] = useState<string|null>(null)
  const [classStudents, setClassStudents] = useState<Record<string, Student[]>>({})
  const [copied, setCopied] = useState('')
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ name: 'B.Tech', section: 'A', semester: '1', branch: 'CSE', year: new Date().getFullYear().toString() })
  const token = session?.user?.backendToken

  const fetchAll = async () => {
    if (!token) return
    const h = { Authorization: 'Bearer ' + token }
    const [c, u] = await Promise.all([
      fetch(API + '/auth/classes', { headers: h }).then(r => r.json()),
      fetch(API + '/auth/users?role=student', { headers: h }).then(r => r.json()),
    ])
    if (c.success) setClasses(c.data || [])
    if (u.success) setAllUsers(u.data || [])
    setLoading(false)
  }

  useEffect(() => { if (token) fetchAll() }, [token])

  const getStudentsForClass = (classId: string) => allUsers.filter(u => u.classSectionId === classId)
  const noClassStudents = allUsers.filter(u => !u.classSectionId)
  const totalStudents = allUsers.length

  const handleCreate = async () => {
    if (!form.name || !token) return
    setCreating(true)
    const res = await fetch(API + '/auth/classes', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    const d = await res.json()
    if (d.success) { await fetchAll(); setShowCreate(false); setForm({ name: 'B.Tech', section: 'A', semester: '1', branch: 'CSE', year: new Date().getFullYear().toString() }) }
    setCreating(false)
  }

  const handleDelete = async (id: string) => {
    if (!token || !confirm('Delete this class?')) return
    await fetch(API + '/auth/classes/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } })
    fetchAll()
  }

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopied(code)
    setTimeout(() => setCopied(''), 2000)
  }

  // Group by course name
  const grouped = classes.reduce((acc, c) => {
    if (!acc[c.name]) acc[c.name] = []
    acc[c.name].push(c)
    return acc
  }, {} as Record<string, ClassSection[]>)

  const COURSES = ['B.Tech', 'BCA', 'MCA', 'MBA', 'B.Sc', 'M.Sc', 'B.Com', 'Other']
  const BRANCHES = ['CSE', 'ECE', 'ME', 'CE', 'IT', 'EE', 'Computer Science', 'Electronics', 'N/A']

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Class Management</h1>
          <p className="text-slate-400 text-sm">Manage classes and view enrolled students</p>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="px-4 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600">
          + Create Class
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-900 rounded-xl border border-white/5 p-4 text-center">
          <p className="text-2xl font-bold text-blue-400">{classes.length}</p>
          <p className="text-xs text-slate-500 mt-1">Total Classes</p>
        </div>
        <div className="bg-slate-900 rounded-xl border border-white/5 p-4 text-center">
          <p className="text-2xl font-bold text-green-400">{totalStudents}</p>
          <p className="text-xs text-slate-500 mt-1">Total Students</p>
        </div>
        <div className="bg-slate-900 rounded-xl border border-white/5 p-4 text-center">
          <p className={'text-2xl font-bold ' + (noClassStudents.length > 0 ? 'text-yellow-400' : 'text-slate-400')}>{noClassStudents.length}</p>
          <p className="text-xs text-slate-500 mt-1">Not in any class</p>
        </div>
      </div>

      {/* Info box */}
      <div className="bg-blue-500/5 border border-blue-500/15 rounded-xl p-4 mb-6">
        <p className="text-xs text-blue-400">ℹ️ Share the unique code with students. They enter it to join the class and see class-specific tasks and materials.</p>
      </div>

      {/* No class students warning */}
      {noClassStudents.length > 0 && (
        <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-4 mb-5">
          <p className="text-xs text-yellow-400 font-semibold mb-2">⚠️ {noClassStudents.length} students not assigned to any class:</p>
          <div className="flex gap-2 flex-wrap">
            {noClassStudents.map(s => (
              <span key={s.id} className="text-xs text-slate-300 bg-slate-800 px-2 py-1 rounded-lg border border-white/5">{s.name}</span>
            ))}
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : classes.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">🏫</p>
          <p className="text-white font-medium mb-1">No classes yet</p>
          <button onClick={() => setShowCreate(true)} className="mt-3 px-4 py-2 bg-blue-500 text-white text-sm rounded-xl">Create First Class</button>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([courseName, courseClasses]) => (
            <div key={courseName}>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">{courseName}</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {courseClasses.map(c => {
                  const students = getStudentsForClass(c.id)
                  const isExpanded = expandedClass === c.id
                  return (
                    <div key={c.id} className="bg-slate-900 rounded-2xl border border-white/5 hover:border-white/10 transition-all overflow-hidden">
                      <div className="p-5">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h3 className="text-sm font-semibold text-white">{c.name} — Section {c.section}</h3>
                            <p className="text-xs text-slate-500 mt-0.5">{c.branch} · Semester {c.semester} · {c.year}</p>
                          </div>
                          <button onClick={() => handleDelete(c.id)} className="text-slate-600 hover:text-red-400 w-7 h-7 flex items-center justify-center rounded-lg hover:bg-red-500/10">✕</button>
                        </div>

                        {/* Unique Code */}
                        <div className="bg-slate-800 rounded-xl p-3 border border-white/5 mb-4">
                          <p className="text-[10px] text-slate-500 uppercase mb-1">Share this code with students</p>
                          <div className="flex items-center justify-between">
                            <span className="text-lg font-mono font-bold text-green-400 tracking-widest">{c.uniqueCode}</span>
                            <button onClick={() => copyCode(c.uniqueCode)}
                              className={'text-xs px-3 py-1.5 rounded-lg transition-all ' + (copied === c.uniqueCode ? 'bg-green-500 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600')}>
                              {copied === c.uniqueCode ? '✓ Copied!' : '📋 Copy'}
                            </button>
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-400">{students.length} students enrolled</span>
                          <button onClick={() => setExpandedClass(isExpanded ? null : c.id)}
                            className="text-xs text-blue-400 hover:text-blue-300">
                            {isExpanded ? 'Hide students ▲' : 'View students ▼'}
                          </button>
                        </div>
                      </div>

                      {/* Student list */}
                      {isExpanded && (
                        <div className="border-t border-white/5 p-4">
                          {students.length === 0 ? (
                            <p className="text-xs text-slate-500 text-center py-2">No students joined yet. Share the code!</p>
                          ) : (
                            <div className="space-y-2">
                              {students.map(s => (
                                <div key={s.id} className="flex items-center gap-3 p-2 bg-slate-800 rounded-xl border border-white/5">
                                  <div className="w-7 h-7 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold flex-shrink-0">
                                    {s.name.charAt(0)}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-xs font-medium text-white truncate">{s.name}</p>
                                    <p className="text-[10px] text-slate-500">{s.rollNumber ? 'Roll: ' + s.rollNumber : s.email}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Class Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-md">
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <p className="text-sm font-semibold text-white">Create New Class</p>
              <button onClick={() => setShowCreate(false)} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center">✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-xs text-slate-500 uppercase mb-2">Course / Programme *</label>
                <div className="grid grid-cols-4 gap-2 mb-2">
                  {COURSES.map(c => (
                    <button key={c} onClick={() => setForm(p => ({ ...p, name: c }))}
                      className={'py-2 rounded-xl text-xs font-medium border transition-all ' + (form.name === c ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                      {c}
                    </button>
                  ))}
                </div>
                <input type="text" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                  placeholder="Or type custom name"
                  className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 uppercase mb-2">Branch</label>
                  <select value={form.branch} onChange={e => setForm(p => ({ ...p, branch: e.target.value }))}
                    className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none">
                    {BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-500 uppercase mb-2">Semester</label>
                  <select value={form.semester} onChange={e => setForm(p => ({ ...p, semester: e.target.value }))}
                    className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none">
                    {['1','2','3','4','5','6','7','8'].map(s => <option key={s} value={s}>Sem {s}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 uppercase mb-2">Section</label>
                  <div className="grid grid-cols-4 gap-1">
                    {['A','B','C','D'].map(s => (
                      <button key={s} onClick={() => setForm(p => ({ ...p, section: s }))}
                        className={'py-2 rounded-xl text-xs font-medium border transition-all ' + (form.section === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-slate-500 uppercase mb-2">Year</label>
                  <select value={form.year} onChange={e => setForm(p => ({ ...p, year: e.target.value }))}
                    className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none">
                    {['2024','2025','2026','2027'].map(y => <option key={y} value={y}>{y}</option>)}
                  </select>
                </div>
              </div>
              <div className="bg-slate-800 rounded-xl p-3 border border-white/5">
                <p className="text-xs text-slate-500">A unique code will be auto-generated. Share it with students to join this class.</p>
              </div>
              <button onClick={handleCreate} disabled={!form.name || creating}
                className="w-full py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600 disabled:opacity-40 flex items-center justify-center gap-2">
                {creating ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Creating...</> : 'Create Class'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Teacher Classes done!")

print("\n=== ALL FRONTEND DONE ===")