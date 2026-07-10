import os

# ═══════════════════════════════════════════
# FIX 1: Student Layout - token wait karo
# ═══════════════════════════════════════════
with open("../frontend/app/(student)/layout.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter, usePathname } from 'next/navigation'
import StudentSidebar from '@/components/student/StudentSidebar'
import StudentNavbar from '@/components/student/StudentNavbar'

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const pathname = usePathname()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (status === 'loading') return
    if (!session) { router.push('/login'); return }
    if (session.user.role !== 'student') { router.push('/teacher'); return }
    if (pathname === '/student/select-class') { setReady(true); return }

    const classSelected = localStorage.getItem('studentClassSelected')
    if (!classSelected) {
      router.push('/student/select-class')
      return
    }
    setReady(true)
  }, [session, status, pathname])

  if (!ready || status === 'loading') return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Loading your dashboard...</p>
      </div>
    </div>
  )

  if (pathname === '/student/select-class') return <>{children}</>

  return (
    <div className="flex min-h-screen bg-slate-950">
      <StudentSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <StudentNavbar />
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  )
}
""")
print("Student layout done!")

# ═══════════════════════════════════════════
# FIX 2: Student Select Class Page - Better UX
# ═══════════════════════════════════════════
os.makedirs("../frontend/app/(student)/student/select-class", exist_ok=True)
with open("../frontend/app/(student)/student/select-class/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type ClassSection = {
  id: string
  name: string
  section: string
  branch: string
  semester: number
  year: number
  uniqueCode: string
  _count: { students: number }
}

export default function SelectClassPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState<'code' | 'browse'>('code')
  const [codeInput, setCodeInput] = useState('')
  const [joining, setJoining] = useState(false)
  const [error, setError] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  // Browse mode filters
  const [selectedBranch, setSelectedBranch] = useState('')
  const [selectedSem, setSelectedSem] = useState('')
  const [selectedClass, setSelectedClass] = useState('')

  const token = session?.user?.backendToken

  useEffect(() => {
    if (status === 'loading') return
    if (!token) return
    fetch(API + '/auth/classes', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(data => { if (data.success) setClasses(data.data); setLoading(false) })
  }, [token, status])

  const branches = Array.from(new Set(classes.map(c => c.branch))).sort()
  const semesters = Array.from(new Set(
    classes.filter(c => !selectedBranch || c.branch === selectedBranch).map(c => c.semester.toString())
  )).sort()
  const filteredClasses = classes.filter(c =>
    (!selectedBranch || c.branch === selectedBranch) &&
    (!selectedSem || c.semester.toString() === selectedSem)
  )

  const joinByCode = async () => {
    if (!codeInput.trim() || !token) return
    setJoining(true); setError('')
    try {
      const res = await fetch(API + '/auth/join-class', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: codeInput.toUpperCase().trim() })
      })
      const data = await res.json()
      if (data.success) {
        setSuccessMsg('Joined ' + data.data.class.name + ' Section ' + data.data.class.section + ' successfully!')
        localStorage.setItem('studentClassSelected', 'true')
        setTimeout(() => router.push('/student'), 1500)
      } else {
        setError(data.message || 'Invalid code. Check with your teacher.')
      }
    } catch { setError('Connection error. Please try again.') }
    setJoining(false)
  }

  const joinBySelect = async () => {
    if (!selectedClass || !token) return
    setJoining(true); setError('')
    try {
      const res = await fetch(API + '/auth/select-class', {
        method: 'PATCH',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ classSectionId: selectedClass })
      })
      const data = await res.json()
      if (data.success) {
        localStorage.setItem('studentClassSelected', 'true')
        router.push('/student')
      } else { setError(data.message || 'Failed') }
    } catch { setError('Connection error') }
    setJoining(false)
  }

  const skipAndContinue = () => {
    localStorage.setItem('studentClassSelected', 'true')
    router.push('/student')
  }

  if (status === 'loading' || (loading && token)) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-green-500/20 to-blue-500/20 border border-green-500/30 flex items-center justify-center text-4xl mx-auto mb-4 shadow-xl shadow-green-500/10">
            🎓
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Join Your Class</h1>
          <p className="text-slate-400 text-sm">Connect with your class to see assignments, notes and materials</p>
          {session?.user?.name && (
            <p className="text-green-400 text-xs mt-2">Welcome, {session.user.name.split(' ')[0]}!</p>
          )}
        </div>

        {/* Mode toggle */}
        <div className="flex gap-1 bg-slate-900 border border-white/10 rounded-2xl p-1.5 mb-6">
          <button
            onClick={() => { setMode('code'); setError('') }}
            className={'flex-1 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2 ' + (mode === 'code' ? 'bg-green-500 text-white shadow-lg shadow-green-500/25' : 'text-slate-400 hover:text-white')}
          >
            🔑 Enter Class Code
          </button>
          <button
            onClick={() => { setMode('browse'); setError('') }}
            className={'flex-1 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2 ' + (mode === 'browse' ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/25' : 'text-slate-400 hover:text-white')}
          >
            📋 Browse & Select
          </button>
        </div>

        {/* Enter Code Mode */}
        {mode === 'code' && (
          <div className="bg-slate-900/80 backdrop-blur rounded-2xl border border-white/10 p-6 shadow-xl">
            <label className="block text-xs text-slate-500 uppercase tracking-widest mb-3">Class Code from Teacher</label>
            <input
              type="text"
              value={codeInput}
              onChange={e => { setCodeInput(e.target.value.toUpperCase()); setError('') }}
              onKeyDown={e => e.key === 'Enter' && joinByCode()}
              placeholder="e.g. CSE1A-B3F2"
              maxLength={12}
              className="w-full bg-slate-800 border border-white/10 rounded-xl px-5 py-4 text-xl font-mono font-bold text-white text-center tracking-widest outline-none focus:border-green-500/60 focus:bg-slate-800/80 transition-all placeholder:text-slate-700 placeholder:text-sm placeholder:font-normal mb-4"
            />
            {error && (
              <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2.5 mb-4">
                <span className="text-red-400">⚠️</span>
                <p className="text-xs text-red-400">{error}</p>
              </div>
            )}
            {successMsg && (
              <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-xl px-4 py-2.5 mb-4">
                <span className="text-green-400">✓</span>
                <p className="text-xs text-green-400">{successMsg}</p>
              </div>
            )}
            <button
              onClick={joinByCode}
              disabled={codeInput.length < 5 || joining}
              className="w-full py-3.5 bg-green-500 text-white text-sm font-semibold rounded-xl hover:bg-green-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-green-500/20 flex items-center justify-center gap-2 mb-3"
            >
              {joining ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Joining class...</> : '🚀 Join Class'}
            </button>
            <p className="text-center text-xs text-slate-600">Ask your teacher for the unique class code</p>
          </div>
        )}

        {/* Browse Mode */}
        {mode === 'browse' && (
          <div className="bg-slate-900/80 backdrop-blur rounded-2xl border border-white/10 p-6 shadow-xl">
            {loading ? (
              <div className="text-center py-8">
                <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                <p className="text-slate-400 text-sm">Loading classes...</p>
              </div>
            ) : classes.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-3">⏳</p>
                <p className="text-white font-medium mb-1">No classes available yet</p>
                <p className="text-slate-400 text-sm mb-4">Your teacher hasn't created any classes. Ask them for the class code.</p>
                <button onClick={() => setMode('code')} className="px-4 py-2 bg-green-500 text-white text-sm rounded-xl hover:bg-green-600">Use Class Code Instead</button>
              </div>
            ) : (
              <>
                {/* Step 1: Branch */}
                <div className="mb-5">
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">1. Select Branch</label>
                  <div className="grid grid-cols-3 gap-2">
                    {branches.map(b => (
                      <button key={b} onClick={() => { setSelectedBranch(b); setSelectedSem(''); setSelectedClass('') }} className={'py-2.5 rounded-xl text-sm font-medium border transition-all ' + (selectedBranch === b ? 'bg-blue-500 text-white border-blue-500 shadow-lg shadow-blue-500/20' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/20 hover:text-white')}>
                        {b}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Step 2: Semester */}
                {selectedBranch && (
                  <div className="mb-5">
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">2. Select Semester</label>
                    <div className="grid grid-cols-4 gap-2">
                      {semesters.map(s => (
                        <button key={s} onClick={() => { setSelectedSem(s); setSelectedClass('') }} className={'py-2.5 rounded-xl text-sm font-medium border transition-all ' + (selectedSem === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/20 hover:text-white')}>
                          Sem {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Step 3: Class + Section */}
                {selectedSem && (
                  <div className="mb-5">
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">3. Select Class & Section</label>
                    <div className="space-y-2">
                      {filteredClasses.map(c => (
                        <button key={c.id} onClick={() => setSelectedClass(c.id)} className={'w-full p-4 rounded-xl border text-left transition-all ' + (selectedClass === c.id ? 'border-green-500/60 bg-green-500/10 shadow-lg shadow-green-500/10' : 'border-white/5 bg-slate-800 hover:border-white/20')}>
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-semibold text-white">{c.name} — Section {c.section}</p>
                              <p className="text-xs text-slate-500 mt-0.5">{c.branch} · Semester {c.semester} · {c.year} · {c._count.students} students</p>
                            </div>
                            <div className="flex flex-col items-end gap-1">
                              <span className="text-xs font-mono text-green-400 bg-green-500/10 px-2 py-1 rounded-lg border border-green-500/20">{c.uniqueCode}</span>
                              {selectedClass === c.id && <span className="text-[10px] text-green-400">✓ Selected</span>}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {error && (
                  <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2.5 mb-4">
                    <p className="text-xs text-red-400">{error}</p>
                  </div>
                )}

                {selectedClass && (
                  <button onClick={joinBySelect} disabled={joining} className="w-full py-3.5 bg-green-500 text-white text-sm font-semibold rounded-xl hover:bg-green-600 disabled:opacity-40 transition-all shadow-lg shadow-green-500/20 flex items-center justify-center gap-2 mb-3">
                    {joining ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Joining...</> : '✓ Join This Class'}
                  </button>
                )}
              </>
            )}
          </div>
        )}

        {/* Skip button */}
        <div className="text-center mt-4">
          <button onClick={skipAndContinue} className="text-slate-600 hover:text-slate-400 text-xs transition-colors">
            Skip for now — I'll join later
          </button>
        </div>
      </div>
    </div>
  )
}
""")
print("Select class page done!")

