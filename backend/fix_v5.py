import os

# ═══════════════════════════════════════
# FIX 1: Document inline view - proxy route
# ═══════════════════════════════════════
with open("src/routes/material.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { uploadMaterial, getMaterials, downloadMaterial, previewMaterial, deleteMaterial } from '../controllers/material.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'
import path from 'path'
import fs from 'fs'

const router = Router()
router.post('/upload', authenticate, authorize('teacher', 'admin'), upload.single('file'), uploadMaterial)
router.get('/', authenticate, getMaterials)
router.get('/:id/download', authenticate, downloadMaterial)
router.get('/:id/preview', authenticate, previewMaterial)
router.delete('/:id', authenticate, authorize('teacher', 'admin'), deleteMaterial)

// Public inline view - no auth needed for iframe
router.get('/:id/view', async (req: any, res: any) => {
  try {
    const { PrismaClient } = require('@prisma/client')
    const prisma = new PrismaClient()
    const material = await prisma.material.findUnique({ where: { id: req.params.id } })
    if (!material) return res.status(404).send('Not found')
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return res.status(404).send('File not found')
    const ext = path.extname(material.fileName).toLowerCase()
    const mimeMap: Record<string, string> = {
      '.pdf': 'application/pdf',
      '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
      '.txt': 'text/plain', '.mp4': 'video/mp4',
    }
    const mime = mimeMap[ext] || 'application/pdf'
    res.setHeader('Content-Type', mime)
    res.setHeader('Content-Disposition', 'inline')
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('Cache-Control', 'no-cache')
    return res.sendFile(path.resolve(filePath))
  } catch (e: any) { return res.status(500).send(e.message) }
})

export default router
""")
print("Material routes done - view route added!")

# ═══════════════════════════════════════
# FIX 2: Generate page - unique keys + topics field
# ═══════════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/generate", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/generate/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect, useRef } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

const ALL_SUBJECTS = [
  'Data Structures and Algorithms', 'Operating Systems', 'Computer Networks',
  'Database Management Systems', 'Software Engineering', 'Artificial Intelligence',
  'Machine Learning', 'Web Technologies', 'Object Oriented Programming',
  'Discrete Mathematics', 'Computer Organization', 'Theory of Computation',
  'Compiler Design', 'Digital Electronics', 'Mathematics', 'Physics',
  'Chemistry', 'English', 'Management', 'Other',
]

type Section = { name: string; total: number; attempt: number; marks: number }
type Question = {
  uid: string   // unique identifier - NEVER duplicate
  id: number; section: string; questionNo: number; text: string
  marks: number; unit: string; difficulty: string; type: string; selected: boolean
}

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

let uidCounter = 0
const nextUid = () => 'q_' + (++uidCounter) + '_' + Math.random().toString(36).slice(2, 7)

export default function GeneratePage() {
  const { data: session } = useSession()
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [subject, setSubject] = useState('')
  const [availableUnits, setAvailableUnits] = useState<string[]>([])
  const [selectedUnits, setSelectedUnits] = useState<string[]>([])
  const [extraTopics, setExtraTopics] = useState<string[]>([])
  const [newTopic, setNewTopic] = useState('')
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

  useEffect(() => {
    if (!subject || !token) return
    setLoadingUnits(true)
    setAvailableUnits([])
    setSelectedUnits([])
    fetch(API + '/materials?subject=' + encodeURIComponent(subject), {
      headers: { Authorization: 'Bearer ' + token }
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          const units = Array.from(new Set(
            d.data.map((m: any) => m.unit).filter(Boolean)
          )) as string[]
          setAvailableUnits(units.length > 0 ? units : ['Unit 1', 'Unit 2', 'Unit 3', 'Unit 4', 'Unit 5'])
        }
        setLoadingUnits(false)
      })
      .catch(() => {
        setAvailableUnits(['Unit 1', 'Unit 2', 'Unit 3', 'Unit 4', 'Unit 5'])
        setLoadingUnits(false)
      })
  }, [subject, token])

  const toggleUnit = (u: string) =>
    setSelectedUnits(p => p.includes(u) ? p.filter(x => x !== u) : [...p, u])

  const addTopic = () => {
    const t = newTopic.trim()
    if (t && !extraTopics.includes(t)) {
      setExtraTopics(p => [...p, t])
      setNewTopic('')
    }
  }

  const removeTopic = (t: string) => setExtraTopics(p => p.filter(x => x !== t))

  const updateSection = (idx: number, field: keyof Section, val: number) =>
    setSections(p => p.map((s, i) => i === idx ? { ...s, [field]: val } : s))

  const generate = async () => {
    if (!token) return
    setGenerating(true); setGenError('')
    try {
      const allTopics = [
        ...(selectedUnits.length > 0 ? selectedUnits : availableUnits),
        ...extraTopics
      ]
      const res = await fetch(API + '/ai/generate-questions', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject, units: allTopics, sections, difficulty })
      })
      const data = await res.json()
      if (data.success && data.data.questions?.length > 0) {
        // Add unique uid to every question to avoid key conflicts
        const withUids = data.data.questions.map((q: any) => ({
          ...q,
          uid: nextUid(),
          selected: true,
        }))
        setQuestions(withUids)
        setStep(4)
      } else {
        setGenError(data.message || 'Generation failed. Check GROQ_API_KEY in backend .env')
      }
    } catch (e: any) { setGenError('Error: ' + e.message) }
    setGenerating(false)
  }

  const regenerate = () => { setQuestions([]); generate() }

  const editQ = (uid: string, text: string) =>
    setQuestions(p => p.map(q => q.uid === uid ? { ...q, text } : q))

  const toggleQ = (uid: string) =>
    setQuestions(p => p.map(q => q.uid === uid ? { ...q, selected: !q.selected } : q))

  const deleteQ = (uid: string) =>
    setQuestions(p => p.filter(q => q.uid !== uid))

  const editMarks = (uid: string, marks: number) =>
    setQuestions(p => p.map(q => q.uid === uid ? { ...q, marks } : q))

  const editSection = (uid: string, section: string) =>
    setQuestions(p => p.map(q => q.uid === uid ? { ...q, section } : q))

  const addQuestion = (section: string) => {
    const secConf = sections.find(s => s.name === section)
    setQuestions(p => [...p, {
      uid: nextUid(),
      id: p.length + 1, section, questionNo: p.length + 1,
      text: '', marks: secConf?.marks || 2, unit: '', difficulty: 'medium',
      type: 'descriptive', selected: true,
    }])
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
        subject, examType: 'end_term', totalMarks, duration: 180,
        questions: selected.map(({ uid, ...rest }) => rest),
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
        <p className="text-slate-400 text-sm">AI generates questions from your uploaded units and topics</p>
      </div>

      {/* Steps indicator */}
      <div className="flex items-center mb-8">
        {['Subject', 'Units & Topics', 'Marks Config', 'Review & Edit'].map((label, i) => (
          <div key={label} className="flex items-center flex-1">
            <div className="flex items-center gap-2 flex-shrink-0">
              <div className={'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border ' +
                (step > i+1 ? 'bg-green-500 border-green-500 text-white' :
                 step === i+1 ? 'bg-blue-500 border-blue-500 text-white' :
                 'bg-slate-800 border-white/10 text-slate-500')}>
                {step > i+1 ? '✓' : i+1}
              </div>
              <p className={'text-xs font-medium hidden sm:block ' +
                (step === i+1 ? 'text-white' : step > i+1 ? 'text-green-400' : 'text-slate-600')}>
                {label}
              </p>
            </div>
            {i < 3 && <div className={'flex-1 h-px mx-2 ' + (step > i+1 ? 'bg-green-500' : 'bg-slate-700')} />}
          </div>
        ))}
      </div>

      {/* STEP 1: Subject */}
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
            Next: Select Units & Topics →
          </button>
        </div>
      )}

      {/* STEP 2: Units + Custom Topics */}
      {step === 2 && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white">Units for {subject}</h2>
            {availableUnits.length > 0 && (
              <button onClick={() => setSelectedUnits(
                selectedUnits.length === availableUnits.length ? [] : [...availableUnits]
              )} className="text-xs text-blue-400 hover:text-blue-300">
                {selectedUnits.length === availableUnits.length ? 'Deselect All' : 'Select All'}
              </button>
            )}
          </div>

          {loadingUnits ? (
            <div className="flex items-center gap-3 py-4 text-slate-400 text-sm">
              <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              Loading units from your materials...
            </div>
          ) : (
            <div className="space-y-2">
              {availableUnits.map(u => (
                <button key={u} onClick={() => toggleUnit(u)} className={'w-full p-3.5 rounded-xl border text-left flex items-center gap-3 transition-all ' + (selectedUnits.includes(u) ? 'border-blue-500/50 bg-blue-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                  <div className={'w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 ' + (selectedUnits.includes(u) ? 'bg-blue-500 border-blue-500' : 'border-white/20')}>
                    {selectedUnits.includes(u) && <span className="text-white text-xs font-bold">✓</span>}
                  </div>
                  <p className="text-sm text-white">{u}</p>
                </button>
              ))}
            </div>
          )}

          {/* EXTRA TOPICS */}
          <div className="border-t border-white/5 pt-5">
            <p className="text-sm font-semibold text-white mb-1">Add Extra Topics</p>
            <p className="text-xs text-slate-500 mb-3">Add specific topics/concepts you want questions on</p>
            <div className="flex gap-2 mb-3">
              <input
                type="text" value={newTopic}
                onChange={e => setNewTopic(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addTopic()}
                placeholder="e.g. Dijkstra Algorithm, Deadlock Prevention, SQL Joins..."
                className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600"
              />
              <button onClick={addTopic} disabled={!newTopic.trim()} className="px-4 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40">Add</button>
            </div>
            {extraTopics.length > 0 && (
              <div className="flex gap-2 flex-wrap">
                {extraTopics.map(t => (
                  <span key={t} className="flex items-center gap-1.5 text-xs bg-purple-500/10 text-purple-400 border border-purple-500/20 px-3 py-1.5 rounded-full">
                    {t}
                    <button onClick={() => removeTopic(t)} className="hover:text-red-400 ml-0.5">✕</button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Difficulty */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Difficulty</p>
            <div className="flex gap-2 flex-wrap">
              {[['mixed','🎯 Mixed (Recommended)'],['easy','🟢 Easy'],['medium','🟡 Medium'],['hard','🔴 Hard']].map(([v,l]) => (
                <button key={v} onClick={() => setDifficulty(v)} className={'px-4 py-2 rounded-xl text-xs font-medium border transition-all ' + (difficulty === v ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                  {l}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button onClick={() => setStep(1)} className="px-5 py-3 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">← Back</button>
            <button onClick={() => setStep(3)} className="flex-1 py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600">
              Next: Configure Marks →
              {(selectedUnits.length > 0 || extraTopics.length > 0) && (
                <span className="ml-2 opacity-70 text-xs">({selectedUnits.length} units + {extraTopics.length} topics)</span>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Marks config */}
      {step === 3 && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
          <h2 className="text-base font-semibold text-white mb-5">Configure Sections & Marks</h2>
          <div className="space-y-4 mb-6">
            {sections.map((sec, i) => (
              <div key={sec.name} className="bg-slate-800 rounded-xl p-4 border border-white/5">
                <div className="flex items-center gap-2 mb-3">
                  <span className={'text-xs px-2 py-0.5 rounded border font-semibold ' + (sectionColors[sec.name])}>Section {sec.name}</span>
                  <span className="text-xs text-slate-500">{sec.marks}M each · attempt {sec.attempt}/{sec.total}</span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[['Total Questions','total',1,20],['To Attempt','attempt',1,sec.total],['Marks Each','marks',1,25]].map(([label,field,min,max]) => (
                    <div key={field as string}>
                      <label className="block text-[10px] text-slate-500 uppercase mb-1">{label as string}</label>
                      <input type="number" value={sec[field as keyof Section]} onChange={e => updateSection(i, field as keyof Section, parseInt(e.target.value)||1)} min={min as number} max={max as number} className="w-full bg-slate-700 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none" />
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
            <p className="text-xs text-slate-500">
              {subject} · Units: {selectedUnits.length > 0 ? selectedUnits.slice(0,2).join(', ') + (selectedUnits.length > 2 ? '...' : '') : 'All'}
              {extraTopics.length > 0 && ' + ' + extraTopics.length + ' extra topics'}
            </p>
          </div>

          {genError && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4">
              <p className="text-xs text-red-400">⚠️ {genError}</p>
            </div>
          )}

          <div className="flex gap-3">
            <button onClick={() => setStep(2)} className="px-5 py-3 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">← Back</button>
            <button onClick={generate} disabled={generating} className="flex-1 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-semibold rounded-xl disabled:opacity-40 flex items-center justify-center gap-2">
              {generating ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />AI is generating unique questions...</> : '🤖 Generate with AI'}
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Review, Edit, Delete - uses uid as key (NEVER duplicates) */}
      {step === 4 && questions.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
            <div>
              <p className="text-sm font-semibold text-white">{selectedCount} questions selected</p>
              <p className="text-xs text-slate-500">Click text to edit · ✕ to delete · −/+ to change marks</p>
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

          {['A','B','C'].map(secName => {
            const secQs = questions.filter(q => q.section === secName)
            if (secQs.length === 0 && secName === 'C') return null
            const secConf = sections.find(s => s.name === secName)
            return (
              <div key={secName} className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className={'text-sm font-semibold px-3 py-1 rounded-lg border ' + sectionColors[secName]}>
                      Section {secName} — {secConf?.marks || 0}M each
                    </span>
                    <span className="text-xs text-slate-500">{secQs.length} questions</span>
                  </div>
                  <button onClick={() => addQuestion(secName)} className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20">
                    + Add
                  </button>
                </div>
                <div className="space-y-2">
                  {/* KEY = q.uid — guaranteed unique */}
                  {secQs.map((q, qi) => (
                    <div key={q.uid} className={'rounded-xl border p-4 transition-all ' + (q.selected ? 'bg-slate-900 border-white/5' : 'bg-slate-900/40 opacity-50')}>
                      <div className="flex items-start gap-3">
                        <input type="checkbox" checked={q.selected} onChange={() => toggleQ(q.uid)} className="mt-1 flex-shrink-0 accent-blue-500 w-4 h-4" />
                        <span className="text-xs text-slate-500 mt-1 flex-shrink-0">Q{qi+1}.</span>
                        <div className="flex-1 min-w-0">
                          <textarea
                            value={q.text}
                            onChange={e => editQ(q.uid, e.target.value)}
                            placeholder="Type question here..."
                            className="w-full bg-transparent text-sm text-white outline-none resize-none leading-relaxed border-b border-transparent focus:border-blue-500/30 transition-all"
                            rows={q.text.length > 120 ? 3 : 2}
                          />
                          <div className="flex gap-2 mt-2 flex-wrap items-center">
                            <span className={'text-[10px] px-2 py-0.5 rounded border ' + (diffColors[q.difficulty] || 'text-slate-400 bg-slate-700 border-white/10')}>{q.difficulty}</span>
                            {q.unit && <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded border border-white/5">{q.unit}</span>}
                            <select value={q.section} onChange={e => editSection(q.uid, e.target.value)} className="text-[10px] bg-slate-800 border border-white/10 rounded px-1 py-0.5 text-slate-400 outline-none">
                              <option value="A">Sec A</option>
                              <option value="B">Sec B</option>
                              <option value="C">Sec C</option>
                            </select>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <button onClick={() => editMarks(q.uid, Math.max(1, q.marks - 1))} className="w-6 h-6 rounded bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center border border-white/5 text-sm">−</button>
                          <span className="text-xs font-bold text-blue-400 w-8 text-center">{q.marks}M</span>
                          <button onClick={() => editMarks(q.uid, q.marks + 1)} className="w-6 h-6 rounded bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center border border-white/5 text-sm">+</button>
                          <button onClick={() => deleteQ(q.uid)} className="w-7 h-7 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 flex items-center justify-center border border-red-500/20 text-sm">✕</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}

          <div className="sticky bottom-4 bg-slate-900 rounded-xl border border-white/10 p-4 flex items-center justify-between shadow-2xl">
            <p className="text-sm font-semibold text-white">
              {selectedCount} questions · {questions.filter(q=>q.selected&&q.text.trim()).reduce((s,q)=>s+q.marks,0)} marks
            </p>
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
print("Generate page done - unique keys!")

# Fix materials page - view opens inline in browser
with open("../frontend/app/(student)/student/materials/page.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Replace preview iframe to use /view route (no auth needed = no blank iframe)
content = content.replace(
    "src={'http://localhost:5000' + preview.fileUrl}",
    "src={'http://localhost:5000/api/v1/materials/' + preview.id + '/view'}"
)
with open("../frontend/app/(student)/student/materials/page.tsx", "w", encoding="utf-8") as f:
    f.write(content)
print("Student materials - view URL fixed!")

# Fix teacher materials view too
with open("../frontend/app/(dashboard)/teacher/materials/page.tsx", "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace(
    "href={'http://localhost:5000' + m.fileUrl}",
    "href={'http://localhost:5000/api/v1/materials/' + m.id + '/view'}"
)
with open("../frontend/app/(dashboard)/teacher/materials/page.tsx", "w", encoding="utf-8") as f:
    f.write(content)
print("Teacher materials - view URL fixed!")

print("\n=== ALL DONE ===")