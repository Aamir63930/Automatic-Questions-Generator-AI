import os

# Student Dashboard - fix infinite loading
with open("../frontend/app/(student)/student/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type ClassSection = {
  id: string; name: string; section: string; branch: string
  semester: number; year: number; uniqueCode: string
  _count: { students: number }
}

export default function StudentDashboard() {
  const { data: session, status } = useSession()
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [selectedClass, setSelectedClass] = useState<ClassSection | null>(null)
  const [tasks, setTasks] = useState<any[]>([])
  const [materials, setMaterials] = useState<any[]>([])
  const [submissions, setSubmissions] = useState<any[]>([])
  const [dataLoading, setDataLoading] = useState(false)
  const [classLoading, setClassLoading] = useState(true)
  const [showClassPicker, setShowClassPicker] = useState(false)
  const [error, setError] = useState('')
  const token = session?.user?.backendToken

  // Load classes once
  useEffect(() => {
    if (status === 'loading') return
    if (!token) { setClassLoading(false); return }

    fetch(API + '/auth/classes', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          setClasses(d.data || [])
          const savedId = localStorage.getItem('myClassId')
          if (savedId && d.data) {
            const found = d.data.find((c: ClassSection) => c.id === savedId)
            if (found) setSelectedClass(found)
          }
        }
      })
      .catch(e => setError('Cannot connect to backend: ' + e.message))
      .finally(() => setClassLoading(false))
  }, [token, status])

  // Load data when class selected or on first load (no class)
  useEffect(() => {
    if (status === 'loading' || !token) return
    if (classLoading) return // Wait for classes to load first

    const classId = selectedClass?.id || localStorage.getItem('myClassId') || ''
    setDataLoading(true)
    setError('')

    const headers = { Authorization: 'Bearer ' + token }
    const taskUrl = classId ? API + '/tasks?classId=' + classId : API + '/tasks'
    const matUrl = classId ? API + '/materials?classId=' + classId : API + '/materials'

    Promise.all([
      fetch(taskUrl, { headers }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
      fetch(matUrl, { headers }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
      fetch(API + '/submissions', { headers }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
    ]).then(([t, m, s]) => {
      if (t.success) setTasks(t.data || [])
      if (m.success) setMaterials(m.data || [])
      if (s.success) setSubmissions(s.data || [])
      if (!t.success || !m.success) setError('Some data failed to load. Backend running?')
    }).catch(e => {
      setError('Network error: ' + e.message)
    }).finally(() => setDataLoading(false))
  }, [token, status, selectedClass, classLoading])

  const switchClass = (cls: ClassSection) => {
    setSelectedClass(cls)
    localStorage.setItem('myClassId', cls.id)
    setShowClassPicker(false)
    setTasks([]); setMaterials([]); setSubmissions([])
  }

  const notes = materials.filter(m => !m.isPyq)
  const pyqs = materials.filter(m => m.isPyq)
  const subIds = submissions.map((s: any) => s.taskId)
  const pending = tasks.filter(t => !subIds.includes(t.id))
  const graded = submissions.filter(s => s.status === 'graded')

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

  // Only show loading on FIRST load
  if (status === 'loading' || classLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Loading dashboard...</p>
      </div>
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">
            Welcome, {session?.user?.name?.split(' ')[0] || 'Student'} 👋
          </h1>
          <p className="text-slate-400 text-sm">Your academic overview</p>
        </div>

        {/* Class switcher */}
        <div className="relative">
          <button onClick={() => setShowClassPicker(!showClassPicker)}
            className="flex items-center gap-3 bg-slate-900 border border-white/10 hover:border-green-500/30 rounded-xl px-4 py-3 transition-all">
            <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center text-green-400 font-bold text-sm">
              {selectedClass ? selectedClass.section : '?'}
            </div>
            <div className="text-left">
              <p className="text-xs font-semibold text-white">
                {selectedClass ? selectedClass.name + ' — Sec ' + selectedClass.section : 'Select Class'}
              </p>
              <p className="text-[10px] text-slate-500">
                {selectedClass ? selectedClass.branch + ' · Sem ' + selectedClass.semester : 'No class selected'}
              </p>
            </div>
            <span className="text-slate-500 text-xs">{showClassPicker ? '▲' : '▼'}</span>
          </button>

          {showClassPicker && (
            <div className="absolute right-0 top-full mt-2 w-72 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden">
              <div className="p-3 border-b border-white/5">
                <p className="text-xs text-slate-500 uppercase tracking-wider">Switch Class</p>
              </div>
              {classes.length === 0 ? (
                <div className="p-4 text-center text-xs text-slate-500">No classes available yet</div>
              ) : classes.map(cls => (
                <button key={cls.id} onClick={() => switchClass(cls)}
                  className={'w-full p-3 text-left hover:bg-slate-800 transition-all flex items-center gap-3 ' + (cls.id === selectedClass?.id ? 'bg-green-500/10' : '')}>
                  <div className={'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ' + (cls.id === selectedClass?.id ? 'bg-green-500 text-white' : 'bg-slate-800 text-slate-400')}>
                    {cls.section}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white">{cls.name} — Sec {cls.section}</p>
                    <p className="text-xs text-slate-500">{cls.branch} · Sem {cls.semester}</p>
                  </div>
                  {cls.id === selectedClass?.id && <span className="text-green-400 text-xs">✓</span>}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {showClassPicker && <div className="fixed inset-0 z-40" onClick={() => setShowClassPicker(false)} />}

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-5">
          <p className="text-red-400 text-sm">⚠️ {error}</p>
          <p className="text-xs text-slate-500 mt-1">Make sure backend is running on port 5000</p>
        </div>
      )}

      {/* Class info banner */}
      {selectedClass && (
        <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/20 rounded-2xl p-4 mb-6 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center text-xl">🏫</div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">{selectedClass.name} — Section {selectedClass.section}</p>
            <p className="text-xs text-slate-400">{selectedClass.branch} · Sem {selectedClass.semester} · Code: <span className="text-green-400 font-mono">{selectedClass.uniqueCode}</span></p>
          </div>
          <div className="text-right">
            <p className="text-lg font-bold text-green-400">{selectedClass._count.students}</p>
            <p className="text-[10px] text-slate-500">classmates</p>
          </div>
        </div>
      )}

      {/* No class selected */}
      {!selectedClass && classes.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4 mb-5">
          <p className="text-sm text-yellow-400 font-medium">⚠️ Select your class to see class-specific tasks</p>
          <p className="text-xs text-slate-500 mt-1">Currently showing all college-wide content</p>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { l: 'Pending Tasks', v: dataLoading ? '...' : pending.length, i: '📋', c: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20', h: '/student/assignments' },
          { l: 'Submitted', v: dataLoading ? '...' : submissions.length, i: '✅', c: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20', h: '/student/assignments' },
          { l: 'Study Notes', v: dataLoading ? '...' : notes.length, i: '📚', c: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20', h: '/student/materials' },
          { l: 'PYQs', v: dataLoading ? '...' : pyqs.length, i: '📄', c: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20', h: '/student/materials' },
        ].map(s => (
          <Link key={s.l} href={s.h}>
            <div className={'bg-slate-900 rounded-2xl border p-5 cursor-pointer hover:scale-[1.02] transition-all ' + s.bg}>
              <div className={'w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-3 border ' + s.bg}>{s.i}</div>
              <p className={'text-2xl font-bold mb-1 ' + s.c}>{s.v}</p>
              <p className="text-xs text-slate-500">{s.l}</p>
            </div>
          </Link>
        ))}
      </div>

      {dataLoading ? (
        <div className="text-center py-8">
          <div className="w-6 h-6 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-slate-500 text-xs">Loading data...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pending Tasks */}
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">📋 Pending ({pending.length})</h2>
              <Link href="/student/assignments" className="text-xs text-blue-400">View all →</Link>
            </div>
            {tasks.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-2">📭</p>
                <p className="text-slate-400 text-sm">No tasks assigned yet</p>
              </div>
            ) : pending.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-2">🎉</p>
                <p className="text-slate-400 text-sm">All tasks submitted!</p>
              </div>
            ) : (
              <div className="space-y-2">
                {pending.slice(0,5).map((t: any) => {
                  const dl = getDL(t.deadline)
                  return (
                    <div key={t.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                      <span className="text-xl flex-shrink-0">{typeIcon[t.taskType] || '📋'}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-white truncate">{t.title}</p>
                        <p className="text-[10px] text-slate-500">{t.subjectName || 'General'} · {t.maxMarks}M</p>
                      </div>
                      <span className={'text-[10px] font-semibold flex-shrink-0 ' + dl.color}>{dl.label}</span>
                    </div>
                  )
                })}
              </div>
            )}
            {pending.length > 0 && (
              <Link href="/student/assignments">
                <button className="w-full mt-3 py-2.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-xl text-xs font-medium hover:bg-blue-500/20">📤 Submit Now</button>
              </Link>
            )}
          </div>

          {/* Notes */}
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">📚 Notes ({notes.length})</h2>
              <Link href="/student/materials" className="text-xs text-blue-400">View all →</Link>
            </div>
            {notes.length === 0 ? (
              <div className="text-center py-8"><p className="text-3xl mb-2">📭</p><p className="text-slate-400 text-sm">No notes uploaded yet</p></div>
            ) : (
              <div className="space-y-2">
                {notes.slice(0,5).map((m: any) => (
                  <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                    <span className="text-xl flex-shrink-0">📚</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{m.title}</p>
                      <div className="flex gap-2 mt-0.5">
                        {m.subject && <span className="text-[10px] text-green-400 truncate max-w-[120px]">{m.subject}</span>}
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
              <h2 className="text-sm font-semibold text-white">📄 PYQs ({pyqs.length})</h2>
              <Link href="/student/materials" className="text-xs text-blue-400">View all →</Link>
            </div>
            {pyqs.length === 0 ? (
              <div className="text-center py-8"><p className="text-3xl mb-2">📄</p><p className="text-slate-400 text-sm">No PYQs yet</p></div>
            ) : (
              <div className="space-y-2">
                {pyqs.slice(0,5).map((m: any) => (
                  <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                    <span className="text-xl flex-shrink-0">📄</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{m.title}</p>
                      <div className="flex gap-2 mt-0.5">
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
                { l: 'Submit Task', i: '📤', h: '/student/assignments', c: 'hover:border-blue-500/30 hover:bg-blue-500/5' },
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
            {graded.length > 0 && (
              <Link href="/student/results">
                <div className="mt-3 p-3 bg-green-500/10 border border-green-500/20 rounded-xl flex items-center justify-between cursor-pointer hover:bg-green-500/15 transition-all">
                  <div>
                    <p className="text-xs font-semibold text-green-400">📊 {graded.length} results available</p>
                    <p className="text-[10px] text-slate-500">View your grades</p>
                  </div>
                  <span className="text-green-400 text-sm">→</span>
                </div>
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Student Dashboard fixed!")

# Teacher Dashboard - fix loading too
os.makedirs("../frontend/app/(dashboard)/teacher", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

export default function TeacherDashboard() {
  const { data: session, status } = useSession()
  const [tasks, setTasks] = useState<any[]>([])
  const [materials, setMaterials] = useState<any[]>([])
  const [classes, setClasses] = useState<any[]>([])
  const [pending, setPending] = useState<{ totalPending: number; tasks: any[] }>({ totalPending: 0, tasks: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const token = session?.user?.backendToken

  useEffect(() => {
    if (status === 'loading') return
    if (!token) { setLoading(false); return }

    const h = { Authorization: 'Bearer ' + token }
    Promise.all([
      fetch(API + '/tasks', { headers: h }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
      fetch(API + '/materials', { headers: h }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
      fetch(API + '/auth/classes', { headers: h }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
      fetch(API + '/submissions/pending-summary', { headers: h }).then(r => r.json()).catch(() => ({ success: false, data: { totalPending: 0, tasks: [] } })),
    ]).then(([t, m, c, p]) => {
      if (t.success) setTasks(t.data || [])
      if (m.success) setMaterials(m.data || [])
      if (c.success) setClasses(c.data || [])
      if (p.success) setPending(p.data || { totalPending: 0, tasks: [] })
    }).catch(e => setError('Backend error: ' + e.message))
    .finally(() => setLoading(false))
  }, [token, status])

  const active = tasks.filter(t => t.status === 'active')
  const totalStudents = classes.reduce((s, c) => s + (c._count?.students || 0), 0)

  if (status === 'loading' || loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Loading dashboard...</p>
      </div>
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">Welcome, {session?.user?.name?.split(' ')[0] || 'Teacher'} 👋</h1>
        <p className="text-slate-400 text-sm">K.R Mangalam University — Teacher Dashboard</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-5">
          <p className="text-red-400 text-sm">⚠️ {error}</p>
        </div>
      )}

      {/* Pending grading alert */}
      {pending.totalPending > 0 && (
        <Link href="/teacher/results">
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4 mb-6 flex items-center gap-3 cursor-pointer hover:bg-yellow-500/15 transition-all">
            <span className="text-2xl">⏳</span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-yellow-400">{pending.totalPending} submissions waiting to be graded</p>
              <p className="text-xs text-slate-500">Click to grade and notify students</p>
            </div>
            <span className="text-yellow-400 text-sm">Grade Now →</span>
          </div>
        </Link>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { l: 'Total Classes', v: classes.length, i: '🏫', c: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20', h: '/teacher/classes' },
          { l: 'Total Students', v: totalStudents, i: '👥', c: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20', h: '/teacher/classes' },
          { l: 'Active Tasks', v: active.length, i: '📋', c: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20', h: '/teacher/tasks' },
          { l: 'Materials', v: materials.length, i: '📚', c: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20', h: '/teacher/materials' },
        ].map(s => (
          <Link key={s.l} href={s.h}>
            <div className={'bg-slate-900 rounded-2xl border p-5 cursor-pointer hover:scale-[1.02] transition-all ' + s.bg}>
              <div className={'w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-3 border ' + s.bg}>{s.i}</div>
              <p className={'text-2xl font-bold mb-1 ' + s.c}>{s.v}</p>
              <p className="text-xs text-slate-500">{s.l}</p>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Tasks */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">Recent Tasks ({tasks.length})</h2>
            <Link href="/teacher/tasks" className="text-xs text-blue-400">Manage →</Link>
          </div>
          {tasks.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-3xl mb-2">📋</p>
              <p className="text-slate-400 text-sm">No tasks created yet</p>
              <Link href="/teacher/tasks"><button className="mt-3 px-4 py-2 bg-blue-500 text-white text-xs rounded-xl">Create Task</button></Link>
            </div>
          ) : (
            <div className="space-y-2">
              {tasks.slice(0,5).map((t: any) => (
                <div key={t.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                  <div className={'w-2 h-2 rounded-full flex-shrink-0 ' + (t.status === 'active' ? 'bg-green-400' : 'bg-slate-600')} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white truncate">{t.title}</p>
                    <p className="text-[10px] text-slate-500">{t.subjectName || 'General'} · {t._count?.submissions || 0} submissions</p>
                  </div>
                  <span className={'text-[10px] px-2 py-0.5 rounded border ' + (t.status === 'active' ? 'text-green-400 bg-green-500/10 border-green-500/20' : 'text-slate-500 bg-slate-700 border-white/10')}>{t.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Classes */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">Classes ({classes.length})</h2>
            <Link href="/teacher/classes" className="text-xs text-blue-400">Manage →</Link>
          </div>
          {classes.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-3xl mb-2">🏫</p>
              <p className="text-slate-400 text-sm">No classes created yet</p>
              <Link href="/teacher/classes"><button className="mt-3 px-4 py-2 bg-blue-500 text-white text-xs rounded-xl">Create Class</button></Link>
            </div>
          ) : (
            <div className="space-y-2">
              {classes.map((c: any) => (
                <div key={c.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold text-xs">{c.section}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white">{c.name} — Sec {c.section}</p>
                    <p className="text-[10px] text-slate-500">{c.branch} · Sem {c.semester} · {c._count?.students || 0} students</p>
                  </div>
                  <span className="text-xs font-mono text-green-400 bg-green-500/10 px-2 py-0.5 rounded-lg border border-green-500/20">{c.uniqueCode}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5 lg:col-span-2">
          <h2 className="text-sm font-semibold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { l: 'Generate QP', i: '🤖', h: '/teacher/generate', c: 'hover:border-blue-500/30 hover:bg-blue-500/5' },
              { l: 'Create Task', i: '📋', h: '/teacher/tasks', c: 'hover:border-purple-500/30 hover:bg-purple-500/5' },
              { l: 'Upload Notes', i: '📚', h: '/teacher/materials', c: 'hover:border-green-500/30 hover:bg-green-500/5' },
              { l: 'Grade Results', i: '📊', h: '/teacher/results', c: 'hover:border-yellow-500/30 hover:bg-yellow-500/5' },
              { l: 'Manage Classes', i: '🏫', h: '/teacher/classes', c: 'hover:border-blue-500/30 hover:bg-blue-500/5' },
              { l: 'Send Notification', i: '🔔', h: '/teacher/notifications', c: 'hover:border-orange-500/30 hover:bg-orange-500/5' },
              { l: 'View Complaints', i: '💬', h: '/teacher/complaints', c: 'hover:border-red-500/30 hover:bg-red-500/5' },
              { l: 'My Papers', i: '📄', h: '/teacher/papers', c: 'hover:border-purple-500/30 hover:bg-purple-500/5' },
            ].map(a => (
              <Link key={a.l} href={a.h}>
                <div className={'p-4 bg-slate-800 rounded-xl border border-white/5 transition-all cursor-pointer text-center ' + a.c}>
                  <span className="text-2xl">{a.i}</span>
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
print("Teacher Dashboard fixed!")

print("\n=== ALL DONE ===")