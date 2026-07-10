import os

API = "process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'"

# ════════════════════════════════════════
# Student Join Class Page (with code)
# ════════════════════════════════════════
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
  const { data: session } = useSession()
  const router = useRouter()
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [selected, setSelected] = useState('')
  const [codeInput, setCodeInput] = useState('')
  const [mode, setMode] = useState<'browse' | 'code'>('code')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    fetch(API + '/auth/classes', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(data => { if (data.success) setClasses(data.data); setLoading(false) })
  }, [token])

  const handleJoinByCode = async () => {
    if (!codeInput.trim() || !token) return
    setSaving(true)
    setError('')
    const res = await fetch(API + '/auth/join-class', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: codeInput.toUpperCase() })
    })
    const data = await res.json()
    if (data.success) {
      setSuccess('Joined ' + data.data.class.name + ' Section ' + data.data.class.section + '!')
      localStorage.setItem('studentClassSelected', 'true')
      setTimeout(() => router.push('/student'), 1500)
    } else {
      setError(data.message || 'Invalid code')
    }
    setSaving(false)
  }

  const handleSelectFromList = async () => {
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
    const key = c.branch + ' Sem ' + c.semester
    if (!acc[key]) acc[key] = []
    acc[key].push(c)
    return acc
  }, {} as Record<string, ClassSection[]>)

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center text-3xl mx-auto mb-4">🎓</div>
          <h1 className="text-2xl font-semibold text-white mb-2">Join Your Class</h1>
          <p className="text-slate-400 text-sm">Enter the unique class code given by your teacher</p>
        </div>

        {/* Mode Toggle */}
        <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-xl p-1 mb-6">
          <button onClick={() => setMode('code')} className={'flex-1 py-2 rounded-lg text-sm font-medium transition-all ' + (mode === 'code' ? 'bg-green-500 text-white' : 'text-slate-400 hover:text-white')}>
            🔑 Enter Class Code
          </button>
          <button onClick={() => setMode('browse')} className={'flex-1 py-2 rounded-lg text-sm font-medium transition-all ' + (mode === 'browse' ? 'bg-green-500 text-white' : 'text-slate-400 hover:text-white')}>
            📋 Browse Classes
          </button>
        </div>

        {mode === 'code' && (
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
            <label className="block text-xs text-slate-500 uppercase tracking-wider mb-3">Class Code</label>
            <input
              type="text"
              value={codeInput}
              onChange={e => { setCodeInput(e.target.value.toUpperCase()); setError('') }}
              onKeyDown={e => e.key === 'Enter' && handleJoinByCode()}
              placeholder="e.g. CSE-A1B2C3"
              className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-4 text-lg font-mono text-white outline-none focus:border-green-500/50 placeholder:text-slate-600 text-center tracking-widest mb-4"
            />
            {error && <p className="text-xs text-red-400 text-center mb-3">{error}</p>}
            {success && <p className="text-xs text-green-400 text-center mb-3">✓ {success}</p>}
            <button
              onClick={handleJoinByCode}
              disabled={!codeInput.trim() || saving}
              className="w-full py-3 bg-green-500 text-white text-sm font-medium rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center justify-center gap-2 mb-3"
            >
              {saving ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Joining...</> : '🚀 Join Class'}
            </button>
            <button onClick={() => { localStorage.setItem('studentClassSelected', 'true'); router.push('/student') }} className="w-full py-2 text-slate-500 text-xs hover:text-slate-300 transition-colors">
              Skip for now — I don't have a code yet
            </button>
          </div>
        )}

        {mode === 'browse' && (
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
            {loading ? (
              <div className="text-center py-8"><div className="w-6 h-6 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
            ) : classes.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-3xl mb-2">⏳</p>
                <p className="text-white font-medium mb-1">No classes available</p>
                <p className="text-slate-400 text-sm mb-4">Ask your teacher for the class code</p>
                <button onClick={() => setMode('code')} className="px-4 py-2 bg-green-500 text-white text-sm rounded-xl">Enter Code Instead</button>
              </div>
            ) : (
              <>
                <div className="space-y-4 max-h-[350px] overflow-y-auto pr-1 mb-4">
                  {Object.entries(grouped).map(([group, groupClasses]) => (
                    <div key={group}>
                      <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{group}</p>
                      <div className="space-y-2">
                        {groupClasses.map(c => (
                          <button key={c.id} onClick={() => setSelected(c.id)} className={'w-full p-3 rounded-xl border text-left transition-all ' + (selected === c.id ? 'border-green-500/50 bg-green-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm font-medium text-white">{c.name} — Section {c.section}</p>
                                <p className="text-xs text-slate-500 mt-0.5">{c.branch} · Sem {c.semester} · {c._count.students} students</p>
                              </div>
                              <span className="text-xs font-mono text-green-400 bg-green-500/10 px-2 py-1 rounded border border-green-500/20">{c.uniqueCode}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex gap-3">
                  <button onClick={() => { localStorage.setItem('studentClassSelected', 'true'); router.push('/student') }} className="px-4 py-2.5 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">Skip</button>
                  <button onClick={handleSelectFromList} disabled={!selected || saving} className="flex-1 py-2.5 bg-green-500 text-white text-sm font-medium rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center justify-center gap-2">
                    {saving ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Joining...</> : 'Join Class'}
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
""")
print("Select Class page done!")

# ════════════════════════════════════════
# Teacher Class Management Page
# ════════════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/classes", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/classes/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type ClassSection = {
  id: string
  name: string
  section: string
  branch: string
  semester: number
  year: number
  uniqueCode: string
  isActive: boolean
  _count: { students: number }
}

export default function ClassesPage() {
  const { data: session } = useSession()
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', section: 'A', semester: '1', branch: 'CSE', year: new Date().getFullYear().toString() })
  const [creating, setCreating] = useState(false)
  const [copied, setCopied] = useState('')

  const token = session?.user?.backendToken

  const fetchClasses = async () => {
    if (!token) return
    const res = await fetch(API + '/auth/classes', { headers: { Authorization: 'Bearer ' + token } })
    const data = await res.json()
    if (data.success) setClasses(data.data)
    setLoading(false)
  }

  useEffect(() => { if (token) fetchClasses() }, [token])

  const handleCreate = async () => {
    if (!form.name || !token) return
    setCreating(true)
    const res = await fetch(API + '/auth/classes', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    const data = await res.json()
    if (data.success) { await fetchClasses(); setShowCreate(false); setForm({ name: '', section: 'A', semester: '1', branch: 'CSE', year: new Date().getFullYear().toString() }) }
    setCreating(false)
  }

  const handleDelete = async (id: string) => {
    if (!token || !confirm('Delete this class?')) return
    await fetch(API + '/auth/classes/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } })
    fetchClasses()
  }

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopied(code)
    setTimeout(() => setCopied(''), 2000)
  }

  const grouped = classes.reduce((acc, c) => {
    const key = c.branch + ' — Sem ' + c.semester
    if (!acc[key]) acc[key] = []
    acc[key].push(c)
    return acc
  }, {} as Record<string, ClassSection[]>)

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Class Management</h1>
          <p className="text-slate-400 text-sm">Create classes and share unique codes with students</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 transition-all">+ Create Class</button>
      </div>

      {/* Info box */}
      <div className="bg-blue-500/5 border border-blue-500/15 rounded-xl p-4 flex gap-3 mb-6">
        <span className="text-blue-400 text-lg">ℹ️</span>
        <div>
          <p className="text-sm font-medium text-white mb-1">How it works</p>
          <p className="text-xs text-slate-400 leading-relaxed">
            Create a class and share its unique code with students. Students enter this code to join your class.
            Tasks assigned to a class will only be visible to students in that class.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : classes.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">🏫</p>
          <p className="text-white font-medium mb-1">No classes created yet</p>
          <p className="text-slate-500 text-sm mb-4">Create your first class to get started</p>
          <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-blue-500 text-white text-sm rounded-xl hover:bg-blue-600">Create First Class</button>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([group, groupClasses]) => (
            <div key={group}>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">{group}</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {groupClasses.map(c => (
                  <div key={c.id} className="bg-slate-900 rounded-2xl border border-white/5 hover:border-white/10 transition-all p-5">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-sm font-semibold text-white">{c.name} — Section {c.section}</h3>
                        <p className="text-xs text-slate-500 mt-0.5">{c.branch} · Semester {c.semester} · {c.year}</p>
                      </div>
                      <button onClick={() => handleDelete(c.id)} className="text-slate-600 hover:text-red-400 transition-colors text-sm w-7 h-7 flex items-center justify-center rounded-lg hover:bg-red-500/10">✕</button>
                    </div>

                    {/* Unique Code */}
                    <div className="bg-slate-800 rounded-xl p-3 border border-white/5 mb-4">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Unique Class Code</p>
                      <div className="flex items-center justify-between">
                        <span className="text-lg font-mono font-bold text-green-400 tracking-widest">{c.uniqueCode}</span>
                        <button
                          onClick={() => copyCode(c.uniqueCode)}
                          className={'text-xs px-3 py-1.5 rounded-lg transition-all ' + (copied === c.uniqueCode ? 'bg-green-500 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600')}
                        >
                          {copied === c.uniqueCode ? '✓ Copied!' : '📋 Copy'}
                        </button>
                      </div>
                      <p className="text-[10px] text-slate-600 mt-1">Share this code with your students</p>
                    </div>

                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">{c._count.students} students enrolled</span>
                      <span className="text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full">Active</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-md">
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <p className="text-sm font-medium text-white">Create New Class</p>
              <button onClick={() => setShowCreate(false)} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center">✕</button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Class / Programme Name</label>
                <input type="text" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} placeholder="e.g. B.Tech, BCA, MCA" className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Branch</label>
                  <select value={form.branch} onChange={e => setForm(p => ({ ...p, branch: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50">
                    {['CSE', 'ECE', 'ME', 'CE', 'IT', 'EE', 'MCA', 'BCA', 'MBA', 'Other'].map(b => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Semester</label>
                  <select value={form.semester} onChange={e => setForm(p => ({ ...p, semester: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50">
                    {['1','2','3','4','5','6','7','8'].map(s => <option key={s} value={s}>Sem {s}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Section</label>
                  <div className="grid grid-cols-4 gap-1">
                    {['A', 'B', 'C', 'D'].map(s => (
                      <button key={s} onClick={() => setForm(p => ({ ...p, section: s }))} className={'py-2 rounded-xl text-xs font-medium border transition-all ' + (form.section === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Year</label>
                  <select value={form.year} onChange={e => setForm(p => ({ ...p, year: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50">
                    {['2024','2025','2026','2027','2028'].map(y => <option key={y} value={y}>{y}</option>)}
                  </select>
                </div>
              </div>

              <div className="bg-slate-800 rounded-xl p-3 border border-white/5">
                <p className="text-xs text-slate-500">A unique class code will be auto-generated and shown after creation. Share it with your students.</p>
              </div>

              <button onClick={handleCreate} disabled={!form.name || creating} className="w-full py-3 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40 flex items-center justify-center gap-2">
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
print("Classes page done!")

# ════════════════════════════════════════
# My Papers Upload - backend connected
# ════════════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/papers", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/papers/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type Paper = {
  id: string
  title: string
  subject: string
  year?: number | null
  examType?: string | null
  fileType: string
  fileSizeKb?: number | null
  fileUrl: string
  fileName: string
  isPyq: boolean
  createdAt: string
  uploader: { name: string }
}

const SUBJECTS = [
  'Data Structures and Algorithms', 'Operating Systems', 'Computer Networks',
  'Database Management Systems', 'Software Engineering', 'Artificial Intelligence',
  'Machine Learning', 'Web Technologies', 'Object Oriented Programming', 'Discrete Mathematics',
]

export default function MyPapersPage() {
  const { data: session } = useSession()
  const [papers, setPapers] = useState<Paper[]>([])
  const [loading, setLoading] = useState(true)
  const [filterSubject, setFilterSubject] = useState('all')
  const [filterYear, setFilterYear] = useState('all')
  const [filterExam, setFilterExam] = useState('all')
  const [showUpload, setShowUpload] = useState(false)
  const [uploadStep, setUploadStep] = useState(1)
  const [uploadSubject, setUploadSubject] = useState('')
  const [uploadYear, setUploadYear] = useState('')
  const [uploadExamType, setUploadExamType] = useState('')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [previewUrl, setPreviewUrl] = useState('')
  const [previewPaper, setPreviewPaper] = useState<Paper | null>(null)

  const token = session?.user?.backendToken

  const fetchPapers = async () => {
    if (!token) return
    const res = await fetch(API + '/materials?isPyq=true', { headers: { Authorization: 'Bearer ' + token } })
    const data = await res.json()
    if (data.success) setPapers(data.data)
    setLoading(false)
  }

  useEffect(() => { if (token) fetchPapers() }, [token])

  const allSubjects = Array.from(new Set(papers.map(p => p.subject).filter(Boolean)))
  const allYears = Array.from(new Set(papers.map(p => p.year?.toString()).filter(Boolean))).sort((a,b) => (b||'').localeCompare(a||''))

  const filtered = papers.filter(p => {
    if (filterSubject !== 'all' && p.subject !== filterSubject) return false
    if (filterYear !== 'all' && p.year?.toString() !== filterYear) return false
    if (filterExam !== 'all' && p.examType !== filterExam) return false
    return true
  })

  const examLabel = (t?: string | null) => t === 'end_term' ? 'End Term' : t === 'mid_term' ? 'Mid Term' : t === 'unit_test' ? 'Unit Test' : t || 'Paper'
  const examColor = (t?: string | null) => t === 'end_term' ? 'text-blue-400 bg-blue-500/10 border-blue-500/20' : t === 'mid_term' ? 'text-purple-400 bg-purple-500/10 border-purple-500/20' : 'text-green-400 bg-green-500/10 border-green-500/20'

  const handleUpload = async () => {
    if (!uploadFile || !uploadSubject || !token) return
    setUploading(true)
    const fd = new FormData()
    fd.append('file', uploadFile)
    fd.append('title', uploadFile.name.replace(/\\.pdf$/i, ''))
    fd.append('fileType', 'pyq')
    fd.append('isPyq', 'true')
    fd.append('subject', uploadSubject)
    if (uploadYear) fd.append('year', uploadYear)
    if (uploadExamType) fd.append('examType', uploadExamType)

    const res = await fetch(API + '/materials/upload', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token },
      body: fd,
    })
    const data = await res.json()
    if (data.success) {
      await fetchPapers()
      setShowUpload(false)
      setUploadStep(1)
      setUploadFile(null)
      setUploadSubject('')
      setUploadYear('')
      setUploadExamType('')
    }
    setUploading(false)
  }

  const handleDownload = async (paper: Paper) => {
    if (!token) return
    const res = await fetch(API + '/materials/' + paper.id + '/download', {
      headers: { Authorization: 'Bearer ' + token }
    })
    if (res.headers.get('content-type')?.includes('application/json')) {
      const data = await res.json()
      if (data.data?.fileUrl) window.open('http://localhost:5000' + data.data.fileUrl, '_blank')
    } else {
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = paper.fileName; a.click()
      URL.revokeObjectURL(url)
    }
  }

  const handlePreview = async (paper: Paper) => {
    if (!token) return
    setPreviewPaper(paper)
    const url = 'http://localhost:5000' + paper.fileUrl
    setPreviewUrl(url)
  }

  const handleDelete = async (id: string) => {
    if (!token || !confirm('Delete this paper?')) return
    await fetch(API + '/materials/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } })
    fetchPapers()
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">My Papers</h1>
          <p className="text-slate-400 text-sm">Upload and manage previous year question papers</p>
        </div>
        <button onClick={() => setShowUpload(true)} className="px-4 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 transition-all">+ Upload PYQ</button>
      </div>

      {/* Filters */}
      <div className="bg-slate-900 rounded-2xl border border-white/5 p-5 mb-6 space-y-4">
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Filter by Subject</p>
          <div className="flex gap-2 flex-wrap">
            <button onClick={() => { setFilterSubject('all'); setFilterYear('all'); setFilterExam('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterSubject === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
              All <span className="opacity-60 ml-1">{papers.length}</span>
            </button>
            {allSubjects.map(s => (
              <button key={s} onClick={() => { setFilterSubject(s); setFilterYear('all'); setFilterExam('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterSubject === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                {s.length > 25 ? s.slice(0,25)+'...' : s} <span className="opacity-60 ml-1">{papers.filter(p => p.subject === s).length}</span>
              </button>
            ))}
          </div>
        </div>
        {filterSubject !== 'all' && allYears.length > 0 && (
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Filter by Year</p>
            <div className="flex gap-2 flex-wrap">
              <button onClick={() => { setFilterYear('all'); setFilterExam('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterYear === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>All Years</button>
              {allYears.map(y => (
                <button key={y} onClick={() => { setFilterYear(y || ''); setFilterExam('all') }} className={'px-4 py-1.5 rounded-lg text-sm font-medium border transition-all ' + (filterYear === y ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                  {y} <span className="opacity-60 ml-1">{papers.filter(p => p.year?.toString() === y && p.subject === filterSubject).length}</span>
                </button>
              ))}
            </div>
          </div>
        )}
        {filterYear !== 'all' && (
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Filter by Exam Type</p>
            <div className="flex gap-2">
              <button onClick={() => setFilterExam('all')} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterExam === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>All</button>
              {['end_term', 'mid_term', 'unit_test'].map(t => (
                <button key={t} onClick={() => setFilterExam(t)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterExam === t ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>{examLabel(t)}</button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Papers */}
      {loading ? (
        <div className="text-center py-12"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">📭</p>
          <p className="text-white font-medium mb-1">No papers found</p>
          <p className="text-slate-500 text-sm mb-4">Upload your first PYQ</p>
          <button onClick={() => setShowUpload(true)} className="px-4 py-2 bg-blue-500 text-white text-sm rounded-xl hover:bg-blue-600">Upload PYQ</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map(paper => (
            <div key={paper.id} className="bg-slate-900 rounded-2xl border border-white/5 hover:border-white/10 transition-all p-5">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-2xl flex-shrink-0">📋</div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate mb-1">{paper.fileName}</p>
                  <div className="flex gap-2 flex-wrap">
                    {paper.examType && <span className={'text-[10px] px-2 py-0.5 rounded border font-medium ' + examColor(paper.examType)}>{examLabel(paper.examType)}</span>}
                    {paper.year && <span className="text-xs text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded">{paper.year}</span>}
                  </div>
                  <p className="text-xs text-slate-500 mt-1 truncate">{paper.subject} · {paper.fileSizeKb ? (paper.fileSizeKb / 1024).toFixed(1) + ' MB' : ''}</p>
                </div>
              </div>
              <div className="flex gap-2 pt-3 border-t border-white/5">
                <span className="text-xs text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full">✓ Ready</span>
                <div className="flex-1" />
                <button onClick={() => handlePreview(paper)} className="text-xs px-3 py-1.5 bg-slate-800 text-slate-300 border border-white/10 rounded-lg hover:border-white/20 transition-all">👁 View</button>
                <button onClick={() => handleDownload(paper)} className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all">⬇ Download</button>
                <button onClick={() => handleDelete(paper.id)} className="text-xs px-3 py-1.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-all">Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewPaper && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-5xl h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-white/5">
              <div>
                <p className="text-sm font-medium text-white">{previewPaper.fileName}</p>
                <p className="text-xs text-slate-500">{previewPaper.subject} · {previewPaper.year}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleDownload(previewPaper)} className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20">⬇ Download</button>
                <button onClick={() => { setPreviewPaper(null); setPreviewUrl('') }} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center text-lg">✕</button>
              </div>
            </div>
            <div className="flex-1 overflow-hidden rounded-b-2xl">
              {previewUrl ? (
                <iframe src={previewUrl} className="w-full h-full" title={previewPaper.fileName} />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p className="text-slate-400">Loading preview...</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <div>
                <p className="text-sm font-medium text-white">Upload PYQ</p>
                <p className="text-xs text-slate-500">Step {uploadStep} of 3</p>
              </div>
              <button onClick={() => { setShowUpload(false); setUploadStep(1) }} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center">✕</button>
            </div>
            <div className="flex px-5 pt-4 gap-1">
              {['Subject', 'Year & Type', 'File'].map((label, i) => (
                <div key={i} className="flex-1">
                  <div className={'h-1 rounded-full ' + (uploadStep > i ? 'bg-blue-500' : 'bg-slate-700')} />
                  <p className={'text-[10px] mt-1 ' + (uploadStep === i+1 ? 'text-blue-400' : 'text-slate-600')}>{label}</p>
                </div>
              ))}
            </div>
            <div className="p-5">
              {uploadStep === 1 && (
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-3">Select Subject</label>
                  <select value={uploadSubject} onChange={e => setUploadSubject(e.target.value)} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 mb-4">
                    <option value="">-- Select Subject --</option>
                    {SUBJECTS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <button onClick={() => setUploadStep(2)} disabled={!uploadSubject} className="w-full py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed">Next: Select Year</button>
                </div>
              )}
              {uploadStep === 2 && (
                <div>
                  <div className="mb-5">
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Year</label>
                    <div className="grid grid-cols-3 gap-2">
                      {['2025','2024','2023','2022','2021','2020'].map(y => (
                        <button key={y} onClick={() => setUploadYear(y)} className={'py-2 rounded-xl text-sm font-medium border transition-all ' + (uploadYear === y ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>{y}</button>
                      ))}
                    </div>
                  </div>
                  <div className="mb-5">
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Exam Type</label>
                    <div className="grid grid-cols-3 gap-2">
                      {[['end_term','End Term'],['mid_term','Mid Term'],['unit_test','Unit Test']].map(([val, label]) => (
                        <button key={val} onClick={() => setUploadExamType(val)} className={'py-2 rounded-xl text-sm font-medium border transition-all ' + (uploadExamType === val ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>{label}</button>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <button onClick={() => setUploadStep(1)} className="px-5 py-2.5 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">Back</button>
                    <button onClick={() => setUploadStep(3)} disabled={!uploadYear || !uploadExamType} className="flex-1 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40">Next: Upload File</button>
                  </div>
                </div>
              )}
              {uploadStep === 3 && (
                <div>
                  <div className="bg-slate-800 rounded-xl p-3 mb-4 border border-white/5">
                    <p className="text-xs text-white mb-1">{uploadSubject}</p>
                    <div className="flex gap-2">
                      <span className="text-[10px] text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">{uploadYear}</span>
                      <span className="text-[10px] text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">{uploadExamType.replace('_', ' ')}</span>
                    </div>
                  </div>
                  <div onDrop={e => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if(f) setUploadFile(f) }} onDragOver={e => { e.preventDefault(); setDragOver(true) }} onDragLeave={() => setDragOver(false)} onClick={() => document.getElementById('pyq-file')?.click()} className={'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all mb-4 ' + (dragOver ? 'border-blue-500 bg-blue-500/5' : uploadFile ? 'border-green-500/50 bg-green-500/5' : 'border-white/10 hover:border-white/20')}>
                    <input id="pyq-file" type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={e => setUploadFile(e.target.files?.[0] || null)} />
                    {uploadFile ? (
                      <div><p className="text-green-400 text-3xl mb-2">✓</p><p className="text-sm font-medium text-white">{uploadFile.name}</p><p className="text-xs text-slate-500 mt-1">{(uploadFile.size/1024/1024).toFixed(1)} MB</p></div>
                    ) : (
                      <div><p className="text-4xl mb-2">📁</p><p className="text-sm text-slate-400">Drop PDF here or click to browse</p></div>
                    )}
                  </div>
                  <div className="flex gap-3">
                    <button onClick={() => setUploadStep(2)} className="px-5 py-2.5 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">Back</button>
                    <button onClick={handleUpload} disabled={!uploadFile || uploading} className="flex-1 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40 flex items-center justify-center gap-2">
                      {uploading ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Uploading...</> : 'Upload PYQ'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("My Papers page done!")

# ════════════════════════════════════════
# Update Sidebar - add Classes link
# ════════════════════════════════════════
with open("../frontend/components/ui/Sidebar.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useSession, signOut } from 'next-auth/react'

const teacherLinks = [
  { href: '/teacher', icon: '🏠', label: 'Dashboard' },
  { href: '/teacher/generate', icon: '🤖', label: 'Generate Questions' },
  { href: '/teacher/classes', icon: '🏫', label: 'Class Management' },
  { href: '/teacher/tasks', icon: '📋', label: 'Tasks' },
  { href: '/teacher/papers', icon: '📄', label: 'My Papers' },
  { href: '/teacher/results', icon: '📊', label: 'Results & Grading' },
  { href: '/teacher/materials', icon: '📚', label: 'Materials' },
  { href: '/teacher/subjects', icon: '📖', label: 'My Subjects' },
  { href: '/teacher/notifications', icon: '🔔', label: 'Notifications' },
  { href: '/teacher/complaints', icon: '💬', label: 'Complaints' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)
  const { data: session } = useSession()

  return (
    <aside className={`${collapsed ? 'w-[70px]' : 'w-[240px]'} transition-all duration-300 bg-slate-900 border-r border-white/5 flex flex-col min-h-screen flex-shrink-0`}>
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center text-white font-bold">✦</div>
            <span className="text-sm font-semibold text-white">AIQPG</span>
          </div>
        )}
        {collapsed && <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center text-white font-bold mx-auto">✦</div>}
        {!collapsed && <button onClick={() => setCollapsed(true)} className="text-slate-500 hover:text-white text-sm">◀</button>}
      </div>
      {collapsed && <button onClick={() => setCollapsed(false)} className="text-slate-500 hover:text-white p-3 text-center text-sm">▶</button>}

      {!collapsed && (
        <div className="px-4 py-2">
          <span className="text-xs font-medium text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-1 rounded-md uppercase tracking-wider">Teacher</span>
        </div>
      )}

      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {teacherLinks.map(link => {
          const isActive = pathname === link.href
          return (
            <Link key={link.href} href={link.href} className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-all ${isActive ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}>
              <span className="text-base flex-shrink-0">{link.icon}</span>
              {!collapsed && <span className="flex-1 truncate text-xs">{link.label}</span>}
            </Link>
          )
        })}
      </nav>

      <div className="p-3 border-t border-white/5">
        {!collapsed ? (
          <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 transition-all">
            {session?.user?.image ? (
              <img src={session.user.image} alt="" className="w-9 h-9 rounded-full object-cover border border-white/10 flex-shrink-0" />
            ) : (
              <div className="w-9 h-9 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-sm font-semibold flex-shrink-0">
                {session?.user?.name?.charAt(0)?.toUpperCase() || 'T'}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-white truncate">{session?.user?.name || 'Teacher'}</p>
              <p className="text-[10px] text-slate-500 truncate">{session?.user?.email || ''}</p>
            </div>
            <button onClick={() => signOut({ callbackUrl: '/login' })} className="text-slate-600 hover:text-red-400 transition-colors text-sm flex-shrink-0">🚪</button>
          </div>
        ) : (
          <div className="flex justify-center">
            {session?.user?.image ? (
              <img src={session.user.image} alt="" className="w-9 h-9 rounded-full object-cover border border-white/10" />
            ) : (
              <div className="w-9 h-9 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-sm font-semibold">T</div>
            )}
          </div>
        )}
      </div>
    </aside>
  )
}
""")
print("Sidebar done!")

# ════════════════════════════════════════
# AI Chatbot - connected to Claude
# ════════════════════════════════════════
os.makedirs("../frontend/app/(student)/student/chatbot", exist_ok=True)
with open("../frontend/app/(student)/student/chatbot/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useRef, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type Message = {
  id: number
  role: 'user' | 'assistant'
  content: string
  time: string
}

const SUBJECTS = [
  'Data Structures and Algorithms', 'Operating Systems', 'Computer Networks',
  'Database Management Systems', 'Software Engineering', 'Artificial Intelligence',
  'Machine Learning', 'Web Technologies', 'Object Oriented Programming', 'Discrete Mathematics',
]

export default function ChatbotPage() {
  const { data: session } = useSession()
  const [subject, setSubject] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<{role: string; content: string}[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const token = session?.user?.backendToken

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const startSubject = (s: string) => {
    setSubject(s)
    const welcome = { id: 1, role: 'assistant' as const, content: `Hello! I am your AI study assistant powered by Claude AI. I am here to help you with **${s}**. I can explain concepts, solve problems, generate practice questions, and help you prepare for exams. What would you like to learn today?`, time: 'Now' }
    setMessages([welcome])
    setHistory([{ role: 'assistant', content: welcome.content }])
  }

  const sendMessage = async () => {
    if (!input.trim() || !subject || loading || !token) return
    const userMsg: Message = { id: Date.now(), role: 'user', content: input, time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }) }
    const newHistory = [...history, { role: 'user', content: input }]
    setMessages(prev => [...prev, userMsg])
    setHistory(newHistory)
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(API + '/ai/chat', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, subject, history: history.slice(-10) })
      })
      const data = await res.json()
      const reply = data.success ? data.data.reply : 'Sorry, I could not process that. Please try again.'
      const botMsg: Message = { id: Date.now() + 1, role: 'assistant', content: reply, time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }) }
      setMessages(prev => [...prev, botMsg])
      setHistory([...newHistory, { role: 'assistant', content: reply }])
    } catch (e) {
      const errMsg: Message = { id: Date.now() + 1, role: 'assistant', content: 'Connection error. Please check your internet and try again.', time: 'Now' }
      setMessages(prev => [...prev, errMsg])
    }
    setLoading(false)
  }

  const suggestions = [
    'Explain with a simple example',
    'Give me practice questions',
    'What are the key topics for exam?',
    'Explain the difference between...',
    'Write pseudocode for...',
  ]

  const formatMessage = (text: string) => {
    return text
      .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
      .replace(/\\*(.+?)\\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code class="bg-slate-700 px-1 py-0.5 rounded text-green-400 text-xs">$1</code>')
      .replace(/\\n/g, '<br/>')
  }

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold text-white mb-1">AI Study Assistant</h1>
        <p className="text-slate-400 text-sm">Powered by Claude AI — Ask anything about your subjects</p>
      </div>

      {!subject ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-full max-w-lg">
            <div className="text-center mb-8">
              <div className="w-20 h-20 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-4xl mx-auto mb-4">🤖</div>
              <h2 className="text-lg font-semibold text-white mb-2">Select a Subject to Start</h2>
              <p className="text-slate-400 text-sm">I will use Claude AI to give you accurate, detailed answers</p>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {SUBJECTS.map(s => (
                <button key={s} onClick={() => startSubject(s)} className="p-4 bg-slate-900 rounded-xl border border-white/5 hover:border-blue-500/30 hover:bg-blue-500/5 transition-all text-left flex items-center gap-3">
                  <span className="text-2xl">📚</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white">{s}</p>
                  </div>
                  <span className="text-blue-400 text-sm">→</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-3 mb-4 bg-slate-900 rounded-xl border border-white/5 p-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-lg">🤖</div>
            <div className="flex-1">
              <p className="text-xs font-medium text-white">Claude AI — {subject}</p>
              <p className="text-[10px] text-green-400">● Online</p>
            </div>
            <button onClick={() => { setSubject(''); setMessages([]); setHistory([]) }} className="text-xs text-slate-400 hover:text-white px-3 py-1.5 bg-slate-800 rounded-lg border border-white/5">Change Subject</button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 mb-4 bg-slate-900 rounded-2xl border border-white/5 p-4">
            {messages.map(msg => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                  {msg.role === 'assistant' && (
                    <div className="flex items-center gap-1.5 mb-1">
                      <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-sm">🤖</div>
                      <span className="text-[10px] text-slate-500">Claude AI</span>
                    </div>
                  )}
                  <div
                    className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-blue-500 text-white rounded-br-sm' : 'bg-slate-800 text-slate-200 border border-white/5 rounded-bl-sm'}`}
                    dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
                  />
                  <p className="text-[10px] text-slate-600 px-1">{msg.time}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-1.5 mb-1">
                  <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-sm">🤖</div>
                </div>
                <div className="bg-slate-800 border border-white/5 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1 ml-2">
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {messages.length <= 1 && (
            <div className="flex gap-2 flex-wrap mb-3">
              {suggestions.slice(0, 4).map(s => (
                <button key={s} onClick={() => setInput(s)} className="text-xs px-3 py-1.5 bg-slate-900 text-slate-400 border border-white/5 rounded-lg hover:border-blue-500/30 hover:text-blue-400 transition-all">{s}</button>
              ))}
            </div>
          )}

          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder={`Ask anything about ${subject}...`}
              className="flex-1 bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600"
            />
            <button onClick={sendMessage} disabled={!input.trim() || loading} className="px-5 py-3 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 transition-all disabled:opacity-40">Send</button>
          </div>
        </>
      )}
    </div>
  )
}
""")
print("AI Chatbot done!")

print("\n" + "="*60)
print("ALL FRONTEND FIXES COMPLETE!")
print("="*60)