# ═══════════════════════════════════════════
# FIX 3: Student Assignments - fetch properly
# ═══════════════════════════════════════════
os.makedirs("../frontend/app/(student)/student/assignments", exist_ok=True)
with open("../frontend/app/(student)/student/assignments/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect, useCallback } from 'react'
import { useSession } from 'next-auth/react'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type Task = {
  id: string
  title: string
  subjectName?: string | null
  taskType: string
  deadline?: string | null
  maxMarks: number
  instructions?: string | null
  attachmentUrl?: string | null
  status: string
  creator: { name: string }
  classSection?: { name: string; section: string } | null
  _count: { submissions: number }
}

type Submission = {
  id: string
  taskId: string
  status: string
  marksAwarded?: number | null
  feedback?: string | null
  submittedAt: string
  task: { title: string; maxMarks: number }
}

const typeConfig: Record<string, { label: string; icon: string; color: string }> = {
  assignment: { label: 'Assignment', icon: '📝', color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
  class_test: { label: 'Class Test', icon: '✍️', color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
  quiz: { label: 'Quiz', icon: '❓', color: 'text-green-400 bg-green-500/10 border-green-500/20' },
  project: { label: 'Project', icon: '🔬', color: 'text-orange-400 bg-orange-500/10 border-orange-500/20' },
}

export default function StudentAssignmentsPage() {
  const { data: session, status } = useSession()
  const [tasks, setTasks] = useState<Task[]>([])
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [showSubmit, setShowSubmit] = useState(false)
  const [submitText, setSubmitText] = useState('')
  const [submitFile, setSubmitFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [submitSuccess, setSubmitSuccess] = useState('')

  const token = session?.user?.backendToken

  const fetchData = useCallback(async () => {
    if (!token) return
    setLoading(true)
    try {
      const [tasksRes, subsRes] = await Promise.all([
        fetch(API + '/tasks', { headers: { Authorization: 'Bearer ' + token } }),
        fetch(API + '/submissions', { headers: { Authorization: 'Bearer ' + token } }),
      ])
      const [tasksData, subsData] = await Promise.all([tasksRes.json(), subsRes.json()])
      if (tasksData.success) setTasks(tasksData.data)
      if (subsData.success) setSubmissions(subsData.data)
    } catch (e) { console.error('Fetch error:', e) }
    setLoading(false)
  }, [token])

  useEffect(() => {
    if (status !== 'loading' && token) fetchData()
  }, [token, status, fetchData])

  const getSubmission = (taskId: string) => submissions.find(s => s.taskId === taskId)

  const getDaysLeft = (deadline?: string | null) => {
    if (!deadline) return { label: 'No deadline', color: 'text-slate-400' }
    const diff = new Date(deadline).getTime() - Date.now()
    const days = Math.ceil(diff / 86400000)
    if (diff < 0) return { label: 'Overdue!', color: 'text-red-400' }
    if (days === 0) return { label: 'Due Today!', color: 'text-red-400' }
    if (days === 1) return { label: '1 day left', color: 'text-yellow-400' }
    return { label: days + ' days left', color: 'text-green-400' }
  }

  const formatDate = (dt?: string | null) => dt
    ? new Date(dt).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true })
    : 'No deadline'

  const filtered = tasks.filter(t => {
    if (filter === 'pending') return !getSubmission(t.id)
    if (filter === 'submitted') return !!getSubmission(t.id) && getSubmission(t.id)?.status !== 'graded'
    if (filter === 'graded') return getSubmission(t.id)?.status === 'graded'
    return true
  })

  const handleSubmit = async () => {
    if (!selectedTask || !token) return
    if (!submitText.trim() && !submitFile) { setSubmitError('Please write an answer or attach a file'); return }
    setSubmitting(true); setSubmitError(''); setSubmitSuccess('')
    try {
      const fd = new FormData()
      fd.append('taskId', selectedTask.id)
      if (submitText.trim()) fd.append('textAnswer', submitText)
      if (submitFile) fd.append('file', submitFile)

      const res = await fetch(API + '/submissions', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token },
        body: fd
      })
      const data = await res.json()
      if (data.success) {
        setSubmitSuccess('Submitted successfully!')
        await fetchData()
        setTimeout(() => { setShowSubmit(false); setSubmitText(''); setSubmitFile(null); setSelectedTask(null); setSubmitSuccess('') }, 1500)
      } else {
        setSubmitError(data.message || 'Submission failed')
      }
    } catch { setSubmitError('Connection error. Please try again.') }
    setSubmitting(false)
  }

  const pendingCount = tasks.filter(t => !getSubmission(t.id)).length
  const submittedCount = tasks.filter(t => !!getSubmission(t.id)).length

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">Assignments & Tasks</h1>
        <p className="text-slate-400 text-sm">Submit your assignments, tests and quizzes</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { l: 'Total Tasks', v: tasks.length, c: 'text-white' },
          { l: 'Pending', v: pendingCount, c: 'text-yellow-400' },
          { l: 'Submitted', v: submittedCount, c: 'text-green-400' },
        ].map(s => (
          <div key={s.l} className="bg-slate-900 rounded-xl border border-white/5 p-4 text-center">
            <p className={'text-2xl font-bold ' + s.c}>{s.v}</p>
            <p className="text-xs text-slate-500 mt-1">{s.l}</p>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { k: 'all', l: 'All Tasks', count: tasks.length },
          { k: 'pending', l: 'Pending', count: pendingCount },
          { k: 'submitted', l: 'Submitted', count: submittedCount },
          { k: 'graded', l: 'Graded', count: submissions.filter(s => s.status === 'graded').length },
        ].map(tab => (
          <button key={tab.k} onClick={() => setFilter(tab.k)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filter === tab.k ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>
            {tab.l} <span className="ml-1 opacity-60">{tab.count}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-16">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Loading your tasks...</p>
        </div>
      ) : tasks.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">📋</p>
          <p className="text-white font-medium mb-1">No tasks assigned yet</p>
          <p className="text-slate-500 text-sm">Your teacher hasn't assigned any tasks yet. Check back later!</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">✅</p>
          <p className="text-white font-medium mb-1">All done!</p>
          <p className="text-slate-500 text-sm">No tasks in this category</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map(task => {
            const tc = typeConfig[task.taskType] || typeConfig.assignment
            const dl = getDaysLeft(task.deadline)
            const sub = getSubmission(task.id)
            const isGraded = sub?.status === 'graded'

            return (
              <div key={task.id} className={'bg-slate-900 rounded-2xl border transition-all p-5 ' + (sub ? 'border-green-500/20' : 'border-white/5 hover:border-white/10')}>
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-2xl flex-shrink-0">
                    {tc.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex gap-2 mb-1.5 flex-wrap items-center">
                      <span className={'text-[10px] px-2 py-0.5 rounded border font-medium ' + tc.color}>{tc.label}</span>
                      {sub ? (
                        <span className={`text-[10px] px-2 py-0.5 rounded border font-medium ${isGraded ? 'text-purple-400 bg-purple-500/10 border-purple-500/20' : 'text-green-400 bg-green-500/10 border-green-500/20'}`}>
                          {isGraded ? '📊 Graded' : '✓ Submitted'}
                        </span>
                      ) : (
                        <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-yellow-400 bg-yellow-500/10 border-yellow-500/20">Pending</span>
                      )}
                      {task.classSection && (
                        <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-slate-400 bg-slate-700 border-white/10">
                          {task.classSection.name} {task.classSection.section}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-semibold text-white mb-0.5">{task.title}</p>
                    <p className="text-xs text-slate-500">{task.subjectName || 'General'} · By {task.creator.name} · {task.maxMarks} marks</p>
                  </div>
                  {isGraded && sub?.marksAwarded !== null && (
                    <div className="text-right flex-shrink-0">
                      <p className="text-2xl font-bold text-green-400">{sub?.marksAwarded}</p>
                      <p className="text-xs text-slate-500">out of {task.maxMarks}</p>
                    </div>
                  )}
                </div>

                {/* Details */}
                <div className="mt-4 bg-slate-800 rounded-xl p-3 border border-white/5 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider">Deadline</span>
                    <span className="text-xs text-slate-300">{formatDate(task.deadline)}</span>
                  </div>
                  <div className="h-px bg-white/5" />
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider">Time Left</span>
                    <span className={'text-xs font-medium ' + (sub ? 'text-green-400' : dl.color)}>
                      {sub ? 'Submitted ' + new Date(sub.submittedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : dl.label}
                    </span>
                  </div>
                  {task.instructions && (
                    <>
                      <div className="h-px bg-white/5" />
                      <p className="text-xs text-slate-400 leading-relaxed">{task.instructions}</p>
                    </>
                  )}
                  {task.attachmentUrl && (
                    <>
                      <div className="h-px bg-white/5" />
                      <a href={'http://localhost:5000' + task.attachmentUrl} target="_blank" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                        📎 View attached file
                      </a>
                    </>
                  )}
                  {sub?.feedback && (
                    <>
                      <div className="h-px bg-white/5" />
                      <div className="flex gap-2">
                        <span className="text-xs text-purple-400 flex-shrink-0">💬 Feedback:</span>
                        <p className="text-xs text-slate-400">{sub.feedback}</p>
                      </div>
                    </>
                  )}
                </div>

                {/* Action */}
                <div className="mt-4">
                  {!sub ? (
                    <button
                      onClick={() => { setSelectedTask(task); setShowSubmit(true); setSubmitError(''); setSubmitSuccess('') }}
                      className="w-full py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600 transition-all shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2"
                    >
                      📤 Submit Now
                    </button>
                  ) : isGraded ? (
                    <div className="w-full py-3 bg-purple-500/10 text-purple-400 border border-purple-500/20 text-sm font-medium rounded-xl text-center">
                      📊 Graded — {sub.marksAwarded}/{task.maxMarks} marks
                    </div>
                  ) : (
                    <div className="w-full py-3 bg-green-500/10 text-green-400 border border-green-500/20 text-sm font-medium rounded-xl text-center">
                      ✓ Submitted — Awaiting grade
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Submit Modal */}
      {showSubmit && selectedTask && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <div>
                <p className="text-sm font-semibold text-white">Submit Assignment</p>
                <p className="text-xs text-slate-500 mt-0.5">{selectedTask.title}</p>
              </div>
              <button onClick={() => { setShowSubmit(false); setSubmitText(''); setSubmitFile(null) }} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 transition-all">✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-3 gap-3 bg-slate-800 rounded-xl p-3 border border-white/5">
                <div className="text-center">
                  <p className="text-xs font-semibold text-white">{selectedTask.subjectName || 'General'}</p>
                  <p className="text-[10px] text-slate-500">Subject</p>
                </div>
                <div className="text-center">
                  <p className="text-xs font-semibold text-white">{selectedTask.maxMarks}</p>
                  <p className="text-[10px] text-slate-500">Marks</p>
                </div>
                <div className="text-center">
                  <p className="text-xs font-semibold text-white">{selectedTask.deadline ? new Date(selectedTask.deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : 'No limit'}</p>
                  <p className="text-[10px] text-slate-500">Deadline</p>
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Your Answer</label>
                <textarea
                  value={submitText}
                  onChange={e => setSubmitText(e.target.value)}
                  placeholder="Write your answer here..."
                  rows={5}
                  className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 resize-none"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Attach File (Optional)</label>
                <div
                  onClick={() => document.getElementById('sub-file')?.click()}
                  className={'border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ' + (submitFile ? 'border-green-500/50 bg-green-500/5' : 'border-white/10 hover:border-white/20 hover:bg-white/2')}
                >
                  <input id="sub-file" type="file" className="hidden" accept=".pdf,.doc,.docx,.jpg,.png,.zip" onChange={e => setSubmitFile(e.target.files?.[0] || null)} />
                  {submitFile ? (
                    <div>
                      <p className="text-green-400 text-2xl mb-1">✓</p>
                      <p className="text-sm font-medium text-white">{submitFile.name}</p>
                      <p className="text-xs text-slate-500">{(submitFile.size/1024/1024).toFixed(1)} MB</p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-3xl mb-1">📎</p>
                      <p className="text-sm text-slate-400">Click to attach file</p>
                      <p className="text-xs text-slate-600 mt-1">PDF, DOC, Image, ZIP supported</p>
                    </div>
                  )}
                </div>
                {submitFile && (
                  <button onClick={() => setSubmitFile(null)} className="text-xs text-red-400 mt-1.5 hover:text-red-300">Remove file</button>
                )}
              </div>

              {submitError && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                  <p className="text-xs text-red-400">⚠️ {submitError}</p>
                </div>
              )}
              {submitSuccess && (
                <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3">
                  <p className="text-xs text-green-400">✓ {submitSuccess}</p>
                </div>
              )}

              <button
                onClick={handleSubmit}
                disabled={submitting || !!submitSuccess}
                className={'w-full py-3.5 text-white text-sm font-semibold rounded-xl transition-all flex items-center justify-center gap-2 ' + (submitSuccess ? 'bg-green-500' : 'bg-blue-500 hover:bg-blue-600 disabled:opacity-40 shadow-lg shadow-blue-500/20')}
              >
                {submitting ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Submitting...</>
                  : submitSuccess ? '✓ Submitted!'
                  : '📤 Submit Assignment'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Student assignments done!")

# ═══════════════════════════════════════════
# FIX 4: AI Chatbot with REAL Claude API
# ═══════════════════════════════════════════
os.makedirs("../frontend/app/(student)/student/chatbot", exist_ok=True)
with open("../frontend/app/(student)/student/chatbot/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useRef, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type Message = { id: number; role: 'user' | 'assistant'; content: string; time: string }

const SUBJECTS = [
  { name: 'Data Structures and Algorithms', icon: '🌳' },
  { name: 'Operating Systems', icon: '💻' },
  { name: 'Computer Networks', icon: '🌐' },
  { name: 'Database Management Systems', icon: '🗄️' },
  { name: 'Software Engineering', icon: '⚙️' },
  { name: 'Artificial Intelligence', icon: '🤖' },
  { name: 'Machine Learning', icon: '📊' },
  { name: 'Web Technologies', icon: '🌍' },
  { name: 'Object Oriented Programming', icon: '📦' },
  { name: 'Discrete Mathematics', icon: '📐' },
]

const QUICK_PROMPTS = [
  'Explain this concept with a simple example',
  'What are the key exam topics?',
  'Give me 5 practice questions',
  'Explain the difference between...',
  'Write pseudocode for...',
  'What are common mistakes to avoid?',
]

export default function AIChatbotPage() {
  const { data: session } = useSession()
  const [subject, setSubject] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<{role: string; content: string}[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const token = session?.user?.backendToken

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const startSubject = (s: string) => {
    setSubject(s)
    const welcome = `Hello! I'm your AI study assistant powered by **Claude**, the most advanced AI by Anthropic. I'm here to help you master **${s}**. I can:

- 📚 Explain concepts clearly with examples
- ✍️ Generate practice questions from your syllabus
- 🎯 Help you prepare for exams
- 🔍 Clarify doubts instantly
- 📝 Review your answers

What would you like to learn today?`

    const msg: Message = { id: 1, role: 'assistant', content: welcome, time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }) }
    setMessages([msg])
    setHistory([{ role: 'assistant', content: welcome }])
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  const sendMessage = async (messageText?: string) => {
    const text = messageText || input.trim()
    if (!text || !subject || loading || !token) return

    const userMsg: Message = {
      id: Date.now(), role: 'user', content: text,
      time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    }
    const newHistory = [...history, { role: 'user', content: text }]
    setMessages(prev => [...prev, userMsg])
    setHistory(newHistory)
    if (!messageText) setInput('')
    setLoading(true)

    try {
      const res = await fetch(API + '/ai/chat', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, subject, history: history.slice(-8) })
      })
      const data = await res.json()
      const reply = data.success ? data.data.reply : '❌ Sorry, I could not connect to the AI. Please check if the backend is running and API key is configured.'
      const botMsg: Message = {
        id: Date.now() + 1, role: 'assistant', content: reply,
        time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
      }
      setMessages(prev => [...prev, botMsg])
      setHistory([...newHistory, { role: 'assistant', content: reply }])
    } catch {
      const errMsg: Message = { id: Date.now() + 1, role: 'assistant', content: '❌ Connection error. Please make sure the backend server is running.', time: 'Now' }
      setMessages(prev => [...prev, errMsg])
    }
    setLoading(false)
  }

  const formatContent = (text: string) => {
    return text
      .replace(/\\*\\*(.+?)\\*\\*/g, '<strong class="text-white">$1</strong>')
      .replace(/`(.+?)`/g, '<code class="bg-slate-700 px-1.5 py-0.5 rounded text-green-400 text-xs font-mono">$1</code>')
      .replace(/^• (.+)$/gm, '<div class="flex gap-2 mt-1"><span class="text-blue-400 flex-shrink-0">•</span><span>$1</span></div>')
      .replace(/\\n/g, '<br/>')
  }

  return (
    <div className="max-w-4xl mx-auto flex flex-col" style={{ height: 'calc(100vh - 120px)' }}>
      {/* Header */}
      <div className="mb-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xl shadow-lg shadow-blue-500/20">🤖</div>
          <div>
            <h1 className="text-xl font-bold text-white">AI Study Assistant</h1>
            <p className="text-slate-400 text-xs">Powered by Claude AI — Ask anything, get instant help</p>
          </div>
          {subject && (
            <div className="ml-auto flex items-center gap-2">
              <span className="text-xs text-blue-400 bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded-full">{subject.length > 25 ? subject.slice(0,25)+'...' : subject}</span>
              <button onClick={() => { setSubject(''); setMessages([]); setHistory([]) }} className="text-xs text-slate-500 hover:text-slate-300 px-2 py-1 bg-slate-800 rounded-lg border border-white/5 hover:border-white/10 transition-all">Change</button>
            </div>
          )}
        </div>
      </div>

      {!subject ? (
        /* Subject selection */
        <div className="flex-1 overflow-y-auto">
          <div className="text-center mb-8 py-6">
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 flex items-center justify-center text-4xl mx-auto mb-4 shadow-xl shadow-blue-500/10">🤖</div>
            <h2 className="text-lg font-bold text-white mb-2">Select a Subject to Start</h2>
            <p className="text-slate-400 text-sm">Claude AI will answer your questions with deep expertise</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {SUBJECTS.map(s => (
              <button
                key={s.name}
                onClick={() => startSubject(s.name)}
                className="p-4 bg-slate-900 rounded-2xl border border-white/5 hover:border-blue-500/30 hover:bg-blue-500/5 transition-all text-left group shadow-lg hover:shadow-blue-500/5"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl group-hover:scale-110 transition-transform">{s.icon}</span>
                  <div>
                    <p className="text-sm font-medium text-white leading-snug">{s.name}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* Chat interface */
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto bg-slate-900/50 rounded-2xl border border-white/5 p-4 mb-4 space-y-4">
            {messages.map(msg => (
              <div key={msg.id} className={'flex ' + (msg.role === 'user' ? 'justify-end' : 'justify-start')}>
                <div className={'max-w-[85%] ' + (msg.role === 'user' ? 'items-end' : 'items-start') + ' flex flex-col gap-1'}>
                  {msg.role === 'assistant' && (
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs">🤖</div>
                      <span className="text-[10px] text-slate-500 font-medium">Claude AI</span>
                    </div>
                  )}
                  <div
                    className={'px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-lg ' + (msg.role === 'user' ? 'bg-blue-500 text-white rounded-br-sm shadow-blue-500/20' : 'bg-slate-800 text-slate-200 border border-white/5 rounded-bl-sm')}
                    dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }}
                  />
                  <p className="text-[10px] text-slate-600 px-1">{msg.time}</p>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs">🤖</div>
                </div>
                <div className="bg-slate-800 border border-white/5 rounded-2xl rounded-bl-sm px-4 py-3 ml-2 flex items-center gap-1">
                  <span className="text-xs text-slate-500 mr-2">Claude is thinking</span>
                  {[0, 1, 2].map(i => (
                    <div key={i} className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: i * 150 + 'ms' }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick prompts - show at start */}
          {messages.length <= 1 && (
            <div className="flex gap-2 flex-wrap mb-3 flex-shrink-0">
              {QUICK_PROMPTS.slice(0, 4).map(p => (
                <button key={p} onClick={() => sendMessage(p)} className="text-xs px-3 py-1.5 bg-slate-900 text-slate-400 border border-white/5 rounded-full hover:border-blue-500/30 hover:text-blue-400 transition-all">
                  {p}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="flex gap-2 flex-shrink-0">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
              placeholder={'Ask anything about ' + (subject.length > 30 ? subject.slice(0,30)+'...' : subject) + '...'}
              disabled={loading}
              className="flex-1 bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 disabled:opacity-50 transition-all"
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="px-5 py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20"
            >
              Send
            </button>
          </div>
          <p className="text-[10px] text-slate-600 text-center mt-2">Powered by Claude AI — Anthropic's most capable model</p>
        </>
      )}
    </div>
  )
}
""")
print("AI Chatbot done!")

# ═══════════════════════════════════════════
# FIX 5: Student Results page
# ═══════════════════════════════════════════
os.makedirs("../frontend/app/(student)/student/results", exist_ok=True)
with open("../frontend/app/(student)/student/results/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type Submission = {
  id: string
  taskId: string
  status: string
  marksAwarded?: number | null
  feedback?: string | null
  submittedAt: string
  task: { title: string; maxMarks: number; taskType: string; subjectName?: string | null }
}

export default function StudentResultsPage() {
  const { data: session } = useSession()
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    fetch(API + '/submissions', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(data => { if (data.success) setSubmissions(data.data); setLoading(false) })
  }, [token])

  const graded = submissions.filter(s => s.status === 'graded' && s.marksAwarded !== null)
  const pending = submissions.filter(s => s.status !== 'graded')
  const totalMarks = graded.reduce((s, r) => s + (r.marksAwarded || 0), 0)
  const totalMax = graded.reduce((s, r) => s + r.task.maxMarks, 0)
  const avg = totalMax > 0 ? Math.round((totalMarks / totalMax) * 100) : 0

  const getGrade = (m: number, max: number) => {
    const p = (m/max)*100
    return p >= 80 ? { grade: 'A', color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' }
      : p >= 60 ? { grade: 'B', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' }
      : p >= 40 ? { grade: 'C', color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' }
      : { grade: 'F', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' }
  }

  const typeIcon: Record<string, string> = { assignment: '📝', class_test: '✍️', quiz: '❓', project: '🔬' }

  const filtered = filter === 'graded' ? graded : filter === 'pending' ? pending : submissions

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">My Results</h1>
        <p className="text-slate-400 text-sm">View your marks and teacher feedback</p>
      </div>

      {/* Overall stats */}
      {graded.length > 0 && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[
            { l: 'Total Graded', v: graded.length, c: 'text-white' },
            { l: 'Overall %', v: avg + '%', c: avg >= 80 ? 'text-green-400' : avg >= 60 ? 'text-blue-400' : 'text-yellow-400' },
            { l: 'Overall Grade', v: avg >= 80 ? 'A' : avg >= 60 ? 'B' : avg >= 40 ? 'C' : 'F', c: avg >= 80 ? 'text-green-400' : avg >= 60 ? 'text-blue-400' : 'text-yellow-400' },
            { l: 'Pending', v: pending.length, c: 'text-yellow-400' },
          ].map(s => (
            <div key={s.l} className="bg-slate-900 rounded-2xl border border-white/5 p-4 text-center">
              <p className={'text-2xl font-bold ' + s.c}>{s.v}</p>
              <p className="text-xs text-slate-500 mt-1">{s.l}</p>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2 mb-6">
        {[
          { k: 'all', l: 'All', count: submissions.length },
          { k: 'graded', l: 'Graded', count: graded.length },
          { k: 'pending', l: 'Pending', count: pending.length },
        ].map(tab => (
          <button key={tab.k} onClick={() => setFilter(tab.k)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filter === tab.k ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>
            {tab.l} <span className="ml-1 opacity-60">{tab.count}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-16"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">📊</p>
          <p className="text-white font-medium mb-1">No results yet</p>
          <p className="text-slate-500 text-sm">Submit assignments to see your results here</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map(sub => {
            const isGraded = sub.status === 'graded' && sub.marksAwarded !== null
            const g = isGraded ? getGrade(sub.marksAwarded!, sub.task.maxMarks) : null

            return (
              <div key={sub.id} className={'bg-slate-900 rounded-2xl border transition-all p-5 ' + (isGraded ? 'border-white/10 hover:border-white/15' : 'border-white/5')}>
                <div className="flex items-start gap-4">
                  {isGraded && g ? (
                    <div className={'w-14 h-14 rounded-2xl border flex items-center justify-center flex-shrink-0 ' + g.bg}>
                      <span className={'text-2xl font-bold ' + g.color}>{g.grade}</span>
                    </div>
                  ) : (
                    <div className="w-14 h-14 rounded-2xl border border-white/5 bg-slate-800 flex items-center justify-center flex-shrink-0 text-2xl">
                      {typeIcon[sub.task.taskType] || '📝'}
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-white mb-0.5">{sub.task.title}</p>
                    <p className="text-xs text-slate-500">{sub.task.subjectName || 'General'} · Submitted {new Date(sub.submittedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                    {isGraded && (
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                          <span>Score</span>
                          <span>{sub.marksAwarded}/{sub.task.maxMarks} · {Math.round((sub.marksAwarded!/sub.task.maxMarks)*100)}%</span>
                        </div>
                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={'h-full rounded-full transition-all ' + (g?.color.replace('text-', 'bg-'))}
                            style={{ width: Math.round((sub.marksAwarded!/sub.task.maxMarks)*100) + '%' }}
                          />
                        </div>
                      </div>
                    )}
                    {sub.feedback && (
                      <div className="mt-3 flex gap-2 p-3 bg-slate-800 rounded-xl border border-white/5">
                        <span className="text-purple-400 flex-shrink-0">💬</span>
                        <p className="text-xs text-slate-400 leading-relaxed">{sub.feedback}</p>
                      </div>
                    )}
                  </div>
                  <div className="flex-shrink-0 text-right">
                    {isGraded ? (
                      <>
                        <p className={'text-2xl font-bold ' + g?.color}>{sub.marksAwarded}<span className="text-sm text-slate-500">/{sub.task.maxMarks}</span></p>
                      </>
                    ) : (
                      <span className="text-xs text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 px-2.5 py-1 rounded-lg">Awaiting</span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
""")
print("Student Results done!")

print("\n" + "="*50)
print("ALL FIXES DONE!")
print("="*50)