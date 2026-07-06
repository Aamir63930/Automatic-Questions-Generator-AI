import os

# ══════════════════════════════════════════════
# FIX 1: Generate Questions - Units from uploaded materials (dynamic)
# + Edit/Delete questions
# ══════════════════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/generate", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/generate/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

const ALL_SUBJECTS = [
  'Data Structures and Algorithms', 'Operating Systems', 'Computer Networks',
  'Database Management Systems', 'Software Engineering', 'Artificial Intelligence',
  'Machine Learning', 'Web Technologies', 'Object Oriented Programming',
  'Discrete Mathematics', 'Computer Organization', 'Theory of Computation',
  'Compiler Design', 'Digital Electronics', 'Mathematics', 'Physics',
  'Chemistry', 'English', 'Management', 'Other',
]

type Section = { name: string; total: number; attempt: number; marks: number }
type Question = { id: number; section: string; questionNo: number; text: string; marks: number; unit: string; difficulty: string; type: string; selected: boolean; editing?: boolean }

const sectionColors: Record<string, string> = {
  A: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  B: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  C: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
}

const diffColors: Record<string, string> = {
  easy: 'text-green-400 bg-green-500/10 border-green-500/20',
  medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  hard: 'text-red-400 bg-red-500/10 border-red-500/20',
}

