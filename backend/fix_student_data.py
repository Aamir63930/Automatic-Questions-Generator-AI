import os

# Fix student select-class page - token update karo
os.makedirs("../frontend/app/(student)/student/select-class", exist_ok=True)
with open("../frontend/app/(student)/student/select-class/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession, signIn } from 'next-auth/react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type ClassSection = {
  id: string; name: string; section: string; branch: string
  semester: number; year: number; uniqueCode: string
  _count: { students: number }
}

export default function SelectClassPage() {
  const { data: session, status, update } = useSession()
  const router = useRouter()
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState<'code'|'browse'>('code')
  const [code, setCode] = useState('')
  const [joining, setJoining] = useState(false)
  const [err, setErr] = useState('')
  const [ok, setOk] = useState('')
  const [selBranch, setSelBranch] = useState('')
  const [selSem, setSelSem] = useState('')
  const [selClass, setSelClass] = useState('')

  const token = session?.user?.backendToken

  useEffect(() => {
    if (status === 'loading') return
    if (!token) return
    fetch(API + '/auth/classes', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(d => { if (d.success) setClasses(d.data); setLoading(false) })
  }, [token, status])

  const branches = Array.from(new Set(classes.map(c => c.branch))).sort()
  const sems = Array.from(new Set(
    classes.filter(c => !selBranch || c.branch === selBranch).map(c => c.semester.toString())
  )).sort()
  const filteredClasses = classes.filter(c =>
    (!selBranch || c.branch === selBranch) && (!selSem || c.semester.toString() === selSem)
  )

  const afterJoin = async (newToken?: string) => {
    // Update session with new token that has classSectionId
    if (newToken) {
      await update({ backendToken: newToken })
    }
    localStorage.setItem('studentClassSelected', 'true')
    localStorage.removeItem('studentClassSelected') // clear first
    localStorage.setItem('studentClassSelected', 'true')
    setOk('Class joined! Redirecting...')
    setTimeout(() => {
      window.location.href = '/student'  // hard redirect to reload session
    }, 1200)
  }

  const joinByCode = async () => {
    if (!code.trim() || !token) return
    setJoining(true); setErr('')
    try {
      const res = await fetch(API + '/auth/join-class', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code.toUpperCase().trim() })
      })
      const d = await res.json()
      if (d.success) {
        await afterJoin(d.data.token)
      } else {
        setErr(d.message || 'Invalid code. Check with your teacher.')
      }
    } catch { setErr('Connection error. Is backend running?') }
    setJoining(false)
  }

  const joinBySelect = async () => {
    if (!selClass || !token) return
    setJoining(true); setErr('')
    try {
      const res = await fetch(API + '/auth/select-class', {
        method: 'PATCH',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ classSectionId: selClass })
      })
      const d = await res.json()
      if (d.success) {
        await afterJoin()
      } else { setErr(d.message || 'Failed') }
    } catch { setErr('Connection error') }
    setJoining(false)
  }

  const skip = () => {
    localStorage.setItem('studentClassSelected', 'true')
    window.location.href = '/student'
  }

  if (status === 'loading') return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-green-500/20 to-blue-500/20 border border-green-500/30 flex items-center justify-center text-4xl mx-auto mb-4">🎓</div>
          <h1 className="text-2xl font-bold text-white mb-2">Join Your Class</h1>
          <p className="text-slate-400 text-sm">Enter the class code from your teacher to get tasks and materials</p>
          {session?.user?.name && <p className="text-green-400 text-xs mt-2">Welcome, {session.user.name.split(' ')[0]}!</p>}
        </div>

        {/* Mode tabs */}
        <div className="flex gap-1 bg-slate-900 border border-white/10 rounded-2xl p-1.5 mb-6">
          <button onClick={() => { setMode('code'); setErr('') }} className={'flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ' + (mode === 'code' ? 'bg-green-500 text-white shadow-lg shadow-green-500/25' : 'text-slate-400 hover:text-white')}>
            🔑 Enter Code
          </button>
          <button onClick={() => { setMode('browse'); setErr('') }} className={'flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ' + (mode === 'browse' ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/25' : 'text-slate-400 hover:text-white')}>
            📋 Browse Classes
          </button>
        </div>

        {mode === 'code' && (
          <div className="bg-slate-900/80 rounded-2xl border border-white/10 p-6">
            <label className="block text-xs text-slate-500 uppercase tracking-widest mb-3">Class Code from Teacher</label>
            <input
              type="text"
              value={code}
              onChange={e => { setCode(e.target.value.toUpperCase()); setErr('') }}
              onKeyDown={e => e.key === 'Enter' && joinByCode()}
              placeholder="e.g. CSE1A-B3F2"
              maxLength={15}
              className="w-full bg-slate-800 border border-white/10 rounded-xl px-5 py-4 text-2xl font-mono font-bold text-white text-center tracking-widest outline-none focus:border-green-500/60 placeholder:text-slate-700 placeholder:text-sm placeholder:font-normal mb-4"
            />
            {err && <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2.5 mb-4"><p className="text-xs text-red-400">⚠️ {err}</p></div>}
            {ok && <div className="bg-green-500/10 border border-green-500/20 rounded-xl px-4 py-2.5 mb-4"><p className="text-xs text-green-400">✓ {ok}</p></div>}
            <button
              onClick={joinByCode}
              disabled={code.length < 5 || joining}
              className="w-full py-3.5 bg-green-500 text-white text-sm font-semibold rounded-xl hover:bg-green-600 disabled:opacity-40 transition-all flex items-center justify-center gap-2 mb-3"
            >
              {joining ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Joining...</> : '🚀 Join Class'}
            </button>
            <p className="text-center text-xs text-slate-600">Get the code from your teacher's Class Management page</p>
          </div>
        )}

        {mode === 'browse' && (
          <div className="bg-slate-900/80 rounded-2xl border border-white/10 p-6">
            {loading ? (
              <div className="text-center py-8"><div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" /><p className="text-slate-400 text-sm">Loading...</p></div>
            ) : classes.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-3">⏳</p>
                <p className="text-white font-medium mb-2">No classes created yet</p>
                <p className="text-slate-400 text-sm mb-4">Ask your teacher for the class code</p>
                <button onClick={() => setMode('code')} className="px-4 py-2 bg-green-500 text-white text-sm rounded-xl">Enter Code</button>
              </div>
            ) : (
              <>
                <div className="mb-4">
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Branch</p>
                  <div className="grid grid-cols-3 gap-2">
                    {branches.map(b => (
                      <button key={b} onClick={() => { setSelBranch(b); setSelSem(''); setSelClass('') }} className={'py-2.5 rounded-xl text-sm font-medium border transition-all ' + (selBranch === b ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/20')}>
                        {b}
                      </button>
                    ))}
                  </div>
                </div>

                {selBranch && (
                  <div className="mb-4">
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Semester</p>
                    <div className="grid grid-cols-4 gap-2">
                      {sems.map(s => (
                        <button key={s} onClick={() => { setSelSem(s); setSelClass('') }} className={'py-2.5 rounded-xl text-sm font-medium border transition-all ' + (selSem === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/20')}>
                          Sem {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {selSem && (
                  <div className="mb-4">
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Class & Section</p>
                    <div className="space-y-2">
                      {filteredClasses.map(c => (
                        <button key={c.id} onClick={() => setSelClass(c.id)} className={'w-full p-3.5 rounded-xl border text-left transition-all ' + (selClass === c.id ? 'border-green-500/60 bg-green-500/10' : 'border-white/5 bg-slate-800 hover:border-white/20')}>
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-semibold text-white">{c.name} — Section {c.section}</p>
                              <p className="text-xs text-slate-500">{c.branch} · Sem {c.semester} · {c._count.students} students</p>
                            </div>
                            <span className="text-xs font-mono text-green-400 bg-green-500/10 px-2 py-1 rounded-lg border border-green-500/20">{c.uniqueCode}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {err && <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2.5 mb-3"><p className="text-xs text-red-400">{err}</p></div>}
                {ok && <div className="bg-green-500/10 border border-green-500/20 rounded-xl px-4 py-2.5 mb-3"><p className="text-xs text-green-400">✓ {ok}</p></div>}

                {selClass && (
                  <button onClick={joinBySelect} disabled={joining} className="w-full py-3.5 bg-green-500 text-white text-sm font-semibold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center justify-center gap-2">
                    {joining ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Joining...</> : '✓ Join This Class'}
                  </button>
                )}
              </>
            )}
          </div>
        )}

        <div className="text-center mt-5">
          <button onClick={skip} className="text-slate-600 hover:text-slate-400 text-xs transition-colors">
            Skip — I'll join later
          </button>
        </div>
      </div>
    </div>
  )
}
""")
print("Select class page done!")

# Fix student dashboard - with proper error handling
with open("../frontend/app/(student)/student/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

export default function StudentDashboard() {
  const { data: session, status } = useSession()
  const [tasks, setTasks] = useState<any[]>([])
  const [materials, setMaterials] = useState<any[]>([])
  const [submissions, setSubmissions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const token = session?.user?.backendToken

  useEffect(() => {
    if (status === 'loading') return
    if (!token) { setLoading(false); return }

    const headers = { Authorization: 'Bearer ' + token }
    setLoading(true)

    Promise.all([
      fetch(API + '/tasks', { headers }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
      fetch(API + '/materials', { headers }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
      fetch(API + '/submissions', { headers }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
    ]).then(([t, m, s]) => {
      if (t.success) setTasks(t.data || [])
      if (m.success) setMaterials(m.data || [])
      if (s.success) setSubmissions(s.data || [])
      if (!t.success && !m.success) setError('Could not load data. Check backend connection.')
      setLoading(false)
    })
  }, [token, status])

  const subIds = submissions.map((s: any) => s.taskId)
  const pending = tasks.filter((t: any) => !subIds.includes(t.id))
  const notes = materials.filter((m: any) => !m.isPyq)
  const pyqs = materials.filter((m: any) => m.isPyq)

  const typeIcon: Record<string, string> = { assignment: '📝', class_test: '✍️', quiz: '❓', project: '🔬' }

  const getDL = (d?: string) => {
    if (!d) return { label: 'No deadline', color: 'text-slate-400' }
    const diff = new Date(d).getTime() - Date.now()
    const days = Math.ceil(diff / 86400000)
    if (diff < 0) return { label: 'Overdue!', color: 'text-red-400' }
    if (days === 0) return { label: 'Due Today!', color: 'text-red-400' }
    if (days <= 2) return { label: days + 'd left', color: 'text-yellow-400' }
    return { label: days + 'd left', color: 'text-green-400' }
  }

  if (status === 'loading' || loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Loading your dashboard...</p>
      </div>
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">
          Welcome, {session?.user?.name?.split(' ')[0] || 'Student'} 👋
        </h1>
        <p className="text-slate-400 text-sm">Your academic overview</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6">
          <p className="text-red-400 text-sm">⚠️ {error}</p>
          <p className="text-xs text-slate-500 mt-1">Make sure backend is running on port 5000</p>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { l: 'Pending Tasks', v: pending.length, i: '📋', c: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20', h: '/student/assignments' },
          { l: 'Submitted', v: submissions.length, i: '✅', c: 'text-green-400 bg-green-500/10 border-green-500/20', h: '/student/assignments' },
          { l: 'Study Notes', v: notes.length, i: '📚', c: 'text-purple-400 bg-purple-500/10 border-purple-500/20', h: '/student/materials' },
          { l: 'PYQs Available', v: pyqs.length, i: '📋', c: 'text-blue-400 bg-blue-500/10 border-blue-500/20', h: '/student/materials' },
        ].map(s => (
          <Link key={s.l} href={s.h}>
            <div className="bg-slate-900 rounded-2xl border border-white/5 hover:border-white/10 p-5 cursor-pointer transition-all">
              <div className={'w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-3 border ' + s.c}>{s.i}</div>
              <p className={'text-2xl font-bold mb-1 ' + s.c.split(' ')[0]}>{s.v}</p>
              <p className="text-xs text-slate-500">{s.l}</p>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Tasks */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">Pending Tasks ({pending.length})</h2>
            <Link href="/student/assignments" className="text-xs text-blue-400">View all →</Link>
          </div>
          {pending.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-2xl mb-2">{tasks.length === 0 ? '📭' : '🎉'}</p>
              <p className="text-slate-400 text-sm">{tasks.length === 0 ? 'No tasks assigned yet' : 'All tasks submitted!'}</p>
            </div>
          ) : (
            <div className="space-y-2">
              {pending.slice(0,4).map((t: any) => {
                const dl = getDL(t.deadline)
                return (
                  <div key={t.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                    <span className="text-xl flex-shrink-0">{typeIcon[t.taskType] || '📋'}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{t.title}</p>
                      <p className="text-[10px] text-slate-500">{t.subjectName || 'General'} · {t.maxMarks}M</p>
                    </div>
                    <span className={'text-[10px] font-medium flex-shrink-0 ' + dl.color}>{dl.label}</span>
                  </div>
                )
              })}
            </div>
          )}
          {pending.length > 0 && (
            <Link href="/student/assignments">
              <button className="w-full mt-3 py-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-xl text-xs font-medium hover:bg-blue-500/20">📤 Submit Assignments</button>
            </Link>
          )}
        </div>

        {/* Recent Notes */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">Study Notes ({notes.length})</h2>
            <Link href="/student/materials" className="text-xs text-blue-400">View all →</Link>
          </div>
          {notes.length === 0 ? (
            <div className="text-center py-6"><p className="text-2xl mb-2">📭</p><p className="text-slate-400 text-sm">No notes uploaded yet</p></div>
          ) : (
            <div className="space-y-2">
              {notes.slice(0,4).map((m: any) => (
                <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                  <span className="text-xl flex-shrink-0">📚</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white truncate">{m.title}</p>
                    <div className="flex gap-1.5 flex-wrap mt-0.5">
                      {m.subject && <span className="text-[10px] text-green-400">{m.subject.length > 18 ? m.subject.slice(0,18)+'...' : m.subject}</span>}
                      {m.unit && <span className="text-[10px] text-slate-500">· {m.unit}</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* PYQs */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">Previous Year Papers ({pyqs.length})</h2>
            <Link href="/student/materials" className="text-xs text-blue-400">View all →</Link>
          </div>
          {pyqs.length === 0 ? (
            <div className="text-center py-6"><p className="text-2xl mb-2">📋</p><p className="text-slate-400 text-sm">No PYQs uploaded yet</p></div>
          ) : (
            <div className="space-y-2">
              {pyqs.slice(0,4).map((m: any) => (
                <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                  <span className="text-xl flex-shrink-0">📋</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white truncate">{m.title}</p>
                    <div className="flex gap-1.5 mt-0.5">
                      {m.subject && <span className="text-[10px] text-blue-400">{m.subject.length > 18 ? m.subject.slice(0,18)+'...' : m.subject}</span>}
                      {m.year && <span className="text-[10px] text-slate-500">· {m.year}</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
          <h2 className="text-sm font-semibold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-2">
            {[
              { l: 'Submit Assignment', i: '📤', h: '/student/assignments', c: 'hover:border-blue-500/30 hover:bg-blue-500/5' },
              { l: 'Study Notes', i: '📚', h: '/student/materials', c: 'hover:border-green-500/30 hover:bg-green-500/5' },
              { l: 'Previous Papers', i: '📋', h: '/student/materials', c: 'hover:border-purple-500/30 hover:bg-purple-500/5' },
              { l: 'AI Assistant', i: '🤖', h: '/student/chatbot', c: 'hover:border-orange-500/30 hover:bg-orange-500/5' },
            ].map(a => (
              <Link key={a.l} href={a.h}>
                <div className={'p-3 bg-slate-800 rounded-xl border border-white/5 transition-all cursor-pointer ' + a.c}>
                  <span className="text-xl">{a.i}</span>
                  <p className="text-xs font-medium text-white mt-2">{a.l}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
""")
print("Student Dashboard done!")

# Fix auth.ts - include classSectionId in token session
with open("../frontend/lib/auth.ts", "w", encoding="utf-8") as f:
    f.write("""import NextAuth from 'next-auth'
import AzureAD from 'next-auth/providers/microsoft-entra-id'

const SPECIAL_ACCOUNTS: Record<string, string> = {
  'akumarjaan123@gmail.com': 'teacher',
}

function getRoleFromEmail(email: string): string {
  if (!email) return 'unknown'
  if (SPECIAL_ACCOUNTS[email]) return SPECIAL_ACCOUNTS[email]
  const prefix = email.split('@')[0]
  const domain = email.split('@')[1]
  if (domain !== 'krmu.edu.in') return 'unknown'
  if (/^[0-9]/.test(prefix)) return 'student'
  if (/^[a-zA-Z]/.test(prefix)) return 'teacher'
  return 'unknown'
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true,
  providers: [
    AzureAD({
      clientId: process.env.AZURE_CLIENT_ID!,
      clientSecret: process.env.AZURE_CLIENT_SECRET!,
      tenantId: process.env.AZURE_TENANT_ID!,
      checks: ['none'],
    }),
  ],
  pages: { signIn: '/login', error: '/login' },
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, account, profile, trigger, session }) {
      // Handle session update (when student joins class)
      if (trigger === 'update' && session?.backendToken) {
        token.backendToken = session.backendToken
      }

      if (account && profile) {
        const email = (profile.email || token.email || '') as string
        const role = getRoleFromEmail(email)
        token.email = email
        token.name = profile.name
        token.role = role
        token.picture = (profile as any).picture || token.picture

        // Register user in backend DB
        try {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'
          const res = await fetch(apiUrl + '/auth/azure', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email,
              name: profile.name,
              azureOid: (profile as any).sub || account.providerAccountId,
              avatarUrl: (profile as any).picture || null,
            }),
          })
          if (res.ok) {
            const data = await res.json()
            token.backendToken = data.data?.token
            token.userId = data.data?.user?.id
            token.collegeId = data.data?.user?.collegeId
            token.classSectionId = data.data?.user?.classSectionId
          }
        } catch (err) {
          console.error('Backend sync error:', err)
        }
      }
      return token
    },
    async session({ session, token }) {
      session.user.role = token.role as string
      session.user.email = token.email as string
      session.user.backendToken = token.backendToken as string
      session.user.userId = token.userId as string
      return session
    },
  },
})
""")
print("auth.ts done!")

# Fix types
os.makedirs("../frontend/types", exist_ok=True)
with open("../frontend/types/next-auth.d.ts", "w", encoding="utf-8") as f:
    f.write("""import 'next-auth'

declare module 'next-auth' {
  interface Session {
    user: {
      name?: string | null
      email?: string | null
      image?: string | null
      role?: string
      backendToken?: string
      userId?: string
    }
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    role?: string
    backendToken?: string
    userId?: string
    collegeId?: string
    classSectionId?: string
  }
}
""")
print("Types done!")

print("\n" + "="*50)
print("ALL FIXES DONE!")
print("="*50)