import os

# Fix Teacher Tasks page - backend se connect
os.makedirs("../frontend/app/(dashboard)/teacher/tasks", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/tasks/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

type Task = {
  id: string
  title: string
  subject?: { name: string; code: string } | null
  classSection?: { name: string; section: string; branch: string } | null
  taskType: string
  createdAt: string
  deadline?: string | null
  maxMarks: number
  instructions?: string | null
  status: string
  creator: { name: string }
  _count: { submissions: number }
}

type ClassSection = {
  id: string
  name: string
  section: string
  branch: string
  semester: number
  _count: { students: number }
}

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

const SUBJECTS = [
  'Data Structures and Algorithms', 'Operating Systems', 'Computer Networks',
  'Database Management Systems', 'Software Engineering', 'Artificial Intelligence',
  'Machine Learning', 'Web Technologies', 'Object Oriented Programming', 'Discrete Mathematics',
]

export default function TasksPage() {
  const { data: session } = useSession()
  const [tasks, setTasks] = useState<Task[]>([])
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [showNewClass, setShowNewClass] = useState(false)
  const [createStep, setCreateStep] = useState(1)
  const [filterType, setFilterType] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterClass, setFilterClass] = useState('all')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    title: '', subject: '', type: 'assignment',
    classSectionId: '', deadline: '',
    totalMarks: '10', instructions: '', allowLate: false
  })
  const [attachFile, setAttachFile] = useState<File | null>(null)
  const [newClass, setNewClass] = useState({ name: '', section: 'A', semester: '1', branch: 'CSE', year: '2025' })

  const token = session?.user?.backendToken

  const fetchTasks = async () => {
    if (!token) return
    try {
      const params = filterClass !== 'all' ? '?classId=' + filterClass : ''
      const res = await fetch(API + '/tasks' + params, {
        headers: { Authorization: 'Bearer ' + token }
      })
      const data = await res.json()
      if (data.success) setTasks(data.data)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const fetchClasses = async () => {
    if (!token) return
    try {
      const res = await fetch(API + '/auth/classes', {
        headers: { Authorization: 'Bearer ' + token }
      })
      const data = await res.json()
      if (data.success) setClasses(data.data)
    } catch (e) { console.error(e) }
  }

  useEffect(() => {
    if (token) { fetchTasks(); fetchClasses() }
  }, [token, filterClass])

  const typeConfig: Record<string, { label: string; icon: string; color: string }> = {
    assignment: { label: 'Assignment', icon: '📝', color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
    class_test: { label: 'Class Test', icon: '✍️', color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
    quiz: { label: 'Quiz', icon: '❓', color: 'text-green-400 bg-green-500/10 border-green-500/20' },
    project: { label: 'Project', icon: '🔬', color: 'text-orange-400 bg-orange-500/10 border-orange-500/20' },
  }

  const formatDate = (dt?: string | null) => dt
    ? new Date(dt).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true })
    : '-'

  const getDaysLeft = (deadline?: string | null) => {
    if (!deadline) return { label: 'No deadline', color: 'text-slate-400' }
    const diff = new Date(deadline).getTime() - Date.now()
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24))
    if (diff < 0) return { label: 'Ended', color: 'text-red-400' }
    if (days === 0) return { label: 'Today', color: 'text-red-400' }
    if (days === 1) return { label: '1 day left', color: 'text-yellow-400' }
    return { label: days + ' days left', color: 'text-green-400' }
  }

  const filtered = tasks.filter(t => {
    if (filterType !== 'all' && t.taskType !== filterType) return false
    if (filterStatus !== 'all' && t.status !== filterStatus) return false
    return true
  })

  const handleCreateTask = async () => {
    if (!token) return
    setSubmitting(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('title', form.title)
      formData.append('taskType', form.type)
      formData.append('maxMarks', form.totalMarks)
      if (form.subject) formData.append('subjectId', form.subject)
      if (form.classSectionId) formData.append('classSectionId', form.classSectionId)
      if (form.deadline) formData.append('deadline', form.deadline)
      if (form.instructions) formData.append('instructions', form.instructions)
      formData.append('allowLate', form.allowLate.toString())
      if (attachFile) formData.append('attachment', attachFile)

      const res = await fetch(API + '/tasks', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token },
        body: formData,
      })
      const data = await res.json()
      if (data.success) {
        await fetchTasks()
        setShowCreate(false)
        setCreateStep(1)
        setForm({ title: '', subject: '', type: 'assignment', classSectionId: '', deadline: '', totalMarks: '10', instructions: '', allowLate: false })
        setAttachFile(null)
      } else {
        setError(data.message || 'Failed to create task')
      }
    } catch (e: any) {
      setError('Network error: ' + e.message)
    }
    setSubmitting(false)
  }

  const handleCreateClass = async () => {
    if (!token) return
    try {
      const res = await fetch(API + '/auth/classes', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify(newClass)
      })
      const data = await res.json()
      if (data.success) {
        await fetchClasses()
        setShowNewClass(false)
        setNewClass({ name: '', section: 'A', semester: '1', branch: 'CSE', year: '2025' })
      }
    } catch (e) { console.error(e) }
  }

  const toggleStatus = async (id: string, currentStatus: string) => {
    if (!token) return
    const newStatus = currentStatus === 'active' ? 'closed' : 'active'
    await fetch(API + '/tasks/' + id + '/status', {
      method: 'PATCH',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    })
    fetchTasks()
  }

  const deleteTask = async (id: string) => {
    if (!token) return
    await fetch(API + '/tasks/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } })
    fetchTasks()
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Tasks</h1>
          <p className="text-slate-400 text-sm">Manage assignments, tests and quizzes by class</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowNewClass(true)} className="px-4 py-2.5 bg-slate-800 text-slate-300 text-sm font-medium rounded-xl border border-white/10 hover:border-white/20 transition-all">+ Add Class</button>
          <button onClick={() => setShowCreate(true)} className="px-4 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 transition-all">+ Create Task</button>
        </div>
      </div>

      {/* Class filter tabs */}
      {classes.length > 0 && (
        <div className="flex gap-2 flex-wrap mb-4">
          <button onClick={() => setFilterClass('all')} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterClass === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>
            All Classes <span className="opacity-60 ml-1">{tasks.length}</span>
          </button>
          {classes.map(c => (
            <button key={c.id} onClick={() => setFilterClass(c.id)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterClass === c.id ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>
              {c.name} {c.section} — {c.branch}
              <span className="opacity-60 ml-1">{c._count.students} students</span>
            </button>
          ))}
        </div>
      )}

      {/* Type + Status filters */}
      <div className="flex gap-2 mb-6 flex-wrap">
        <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-xl p-1">
          {['all', 'assignment', 'class_test', 'quiz', 'project'].map(t => (
            <button key={t} onClick={() => setFilterType(t)} className={'px-3 py-1.5 rounded-lg text-xs font-medium transition-all ' + (filterType === t ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
              {t === 'all' ? 'All' : typeConfig[t]?.label || t}
            </button>
          ))}
        </div>
        <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-xl p-1">
          {['all', 'active', 'closed'].map(s => (
            <button key={s} onClick={() => setFilterStatus(s)} className={'px-3 py-1.5 rounded-lg text-xs font-medium transition-all ' + (filterStatus === s ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
              {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Loading tasks...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">📋</p>
          <p className="text-white font-medium mb-1">No tasks yet</p>
          <p className="text-slate-500 text-sm mb-4">Create your first task for students</p>
          <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-blue-500 text-white text-sm rounded-xl hover:bg-blue-600">Create Task</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map(task => {
            const tc = typeConfig[task.taskType] || typeConfig.assignment
            const dl = getDaysLeft(task.deadline)
            return (
              <div key={task.id} className="bg-slate-900 rounded-2xl border border-white/5 hover:border-white/10 transition-all p-5">
                <div className="flex items-start gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-xl flex-shrink-0">{tc.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex gap-2 mb-1 flex-wrap">
                      <span className={'text-[10px] px-2 py-0.5 rounded border font-medium ' + tc.color}>{tc.label}</span>
                      <span className={'text-[10px] px-2 py-0.5 rounded border font-medium ' + (task.status === 'active' ? 'text-green-400 bg-green-500/10 border-green-500/20' : 'text-slate-400 bg-slate-700 border-white/10')}>
                        {task.status}
                      </span>
                      {task.classSection && (
                        <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-purple-400 bg-purple-500/10 border-purple-500/20">
                          {task.classSection.name} {task.classSection.section}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-white truncate">{task.title}</p>
                    {task.subject && <p className="text-xs text-slate-500 mt-0.5">{task.subject.name}</p>}
                  </div>
                </div>
                <div className="bg-slate-800 rounded-xl p-3 mb-4 border border-white/5 space-y-2">
                  <div className="flex justify-between"><span className="text-[10px] text-slate-500 uppercase">Created</span><span className="text-xs text-slate-300">{formatDate(task.createdAt)}</span></div>
                  <div className="h-px bg-white/5" />
                  <div className="flex justify-between"><span className="text-[10px] text-slate-500 uppercase">Deadline</span><span className="text-xs text-slate-300">{formatDate(task.deadline)}</span></div>
                  <div className="h-px bg-white/5" />
                  <div className="flex justify-between"><span className="text-[10px] text-slate-500 uppercase">Time Left</span><span className={'text-xs font-medium ' + dl.color}>{dl.label}</span></div>
                  <div className="h-px bg-white/5" />
                  <div className="flex justify-between"><span className="text-[10px] text-slate-500 uppercase">Submissions</span><span className="text-xs text-white">{task._count.submissions}</span></div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => toggleStatus(task.id, task.status)} className={'text-xs px-3 py-1.5 border rounded-lg transition-all ' + (task.status === 'active' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-green-500/10 text-green-400 border-green-500/20')}>
                    {task.status === 'active' ? 'Close' : 'Reopen'}
                  </button>
                  <button onClick={() => deleteTask(task.id)} className="text-xs px-3 py-1.5 bg-slate-800 text-slate-400 border border-white/5 rounded-lg hover:text-red-400 transition-all ml-auto">Delete</button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Create Task Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-white/5 sticky top-0 bg-slate-900 z-10">
              <div>
                <p className="text-sm font-medium text-white">Create New Task</p>
                <p className="text-xs text-slate-500">Step {createStep} of 3</p>
              </div>
              <button onClick={() => { setShowCreate(false); setCreateStep(1); setError('') }} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center">✕</button>
            </div>
            <div className="flex px-5 pt-4 gap-1">
              {['Type & Class', 'Details', 'Attachment'].map((label, i) => (
                <div key={i} className="flex-1">
                  <div className={'h-1 rounded-full ' + (createStep > i ? 'bg-blue-500' : 'bg-slate-700')} />
                  <p className={'text-[10px] mt-1 ' + (createStep === i+1 ? 'text-blue-400' : 'text-slate-600')}>{label}</p>
                </div>
              ))}
            </div>
            {error && (
              <div className="mx-5 mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                <p className="text-xs text-red-400">{error}</p>
              </div>
            )}
            <div className="p-5">
              {createStep === 1 && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Task Type</label>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(typeConfig).map(([key, val]) => (
                        <button key={key} onClick={() => setForm(p => ({ ...p, type: key }))} className={'p-3 rounded-xl border text-left transition-all ' + (form.type === key ? 'border-blue-500/50 bg-blue-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                          <p className="text-xl mb-1">{val.icon}</p>
                          <p className="text-xs font-medium text-white">{val.label}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Assign to Class (Optional)</label>
                    <select value={form.classSectionId} onChange={e => setForm(p => ({ ...p, classSectionId: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50">
                      <option value="">All Students</option>
                      {classes.map(c => (
                        <option key={c.id} value={c.id}>{c.name} — Section {c.section} — {c.branch} ({c._count.students} students)</option>
                      ))}
                    </select>
                    {classes.length === 0 && (
                      <p className="text-xs text-amber-400 mt-1">No classes created yet. <button onClick={() => { setShowCreate(false); setShowNewClass(true) }} className="underline">Create a class first</button></p>
                    )}
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Subject</label>
                    <select value={form.subject} onChange={e => setForm(p => ({ ...p, subject: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50">
                      <option value="">-- Select Subject --</option>
                      {SUBJECTS.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Title</label>
                    <input type="text" value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} placeholder="e.g. Assignment 1 - Sorting" className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
                  </div>
                  <button onClick={() => setCreateStep(2)} disabled={!form.title} className="w-full py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed">Next</button>
                </div>
              )}
              {createStep === 2 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Deadline</label>
                      <input type="datetime-local" value={form.deadline} onChange={e => setForm(p => ({ ...p, deadline: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50" />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Total Marks</label>
                      <input type="number" value={form.totalMarks} min={1} max={100} onChange={e => setForm(p => ({ ...p, totalMarks: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Instructions</label>
                    <textarea value={form.instructions} onChange={e => setForm(p => ({ ...p, instructions: e.target.value }))} placeholder="Instructions for students..." rows={4} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 resize-none" />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-800 rounded-xl border border-white/5">
                    <div>
                      <p className="text-xs font-medium text-white">Allow Late Submission</p>
                      <p className="text-[10px] text-slate-500">Students can submit after deadline</p>
                    </div>
                    <button onClick={() => setForm(p => ({ ...p, allowLate: !p.allowLate }))} className={'w-10 h-5 rounded-full transition-all relative ' + (form.allowLate ? 'bg-blue-500' : 'bg-slate-700')}>
                      <span className={'absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ' + (form.allowLate ? 'left-5' : 'left-0.5')} />
                    </button>
                  </div>
                  <div className="flex gap-3">
                    <button onClick={() => setCreateStep(1)} className="px-5 py-2.5 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">Back</button>
                    <button onClick={() => setCreateStep(3)} className="flex-1 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600">Next</button>
                  </div>
                </div>
              )}
              {createStep === 3 && (
                <div className="space-y-4">
                  <div className="bg-slate-800 rounded-xl p-3 border border-white/5">
                    <p className="text-xs text-slate-500 mb-1">Summary</p>
                    <p className="text-sm font-medium text-white">{form.title}</p>
                    <div className="flex gap-2 mt-1 text-[10px] flex-wrap">
                      <span className={'px-2 py-0.5 rounded border ' + typeConfig[form.type]?.color}>{typeConfig[form.type]?.label}</span>
                      {form.classSectionId && <span className="text-purple-400">{classes.find(c => c.id === form.classSectionId)?.name} {classes.find(c => c.id === form.classSectionId)?.section}</span>}
                      <span className="text-slate-400">{form.totalMarks} marks</span>
                      {form.deadline && <span className="text-slate-400">Due: {new Date(form.deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span>}
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Attach File (Optional)</label>
                    <div onClick={() => document.getElementById('task-attach')?.click()} className={'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer ' + (attachFile ? 'border-green-500/50 bg-green-500/5' : 'border-white/10 hover:border-white/20')}>
                      <input id="task-attach" type="file" className="hidden" onChange={e => setAttachFile(e.target.files?.[0] || null)} />
                      {attachFile ? <div><p className="text-green-400 text-2xl mb-1">✓</p><p className="text-sm text-white">{attachFile.name}</p></div>
                        : <div><p className="text-3xl mb-1">📎</p><p className="text-sm text-slate-400">Click to attach file</p></div>}
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <button onClick={() => setCreateStep(2)} className="px-5 py-2.5 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">Back</button>
                    <button onClick={handleCreateTask} disabled={submitting} className="flex-1 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40 flex items-center justify-center gap-2">
                      {submitting ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Creating...</> : 'Create Task'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create Class Modal */}
      {showNewClass && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-md">
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <p className="text-sm font-medium text-white">Create New Class</p>
              <button onClick={() => setShowNewClass(false)} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center">✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Class Name</label>
                  <input type="text" value={newClass.name} onChange={e => setNewClass(p => ({ ...p, name: e.target.value }))} placeholder="e.g. BCA, B.Tech, MCA" className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Section</label>
                  <div className="flex gap-2">
                    {['A', 'B', 'C', 'D'].map(s => (
                      <button key={s} onClick={() => setNewClass(p => ({ ...p, section: s }))} className={'flex-1 py-2 rounded-xl text-xs font-medium border transition-all ' + (newClass.section === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Branch</label>
                  <select value={newClass.branch} onChange={e => setNewClass(p => ({ ...p, branch: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50">
                    {['CSE', 'ECE', 'ME', 'CE', 'IT', 'EE', 'MCA', 'BCA'].map(b => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Semester</label>
                  <select value={newClass.semester} onChange={e => setNewClass(p => ({ ...p, semester: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50">
                    {['1','2','3','4','5','6','7','8'].map(s => <option key={s} value={s}>Sem {s}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Year</label>
                <select value={newClass.year} onChange={e => setNewClass(p => ({ ...p, year: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50">
                  {['2025', '2026', '2027', '2028'].map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <button onClick={handleCreateClass} disabled={!newClass.name} className="w-full py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40">
                Create Class
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Teacher Tasks page done!")

# Fix Student Complaints - backend se connect
os.makedirs("../frontend/app/(student)/student/complaints", exist_ok=True)
with open("../frontend/app/(student)/student/complaints/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

type Message = {
  id: string
  sentBy: string
  senderName: string
  senderRole: string
  message: string
  createdAt: string
}

type Complaint = {
  id: string
  subject: string
  category: string
  status: string
  createdAt: string
  raiser: { name: string; email: string }
  messages: Message[]
}

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

export default function StudentComplaintsPage() {
  const { data: session } = useSession()
  const [complaints, setComplaints] = useState<Complaint[]>([])
  const [selected, setSelected] = useState<Complaint | null>(null)
  const [showNew, setShowNew] = useState(false)
  const [replyText, setReplyText] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ subject: '', category: 'Marks', description: '' })

  const token = session?.user?.backendToken

  const fetchComplaints = async () => {
    if (!token) return
    const res = await fetch(API + '/complaints', { headers: { Authorization: 'Bearer ' + token } })
    const data = await res.json()
    if (data.success) {
      setComplaints(data.data)
      if (selected) {
        const updated = data.data.find((c: Complaint) => c.id === selected.id)
        if (updated) setSelected(updated)
      }
    }
    setLoading(false)
  }

  useEffect(() => { if (token) fetchComplaints() }, [token])

  const statusConfig: Record<string, { label: string; color: string }> = {
    open: { label: 'Open', color: 'text-red-400 bg-red-500/10 border-red-500/20' },
    in_progress: { label: 'In Progress', color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' },
    resolved: { label: 'Resolved', color: 'text-green-400 bg-green-500/10 border-green-500/20' },
    closed: { label: 'Closed', color: 'text-slate-400 bg-slate-700 border-white/10' },
  }

  const sendReply = async () => {
    if (!replyText.trim() || !selected || !token) return
    const res = await fetch(API + '/complaints/' + selected.id + '/reply', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: replyText })
    })
    const data = await res.json()
    if (data.success) { setReplyText(''); fetchComplaints() }
  }

  const submitComplaint = async () => {
    if (!form.subject || !form.description || !token) return
    setSubmitting(true)
    const res = await fetch(API + '/complaints', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    const data = await res.json()
    if (data.success) {
      setForm({ subject: '', category: 'Marks', description: '' })
      setShowNew(false)
      fetchComplaints()
    }
    setSubmitting(false)
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Complaints</h1>
          <p className="text-slate-400 text-sm">Raise and track your complaints with teachers</p>
        </div>
        <button onClick={() => setShowNew(true)} className="px-4 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 transition-all">+ New Complaint</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6" style={{ minHeight: '500px' }}>
        <div className="lg:col-span-2 space-y-2">
          {loading ? (
            <div className="text-center py-8"><div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
          ) : complaints.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-8 text-center">
              <p className="text-3xl mb-2">💬</p>
              <p className="text-white text-sm font-medium mb-1">No complaints yet</p>
              <p className="text-slate-500 text-xs mb-3">Raise a complaint to get help from your teacher</p>
              <button onClick={() => setShowNew(true)} className="px-3 py-1.5 bg-blue-500 text-white text-xs rounded-lg hover:bg-blue-600">Raise Complaint</button>
            </div>
          ) : complaints.map(c => {
            const sc = statusConfig[c.status] || statusConfig.open
            return (
              <button key={c.id} onClick={() => setSelected(c)} className={'w-full text-left p-4 rounded-xl border transition-all ' + (selected?.id === c.id ? 'bg-blue-500/10 border-blue-500/30' : 'bg-slate-900 border-white/5 hover:border-white/10')}>
                <div className="flex items-start justify-between gap-2 mb-1">
                  <p className="text-sm font-medium text-white leading-snug flex-1">{c.subject}</p>
                  <span className={'text-[10px] px-1.5 py-0.5 rounded border font-medium flex-shrink-0 ' + sc.color}>{sc.label}</span>
                </div>
                <p className="text-xs text-slate-500">{c.category} · {new Date(c.createdAt).toLocaleDateString('en-IN')}</p>
                <p className="text-[10px] text-slate-600 mt-1">{c.messages.length} message{c.messages.length !== 1 ? 's' : ''}</p>
              </button>
            )
          })}
        </div>

        <div className="lg:col-span-3 bg-slate-900 rounded-2xl border border-white/5 flex flex-col" style={{ minHeight: '400px' }}>
          {!selected ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <p className="text-4xl mb-3">💬</p>
                <p className="text-white font-medium mb-1">Select a complaint</p>
                <p className="text-slate-500 text-sm">Click on a complaint to view thread</p>
              </div>
            </div>
          ) : (
            <>
              <div className="p-4 border-b border-white/5">
                <p className="text-sm font-medium text-white">{selected.subject}</p>
                <div className="flex gap-2 mt-1 flex-wrap">
                  <span className={'text-[10px] px-2 py-0.5 rounded border font-medium ' + (statusConfig[selected.status]?.color || statusConfig.open.color)}>{statusConfig[selected.status]?.label}</span>
                  <span className="text-[10px] text-slate-500">{selected.category}</span>
                  <span className="text-[10px] text-slate-500">{new Date(selected.createdAt).toLocaleDateString('en-IN')}</span>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {selected.messages.map(msg => {
                  const isMe = msg.senderRole === 'student'
                  return (
                    <div key={msg.id} className={'flex ' + (isMe ? 'justify-end' : 'justify-start')}>
                      <div className={'max-w-[80%] flex flex-col gap-1 ' + (isMe ? 'items-end' : 'items-start')}>
                        <p className="text-[10px] text-slate-500 px-1">{msg.senderName} ({msg.senderRole})</p>
                        <div className={'px-4 py-2.5 rounded-2xl text-sm leading-relaxed ' + (isMe ? 'bg-blue-500 text-white rounded-br-sm' : 'bg-slate-800 text-slate-200 border border-white/5 rounded-bl-sm')}>
                          {msg.message}
                        </div>
                        <p className="text-[10px] text-slate-600 px-1">{new Date(msg.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true })}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
              {selected.status !== 'resolved' && selected.status !== 'closed' ? (
                <div className="p-4 border-t border-white/5">
                  <div className="flex gap-2">
                    <input type="text" value={replyText} onChange={e => setReplyText(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendReply()} placeholder="Type your message..." className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
                    <button onClick={sendReply} disabled={!replyText.trim()} className="px-4 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 transition-all disabled:opacity-40">Send</button>
                  </div>
                </div>
              ) : (
                <div className="p-4 border-t border-white/5 text-center">
                  <p className="text-xs text-green-400">✓ This complaint has been {selected.status}</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {showNew && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <p className="text-sm font-medium text-white">Raise New Complaint</p>
              <button onClick={() => setShowNew(false)} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center">✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Category</label>
                <div className="grid grid-cols-3 gap-2">
                  {['Marks', 'Submission', 'Paper', 'Attendance', 'Other'].map(cat => (
                    <button key={cat} onClick={() => setForm(p => ({ ...p, category: cat }))} className={'py-2 rounded-xl text-xs font-medium border transition-all ' + (form.category === cat ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>{cat}</button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Subject / Title</label>
                <input type="text" value={form.subject} onChange={e => setForm(p => ({ ...p, subject: e.target.value }))} placeholder="Brief title of your complaint" className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
              </div>
              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Description</label>
                <textarea value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} placeholder="Describe your complaint in detail..." rows={4} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 resize-none" />
              </div>
              <button onClick={submitComplaint} disabled={!form.subject || !form.description || submitting} className="w-full py-3 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40 flex items-center justify-center gap-2">
                {submitting ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Submitting...</> : '📤 Submit Complaint'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Student Complaints done!")

# Fix Teacher Complaints - backend se connect
os.makedirs("../frontend/app/(dashboard)/teacher/complaints", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/complaints/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

type Message = {
  id: string
  sentBy: string
  senderName: string
  senderRole: string
  message: string
  createdAt: string
}

type Complaint = {
  id: string
  subject: string
  category: string
  status: string
  priority: string
  createdAt: string
  raiser: { name: string; email: string; rollNumber?: string | null; avatarUrl?: string | null }
  messages: Message[]
}

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

export default function TeacherComplaintsPage() {
  const { data: session } = useSession()
  const [complaints, setComplaints] = useState<Complaint[]>([])
  const [selected, setSelected] = useState<Complaint | null>(null)
  const [replyText, setReplyText] = useState('')
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  const token = session?.user?.backendToken

  const fetchComplaints = async () => {
    if (!token) return
    const res = await fetch(API + '/complaints', { headers: { Authorization: 'Bearer ' + token } })
    const data = await res.json()
    if (data.success) {
      setComplaints(data.data)
      if (selected) {
        const updated = data.data.find((c: Complaint) => c.id === selected.id)
        if (updated) setSelected(updated)
      }
    }
    setLoading(false)
  }

  useEffect(() => { if (token) fetchComplaints() }, [token])

  const statusConfig: Record<string, { label: string; color: string }> = {
    open: { label: 'Open', color: 'text-red-400 bg-red-500/10 border-red-500/20' },
    in_progress: { label: 'In Progress', color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' },
    resolved: { label: 'Resolved', color: 'text-green-400 bg-green-500/10 border-green-500/20' },
    closed: { label: 'Closed', color: 'text-slate-400 bg-slate-700 border-white/10' },
  }

  const sendReply = async () => {
    if (!replyText.trim() || !selected || !token) return
    const res = await fetch(API + '/complaints/' + selected.id + '/reply', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: replyText })
    })
    if (res.ok) { setReplyText(''); fetchComplaints() }
  }

  const updateStatus = async (id: string, status: string) => {
    if (!token) return
    await fetch(API + '/complaints/' + id + '/status', {
      method: 'PATCH',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    })
    fetchComplaints()
  }

  const filtered = filter === 'all' ? complaints : complaints.filter(c => c.status === filter)

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">Complaints</h1>
        <p className="text-slate-400 text-sm">Manage and respond to student complaints</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6" style={{ minHeight: '500px' }}>
        <div className="lg:col-span-2 flex flex-col">
          <div className="flex gap-2 mb-3 flex-wrap">
            {[
              { key: 'all', label: 'All', count: complaints.length },
              { key: 'open', label: 'Open', count: complaints.filter(c => c.status === 'open').length },
              { key: 'in_progress', label: 'In Progress', count: complaints.filter(c => c.status === 'in_progress').length },
              { key: 'resolved', label: 'Resolved', count: complaints.filter(c => c.status === 'resolved').length },
            ].map(tab => (
              <button key={tab.key} onClick={() => setFilter(tab.key)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filter === tab.key ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>
                {tab.label} <span className="opacity-70 ml-1">{tab.count}</span>
              </button>
            ))}
          </div>
          <div className="space-y-2 overflow-y-auto flex-1">
            {loading ? (
              <div className="text-center py-8"><div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
            ) : filtered.length === 0 ? (
              <div className="bg-slate-900 rounded-xl border border-white/5 p-6 text-center">
                <p className="text-3xl mb-2">💬</p>
                <p className="text-slate-500 text-sm">No complaints yet</p>
              </div>
            ) : filtered.map(c => {
              const sc = statusConfig[c.status] || statusConfig.open
              return (
                <button key={c.id} onClick={() => setSelected(c)} className={'w-full text-left p-4 rounded-xl border transition-all ' + (selected?.id === c.id ? 'bg-blue-500/10 border-blue-500/30' : 'bg-slate-900 border-white/5 hover:border-white/10')}>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <p className="text-sm font-medium text-white leading-snug flex-1">{c.subject}</p>
                    <span className={'text-[10px] px-1.5 py-0.5 rounded border font-medium flex-shrink-0 ' + sc.color}>{sc.label}</span>
                  </div>
                  <p className="text-xs text-slate-400">{c.raiser.name}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{c.category} · {new Date(c.createdAt).toLocaleDateString('en-IN')}</p>
                  <p className="text-[10px] text-slate-600 mt-1">{c.messages.length} message{c.messages.length !== 1 ? 's' : ''}</p>
                </button>
              )
            })}
          </div>
        </div>

        <div className="lg:col-span-3 bg-slate-900 rounded-2xl border border-white/5 flex flex-col">
          {!selected ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <p className="text-4xl mb-3">💬</p>
                <p className="text-white font-medium mb-1">Select a complaint</p>
                <p className="text-slate-500 text-sm">Click on a complaint to view and reply</p>
              </div>
            </div>
          ) : (
            <>
              <div className="p-4 border-b border-white/5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-white mb-1">{selected.subject}</p>
                    <div className="flex items-center gap-2 flex-wrap text-xs text-slate-500">
                      <span>{selected.raiser.name}</span>
                      <span>·</span>
                      <span>{selected.raiser.email}</span>
                      {selected.raiser.rollNumber && <><span>·</span><span>Roll: {selected.raiser.rollNumber}</span></>}
                    </div>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    {selected.status !== 'resolved' && (
                      <button onClick={() => updateStatus(selected.id, 'resolved')} className="text-xs px-3 py-1.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded-lg hover:bg-green-500/20">Mark Resolved</button>
                    )}
                    {selected.status === 'resolved' && (
                      <button onClick={() => updateStatus(selected.id, 'open')} className="text-xs px-3 py-1.5 bg-slate-800 text-slate-400 border border-white/10 rounded-lg hover:border-white/20">Reopen</button>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {selected.messages.map(msg => {
                  const isTeacher = msg.senderRole === 'teacher'
                  return (
                    <div key={msg.id} className={'flex ' + (isTeacher ? 'justify-end' : 'justify-start')}>
                      <div className={'max-w-[80%] flex flex-col gap-1 ' + (isTeacher ? 'items-end' : 'items-start')}>
                        <p className="text-[10px] text-slate-500 px-1">{msg.senderName}</p>
                        <div className={'px-4 py-2.5 rounded-2xl text-sm leading-relaxed ' + (isTeacher ? 'bg-blue-500 text-white rounded-br-sm' : 'bg-slate-800 text-slate-200 border border-white/5 rounded-bl-sm')}>
                          {msg.message}
                        </div>
                        <p className="text-[10px] text-slate-600 px-1">{new Date(msg.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true })}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
              {selected.status !== 'resolved' && selected.status !== 'closed' ? (
                <div className="p-4 border-t border-white/5">
                  <div className="flex gap-2">
                    <input type="text" value={replyText} onChange={e => setReplyText(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendReply()} placeholder="Type your reply..." className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
                    <button onClick={sendReply} disabled={!replyText.trim()} className="px-4 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40">Send</button>
                  </div>
                </div>
              ) : (
                <div className="p-4 border-t border-white/5 text-center">
                  <p className="text-xs text-green-400">✓ Complaint {selected.status}</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
""")
print("Teacher Complaints done!")

# Student class selection page
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
  _count: { students: number }
}

export default function SelectClassPage() {
  const { data: session, update } = useSession()
  const router = useRouter()
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [selected, setSelected] = useState('')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)

  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    fetch(API + '/auth/classes', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(data => { if (data.success) setClasses(data.data); setLoading(false) })
  }, [token])

  const handleSelect = async () => {
    if (!selected || !token) return
    setSaving(true)
    const res = await fetch(API + '/auth/select-class', {
      method: 'PATCH',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ classSectionId: selected })
    })
    const data = await res.json()
    if (data.success) {
      localStorage.setItem('studentClassSelected', 'true')
      router.push('/student')
    }
    setSaving(false)
  }

  const grouped = classes.reduce((acc, c) => {
    const key = c.branch + ' — Sem ' + c.semester
    if (!acc[key]) acc[key] = []
    acc[key].push(c)
    return acc
  }, {} as Record<string, ClassSection[]>)

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center text-3xl mx-auto mb-4">🎓</div>
          <h1 className="text-2xl font-semibold text-white mb-2">Select Your Class</h1>
          <p className="text-slate-400 text-sm">Choose your class and section to see relevant tasks and materials</p>
        </div>

        {loading ? (
          <div className="text-center py-8"><div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
        ) : classes.length === 0 ? (
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-8 text-center">
            <p className="text-3xl mb-3">⏳</p>
            <p className="text-white font-medium mb-1">No classes created yet</p>
            <p className="text-slate-400 text-sm mb-4">Your teacher has not created any classes yet. You can continue without selecting a class.</p>
            <button onClick={() => router.push('/student')} className="px-4 py-2 bg-green-500 text-white text-sm rounded-xl hover:bg-green-600">Continue to Dashboard</button>
          </div>
        ) : (
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
            <div className="space-y-4 mb-6 max-h-[400px] overflow-y-auto pr-1">
              {Object.entries(grouped).map(([group, groupClasses]) => (
                <div key={group}>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{group}</p>
                  <div className="grid grid-cols-2 gap-2">
                    {groupClasses.map(c => (
                      <button key={c.id} onClick={() => setSelected(c.id)} className={'p-3 rounded-xl border text-left transition-all ' + (selected === c.id ? 'border-green-500/50 bg-green-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                        <p className="text-sm font-medium text-white">{c.name} — Section {c.section}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{c.branch} · Sem {c.semester} · {c.year}</p>
                        <p className="text-xs text-slate-600 mt-0.5">{c._count.students} students</p>
                        {selected === c.id && <p className="text-[10px] text-green-400 mt-1 font-medium">✓ Selected</p>}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex gap-3">
              <button onClick={() => router.push('/student')} className="px-5 py-2.5 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">Skip for now</button>
              <button onClick={handleSelect} disabled={!selected || saving} className="flex-1 py-2.5 bg-green-500 text-white text-sm font-medium rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center justify-center gap-2">
                {saving ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Saving...</> : 'Confirm Class'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
""")
print("Select Class page done!")

# Update Student Layout to check class selection
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
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    if (status === 'loading') return
    if (!session) { router.push('/login'); return }
    if (session.user.role !== 'student') { router.push('/teacher'); return }

    // Check if student has selected class (skip for select-class page)
    if (pathname !== '/student/select-class') {
      const classSelected = localStorage.getItem('studentClassSelected')
      if (!classSelected && session.user.backendToken) {
        router.push('/student/select-class')
        return
      }
    }

    setChecked(true)
  }, [session, status, pathname])

  if (!checked) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (pathname === '/student/select-class') {
    return <>{children}</>
  }

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
print("Student Layout done!")

print("\n" + "="*50)
print("ALL FRONTEND FIXES DONE!")
print("="*50)