export default function GeneratePage() {
  const { data: session } = useSession()
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [subject, setSubject] = useState('')
  const [availableUnits, setAvailableUnits] = useState<string[]>([])
  const [selectedUnits, setSelectedUnits] = useState<string[]>([])
  const [difficulty, setDifficulty] = useState('mixed')
  const [sections, setSections] = useState<Section[]>([
    { name: 'A', total: 5, attempt: 5, marks: 2 },
    { name: 'B', total: 3, attempt: 3, marks: 5 },
    { name: 'C', total: 2, attempt: 2, marks: 10 },
  ])
  const [questions, setQuestions] = useState<Question[]>([])
  const [generating, setGenerating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [genError, setGenError] = useState('')
  const [loadingUnits, setLoadingUnits] = useState(false)
  const token = session?.user?.backendToken

  // Load units from uploaded materials when subject changes
  useEffect(() => {
    if (!subject || !token) return
    setLoadingUnits(true)
    setAvailableUnits([])
    setSelectedUnits([])
    fetch(API + '/materials?subject=' + encodeURIComponent(subject), { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          const units = Array.from(new Set(d.data.map((m: any) => m.unit).filter(Boolean))) as string[]
          setAvailableUnits(units)
          if (units.length === 0) {
            // No uploaded materials - show default units
            setAvailableUnits(['Unit 1', 'Unit 2', 'Unit 3', 'Unit 4', 'Unit 5'])
          }
        }
        setLoadingUnits(false)
      })
      .catch(() => {
        setAvailableUnits(['Unit 1', 'Unit 2', 'Unit 3', 'Unit 4', 'Unit 5'])
        setLoadingUnits(false)
      })
  }, [subject, token])

  const toggleUnit = (u: string) => {
    setSelectedUnits(p => p.includes(u) ? p.filter(x => x !== u) : [...p, u])
  }

  const updateSection = (idx: number, field: keyof Section, val: number) => {
    setSections(p => p.map((s, i) => i === idx ? { ...s, [field]: val } : s))
  }

  const generate = async () => {
    if (!token) return
    setGenerating(true); setGenError('')
    try {
      const res = await fetch(API + '/ai/generate-questions', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject,
          units: selectedUnits.length > 0 ? selectedUnits : availableUnits,
          sections, difficulty,
        })
      })
      const data = await res.json()
      if (data.success && data.data.questions?.length > 0) {
        setQuestions(data.data.questions.map((q: any) => ({ ...q, selected: true, editing: false })))
        setStep(4)
      } else {
        setGenError(data.message || 'Generation failed. Check if GROQ_API_KEY is set.')
      }
    } catch (e: any) { setGenError('Error: ' + e.message) }
    setGenerating(false)
  }

  const regenerate = () => { setQuestions([]); generate() }

  // Edit question text
  const editQ = (id: number, text: string) => {
    setQuestions(p => p.map(q => q.id === id ? { ...q, text } : q))
  }

  // Toggle question selection (deselect = exclude from paper)
  const toggleQ = (id: number) => {
    setQuestions(p => p.map(q => q.id === id ? { ...q, selected: !q.selected } : q))
  }

  // Delete question completely
  const deleteQ = (id: number) => {
    setQuestions(p => p.filter(q => q.id !== id))
  }

  // Change question marks
  const editMarks = (id: number, marks: number) => {
    setQuestions(p => p.map(q => q.id === id ? { ...q, marks } : q))
  }

  // Change question section
  const editSection = (id: number, section: string) => {
    setQuestions(p => p.map(q => q.id === id ? { ...q, section } : q))
  }

  // Add new blank question
  const addQuestion = (section: string) => {
    const newId = Math.max(...questions.map(q => q.id), 0) + 1
    const secConf = sections.find(s => s.name === section)
    setQuestions(p => [...p, { id: newId, section, questionNo: newId, text: '', marks: secConf?.marks || 2, unit: '', difficulty: 'medium', type: 'descriptive', selected: true, editing: true }])
  }

  const savePaper = async () => {
    if (!token) return
    setSaving(true)
    const selected = questions.filter(q => q.selected && q.text.trim())
    const totalMarks = selected.reduce((s, q) => s + q.marks, 0)
    const res = await fetch(API + '/papers', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: subject + ' — ' + new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
        subject, examType: 'end_term', totalMarks, duration: 180, questions: selected,
      })
    })
    const data = await res.json()
    if (data.success) router.push('/teacher/generate/preview?id=' + data.data.id)
    setSaving(false)
  }

  const selectedCount = questions.filter(q => q.selected && q.text.trim()).length
  const totalMarks = sections.reduce((s, sec) => s + sec.attempt * sec.marks, 0)

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">Generate Question Paper</h1>
        <p className="text-slate-400 text-sm">AI generates questions from your uploaded unit materials</p>
      </div>

      {/* Steps */}
      <div className="flex items-center gap-0 mb-8">
        {['Subject', 'Units', 'Marks Config', 'Review & Edit'].map((label, i) => (
          <div key={i} className="flex items-center flex-1">
            <div className="flex items-center gap-2">
              <div className={'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 border ' + (step > i+1 ? 'bg-green-500 border-green-500 text-white' : step === i+1 ? 'bg-blue-500 border-blue-500 text-white' : 'bg-slate-800 border-white/10 text-slate-500')}>
                {step > i+1 ? '✓' : i+1}
              </div>
              <p className={'text-xs font-medium hidden sm:block ' + (step === i+1 ? 'text-white' : step > i+1 ? 'text-green-400' : 'text-slate-600')}>{label}</p>
            </div>
            {i < 3 && <div className={'flex-1 h-px mx-2 ' + (step > i+1 ? 'bg-green-500' : 'bg-slate-700')} />}
          </div>
        ))}
      </div>

      {/* Step 1: Subject */}
      {step === 1 && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
          <h2 className="text-base font-semibold text-white mb-5">Select Subject</h2>
          <div className="grid grid-cols-2 gap-2 mb-6">
            {ALL_SUBJECTS.map(s => (
              <button key={s} onClick={() => setSubject(s)} className={'p-3.5 rounded-xl border text-left transition-all ' + (subject === s ? 'border-blue-500/60 bg-blue-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                <p className="text-sm font-medium text-white">{s}</p>
              </button>
            ))}
          </div>
          <button onClick={() => setStep(2)} disabled={!subject} className="w-full py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600 disabled:opacity-40">
            Next: Select Units →
          </button>
        </div>
      )}

      {/* Step 2: Units - DYNAMIC from uploaded materials */}
      {step === 2 && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-base font-semibold text-white">Units for {subject}</h2>
            {availableUnits.length > 0 && (
              <button onClick={() => selectedUnits.length === availableUnits.length ? setSelectedUnits([]) : setSelectedUnits([...availableUnits])} className="text-xs text-blue-400 hover:text-blue-300">
                {selectedUnits.length === availableUnits.length ? 'Deselect All' : 'Select All'}
              </button>
            )}
          </div>

          {loadingUnits ? (
            <div className="flex items-center gap-3 py-6 text-slate-400 text-sm">
              <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              Loading units from your uploaded materials...
            </div>
          ) : (
            <>
              {availableUnits.length > 0 ? (
                <p className="text-xs text-slate-500 mb-4">
                  {availableUnits.some(u => u.startsWith('Unit')) && availableUnits.length === 5 && !availableUnits.includes('Unit 1'.replace('Unit ', 'Unit '))
                    ? '⚠️ No materials uploaded for this subject. Showing default units. Upload materials first for better questions.'
                    : '✓ Units loaded from your uploaded materials for ' + subject}
                </p>
              ) : null}

              <div className="space-y-2 mb-5">
                {availableUnits.map(u => (
                  <button key={u} onClick={() => toggleUnit(u)} className={'w-full p-4 rounded-xl border text-left flex items-center gap-3 transition-all ' + (selectedUnits.includes(u) ? 'border-blue-500/50 bg-blue-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                    <div className={'w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 ' + (selectedUnits.includes(u) ? 'bg-blue-500 border-blue-500' : 'border-white/20')}>
                      {selectedUnits.includes(u) && <span className="text-white text-xs font-bold">✓</span>}
                    </div>
                    <p className="text-sm text-white">{u}</p>
                  </button>
                ))}
              </div>
            </>
          )}

          <div className="mb-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Difficulty</p>
            <div className="flex gap-2 flex-wrap">
              {[['mixed', '🎯 Mixed'], ['easy', '🟢 Easy'], ['medium', '🟡 Medium'], ['hard', '🔴 Hard']].map(([v, l]) => (
                <button key={v} onClick={() => setDifficulty(v)} className={'px-4 py-2 rounded-xl text-xs font-medium border transition-all ' + (difficulty === v ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                  {l}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={() => setStep(1)} className="px-5 py-3 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">← Back</button>
            <button onClick={() => setStep(3)} className="flex-1 py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600">
              Next: Configure Marks → {selectedUnits.length > 0 ? '(' + selectedUnits.length + ' units)' : '(all units)'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Marks */}
      {step === 3 && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
          <h2 className="text-base font-semibold text-white mb-5">Configure Sections & Marks</h2>
          <div className="space-y-4 mb-6">
            {sections.map((sec, i) => (
              <div key={sec.name} className="bg-slate-800 rounded-xl p-4 border border-white/5">
                <div className="flex items-center gap-2 mb-3">
                  <span className={'text-xs px-2 py-0.5 rounded border font-semibold ' + (sectionColors[sec.name] || 'text-white bg-slate-700 border-white/10')}>Section {sec.name}</span>
                  <span className="text-xs text-slate-500">{sec.marks}M each · attempt {sec.attempt}/{sec.total}</span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[['Total Questions', 'total', 1, 20], ['To Attempt', 'attempt', 1, sec.total], ['Marks Each', 'marks', 1, 25]].map(([label, field, min, max]) => (
                    <div key={field as string}>
                      <label className="block text-[10px] text-slate-500 uppercase mb-1">{label as string}</label>
                      <input type="number" value={sec[field as keyof Section]} onChange={e => updateSection(i, field as keyof Section, parseInt(e.target.value) || 1)} min={min as number} max={max as number} className="w-full bg-slate-700 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 mb-5">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-400">Total Marks</span>
              <span className="text-blue-400 font-bold text-lg">{totalMarks}</span>
            </div>
            <p className="text-xs text-slate-500">{subject} · Units: {selectedUnits.length > 0 ? selectedUnits.join(', ') : 'All'}</p>
          </div>

          {genError && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4">
              <p className="text-xs text-red-400">⚠️ {genError}</p>
              <p className="text-xs text-slate-500 mt-1">Get free Groq key at console.groq.com → add GROQ_API_KEY to backend .env</p>
            </div>
          )}

          <div className="flex gap-3">
            <button onClick={() => setStep(2)} className="px-5 py-3 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">← Back</button>
            <button onClick={generate} disabled={generating} className="flex-1 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-semibold rounded-xl disabled:opacity-40 flex items-center justify-center gap-2">
              {generating ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Generating unique questions...</> : '🤖 Generate with AI'}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Review, Edit, Delete */}
      {step === 4 && questions.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
            <div>
              <p className="text-sm font-semibold text-white">{selectedCount} questions · {questions.filter(q => q.selected && q.text.trim()).reduce((s, q) => s + q.marks, 0)} marks</p>
              <p className="text-xs text-slate-500">{subject} · Click text to edit · ✕ to delete</p>
            </div>
            <div className="flex gap-2">
              <button onClick={regenerate} disabled={generating} className="px-4 py-2 bg-slate-800 text-slate-300 text-xs font-medium rounded-xl border border-white/10 hover:border-white/20 disabled:opacity-40 flex items-center gap-1.5">
                {generating ? <div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> : '🔄'} Regenerate
              </button>
              <button onClick={savePaper} disabled={saving || selectedCount === 0} className="px-5 py-2 bg-green-500 text-white text-xs font-semibold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center gap-1.5">
                {saving ? <div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> : '💾'} Save Paper
              </button>
            </div>
          </div>

          {['A', 'B', 'C'].map(secName => {
            const secQs = questions.filter(q => q.section === secName)
            const secConf = sections.find(s => s.name === secName)
            return (
              <div key={secName} className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className={'text-sm font-semibold px-3 py-1 rounded-lg border ' + (sectionColors[secName] || 'text-white')}>
                      Section {secName} — {secConf?.marks || 0}M each
                    </span>
                    <span className="text-xs text-slate-500">Attempt {secConf?.attempt}/{secQs.length}</span>
                  </div>
                  <button onClick={() => addQuestion(secName)} className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20">
                    + Add Question
                  </button>
                </div>

                <div className="space-y-2">
                  {secQs.map((q, qi) => (
                    <div key={q.id} className={'rounded-xl border p-4 transition-all ' + (q.selected ? 'bg-slate-900 border-white/5' : 'bg-slate-900/40 border-white/3 opacity-50')}>
                      <div className="flex items-start gap-3">
                        {/* Checkbox */}
                        <input type="checkbox" checked={q.selected} onChange={() => toggleQ(q.id)} className="mt-1 flex-shrink-0 accent-blue-500 w-4 h-4" />

                        {/* Question number */}
                        <span className="text-xs text-slate-500 mt-1 flex-shrink-0 w-6">Q{qi+1}.</span>

                        {/* Editable question text */}
                        <div className="flex-1 min-w-0">
                          <textarea
                            value={q.text}
                            onChange={e => editQ(q.id, e.target.value)}
                            placeholder="Type question here..."
                            className="w-full bg-transparent text-sm text-white outline-none resize-none leading-relaxed border-b border-transparent focus:border-blue-500/30 transition-all"
                            rows={q.text.length > 120 ? 3 : 2}
                          />
                          <div className="flex gap-2 mt-2 flex-wrap items-center">
                            <span className={'text-[10px] px-2 py-0.5 rounded border font-medium ' + (diffColors[q.difficulty] || 'text-slate-400 bg-slate-700 border-white/10')}>{q.difficulty}</span>
                            {q.unit && <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded border border-white/5">{q.unit}</span>}
                            <select value={q.section} onChange={e => editSection(q.id, e.target.value)} className="text-[10px] bg-slate-800 border border-white/10 rounded px-1 py-0.5 text-slate-400 outline-none">
                              {['A', 'B', 'C'].map(s => <option key={s} value={s}>Sec {s}</option>)}
                            </select>
                          </div>
                        </div>

                        {/* Marks + Delete */}
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <div className="flex items-center gap-1">
                            <button onClick={() => editMarks(q.id, Math.max(1, q.marks - 1))} className="w-6 h-6 rounded bg-slate-800 text-slate-400 hover:text-white text-sm flex items-center justify-center border border-white/5">−</button>
                            <span className="text-xs font-semibold text-blue-400 w-8 text-center">{q.marks}M</span>
                            <button onClick={() => editMarks(q.id, q.marks + 1)} className="w-6 h-6 rounded bg-slate-800 text-slate-400 hover:text-white text-sm flex items-center justify-center border border-white/5">+</button>
                          </div>
                          <button onClick={() => deleteQ(q.id)} className="w-7 h-7 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 flex items-center justify-center text-sm border border-red-500/20">✕</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}

          <div className="sticky bottom-4 bg-slate-900 rounded-xl border border-white/10 p-4 flex items-center justify-between shadow-2xl">
            <div>
              <p className="text-sm font-semibold text-white">{selectedCount} questions · {questions.filter(q => q.selected && q.text.trim()).reduce((s, q) => s + q.marks, 0)} marks total</p>
            </div>
            <button onClick={savePaper} disabled={saving || selectedCount === 0} className="px-6 py-2.5 bg-green-500 text-white text-sm font-semibold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center gap-2">
              {saving ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Saving...</> : '💾 Save & Preview Paper'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Generate page done!")

# ══════════════════════════════════════════════
# FIX 2: Teacher Materials - Multiple files per unit
# ══════════════════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/materials", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/materials/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Material = {
  id: string; title: string; fileName: string; fileUrl: string; fileType: string
  subject?: string | null; unit?: string | null; year?: number | null; examType?: string | null
  isPyq: boolean; fileSizeKb?: number | null; createdAt: string; uploader: { name: string }
}

type UploadItem = { file: File; title: string }

const SUBJECTS = [
  'Data Structures and Algorithms', 'Operating Systems', 'Computer Networks',
  'Database Management Systems', 'Software Engineering', 'Artificial Intelligence',
  'Machine Learning', 'Web Technologies', 'Object Oriented Programming',
  'Discrete Mathematics', 'Computer Organization', 'Theory of Computation',
  'Compiler Design', 'Digital Electronics', 'Mathematics', 'Physics',
  'Chemistry', 'English', 'Management', 'Other',
]

export default function TeacherMaterialsPage() {
  const { data: session } = useSession()
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'all'|'notes'|'pyq'>('all')
  const [filterSubject, setFilterSubject] = useState('all')
  const [showUpload, setShowUpload] = useState(false)
  const [form, setForm] = useState({ subject: '', unit: '', fileType: 'notes', isPyq: false, year: '', examType: '' })
  const [uploadItems, setUploadItems] = useState<UploadItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragOver, setDragOver] = useState(false)
  const [existingUnits, setExistingUnits] = useState<string[]>([])
  const [customUnit, setCustomUnit] = useState('')
  const [showCustomUnit, setShowCustomUnit] = useState(false)
  const token = session?.user?.backendToken

  const fetchMaterials = async () => {
    if (!token) return
    const res = await fetch(API + '/materials', { headers: { Authorization: 'Bearer ' + token } })
    const data = await res.json()
    if (data.success) setMaterials(data.data)
    setLoading(false)
  }

  useEffect(() => { if (token) fetchMaterials() }, [token])

  // Load existing units when subject changes
  useEffect(() => {
    if (!form.subject || !token) return
    const units = Array.from(new Set(materials.filter(m => m.subject === form.subject && m.unit).map(m => m.unit!).filter(Boolean)))
    setExistingUnits(units)
  }, [form.subject, materials])

  const current = materials.filter(m => {
    if (tab === 'notes' && m.isPyq) return false
    if (tab === 'pyq' && !m.isPyq) return false
    if (filterSubject !== 'all' && m.subject !== filterSubject) return false
    return true
  })

  const allSubjects = Array.from(new Set(materials.map(m => m.subject).filter(Boolean))) as string[]

  // Group by unit for display
  const grouped = current.reduce((acc, m) => {
    const key = m.subject + ' > ' + (m.unit || 'No Unit')
    if (!acc[key]) acc[key] = { subject: m.subject || '', unit: m.unit || '', files: [] }
    acc[key].files.push(m)
    return acc
  }, {} as Record<string, { subject: string; unit: string; files: Material[] }>)

  const addFiles = (files: FileList | null) => {
    if (!files) return
    const items: UploadItem[] = Array.from(files).map(f => ({ file: f, title: f.name.replace(/\.[^.]+$/, '') }))
    setUploadItems(p => [...p, ...items])
  }

  const removeItem = (idx: number) => setUploadItems(p => p.filter((_, i) => i !== idx))
  const updateTitle = (idx: number, title: string) => setUploadItems(p => p.map((item, i) => i === idx ? { ...item, title } : item))

  const handleUpload = async () => {
    if (uploadItems.length === 0 || !form.subject || !token) return
    setUploading(true)
    setUploadProgress(0)

    const unitToUse = showCustomUnit ? customUnit : form.unit

    let done = 0
    for (const item of uploadItems) {
      const fd = new FormData()
      fd.append('file', item.file)
      fd.append('title', item.title)
      fd.append('subject', form.subject)
      if (unitToUse) fd.append('unit', unitToUse)
      fd.append('fileType', form.isPyq ? 'pyq' : form.fileType)
      fd.append('isPyq', form.isPyq ? 'true' : 'false')
      if (form.year) fd.append('year', form.year)
      if (form.examType) fd.append('examType', form.examType)

      await fetch(API + '/materials/upload', {
        method: 'POST', headers: { Authorization: 'Bearer ' + token }, body: fd
      })
      done++
      setUploadProgress(Math.round((done / uploadItems.length) * 100))
    }

    await fetchMaterials()
    setShowUpload(false)
    setUploadItems([])
    setForm({ subject: '', unit: '', fileType: 'notes', isPyq: false, year: '', examType: '' })
    setCustomUnit('')
    setShowCustomUnit(false)
    setUploading(false)
    setUploadProgress(0)
  }

  const handleDelete = async (id: string) => {
    if (!token || !confirm('Delete this material?')) return
    await fetch(API + '/materials/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } })
    fetchMaterials()
  }

  const formatSize = (kb?: number | null) => kb ? kb >= 1024 ? (kb/1024).toFixed(1) + 'MB' : kb + 'KB' : ''
  const examLabel = (t?: string | null) => t === 'end_term' ? 'End Term' : t === 'mid_term' ? 'Mid Term' : t === 'unit_test' ? 'Unit Test' : t || ''

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Materials</h1>
          <p className="text-slate-400 text-sm">Upload multiple notes per unit and PYQs</p>
        </div>
        <button onClick={() => setShowUpload(true)} className="px-4 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600">+ Upload Materials</button>
      </div>

      {/* Tabs + Filter */}
      <div className="flex gap-2 mb-5 flex-wrap">
        <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-xl p-1">
          {[['all','📁 All',materials.length],['notes','📚 Notes',materials.filter(m=>!m.isPyq).length],['pyq','📋 PYQs',materials.filter(m=>m.isPyq).length]].map(([k,l,c]) => (
            <button key={k as string} onClick={() => setTab(k as any)} className={'px-4 py-2 rounded-lg text-xs font-medium transition-all ' + (tab === k ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
              {l as string} ({c as number})
            </button>
          ))}
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => setFilterSubject('all')} className={'px-3 py-1.5 rounded-lg text-xs border transition-all ' + (filterSubject === 'all' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-slate-900 text-slate-400 border-white/5')}>All</button>
          {allSubjects.map(s => (
            <button key={s} onClick={() => setFilterSubject(s)} className={'px-3 py-1.5 rounded-lg text-xs border transition-all ' + (filterSubject === s ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-slate-900 text-slate-400 border-white/5')}>
              {s.length > 20 ? s.slice(0,20)+'...' : s}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : Object.keys(grouped).length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">📭</p>
          <p className="text-white font-medium mb-1">No materials yet</p>
          <button onClick={() => setShowUpload(true)} className="mt-3 px-4 py-2 bg-blue-500 text-white text-sm rounded-xl">Upload First Material</button>
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(grouped).map(([key, group]) => (
            <div key={key} className="bg-slate-900 rounded-2xl border border-white/5 overflow-hidden">
              <div className="p-4 border-b border-white/5 bg-slate-800/50 flex items-center gap-3">
                <div>
                  <p className="text-sm font-semibold text-white">{group.subject}</p>
                  {group.unit && <p className="text-xs text-blue-400">{group.unit}</p>}
                </div>
                <span className="ml-auto text-xs text-slate-500">{group.files.length} file{group.files.length !== 1 ? 's' : ''}</span>
              </div>
              <div className="divide-y divide-white/5">
                {group.files.map(m => (
                  <div key={m.id} className="flex items-center gap-4 p-4 hover:bg-slate-800/30 transition-all">
                    <div className={'w-10 h-10 rounded-lg flex items-center justify-center text-xl flex-shrink-0 ' + (m.isPyq ? 'bg-blue-500/10 border border-blue-500/20' : 'bg-green-500/10 border border-green-500/20')}>
                      {m.isPyq ? '📋' : '📄'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{m.title}</p>
                      <div className="flex gap-2 mt-0.5 flex-wrap">
                        {m.year && <span className="text-[10px] text-blue-400">{m.year}</span>}
                        {m.examType && <span className="text-[10px] text-orange-400">{examLabel(m.examType)}</span>}
                        <span className="text-[10px] text-slate-600">{formatSize(m.fileSizeKb)}</span>
                      </div>
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      <a href={'http://localhost:5000' + m.fileUrl} target="_blank" className="text-xs px-3 py-1.5 bg-slate-800 text-slate-300 border border-white/10 rounded-lg hover:border-white/20">👁 View</a>
                      <button onClick={() => handleDelete(m.id)} className="text-xs px-3 py-1.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500/20">✕</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/85 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-white/5 sticky top-0 bg-slate-900 z-10">
              <div>
                <p className="text-sm font-semibold text-white">Upload Materials</p>
                <p className="text-xs text-slate-500">Upload multiple files to the same unit at once</p>
              </div>
              <button onClick={() => { setShowUpload(false); setUploadItems([]) }} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center">✕</button>
            </div>
            <div className="p-5 space-y-5">
              {/* Type toggle */}
              <div className="flex gap-2">
                <button onClick={() => setForm(p => ({ ...p, isPyq: false }))} className={'flex-1 py-2.5 rounded-xl text-sm font-medium border transition-all ' + (!form.isPyq ? 'bg-green-500 text-white border-green-500' : 'bg-slate-800 text-slate-400 border-white/5')}>
                  📚 Study Notes
                </button>
                <button onClick={() => setForm(p => ({ ...p, isPyq: true }))} className={'flex-1 py-2.5 rounded-xl text-sm font-medium border transition-all ' + (form.isPyq ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>
                  📋 Previous Year QP
                </button>
              </div>

              {/* Subject */}
              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Subject *</label>
                <select value={form.subject} onChange={e => setForm(p => ({ ...p, subject: e.target.value, unit: '' }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50">
                  <option value="">-- Select Subject --</option>
                  {SUBJECTS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>

              {/* Unit - dynamic from existing + add new */}
              {!form.isPyq && form.subject && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs text-slate-500 uppercase tracking-wider">Unit</label>
                    <button onClick={() => { setShowCustomUnit(!showCustomUnit); setForm(p => ({ ...p, unit: '' })) }} className="text-xs text-blue-400 hover:text-blue-300">
                      {showCustomUnit ? 'Select existing unit' : '+ Create new unit'}
                    </button>
                  </div>
                  {showCustomUnit ? (
                    <input type="text" value={customUnit} onChange={e => setCustomUnit(e.target.value)} placeholder="Enter unit name e.g. Unit 1: Introduction to DSA" className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
                  ) : (
                    <div className="space-y-2">
                      {existingUnits.length > 0 ? (
                        <>
                          <div className="flex gap-2 flex-wrap">
                            {existingUnits.map(u => (
                              <button key={u} onClick={() => setForm(p => ({ ...p, unit: u }))} className={'px-3 py-2 rounded-xl text-xs font-medium border transition-all ' + (form.unit === u ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/20')}>
                                {u} {form.unit === u && '✓'}
                              </button>
                            ))}
                          </div>
                          <p className="text-[10px] text-slate-600">Select existing unit to add more files to it, or create a new unit</p>
                        </>
                      ) : (
                        <div className="p-3 bg-slate-800 rounded-xl border border-white/5 text-center">
                          <p className="text-xs text-slate-500 mb-2">No units exist for {form.subject} yet</p>
                          <button onClick={() => setShowCustomUnit(true)} className="text-xs text-blue-400 hover:text-blue-300">+ Create first unit</button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* PYQ fields */}
              {form.isPyq && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Year</label>
                    <select value={form.year} onChange={e => setForm(p => ({ ...p, year: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none">
                      <option value="">Select Year</option>
                      {['2025','2024','2023','2022','2021','2020'].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Exam Type</label>
                    <select value={form.examType} onChange={e => setForm(p => ({ ...p, examType: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none">
                      <option value="">Select Type</option>
                      <option value="end_term">End Term</option>
                      <option value="mid_term">Mid Term</option>
                      <option value="unit_test">Unit Test</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Multi-file drop zone */}
              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Files ({uploadItems.length} selected)
                </label>
                <div
                  onDrop={e => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files) }}
                  onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onClick={() => document.getElementById('mat-files')?.click()}
                  className={'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ' + (dragOver ? 'border-blue-500 bg-blue-500/5' : 'border-white/10 hover:border-white/20')}
                >
                  <input id="mat-files" type="file" multiple accept=".pdf,.doc,.docx,.ppt,.pptx" className="hidden" onChange={e => addFiles(e.target.files)} />
                  <p className="text-3xl mb-2">📁</p>
                  <p className="text-sm text-white font-medium">Drop multiple files here</p>
                  <p className="text-xs text-slate-500 mt-1">Or click to browse · PDF, DOC, PPT supported</p>
                  <p className="text-xs text-blue-400 mt-1">You can add multiple parts of the same unit at once</p>
                </div>

                {/* File list with editable titles */}
                {uploadItems.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {uploadItems.map((item, i) => (
                      <div key={i} className="flex items-center gap-3 bg-slate-800 rounded-xl px-3 py-2.5 border border-white/5">
                        <span className="text-green-400 text-sm flex-shrink-0">✓</span>
                        <input type="text" value={item.title} onChange={e => updateTitle(i, e.target.value)} className="flex-1 bg-transparent text-sm text-white outline-none" />
                        <span className="text-[10px] text-slate-500 flex-shrink-0">{(item.file.size/1024/1024).toFixed(1)}MB</span>
                        <button onClick={() => removeItem(i)} className="text-slate-600 hover:text-red-400 flex-shrink-0 text-sm">✕</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Upload progress */}
              {uploading && (
                <div>
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>Uploading...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: uploadProgress + '%' }} />
                  </div>
                </div>
              )}

              <button onClick={handleUpload} disabled={uploadItems.length === 0 || !form.subject || uploading} className="w-full py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600 disabled:opacity-40 flex items-center justify-center gap-2">
                {uploading ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Uploading {uploadProgress}%...</>
                  : '⬆ Upload ' + uploadItems.length + ' File' + (uploadItems.length !== 1 ? 's' : '')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Teacher Materials done!")

# Fix duplicate key warning in generate page (questions use Date.now which can repeat)
print("All frontend fixes done!")