import os

# ═══════════════════════════════════════════════════════
# FIX 1: Student Class Selection - Course→Branch→Section
# ═══════════════════════════════════════════════════════
os.makedirs("../frontend/app/(student)/student/select-class", exist_ok=True)
with open("../frontend/app/(student)/student/select-class/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type ClassSection = {
  id: string; name: string; section: string; branch: string
  semester: number; year: number; uniqueCode: string
  _count: { students: number }
}

export default function SelectClassPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState<'code'|'browse'>('browse')
  const [code, setCode] = useState('')
  const [joining, setJoining] = useState(false)
  const [err, setErr] = useState('')
  const [ok, setOk] = useState('')

  // Browse hierarchy
  const [selCourse, setSelCourse] = useState('')
  const [selBranch, setSelBranch] = useState('')
  const [selSem, setSelSem] = useState('')
  const [selClass, setSelClass] = useState('')

  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    fetch(API + '/auth/classes', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(d => { if (d.success) setClasses(d.data || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [token])

  // Course = class name (B.Tech, BCA, MCA etc.)
  const courses = Array.from(new Set(classes.map(c => c.name))).sort()
  const branches = Array.from(new Set(classes.filter(c => !selCourse || c.name === selCourse).map(c => c.branch))).sort()
  const semesters = Array.from(new Set(classes.filter(c => (!selCourse || c.name === selCourse) && (!selBranch || c.branch === selBranch)).map(c => c.semester.toString()))).sort()
  const filteredClasses = classes.filter(c =>
    (!selCourse || c.name === selCourse) &&
    (!selBranch || c.branch === selBranch) &&
    (!selSem || c.semester.toString() === selSem)
  )

  const afterJoin = (newToken?: string) => {
    if (newToken) localStorage.setItem('backendToken', newToken)
    setOk('Joined successfully! Redirecting...')
    setTimeout(() => { window.location.href = '/student' }, 1200)
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
      if (d.success) afterJoin(d.data?.token)
      else setErr(d.message || 'Invalid code')
    } catch { setErr('Connection error') }
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
        localStorage.setItem('myClassId', selClass)
        afterJoin(d.data?.token)
      } else setErr(d.message || 'Failed')
    } catch { setErr('Connection error') }
    setJoining(false)
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
          <p className="text-slate-400 text-sm">Select your course, branch and section</p>
          {session?.user?.name && <p className="text-green-400 text-sm mt-2">Welcome, {session.user.name.split(' ')[0]}! 👋</p>}
        </div>

        {/* Mode tabs */}
        <div className="flex gap-1 bg-slate-900 border border-white/10 rounded-2xl p-1.5 mb-6">
          <button onClick={() => { setMode('browse'); setErr('') }} className={'flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ' + (mode === 'browse' ? 'bg-green-500 text-white' : 'text-slate-400 hover:text-white')}>
            📋 Select Class
          </button>
          <button onClick={() => { setMode('code'); setErr('') }} className={'flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ' + (mode === 'code' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
            🔑 Enter Code
          </button>
        </div>

        {mode === 'browse' && (
          <div className="bg-slate-900 rounded-2xl border border-white/10 p-6 space-y-5">
            {loading ? (
              <div className="text-center py-6"><div className="w-6 h-6 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
            ) : classes.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-3xl mb-2">⏳</p>
                <p className="text-white font-medium">No classes created yet</p>
                <p className="text-slate-400 text-sm mt-1">Ask your teacher to create a class or enter the class code</p>
                <button onClick={() => setMode('code')} className="mt-4 px-4 py-2 bg-blue-500 text-white text-sm rounded-xl">Enter Code Instead</button>
              </div>
            ) : (
              <>
                {/* Step 1: Course */}
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-green-500 text-white text-[10px] flex items-center justify-center font-bold">1</span>
                    Select Course / Programme
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {courses.map(c => (
                      <button key={c} onClick={() => { setSelCourse(c); setSelBranch(''); setSelSem(''); setSelClass('') }}
                        className={'p-3.5 rounded-xl border text-left transition-all ' + (selCourse === c ? 'border-green-500/60 bg-green-500/10' : 'border-white/5 bg-slate-800 hover:border-white/20')}>
                        <p className="text-sm font-semibold text-white">{c}</p>
                        <p className="text-[10px] text-slate-500 mt-0.5">{classes.filter(x => x.name === c).length} sections</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Step 2: Branch */}
                {selCourse && branches.length > 0 && (
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-blue-500 text-white text-[10px] flex items-center justify-center font-bold">2</span>
                      Select Branch / Department
                    </p>
                    <div className="grid grid-cols-3 gap-2">
                      {branches.map(b => (
                        <button key={b} onClick={() => { setSelBranch(b); setSelSem(''); setSelClass('') }}
                          className={'py-2.5 rounded-xl text-sm font-medium border transition-all ' + (selBranch === b ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/20')}>
                          {b}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Step 3: Semester */}
                {selBranch && semesters.length > 0 && (
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-purple-500 text-white text-[10px] flex items-center justify-center font-bold">3</span>
                      Select Semester
                    </p>
                    <div className="grid grid-cols-4 gap-2">
                      {semesters.map(s => (
                        <button key={s} onClick={() => { setSelSem(s); setSelClass('') }}
                          className={'py-2.5 rounded-xl text-sm font-medium border transition-all ' + (selSem === s ? 'bg-purple-500 text-white border-purple-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/20')}>
                          Sem {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Step 4: Section */}
                {selSem && filteredClasses.length > 0 && (
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-orange-500 text-white text-[10px] flex items-center justify-center font-bold">4</span>
                      Select Section
                    </p>
                    <div className="space-y-2">
                      {filteredClasses.map(c => (
                        <button key={c.id} onClick={() => setSelClass(c.id)}
                          className={'w-full p-4 rounded-xl border text-left transition-all ' + (selClass === c.id ? 'border-green-500/60 bg-green-500/10' : 'border-white/5 bg-slate-800 hover:border-white/20')}>
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-bold text-white">Section {c.section}</p>
                              <p className="text-xs text-slate-500">{c._count.students} students enrolled</p>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-mono text-green-400 bg-green-500/10 px-2 py-1 rounded-lg border border-green-500/20 block">{c.uniqueCode}</span>
                              {selClass === c.id && <span className="text-[10px] text-green-400 mt-1 block">✓ Selected</span>}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {err && <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-xs text-red-400">⚠️ {err}</div>}
                {ok && <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3 text-xs text-green-400">✓ {ok}</div>}

                {selClass && (
                  <button onClick={joinBySelect} disabled={joining || !!ok}
                    className="w-full py-3.5 bg-green-500 text-white text-sm font-bold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center justify-center gap-2">
                    {joining ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Joining...</> : '🚀 Join This Class'}
                  </button>
                )}
              </>
            )}
          </div>
        )}

        {mode === 'code' && (
          <div className="bg-slate-900 rounded-2xl border border-white/10 p-6">
            <label className="block text-xs text-slate-400 mb-3 uppercase tracking-widest">Class Code from Teacher</label>
            <input type="text" value={code}
              onChange={e => { setCode(e.target.value.toUpperCase()); setErr('') }}
              onKeyDown={e => e.key === 'Enter' && joinByCode()}
              placeholder="e.g. BCA1A-B3F2"
              maxLength={15} autoFocus
              className="w-full bg-slate-800 border border-white/10 rounded-xl px-5 py-4 text-2xl font-mono font-bold text-white text-center tracking-widest outline-none focus:border-green-500/60 placeholder:text-slate-700 placeholder:text-sm placeholder:font-normal mb-4"
            />
            {err && <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4 text-xs text-red-400">⚠️ {err}</div>}
            {ok && <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3 mb-4 text-xs text-green-400">✓ {ok}</div>}
            <button onClick={joinByCode} disabled={code.length < 5 || joining || !!ok}
              className="w-full py-3.5 bg-green-500 text-white text-sm font-bold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center justify-center gap-2 mb-3">
              {joining ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Joining...</> : '🚀 Join Class'}
            </button>
          </div>
        )}

        <div className="text-center mt-4">
          <button onClick={() => { localStorage.setItem('classSkipped', 'true'); window.location.href = '/student' }} className="text-slate-600 hover:text-slate-400 text-xs">
            Skip for now
          </button>
        </div>
      </div>
    </div>
  )
}
""")
print("Student Class Selection done!")

# ═══════════════════════════════════════════════════════
# FIX 2: Teacher Results - fix key error + grading + notify
# ═══════════════════════════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/results", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/results/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect, useCallback } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

export default function TeacherResultsPage() {
  const { data: session } = useSession()
  const [view, setView] = useState<'overview'|'classwise'|'pending'|'grade'>('overview')
  const [classGroups, setClassGroups] = useState<any[]>([])
  const [pendingSummary, setPendingSummary] = useState<any>({ totalPending: 0, tasks: [] })
  const [tasks, setTasks] = useState<any[]>([])
  const [selTask, setSelTask] = useState<any>(null)
  const [taskStatus, setTaskStatus] = useState<any>(null)
  const [subs, setSubs] = useState<any[]>([])
  const [editId, setEditId] = useState<string|null>(null)
  const [editMarks, setEditMarks] = useState('')
  const [editFeedback, setEditFeedback] = useState('')
  const [saving, setSaving] = useState(false)
  const [sendingNotif, setSendingNotif] = useState<string|null>(null)
  const [expandedStudent, setExpandedStudent] = useState<string|null>(null)
  const [expandedClass, setExpandedClass] = useState<string|null>(null)
  const [search, setSearch] = useState('')
  const token = session?.user?.backendToken

  const load = useCallback(async () => {
    if (!token) return
    const h = { Authorization: 'Bearer ' + token }
    try {
      const [r, p, t] = await Promise.all([
        fetch(API + '/submissions/results-summary', { headers: h }).then(x => x.json()),
        fetch(API + '/submissions/pending-summary', { headers: h }).then(x => x.json()),
        fetch(API + '/tasks', { headers: h }).then(x => x.json()),
      ])
      if (r.success) setClassGroups(r.data || [])
      if (p.success) setPendingSummary(p.data || { totalPending: 0, tasks: [] })
      if (t.success) setTasks(t.data || [])
    } catch (e) { console.error(e) }
  }, [token])

  useEffect(() => { load() }, [load])

  const loadTaskSubs = async (taskId: string) => {
    if (!token) return
    const h = { Authorization: 'Bearer ' + token }
    const [s, ts] = await Promise.all([
      fetch(API + '/submissions?taskId=' + taskId, { headers: h }).then(r => r.json()),
      fetch(API + '/submissions/task/' + taskId + '/status', { headers: h }).then(r => r.json()),
    ])
    if (s.success) setSubs(s.data || [])
    if (ts.success) setTaskStatus(ts.data)
  }

  const selectTask = (t: any) => {
    setSelTask(t); setView('grade'); setEditId(null); setSubs([]); setTaskStatus(null)
    loadTaskSubs(t.id)
  }

  const saveGrade = async (sub: any) => {
    if (!token || !editMarks) return
    setSaving(true)
    const res = await fetch(API + '/submissions/' + sub.id + '/grade', {
      method: 'PATCH',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ marks: editMarks, feedback: editFeedback })
    })
    if ((await res.json()).success) {
      await load()
      await loadTaskSubs(sub.taskId)
      setEditId(null)
    }
    setSaving(false)
  }

  const sendReminder = async (taskId: string, studentId: string, studentName: string, taskTitle: string) => {
    if (!token) return
    setSendingNotif(studentId)
    try {
      await fetch(API + '/notifications/send', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: '⚠️ Reminder: Submit Task',
          body: 'Please submit "' + taskTitle + '" before the deadline!',
          type: 'task', target: 'specific_student', studentId, refId: taskId
        })
      })
    } catch {}
    setSendingNotif(null)
  }

  const sendBulkReminder = async (task: any) => {
    if (!token || !task.notSubmitted?.length) return
    setSendingNotif('bulk_' + task.taskId)
    for (const s of task.notSubmitted) {
      await fetch(API + '/notifications', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: s.id, title: '⚠️ Deadline Reminder',
          body: 'Please submit "' + task.title + '" before the deadline. Hurry!',
          type: 'task', refId: task.taskId
        })
      }).catch(() => {})
    }
    setSendingNotif(null)
    alert('Reminder sent to ' + task.notSubmitted.length + ' students!')
  }

  const gc = (m: number, max: number) => {
    const p = (m/max)*100
    return p>=80?'text-green-400':p>=60?'text-blue-400':p>=40?'text-yellow-400':'text-red-400'
  }

  const allStudents = classGroups.flatMap(c => c.students.map((s: any) => ({ ...s, className: c.className })))
  const filtered = search ? allStudents.filter(s => s.name.toLowerCase().includes(search.toLowerCase()) || (s.rollNumber||'').includes(search)) : allStudents

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Results & Grading</h1>
          <p className="text-slate-400 text-sm">Class-wise and student-wise tracking</p>
        </div>
        {pendingSummary.totalPending > 0 && (
          <button onClick={() => setView('pending')} className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl px-4 py-2.5 flex items-center gap-2 hover:bg-yellow-500/15 transition-all">
            <span className="text-yellow-400">⏳</span>
            <div className="text-left">
              <p className="text-sm font-semibold text-yellow-400">{pendingSummary.totalPending} pending</p>
              <p className="text-xs text-slate-500">Click to grade</p>
            </div>
          </button>
        )}
      </div>

      {/* View tabs */}
      <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-2xl p-1.5 mb-6">
        {[
          { k: 'overview', l: '📊 Student Overview' },
          { k: 'classwise', l: '🏫 Class-wise', count: classGroups.length },
          { k: 'pending', l: '⏳ Grade', count: pendingSummary.totalPending || null },
        ].map(tab => (
          <button key={tab.k} onClick={() => setView(tab.k as any)}
            className={'flex-1 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2 ' +
              (view === tab.k ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
            {tab.l}
            {(tab as any).count > 0 && (
              <span className={'text-xs px-1.5 rounded-full ' + (view === tab.k ? 'bg-white/20' : 'bg-blue-500/20 text-blue-400')}>
                {(tab as any).count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* OVERVIEW */}
      {view === 'overview' && (
        <div>
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search student by name or roll number..."
            className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 mb-4" />

          {allStudents.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">📊</p>
              <p className="text-white font-medium">No submissions yet</p>
            </div>
          ) : (
            <div className="bg-slate-900 rounded-2xl border border-white/5 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/5 bg-slate-800/50">
                      {['Student', 'Class', 'Roll No', 'Total Marks', '%', 'Grade', 'Tasks'].map(h => (
                        <th key={h} className="text-left px-4 py-3 text-[10px] text-slate-400 uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((s, i) => (
                      <>
                        <tr key={s.id + '_row'} onClick={() => setExpandedStudent(expandedStudent === s.id ? null : s.id)}
                          className={'border-b border-white/5 cursor-pointer hover:bg-slate-800/30 ' + (i%2===0?'':'bg-slate-800/10')}>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold">{s.name.charAt(0)}</div>
                              <span className="text-sm font-medium text-white">{s.name}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-400">{s.className}</td>
                          <td className="px-4 py-3 text-xs text-slate-400">{s.rollNumber || '-'}</td>
                          <td className="px-4 py-3">
                            <span className={'text-sm font-bold ' + (s.totalMax > 0 ? gc(s.totalObtained, s.totalMax) : 'text-slate-500')}>
                              {s.totalObtained}/{s.totalMax}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            {s.avgPct !== null ? (
                              <div className="flex items-center gap-2">
                                <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                  <div className={'h-full rounded-full ' + gc(s.totalObtained, s.totalMax).replace('text-','bg-')}
                                    style={{ width: s.avgPct + '%' }} />
                                </div>
                                <span className={'text-sm font-semibold ' + gc(s.totalObtained, s.totalMax)}>{s.avgPct}%</span>
                              </div>
                            ) : <span className="text-slate-500 text-xs">Pending</span>}
                          </td>
                          <td className="px-4 py-3">
                            <span className={'text-base font-bold ' + (s.grade === 'A' ? 'text-green-400' : s.grade === 'B' ? 'text-blue-400' : s.grade === 'C' ? 'text-yellow-400' : s.grade === 'F' ? 'text-red-400' : 'text-slate-500')}>
                              {s.grade}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-400">{s.tasks.length} tasks {expandedStudent === s.id ? '▲' : '▼'}</td>
                        </tr>
                        {expandedStudent === s.id && (
                          <tr key={s.id + '_expanded'}>
                            <td colSpan={7} className="px-4 py-3 bg-slate-800/20">
                              <div className="space-y-2">
                                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Task-wise / Subject-wise breakdown</p>
                                {s.tasks.map((t: any, ti: number) => (
                                  <div key={s.id + '_task_' + ti} className="flex items-center gap-4 bg-slate-900 rounded-xl p-3 border border-white/5">
                                    <div className="flex-1">
                                      <p className="text-xs font-medium text-white">{t.title}</p>
                                      {t.subjectName && <p className="text-[10px] text-blue-400">{t.subjectName}</p>}
                                      {t.feedback && <p className="text-[10px] text-slate-500 mt-0.5">💬 {t.feedback}</p>}
                                    </div>
                                    <div className="text-right">
                                      <span className={'text-sm font-bold ' + (t.marksAwarded !== null ? gc(t.marksAwarded, t.maxMarks) : 'text-slate-500')}>
                                        {t.marksAwarded !== null ? t.marksAwarded + '/' + t.maxMarks : 'Not graded'}
                                      </span>
                                    </div>
                                    <span className={'text-[10px] px-2 py-0.5 rounded border ' +
                                      (t.marksAwarded !== null ? 'text-green-400 bg-green-500/10 border-green-500/20' :
                                       t.status === 'submitted' ? 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' :
                                       'text-slate-500 bg-slate-700 border-white/5')}>
                                      {t.marksAwarded !== null ? 'Graded' : t.status}
                                    </span>
                                    {t.marksAwarded === null && t.status === 'submitted' && t.submissionId && (
                                      <button onClick={() => {
                                        const fullTask = tasks.find(x => x.id === t.taskId)
                                        if (fullTask) selectTask(fullTask)
                                      }} className="text-[10px] px-2 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20">
                                        Grade →
                                      </button>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* CLASS-WISE */}
      {view === 'classwise' && (
        <div className="space-y-4">
          {classGroups.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">🏫</p><p className="text-slate-400">No data yet</p>
            </div>
          ) : classGroups.map(cls => {
            const isExpanded = expandedClass === cls.classId
            const avgPct = cls.students.filter((s: any) => s.totalMax > 0).reduce((sum: number, s: any) => sum + (s.avgPct || 0), 0) / (cls.students.filter((s: any) => s.totalMax > 0).length || 1)
            return (
              <div key={cls.classId} className="bg-slate-900 rounded-2xl border border-white/5 overflow-hidden">
                <button onClick={() => setExpandedClass(isExpanded ? null : cls.classId)}
                  className="w-full p-5 text-left hover:bg-slate-800/30 transition-all">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 font-bold">{cls.className.charAt(0)}</div>
                      <div>
                        <p className="text-sm font-semibold text-white">🏫 {cls.className}</p>
                        <p className="text-xs text-slate-500">{cls.branch} · {cls.studentCount} students submitted</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className={'text-lg font-bold ' + gc(avgPct, 100)}>{Math.round(avgPct)}%</p>
                        <p className="text-[10px] text-slate-500">Avg</p>
                      </div>
                      <span className="text-slate-500">{isExpanded ? '▲' : '▼'}</span>
                    </div>
                  </div>
                </button>
                {isExpanded && (
                  <div className="border-t border-white/5 overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-white/5 bg-slate-800/50">
                          {['Rank','Student','Roll No','Marks','%','Grade'].map(h => (
                            <th key={h} className="text-left px-4 py-2.5 text-[10px] text-slate-400 uppercase">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {cls.students.map((s: any, i: number) => (
                          <tr key={cls.classId + '_' + s.id} className={'border-b border-white/5 ' + (i%2===0?'':'bg-slate-800/10')}>
                            <td className="px-4 py-3 text-sm font-bold">{i===0?'🥇':i===1?'🥈':i===2?'🥉':`#${i+1}`}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-7 h-7 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold">{s.name.charAt(0)}</div>
                                <span className="text-sm text-white">{s.name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-xs text-slate-400">{s.rollNumber || '-'}</td>
                            <td className="px-4 py-3 text-sm font-bold">
                              <span className={s.totalMax > 0 ? gc(s.totalObtained, s.totalMax) : 'text-slate-500'}>
                                {s.totalObtained}/{s.totalMax}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                  <div className={'h-full rounded-full ' + (s.totalMax > 0 ? gc(s.totalObtained, s.totalMax).replace('text-','bg-') : 'bg-slate-600')}
                                    style={{ width: (s.avgPct || 0) + '%' }} />
                                </div>
                                <span className={'text-xs font-semibold ' + (s.totalMax > 0 ? gc(s.totalObtained, s.totalMax) : 'text-slate-500')}>
                                  {s.avgPct !== null ? s.avgPct + '%' : '-'}
                                </span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-base font-bold">
                              <span className={s.grade === 'A' ? 'text-green-400' : s.grade === 'B' ? 'text-blue-400' : s.grade === 'C' ? 'text-yellow-400' : s.grade === 'F' ? 'text-red-400' : 'text-slate-500'}>
                                {s.grade}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* PENDING */}
      {view === 'pending' && (
        <div>
          {pendingSummary.tasks.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">🎉</p>
              <p className="text-white font-medium">All caught up!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingSummary.tasks.map((t: any) => (
                <div key={t.taskId} className="bg-slate-900 rounded-2xl border border-white/5 p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <p className="text-sm font-semibold text-white">{t.title}</p>
                      <p className="text-xs text-slate-500">{t.className} · Max: {t.maxMarks}M</p>
                      <div className="flex gap-3 mt-2">
                        <span className="text-xs text-green-400">✓ {t.submittedCount}/{t.totalStudents} submitted</span>
                        {t.notSubmittedCount > 0 && <span className="text-xs text-red-400">✗ {t.notSubmittedCount} pending</span>}
                        {t.graded > 0 && <span className="text-xs text-blue-400">📊 {t.graded} graded</span>}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {t.notSubmittedCount > 0 && (
                        <button onClick={() => sendBulkReminder(t)} disabled={sendingNotif === 'bulk_' + t.taskId}
                          className="text-xs px-3 py-1.5 bg-orange-500/10 text-orange-400 border border-orange-500/20 rounded-lg hover:bg-orange-500/20 flex items-center gap-1.5">
                          {sendingNotif === 'bulk_' + t.taskId ? '...' : '🔔 Remind All'}
                        </button>
                      )}
                      {t.pending > 0 && (
                        <button onClick={() => { const ft = tasks.find((x: any) => x.id === t.taskId); if (ft) selectTask(ft) }}
                          className="text-xs px-3 py-1.5 bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded-lg hover:bg-yellow-500/30">
                          {t.pending} to grade →
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Not submitted students */}
                  {t.notSubmitted?.length > 0 && (
                    <div className="bg-red-500/5 border border-red-500/10 rounded-xl p-3">
                      <p className="text-xs text-red-400 font-semibold mb-2">✗ Haven't submitted ({t.notSubmitted.length}):</p>
                      <div className="flex gap-2 flex-wrap">
                        {t.notSubmitted.map((s: any) => (
                          <div key={t.taskId + '_ns_' + s.id} className="flex items-center gap-1.5 bg-slate-800 rounded-lg px-2 py-1 border border-white/5">
                            <span className="text-xs text-slate-300">{s.name}</span>
                            <button onClick={() => sendReminder(t.taskId, s.id, s.name, t.title)}
                              disabled={sendingNotif === s.id}
                              className="text-[10px] text-orange-400 hover:text-orange-300 ml-1">
                              {sendingNotif === s.id ? '...' : '🔔'}
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* GRADE individual */}
      {view === 'grade' && selTask && (
        <div>
          <button onClick={() => { setView('pending'); setSubs([]); setTaskStatus(null) }}
            className="text-xs text-blue-400 mb-4 hover:text-blue-300 flex items-center gap-1">← Back</button>

          <div className="bg-slate-900 rounded-xl border border-white/5 p-4 mb-4">
            <p className="text-sm font-semibold text-white">{selTask.title}</p>
            {taskStatus && (
              <div className="flex gap-4 mt-2 flex-wrap">
                <span className="text-xs text-green-400">✓ {taskStatus.submittedCount} submitted</span>
                <span className="text-xs text-red-400">✗ {taskStatus.notSubmittedCount} not submitted</span>
                <span className="text-xs text-blue-400">📊 {subs.filter(s => s.marksAwarded !== null).length} graded</span>
              </div>
            )}
          </div>

          {taskStatus?.notSubmitted?.length > 0 && (
            <div className="mb-4 bg-red-500/5 border border-red-500/15 rounded-xl p-4">
              <p className="text-xs text-red-400 font-semibold mb-2">✗ Not submitted:</p>
              <div className="flex gap-2 flex-wrap">
                {taskStatus.notSubmitted.map((s: any) => (
                  <span key={'ns_' + s.id} className="text-xs text-slate-400 bg-slate-800 px-2 py-1 rounded-lg border border-white/5">{s.name}</span>
                ))}
              </div>
            </div>
          )}

          {subs.length === 0 ? (
            <div className="bg-slate-900 rounded-xl border border-white/5 p-8 text-center text-slate-400 text-sm">No submissions yet</div>
          ) : (
            <div className="space-y-3">
              {subs.map(sub => {
                const isEditing = editId === sub.id
                return (
                  <div key={'sub_' + sub.id} className={'bg-slate-900 rounded-xl border p-4 ' + (isEditing ? 'border-blue-500/30' : 'border-white/5')}>
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-semibold flex-shrink-0">
                        {sub.student.name.charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white">{sub.student.name}</p>
                        <p className="text-xs text-slate-500">
                          {sub.student.rollNumber ? 'Roll: ' + sub.student.rollNumber + ' · ' : ''}{sub.student.email}
                        </p>
                        <p className="text-xs text-slate-600 mt-0.5">
                          Submitted: {new Date(sub.submittedAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true })}
                        </p>
                        {sub.textAnswer && (
                          <div className="mt-2 p-2.5 bg-slate-800 rounded-lg border border-white/5 max-h-32 overflow-y-auto">
                            <p className="text-xs text-slate-300 leading-relaxed">{sub.textAnswer}</p>
                          </div>
                        )}
                        {sub.fileUrl && (
                          <a href={'http://localhost:5000' + sub.fileUrl} target="_blank"
                            className="mt-2 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300">
                            📎 {sub.fileName || 'View File'}
                          </a>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {sub.marksAwarded !== null && !isEditing && (
                          <div className="text-right">
                            <p className={'text-lg font-bold ' + gc(sub.marksAwarded, selTask.maxMarks)}>
                              {sub.marksAwarded}<span className="text-slate-500 text-sm">/{selTask.maxMarks}</span>
                            </p>
                            <p className="text-[10px] text-slate-500">{Math.round((sub.marksAwarded/selTask.maxMarks)*100)}%</p>
                          </div>
                        )}
                        {!isEditing && (
                          <button onClick={() => { setEditId(sub.id); setEditMarks(sub.marksAwarded?.toString() || ''); setEditFeedback(sub.feedback || '') }}
                            className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20">
                            {sub.marksAwarded !== null ? '✏ Edit' : '+ Grade'}
                          </button>
                        )}
                      </div>
                    </div>
                    {sub.feedback && !isEditing && (
                      <div className="mt-2 flex gap-2 p-2 bg-slate-800 rounded-lg">
                        <span className="text-purple-400 text-xs">💬</span>
                        <p className="text-xs text-slate-400">{sub.feedback}</p>
                      </div>
                    )}
                    {isEditing && (
                      <div className="mt-3 pt-3 border-t border-white/5 space-y-3">
                        <div className="flex gap-3 items-end">
                          <div>
                            <label className="block text-[10px] text-slate-500 uppercase mb-1">Marks / {selTask.maxMarks}</label>
                            <input type="number" value={editMarks} onChange={e => setEditMarks(e.target.value)}
                              min={0} max={selTask.maxMarks} autoFocus
                              className="w-24 bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500/50" />
                          </div>
                          <div className="flex-1">
                            <label className="block text-[10px] text-slate-500 uppercase mb-1">Feedback</label>
                            <input type="text" value={editFeedback} onChange={e => setEditFeedback(e.target.value)}
                              placeholder="Feedback for student..."
                              className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button onClick={() => saveGrade(sub)} disabled={!editMarks || saving}
                            className="px-4 py-2 bg-blue-500 text-white text-xs font-semibold rounded-lg disabled:opacity-40 flex items-center gap-1.5">
                            {saving ? <div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> : '✓'} Save & Notify
                          </button>
                          <button onClick={() => setEditId(null)} className="px-4 py-2 bg-slate-800 text-slate-400 text-xs rounded-lg border border-white/5">Cancel</button>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
""")
print("Teacher Results done!")

# ═══════════════════════════════════════════════════════
# FIX 3: Generate Questions - Add/Delete custom subjects
# ═══════════════════════════════════════════════════════
# Quick fix - add subject management to generate page
with open("../frontend/app/(dashboard)/teacher/generate/page.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Replace ALL_SUBJECTS with dynamic one + add management
new_subjects_block = """const DEFAULT_SUBJECTS = [
  'Data Structures and Algorithms', 'Operating Systems', 'Computer Networks',
  'Database Management Systems', 'Software Engineering', 'Artificial Intelligence',
  'Machine Learning', 'Web Technologies', 'Object Oriented Programming',
  'Discrete Mathematics', 'Computer Organization', 'Theory of Computation',
  'Compiler Design', 'Digital Electronics', 'Mathematics', 'Physics',
  'Chemistry', 'English', 'Management',
]"""

content = content.replace(
    "const ALL_SUBJECTS = [",
    "const DEFAULT_SUBJECTS_OLD = ["
)

# Write updated file with subject management
with open("../frontend/app/(dashboard)/teacher/generate/page.tsx", "r", encoding="utf-8") as f:
    gen_content = f.read()

# Just patch the subjects part - add custom subject support
if "customSubjects" not in gen_content:
    # Add state for custom subjects after const [step, setStep]
    gen_content = gen_content.replace(
        "const [step, setStep] = useState(1)",
        """const [step, setStep] = useState(1)
  const [customSubjects, setCustomSubjects] = useState<string[]>(() => {
    if (typeof window !== 'undefined') {
      try { return JSON.parse(localStorage.getItem('customSubjects') || '[]') } catch { return [] }
    }
    return []
  })
  const [newSubject, setNewSubject] = useState('')
  const [showAddSubject, setShowAddSubject] = useState(false)"""
    )

    # Add addSubject function after toggleUnit
    gen_content = gen_content.replace(
        "  const toggleUnit = (u: string) =>",
        """  const allSubjects = [...ALL_SUBJECTS, ...customSubjects]

  const addSubject = () => {
    const s = newSubject.trim()
    if (s && !allSubjects.includes(s)) {
      const updated = [...customSubjects, s]
      setCustomSubjects(updated)
      localStorage.setItem('customSubjects', JSON.stringify(updated))
      setSubject(s)
      setNewSubject('')
      setShowAddSubject(false)
    }
  }

  const removeCustomSubject = (s: string) => {
    const updated = customSubjects.filter(x => x !== s)
    setCustomSubjects(updated)
    localStorage.setItem('customSubjects', JSON.stringify(updated))
    if (subject === s) setSubject('')
  }

  const toggleUnit = (u: string) =>"""
    )

    # Replace ALL_SUBJECTS in the JSX grid with allSubjects
    gen_content = gen_content.replace(
        "{ALL_SUBJECTS.map(s => (",
        "{allSubjects.map(s => ("
    )

    # Add custom subject input after the grid
    gen_content = gen_content.replace(
        '<button onClick={() => setStep(2)} disabled={!subject} className="w-full py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600 disabled:opacity-40">',
        '''<div className="mb-4">
            {showAddSubject ? (
              <div className="flex gap-2">
                <input type="text" value={newSubject} onChange={e => setNewSubject(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addSubject()}
                  placeholder="Enter subject name..."
                  className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
                <button onClick={addSubject} disabled={!newSubject.trim()} className="px-4 py-2.5 bg-green-500 text-white text-sm rounded-xl disabled:opacity-40">Add</button>
                <button onClick={() => setShowAddSubject(false)} className="px-3 py-2.5 bg-slate-800 text-slate-400 text-sm rounded-xl border border-white/5">✕</button>
              </div>
            ) : (
              <button onClick={() => setShowAddSubject(true)} className="w-full py-2 text-sm text-blue-400 border border-dashed border-blue-500/30 rounded-xl hover:border-blue-500/60 hover:bg-blue-500/5 transition-all">
                + Add Custom Subject
              </button>
            )}
          </div>
          {customSubjects.length > 0 && (
            <div className="mb-4 flex gap-2 flex-wrap">
              {customSubjects.map(s => (
                <span key={s} className="flex items-center gap-1.5 text-xs bg-green-500/10 text-green-400 border border-green-500/20 px-2.5 py-1 rounded-full">
                  {s}
                  <button onClick={() => removeCustomSubject(s)} className="hover:text-red-400 ml-0.5">✕</button>
                </span>
              ))}
            </div>
          )}
          <button onClick={() => setStep(2)} disabled={!subject} className="w-full py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600 disabled:opacity-40">'''
    )

    with open("../frontend/app/(dashboard)/teacher/generate/page.tsx", "w", encoding="utf-8") as f:
        f.write(gen_content)
    print("Generate page: custom subjects added!")
else:
    print("Generate page: already has custom subjects")

# Fix Notification send for individual student
with open("src/routes/notification.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { getNotifications, markRead, markAllRead, deleteNotification, sendBulkNotification } from '../controllers/notification.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import prisma from '../config/db'

const router = Router()
router.get('/', authenticate, getNotifications)
router.patch('/read-all', authenticate, markAllRead)
router.patch('/:id/read', authenticate, markRead)
router.delete('/:id', authenticate, deleteNotification)
router.post('/send', authenticate, authorize('teacher', 'admin'), sendBulkNotification)

// Direct notification to specific user (for reminder)
router.post('/', authenticate, authorize('teacher', 'admin'), async (req: any, res: any) => {
  try {
    const { userId, title, body, type, refId } = req.body
    if (!userId || !title) return res.status(400).json({ success: false, message: 'userId and title required' })
    const notif = await prisma.notification.create({
      data: { userId, title, body: body || '', type: type || 'announcement', refId: refId || null }
    })
    return res.json({ success: true, data: notif })
  } catch (e: any) { return res.status(500).json({ success: false, message: e.message }) }
})

export default router
""")
print("Notification routes done!")

print("\n=== ALL DONE! ===")