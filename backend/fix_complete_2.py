import os

# ═══════════════════════════════════════
# Student Materials - class + subject filter
# ═══════════════════════════════════════
os.makedirs("../frontend/app/(student)/student/materials", exist_ok=True)
with open("../frontend/app/(student)/student/materials/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Material = {
  id: string; title: string; fileName: string; fileUrl: string
  subject?: string | null; unit?: string | null; year?: number | null; examType?: string | null
  isPyq: boolean; fileSizeKb?: number | null; uploader: { name: string }
  classSection?: { name: string; section: string } | null
}

export default function StudentMaterialsPage() {
  const { data: session } = useSession()
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'notes'|'pyq'>('notes')
  const [fSubject, setFSubject] = useState('all')
  const [fUnit, setFUnit] = useState('all')
  const [fYear, setFYear] = useState('all')
  const [fExam, setFExam] = useState('all')
  const [search, setSearch] = useState('')
  const [preview, setPreview] = useState<Material | null>(null)
  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    const classId = localStorage.getItem('myClassId') || ''
    fetch(API + '/materials?classId=' + classId, { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json()).then(d => { if (d.success) setMaterials(d.data); setLoading(false) })
  }, [token])

  const notes = materials.filter(m => !m.isPyq)
  const pyqs = materials.filter(m => m.isPyq)
  const current = tab === 'notes' ? notes : pyqs

  const subjects = Array.from(new Set(current.map(m => m.subject).filter(Boolean))) as string[]
  const units = Array.from(new Set(notes.filter(m => fSubject === 'all' || m.subject === fSubject).map(m => m.unit).filter(Boolean))) as string[]
  const years = Array.from(new Set(pyqs.filter(m => fSubject === 'all' || m.subject === fSubject).map(m => m.year?.toString()).filter(Boolean))).sort((a,b) => (b||'').localeCompare(a||'')) as string[]

  const filtered = current.filter(m => {
    if (fSubject !== 'all' && m.subject !== fSubject) return false
    if (tab === 'notes' && fUnit !== 'all' && m.unit !== fUnit) return false
    if (tab === 'pyq' && fYear !== 'all' && m.year?.toString() !== fYear) return false
    if (tab === 'pyq' && fExam !== 'all' && m.examType !== fExam) return false
    if (search && !m.title.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const examLabel = (t?: string | null) => t === 'end_term' ? 'End Term' : t === 'mid_term' ? 'Mid Term' : t === 'unit_test' ? 'Unit Test' : t || ''

  const download = async (m: Material) => {
    if (!token) return
    const res = await fetch(API + '/materials/' + m.id + '/download', { headers: { Authorization: 'Bearer ' + token } })
    if (res.headers.get('content-type')?.includes('json')) {
      const d = await res.json()
      if (d.data?.fileUrl) window.open('http://localhost:5000' + d.data.fileUrl, '_blank')
    } else {
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = m.fileName; a.click()
    }
  }

  const reset = () => { setFSubject('all'); setFUnit('all'); setFYear('all'); setFExam('all') }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-white mb-1">Study Materials</h1>
        <p className="text-slate-400 text-sm">Notes and PYQs for your class</p>
      </div>

      <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-2xl p-1.5 mb-6 w-fit">
        <button onClick={() => { setTab('notes'); reset() }} className={'px-5 py-2.5 rounded-xl text-sm font-medium transition-all ' + (tab === 'notes' ? 'bg-green-500 text-white' : 'text-slate-400 hover:text-white')}>
          📚 Notes ({notes.length})
        </button>
        <button onClick={() => { setTab('pyq'); reset() }} className={'px-5 py-2.5 rounded-xl text-sm font-medium transition-all ' + (tab === 'pyq' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
          📋 PYQs ({pyqs.length})
        </button>
      </div>

      <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..." className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 mb-4" />

      <div className="bg-slate-900 rounded-2xl border border-white/5 p-4 mb-5 space-y-4">
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">📚 Subject</p>
          <div className="flex gap-2 flex-wrap">
            <button onClick={() => { setFSubject('all'); setFUnit('all'); setFYear('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fSubject === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>
              All ({current.length})
            </button>
            {subjects.map(s => (
              <button key={s} onClick={() => { setFSubject(s); setFUnit('all'); setFYear('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fSubject === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>
                {s.length > 22 ? s.slice(0,22)+'...' : s} ({current.filter(m => m.subject === s).length})
              </button>
            ))}
          </div>
        </div>

        {tab === 'notes' && fSubject !== 'all' && units.length > 0 && (
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">📖 Unit</p>
            <div className="flex gap-2 flex-wrap">
              <button onClick={() => setFUnit('all')} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fUnit === 'all' ? 'bg-purple-500 text-white border-purple-500' : 'bg-slate-800 text-slate-400 border-white/5')}>All Units</button>
              {units.map(u => (
                <button key={u} onClick={() => setFUnit(u)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fUnit === u ? 'bg-purple-500 text-white border-purple-500' : 'bg-slate-800 text-slate-400 border-white/5')}>{u}</button>
              ))}
            </div>
          </div>
        )}

        {tab === 'pyq' && years.length > 0 && (
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">📅 Year</p>
            <div className="flex gap-2 flex-wrap">
              <button onClick={() => { setFYear('all'); setFExam('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fYear === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>All Years</button>
              {years.map(y => (
                <button key={y} onClick={() => { setFYear(y); setFExam('all') }} className={'px-4 py-1.5 rounded-lg text-sm font-medium border ' + (fYear === y ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>{y}</button>
              ))}
            </div>
          </div>
        )}

        {tab === 'pyq' && fYear !== 'all' && (
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">🎯 Exam Type</p>
            <div className="flex gap-2">
              <button onClick={() => setFExam('all')} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fExam === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>All</button>
              {['end_term', 'mid_term', 'unit_test'].map(t => (
                <button key={t} onClick={() => setFExam(t)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fExam === t ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>{examLabel(t)}</button>
              ))}
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-slate-500 mb-3">Showing {filtered.length} of {current.length}</p>

      {loading ? (
        <div className="text-center py-12"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">{tab === 'notes' ? '📚' : '📋'}</p>
          <p className="text-white font-medium mb-1">No {tab === 'notes' ? 'notes' : 'papers'} found</p>
          <p className="text-slate-500 text-sm">Try different filters or check back later</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map(m => (
            <div key={m.id} className="bg-slate-900 rounded-2xl border border-white/5 hover:border-white/10 p-5">
              <div className="flex items-start gap-4 mb-4">
                <div className={'w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0 ' + (m.isPyq ? 'bg-blue-500/10 border border-blue-500/20' : 'bg-green-500/10 border border-green-500/20')}>
                  {m.isPyq ? '📋' : '📚'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate mb-1.5">{m.title}</p>
                  <div className="flex gap-1.5 flex-wrap">
                    {m.subject && <span className="text-[10px] px-2 py-0.5 rounded-full border font-medium text-green-400 bg-green-500/10 border-green-500/20">{m.subject.length > 18 ? m.subject.slice(0,18)+'...' : m.subject}</span>}
                    {m.unit && <span className="text-[10px] px-2 py-0.5 rounded-full border font-medium text-purple-400 bg-purple-500/10 border-purple-500/20">{m.unit}</span>}
                    {m.year && <span className="text-[10px] px-2 py-0.5 rounded-full border font-medium text-blue-400 bg-blue-500/10 border-blue-500/20">{m.year}</span>}
                    {m.examType && <span className="text-[10px] px-2 py-0.5 rounded-full border font-medium text-orange-400 bg-orange-500/10 border-orange-500/20">{examLabel(m.examType)}</span>}
                  </div>
                  <p className="text-[10px] text-slate-600 mt-1">By {m.uploader.name}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setPreview(m)} className="flex-1 py-2 bg-slate-800 text-slate-300 border border-white/10 rounded-xl text-xs font-medium hover:border-white/20">👁 View</button>
                <button onClick={() => download(m)} className="flex-1 py-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-xl text-xs font-medium hover:bg-blue-500/20">⬇ Download</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {preview && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-5xl h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-white/5">
              <p className="text-sm font-medium text-white">{preview.title}</p>
              <div className="flex gap-2">
                <button onClick={() => download(preview)} className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg">⬇ Download</button>
                <button onClick={() => setPreview(null)} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center">✕</button>
              </div>
            </div>
            <iframe src={'http://localhost:5000' + preview.fileUrl} className="flex-1" title={preview.title} />
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Student Materials done!")

# ═══════════════════════════════════════
# Student Assignments - fetch with classId
# ═══════════════════════════════════════
os.makedirs("../frontend/app/(student)/student/assignments", exist_ok=True)
with open("../frontend/app/(student)/student/assignments/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect, useCallback } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Task = {
  id: string; title: string; subjectName?: string | null; taskType: string
  deadline?: string | null; maxMarks: number; instructions?: string | null
  attachmentUrl?: string | null; status: string
  creator: { name: string }
  classSection?: { name: string; section: string } | null
}

type Submission = {
  id: string; taskId: string; status: string
  marksAwarded?: number | null; feedback?: string | null
  submittedAt: string
  task: { title: string; maxMarks: number; taskType: string; subjectName?: string | null }
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
  const [filter, setFilter] = useState('pending')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [submitText, setSubmitText] = useState('')
  const [submitFile, setSubmitFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [msg, setMsg] = useState({ text: '', type: '' })
  const token = session?.user?.backendToken

  const load = useCallback(async () => {
    if (!token) return
    setLoading(true)
    const classId = localStorage.getItem('myClassId') || ''
    try {
      const [t, s] = await Promise.all([
        fetch(API + '/tasks?classId=' + classId, { headers: { Authorization: 'Bearer ' + token } }).then(r => r.json()),
        fetch(API + '/submissions', { headers: { Authorization: 'Bearer ' + token } }).then(r => r.json()),
      ])
      if (t.success) setTasks(t.data)
      if (s.success) setSubmissions(s.data)
    } catch (e) { console.error('Load error', e) }
    setLoading(false)
  }, [token])

  useEffect(() => { if (status !== 'loading' && token) load() }, [token, status, load])

  const getSub = (taskId: string) => submissions.find(s => s.taskId === taskId)

  const dl = (deadline?: string | null) => {
    if (!deadline) return { label: 'No deadline', color: 'text-slate-400' }
    const diff = new Date(deadline).getTime() - Date.now()
    const days = Math.ceil(diff / 86400000)
    if (diff < 0) return { label: 'Overdue', color: 'text-red-400' }
    if (days === 0) return { label: 'Due Today!', color: 'text-red-400' }
    if (days <= 2) return { label: days + 'd left', color: 'text-yellow-400' }
    return { label: days + ' days left', color: 'text-green-400' }
  }

  const fmt = (dt?: string | null) => dt ? new Date(dt).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true }) : 'No deadline'

  const pending = tasks.filter(t => !getSub(t.id))
  const submitted = tasks.filter(t => !!getSub(t.id) && getSub(t.id)?.status !== 'graded')
  const graded = tasks.filter(t => getSub(t.id)?.status === 'graded')

  const filtered = filter === 'pending' ? pending : filter === 'submitted' ? submitted : filter === 'graded' ? graded : tasks

  const handleSubmit = async () => {
    if (!selectedTask || !token) return
    if (!submitText.trim() && !submitFile) { setMsg({ text: 'Write an answer or attach a file', type: 'error' }); return }
    setSubmitting(true); setMsg({ text: '', type: '' })
    const fd = new FormData()
    fd.append('taskId', selectedTask.id)
    if (submitText.trim()) fd.append('textAnswer', submitText)
    if (submitFile) fd.append('file', submitFile)
    try {
      const res = await fetch(API + '/submissions', { method: 'POST', headers: { Authorization: 'Bearer ' + token }, body: fd })
      const data = await res.json()
      if (data.success) {
        setMsg({ text: 'Submitted successfully! ✓', type: 'success' })
        await load()
        setTimeout(() => { setSelectedTask(null); setSubmitText(''); setSubmitFile(null); setMsg({ text: '', type: '' }) }, 1500)
      } else { setMsg({ text: data.message || 'Failed', type: 'error' }) }
    } catch { setMsg({ text: 'Network error', type: 'error' }) }
    setSubmitting(false)
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-white mb-1">Assignments & Tasks</h1>
        <p className="text-slate-400 text-sm">View and submit your work</p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6">
        {[
          { l: 'Total', v: tasks.length, c: 'text-white', k: 'all' },
          { l: 'Pending', v: pending.length, c: 'text-yellow-400', k: 'pending' },
          { l: 'Submitted', v: submitted.length, c: 'text-blue-400', k: 'submitted' },
          { l: 'Graded', v: graded.length, c: 'text-green-400', k: 'graded' },
        ].map(s => (
          <button key={s.k} onClick={() => setFilter(s.k)} className={'rounded-2xl border p-4 text-center transition-all ' + (filter === s.k ? 'bg-slate-800 border-blue-500/30' : 'bg-slate-900 border-white/5 hover:border-white/10')}>
            <p className={'text-2xl font-bold ' + s.c}>{s.v}</p>
            <p className="text-xs text-slate-500 mt-1">{s.l}</p>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-16">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Loading tasks...</p>
        </div>
      ) : tasks.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-5xl mb-4">📋</p>
          <p className="text-white font-semibold mb-2">No tasks assigned yet</p>
          <p className="text-slate-500 text-sm">Make sure you've joined your class. Your teacher will assign tasks soon.</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">✅</p>
          <p className="text-white font-medium">Nothing here!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map(task => {
            const tc = typeConfig[task.taskType] || typeConfig.assignment
            const sub = getSub(task.id)
            const isGraded = sub?.status === 'graded'
            const daysLeft = dl(task.deadline)

            return (
              <div key={task.id} className={'rounded-2xl border p-5 transition-all ' + (isGraded ? 'bg-slate-900 border-green-500/20' : sub ? 'bg-slate-900 border-blue-500/20' : 'bg-slate-900 border-white/5 hover:border-white/10')}>
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-2xl flex-shrink-0">{tc.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex gap-2 mb-2 flex-wrap">
                      <span className={'text-[10px] px-2 py-0.5 rounded border font-medium ' + tc.color}>{tc.label}</span>
                      {isGraded ? <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-green-400 bg-green-500/10 border-green-500/20">✓ Graded</span>
                        : sub ? <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-blue-400 bg-blue-500/10 border-blue-500/20">📤 Submitted</span>
                        : <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-yellow-400 bg-yellow-500/10 border-yellow-500/20">Pending</span>}
                      {task.classSection && <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-slate-400 bg-slate-700 border-white/10">{task.classSection.name} {task.classSection.section}</span>}
                    </div>
                    <p className="text-sm font-semibold text-white">{task.title}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{task.subjectName || 'General'} · {task.creator.name} · {task.maxMarks} marks</p>
                  </div>
                  {isGraded && sub?.marksAwarded !== null && (
                    <div className="text-right flex-shrink-0">
                      <p className="text-2xl font-bold text-green-400">{sub?.marksAwarded}<span className="text-sm text-slate-500">/{task.maxMarks}</span></p>
                    </div>
                  )}
                </div>

                <div className="mt-4 bg-slate-800 rounded-xl p-3 border border-white/5 space-y-2 text-xs">
                  <div className="flex justify-between"><span className="text-slate-500">Deadline</span><span className="text-slate-300">{fmt(task.deadline)}</span></div>
                  <div className="h-px bg-white/5" />
                  <div className="flex justify-between">
                    <span className="text-slate-500">Status</span>
                    <span className={'font-medium ' + (sub ? 'text-green-400' : daysLeft.color)}>
                      {sub ? 'Submitted ' + new Date(sub.submittedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : daysLeft.label}
                    </span>
                  </div>
                  {task.instructions && <><div className="h-px bg-white/5" /><p className="text-slate-400">{task.instructions}</p></>}
                  {task.attachmentUrl && <><div className="h-px bg-white/5" /><a href={'http://localhost:5000' + task.attachmentUrl} target="_blank" className="text-blue-400 hover:text-blue-300">📎 View attachment</a></>}
                  {sub?.feedback && <><div className="h-px bg-white/5" /><p className="text-purple-400">💬 {sub.feedback}</p></>}
                </div>

                <div className="mt-4">
                  {!sub ? (
                    <button onClick={() => { setSelectedTask(task); setMsg({ text: '', type: '' }) }} className="w-full py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600">📤 Submit Now</button>
                  ) : isGraded ? (
                    <div className="w-full py-2.5 bg-green-500/10 text-green-400 border border-green-500/20 text-sm font-medium rounded-xl text-center">✓ Graded — {sub.marksAwarded}/{task.maxMarks} marks</div>
                  ) : (
                    <div className="w-full py-2.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 text-sm font-medium rounded-xl text-center">📤 Submitted — Awaiting grade</div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {selectedTask && (
        <div className="fixed inset-0 bg-black/85 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <div>
                <p className="text-sm font-semibold text-white">Submit: {selectedTask.title}</p>
                <p className="text-xs text-slate-500">{selectedTask.subjectName} · {selectedTask.maxMarks} marks · Due: {fmt(selectedTask.deadline)}</p>
              </div>
              <button onClick={() => { setSelectedTask(null); setSubmitText(''); setSubmitFile(null); setMsg({ text: '', type: '' }) }} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center">✕</button>
            </div>
            <div className="p-5 space-y-4">
              {selectedTask.instructions && (
                <div className="bg-blue-500/5 border border-blue-500/15 rounded-xl p-3">
                  <p className="text-xs text-blue-400 font-medium mb-1">📋 Instructions</p>
                  <p className="text-xs text-slate-400">{selectedTask.instructions}</p>
                </div>
              )}
              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Your Answer</label>
                <textarea value={submitText} onChange={e => setSubmitText(e.target.value)} placeholder="Write your answer here..." rows={5} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 resize-none" />
              </div>
              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Attach File</label>
                <div onClick={() => document.getElementById('sf')?.click()} className={'border-2 border-dashed rounded-xl p-5 text-center cursor-pointer ' + (submitFile ? 'border-green-500/50 bg-green-500/5' : 'border-white/10 hover:border-white/20')}>
                  <input id="sf" type="file" className="hidden" accept=".pdf,.doc,.docx,.jpg,.png,.zip" onChange={e => setSubmitFile(e.target.files?.[0] || null)} />
                  {submitFile ? <div><p className="text-green-400 text-2xl mb-1">✓</p><p className="text-sm text-white">{submitFile.name}</p></div>
                    : <div><p className="text-3xl mb-1">📎</p><p className="text-sm text-slate-400">Click to attach file</p></div>}
                </div>
              </div>
              {msg.text && <div className={'rounded-xl p-3 text-xs ' + (msg.type === 'error' ? 'bg-red-500/10 border border-red-500/20 text-red-400' : 'bg-green-500/10 border border-green-500/20 text-green-400')}>{msg.text}</div>}
              <button onClick={handleSubmit} disabled={submitting || msg.type === 'success'} className={'w-full py-3.5 text-white text-sm font-semibold rounded-xl transition-all ' + (msg.type === 'success' ? 'bg-green-500' : 'bg-blue-500 hover:bg-blue-600 disabled:opacity-40')}>
                {submitting ? 'Submitting...' : msg.type === 'success' ? '✓ Submitted!' : '📤 Submit Assignment'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Assignments done!")

# ═══════════════════════════════════════
# Teacher Results - class-wise + pending count
# ═══════════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/results", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/results/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect, useCallback } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Task = { id: string; title: string; subjectName?: string | null; maxMarks: number; taskType: string; classSection?: { name: string; section: string } | null; _count: { submissions: number } }
type Sub = {
  id: string; taskId: string; status: string; marksAwarded?: number | null; feedback?: string | null
  submittedAt: string; fileName?: string | null; fileUrl?: string | null; textAnswer?: string | null
  student: { name: string; email: string; rollNumber?: string | null; classSection?: { name: string; section: string } | null }
  task: { title: string; maxMarks: number; taskType: string; subjectName?: string | null }
}

export default function TeacherResultsPage() {
  const { data: session } = useSession()
  const [tasks, setTasks] = useState<Task[]>([])
  const [subs, setSubs] = useState<Sub[]>([])
  const [pendingSummary, setPendingSummary] = useState<{ totalPending: number; tasks: any[] }>({ totalPending: 0, tasks: [] })
  const [selTask, setSelTask] = useState<Task | null>(null)
  const [editId, setEditId] = useState<string | null>(null)
  const [editMarks, setEditMarks] = useState('')
  const [editFeedback, setEditFeedback] = useState('')
  const [saving, setSaving] = useState(false)
  const [view, setView] = useState<'pending'|'classwise'|'task'>('pending')
  const token = session?.user?.backendToken

  const load = useCallback(async () => {
    if (!token) return
    const headers = { Authorization: 'Bearer ' + token }
    const [t, p, allS] = await Promise.all([
      fetch(API + '/tasks', { headers }).then(r => r.json()),
      fetch(API + '/submissions/pending-summary', { headers }).then(r => r.json()),
      fetch(API + '/submissions', { headers }).then(r => r.json()),
    ])
    if (t.success) setTasks(t.data)
    if (p.success) setPendingSummary(p.data)
    if (allS.success) setSubs(allS.data)
  }, [token])

  useEffect(() => { load() }, [load])

  const loadTaskSubs = async (taskId: string) => {
    if (!token) return
    const s = await fetch(API + '/submissions?taskId=' + taskId, { headers: { Authorization: 'Bearer ' + token } }).then(r => r.json())
    if (s.success) setSubs(s.data)
  }

  const selectTask = (t: Task) => { setSelTask(t); setView('task'); setEditId(null); loadTaskSubs(t.id) }

  const taskSubs = selTask ? subs.filter(s => s.taskId === selTask.id) : []
  const graded = taskSubs.filter(s => s.marksAwarded !== null)

  // Class-wise grouping for overview
  const classGroups: Record<string, Sub[]> = {}
  subs.forEach(s => {
    const key = s.student.classSection ? s.student.classSection.name + ' ' + s.student.classSection.section : 'No Class'
    if (!classGroups[key]) classGroups[key] = []
    classGroups[key].push(s)
  })

  const getGradeColor = (m: number, max: number) => {
    const p = (m/max)*100
    return p >= 80 ? 'text-green-400' : p >= 60 ? 'text-blue-400' : p >= 40 ? 'text-yellow-400' : 'text-red-400'
  }

  const saveGrade = async (sub: Sub) => {
    if (!token || !editMarks) return
    setSaving(true)
    const res = await fetch(API + '/submissions/' + sub.id + '/grade', {
      method: 'PATCH', headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ marks: editMarks, feedback: editFeedback })
    })
    const data = await res.json()
    if (data.success) { await load(); if (selTask) await loadTaskSubs(selTask.id); setEditId(null) }
    setSaving(false)
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-white mb-1">Results & Grading</h1>
        <p className="text-slate-400 text-sm">Grade submissions and view results class-wise</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-2xl p-1.5 mb-6 w-fit">
        <button onClick={() => setView('pending')} className={'px-5 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-2 ' + (view === 'pending' ? 'bg-yellow-500 text-white' : 'text-slate-400 hover:text-white')}>
          ⏳ Pending to Grade {pendingSummary.totalPending > 0 && <span className="bg-white/20 px-1.5 rounded-full text-xs">{pendingSummary.totalPending}</span>}
        </button>
        <button onClick={() => setView('classwise')} className={'px-5 py-2.5 rounded-xl text-sm font-medium transition-all ' + (view === 'classwise' ? 'bg-purple-500 text-white' : 'text-slate-400 hover:text-white')}>
          🏫 Class-wise Results
        </button>
      </div>

      {/* Pending view */}
      {view === 'pending' && (
        <div>
          {pendingSummary.tasks.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">🎉</p>
              <p className="text-white font-medium">All caught up! No pending grading.</p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-2xl p-4 mb-4">
                <p className="text-sm text-yellow-400 font-semibold">⚠️ {pendingSummary.totalPending} submissions waiting to be graded across {pendingSummary.tasks.length} tasks</p>
              </div>
              {pendingSummary.tasks.map((t: any) => (
                <button key={t.taskId} onClick={() => { const fullTask = tasks.find(x => x.id === t.taskId); if (fullTask) selectTask(fullTask) }}
                  className="w-full bg-slate-900 rounded-xl border border-white/5 hover:border-yellow-500/30 p-4 text-left transition-all flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">{t.title}</p>
                    <p className="text-xs text-slate-500">{t.className} · {t.graded}/{t.totalSubmissions} graded</p>
                  </div>
                  <span className="text-xs px-3 py-1.5 bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded-full font-semibold">{t.pending} pending →</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Class-wise view */}
      {view === 'classwise' && (
        <div className="space-y-6">
          {Object.keys(classGroups).length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">📊</p>
              <p className="text-slate-400">No submissions yet</p>
            </div>
          ) : Object.entries(classGroups).map(([className, classSubs]) => {
            const classGraded = classSubs.filter(s => s.marksAwarded !== null)
            const avg = classGraded.length > 0 ? (classGraded.reduce((sum, s) => sum + (s.marksAwarded || 0), 0) / classGraded.length).toFixed(1) : '-'
            return (
              <div key={className} className="bg-slate-900 rounded-2xl border border-white/5 overflow-hidden">
                <div className="p-4 border-b border-white/5 flex items-center justify-between bg-slate-800/50">
                  <div>
                    <p className="text-sm font-semibold text-white">🏫 {className}</p>
                    <p className="text-xs text-slate-500">{classSubs.length} submissions · {classGraded.length} graded · Avg: {avg}</p>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-white/5">
                        {['Student', 'Roll No', 'Task', 'Marks', 'Grade', 'Status'].map(h => (
                          <th key={h} className="text-left px-4 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {classSubs.map((sub, i) => {
                        const pct = sub.marksAwarded !== null ? Math.round((sub.marksAwarded! / sub.task.maxMarks) * 100) : null
                        const grade = pct !== null ? (pct >= 80 ? 'A' : pct >= 60 ? 'B' : pct >= 40 ? 'C' : 'F') : '-'
                        return (
                          <tr key={sub.id} className={'border-b border-white/5 ' + (i%2===0 ? '' : 'bg-slate-800/20')}>
                            <td className="px-4 py-2.5 text-xs text-white">{sub.student.name}</td>
                            <td className="px-4 py-2.5 text-xs text-slate-400">{sub.student.rollNumber || '-'}</td>
                            <td className="px-4 py-2.5 text-xs text-slate-400">{sub.task.title}</td>
                            <td className="px-4 py-2.5 text-center"><span className={'text-sm font-semibold ' + (sub.marksAwarded !== null ? getGradeColor(sub.marksAwarded!, sub.task.maxMarks) : 'text-slate-500')}>{sub.marksAwarded !== null ? sub.marksAwarded + '/' + sub.task.maxMarks : 'N/A'}</span></td>
                            <td className="px-4 py-2.5 text-center"><span className={'text-sm font-bold ' + (sub.marksAwarded !== null ? getGradeColor(sub.marksAwarded!, sub.task.maxMarks) : 'text-slate-500')}>{grade}</span></td>
                            <td className="px-4 py-2.5"><span className={'text-[10px] px-2 py-0.5 rounded border ' + (sub.marksAwarded !== null ? 'text-green-400 bg-green-500/10 border-green-500/20' : 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20')}>{sub.marksAwarded !== null ? 'Graded' : 'Pending'}</span></td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Task grading view */}
      {view === 'task' && selTask && (
        <div>
          <button onClick={() => setView('pending')} className="text-xs text-blue-400 mb-4 hover:text-blue-300">← Back to pending list</button>
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-4 mb-4">
            <p className="text-sm font-semibold text-white">{selTask.title}</p>
            <p className="text-xs text-slate-500">{selTask.subjectName} · {graded.length}/{taskSubs.length} graded</p>
          </div>
          <div className="space-y-3">
            {taskSubs.map(sub => {
              const isEditing = editId === sub.id
              return (
                <div key={sub.id} className={'bg-slate-900 rounded-xl border p-4 ' + (isEditing ? 'border-blue-500/30' : 'border-white/5')}>
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-semibold flex-shrink-0">{sub.student.name.charAt(0)}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white">{sub.student.name}</p>
                      <p className="text-xs text-slate-500">{sub.student.rollNumber ? 'Roll: ' + sub.student.rollNumber + ' · ' : ''}{sub.student.email}</p>
                      {sub.textAnswer && <div className="mt-2 p-2.5 bg-slate-800 rounded-lg border border-white/5"><p className="text-xs text-slate-300">{sub.textAnswer}</p></div>}
                      {sub.fileUrl && <a href={'http://localhost:5000' + sub.fileUrl} target="_blank" className="mt-2 inline-block text-xs text-blue-400">📎 {sub.fileName}</a>}
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {sub.marksAwarded !== null && !isEditing && (
                        <p className={'text-lg font-bold ' + getGradeColor(sub.marksAwarded!, selTask.maxMarks)}>{sub.marksAwarded}<span className="text-sm text-slate-500">/{selTask.maxMarks}</span></p>
                      )}
                      {!isEditing && (
                        <button onClick={() => { setEditId(sub.id); setEditMarks(sub.marksAwarded?.toString() || ''); setEditFeedback(sub.feedback || '') }} className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg">
                          {sub.marksAwarded !== null ? '✏ Edit' : '+ Grade'}
                        </button>
                      )}
                    </div>
                  </div>
                  {isEditing && (
                    <div className="mt-3 ml-13 space-y-3 pt-3 border-t border-white/5">
                      <div className="flex gap-3">
                        <input type="number" value={editMarks} onChange={e => setEditMarks(e.target.value)} min={0} max={selTask.maxMarks} autoFocus placeholder={'/' + selTask.maxMarks} className="w-24 bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white outline-none" />
                        <input type="text" value={editFeedback} onChange={e => setEditFeedback(e.target.value)} placeholder="Feedback..." className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white outline-none" />
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => saveGrade(sub)} disabled={!editMarks || saving} className="px-4 py-1.5 bg-blue-500 text-white text-xs font-medium rounded-lg disabled:opacity-40">{saving ? 'Saving...' : '✓ Save & Notify'}</button>
                        <button onClick={() => setEditId(null)} className="px-4 py-1.5 bg-slate-800 text-slate-400 text-xs rounded-lg">Cancel</button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Teacher Results done!")

print("\n=== FRONTEND DONE ===")