import os

# ═══════════════════════════════════════════════════════
# Generate Questions Page - reads actual units from DB + PYQ years
# ═══════════════════════════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/generate", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/generate/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect, useRef } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

const ALL_SUBJECTS = [
  'Data Structures and Algorithms','Operating Systems','Computer Networks',
  'Database Management Systems','Software Engineering','Artificial Intelligence',
  'Machine Learning','Web Technologies','Object Oriented Programming',
  'Discrete Mathematics','Computer Organization','Theory of Computation',
  'Compiler Design','Digital Electronics','Mathematics','Physics',
  'Chemistry','English','Management',
]

type Section = { name: string; total: number; attempt: number; marks: number }
type Question = { uid: string; id: number; section: string; questionNo: number; text: string; marks: number; unit: string; difficulty: string; type: string; selected: boolean }

const sectionColors: Record<string,string> = {
  A: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  B: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  C: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
}

const diffColors: Record<string,string> = {
  easy: 'text-green-400 bg-green-500/10 border-green-500/20',
  medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  hard: 'text-red-400 bg-red-500/10 border-red-500/20',
}

let uid = 0
const nextUid = () => 'q_' + (++uid) + '_' + Math.random().toString(36).slice(2,6)

export default function GeneratePage() {
  const { data: session } = useSession()
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [subject, setSubject] = useState('')
  const [customSubjects, setCustomSubjects] = useState<string[]>(() => {
    if (typeof window !== 'undefined') {
      try { return JSON.parse(localStorage.getItem('genSubjects') || '[]') } catch { return [] }
    }
    return []
  })
  const [newSubj, setNewSubj] = useState('')
  const [showAddSubj, setShowAddSubj] = useState(false)

  // From DB
  const [dbUnits, setDbUnits] = useState<string[]>([])
  const [dbYears, setDbYears] = useState<string[]>([])
  const [loadingUnits, setLoadingUnits] = useState(false)
  const [hasMaterials, setHasMaterials] = useState(false)
  const [hasPyqs, setHasPyqs] = useState(false)

  const [selectedUnits, setSelectedUnits] = useState<string[]>([])
  const [extraTopics, setExtraTopics] = useState<string[]>([])
  const [newTopic, setNewTopic] = useState('')

  // PYQ options
  const [usePyqs, setUsePyqs] = useState(false)
  const [selectedPyqYears, setSelectedPyqYears] = useState<string[]>([])

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
  const token = session?.user?.backendToken

  const allSubjects = [...ALL_SUBJECTS, ...customSubjects]

  // Load units from DB when subject changes
  useEffect(() => {
    if (!subject || !token) return
    setLoadingUnits(true)
    setDbUnits([]); setDbYears([]); setSelectedUnits([]); setSelectedPyqYears([]); setUsePyqs(false)

    fetch(API + '/ai/material-units?subject=' + encodeURIComponent(subject), {
      headers: { Authorization: 'Bearer ' + token }
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          setDbUnits(d.data.units || [])
          setDbYears(d.data.years || [])
          setHasMaterials(d.data.hasMaterials)
          setHasPyqs(d.data.hasPyqs)
        }
        setLoadingUnits(false)
      })
      .catch(() => setLoadingUnits(false))
  }, [subject, token])

  const addSubject = () => {
    const s = newSubj.trim()
    if (s && !allSubjects.includes(s)) {
      const updated = [...customSubjects, s]
      setCustomSubjects(updated)
      localStorage.setItem('genSubjects', JSON.stringify(updated))
      setSubject(s); setNewSubj(''); setShowAddSubj(false)
    }
  }

  const removeSubject = (s: string) => {
    const updated = customSubjects.filter(x => x !== s)
    setCustomSubjects(updated)
    localStorage.setItem('genSubjects', JSON.stringify(updated))
    if (subject === s) setSubject('')
  }

  const toggleUnit = (u: string) =>
    setSelectedUnits(p => p.includes(u) ? p.filter(x => x !== u) : [...p, u])

  const togglePyqYear = (y: string) =>
    setSelectedPyqYears(p => p.includes(y) ? p.filter(x => x !== y) : [...p, y])

  const addTopic = () => {
    const t = newTopic.trim()
    if (t && !extraTopics.includes(t)) { setExtraTopics(p => [...p, t]); setNewTopic('') }
  }

  const updateSection = (idx: number, field: keyof Section, val: number) =>
    setSections(p => p.map((s, i) => i === idx ? { ...s, [field]: val } : s))

  const generate = async () => {
    if (!token) return
    setGenerating(true); setGenError('')
    try {
      const allTopics = [...selectedUnits, ...extraTopics]
      if (allTopics.length === 0) { setGenError('Please select at least one unit or add a topic'); setGenerating(false); return }

      const res = await fetch(API + '/ai/generate-questions', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject, units: selectedUnits, extraTopics, sections, difficulty,
          usePyqs, pyqYears: selectedPyqYears,
        })
      })
      const data = await res.json()
      if (data.success && data.data.questions?.length > 0) {
        setQuestions(data.data.questions.map((q: any) => ({ ...q, uid: nextUid(), selected: true })))
        setStep(4)
      } else {
        setGenError(data.message || 'Generation failed. Check GROQ_API_KEY in backend .env')
      }
    } catch (e: any) { setGenError('Error: ' + e.message) }
    setGenerating(false)
  }

  const regenerate = () => { setQuestions([]); generate() }
  const editQ = (uid: string, text: string) => setQuestions(p => p.map(q => q.uid === uid ? { ...q, text } : q))
  const toggleQ = (uid: string) => setQuestions(p => p.map(q => q.uid === uid ? { ...q, selected: !q.selected } : q))
  const deleteQ = (uid: string) => setQuestions(p => p.filter(q => q.uid !== uid))
  const editMarks = (uid: string, marks: number) => setQuestions(p => p.map(q => q.uid === uid ? { ...q, marks } : q))
  const editSection = (uid: string, sec: string) => setQuestions(p => p.map(q => q.uid === uid ? { ...q, section: sec } : q))
  const addQuestion = (sec: string) => {
    const secConf = sections.find(s => s.name === sec)
    setQuestions(p => [...p, { uid: nextUid(), id: p.length+1, section: sec, questionNo: p.length+1, text: '', marks: secConf?.marks || 2, unit: '', difficulty: 'medium', type: 'descriptive', selected: true }])
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
        questions: selected.map(({ uid: _uid, ...rest }) => rest),
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
        <p className="text-slate-400 text-sm">AI generates from your uploaded units + PYQs</p>
      </div>

      {/* Steps */}
      <div className="flex items-center mb-8">
        {['Subject','Units & PYQs','Configure','Review'].map((label, i) => (
          <div key={label} className="flex items-center flex-1">
            <div className="flex items-center gap-2 flex-shrink-0">
              <div className={'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border ' +
                (step > i+1 ? 'bg-green-500 border-green-500 text-white' : step === i+1 ? 'bg-blue-500 border-blue-500 text-white' : 'bg-slate-800 border-white/10 text-slate-500')}>
                {step > i+1 ? '✓' : i+1}
              </div>
              <p className={'text-xs font-medium hidden sm:block ' + (step === i+1 ? 'text-white' : step > i+1 ? 'text-green-400' : 'text-slate-600')}>{label}</p>
            </div>
            {i < 3 && <div className={'flex-1 h-px mx-2 ' + (step > i+1 ? 'bg-green-500' : 'bg-slate-700')} />}
          </div>
        ))}
      </div>

      {/* STEP 1: Subject */}
      {step === 1 && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
          <h2 className="text-base font-semibold text-white mb-5">Select Subject</h2>
          <div className="grid grid-cols-2 gap-2 mb-4">
            {allSubjects.map(s => (
              <button key={s} onClick={() => setSubject(s)}
                className={'p-3.5 rounded-xl border text-left transition-all group relative ' + (subject === s ? 'border-blue-500/60 bg-blue-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                <p className="text-sm font-medium text-white">{s}</p>
                {customSubjects.includes(s) && (
                  <button onClick={e => { e.stopPropagation(); removeSubject(s) }}
                    className="absolute top-2 right-2 text-[10px] text-red-400 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900 rounded px-1">✕</button>
                )}
              </button>
            ))}
          </div>
          {showAddSubj ? (
            <div className="flex gap-2 mb-4">
              <input type="text" value={newSubj} onChange={e => setNewSubj(e.target.value)} onKeyDown={e => e.key === 'Enter' && addSubject()} placeholder="Subject name..." autoFocus
                className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
              <button onClick={addSubject} disabled={!newSubj.trim()} className="px-4 py-2.5 bg-green-500 text-white text-sm rounded-xl disabled:opacity-40">Add</button>
              <button onClick={() => setShowAddSubj(false)} className="px-3 py-2.5 bg-slate-800 text-slate-400 text-sm rounded-xl border border-white/5">✕</button>
            </div>
          ) : (
            <button onClick={() => setShowAddSubj(true)} className="w-full py-2.5 mb-4 text-sm text-blue-400 border border-dashed border-blue-500/30 rounded-xl hover:bg-blue-500/5">
              + Add Custom Subject
            </button>
          )}
          <button onClick={() => setStep(2)} disabled={!subject} className="w-full py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600 disabled:opacity-40">
            Next: Select Units & PYQs →
          </button>
        </div>
      )}

      {/* STEP 2: Units + PYQs */}
      {step === 2 && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white">Units & Topics for {subject}</h2>
            {dbUnits.length > 0 && (
              <button onClick={() => setSelectedUnits(selectedUnits.length === dbUnits.length ? [] : [...dbUnits])} className="text-xs text-blue-400">
                {selectedUnits.length === dbUnits.length ? 'Deselect All' : 'Select All'}
              </button>
            )}
          </div>

          {loadingUnits ? (
            <div className="flex items-center gap-2 text-slate-400 text-sm"><div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />Loading from your materials...</div>
          ) : !hasMaterials ? (
            <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-4">
              <p className="text-sm text-yellow-400 font-medium mb-1">⚠️ No materials uploaded for {subject} yet</p>
              <p className="text-xs text-slate-500">Go to Materials → Upload notes for {subject}. Then units will appear here automatically.</p>
              <p className="text-xs text-slate-500 mt-1">You can still add topics manually below.</p>
            </div>
          ) : (
            <div>
              <p className="text-xs text-green-400 mb-3">✓ {dbUnits.length} units found from your uploaded materials</p>
              <div className="space-y-2">
                {dbUnits.map(u => (
                  <button key={u} onClick={() => toggleUnit(u)}
                    className={'w-full p-3.5 rounded-xl border text-left flex items-center gap-3 transition-all ' + (selectedUnits.includes(u) ? 'border-blue-500/50 bg-blue-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                    <div className={'w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 ' + (selectedUnits.includes(u) ? 'bg-blue-500 border-blue-500' : 'border-white/20')}>
                      {selectedUnits.includes(u) && <span className="text-white text-xs font-bold">✓</span>}
                    </div>
                    <p className="text-sm text-white">{u}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Extra topics */}
          <div className="border-t border-white/5 pt-4">
            <p className="text-sm font-semibold text-white mb-1">Add Extra Topics</p>
            <p className="text-xs text-slate-500 mb-3">Add specific topics not covered in uploaded units</p>
            <div className="flex gap-2 mb-3">
              <input type="text" value={newTopic} onChange={e => setNewTopic(e.target.value)} onKeyDown={e => e.key === 'Enter' && addTopic()}
                placeholder="e.g. Dijkstra Algorithm, SQL Joins..."
                className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
              <button onClick={addTopic} disabled={!newTopic.trim()} className="px-4 py-2.5 bg-blue-500 text-white text-sm rounded-xl disabled:opacity-40">Add</button>
            </div>
            {extraTopics.length > 0 && (
              <div className="flex gap-2 flex-wrap">
                {extraTopics.map(t => (
                  <span key={t} className="flex items-center gap-1.5 text-xs bg-purple-500/10 text-purple-400 border border-purple-500/20 px-3 py-1.5 rounded-full">
                    {t} <button onClick={() => setExtraTopics(p => p.filter(x => x !== t))} className="hover:text-red-400">✕</button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* PYQ Years */}
          {hasPyqs && dbYears.length > 0 && (
            <div className="border-t border-white/5 pt-4">
              <div className="flex items-center gap-3 mb-3">
                <button onClick={() => setUsePyqs(!usePyqs)}
                  className={'w-10 h-5 rounded-full transition-all relative flex-shrink-0 ' + (usePyqs ? 'bg-blue-500' : 'bg-slate-700')}>
                  <span className={'absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ' + (usePyqs ? 'left-5' : 'left-0.5')} />
                </button>
                <div>
                  <p className="text-sm font-semibold text-white">Include PYQ Style Questions</p>
                  <p className="text-xs text-slate-500">AI will style questions similar to previous year papers</p>
                </div>
              </div>
              {usePyqs && (
                <div>
                  <p className="text-xs text-slate-500 mb-2">Select years to reference:</p>
                  <div className="flex gap-2 flex-wrap">
                    {dbYears.map(y => (
                      <button key={y} onClick={() => togglePyqYear(y)}
                        className={'px-4 py-2 rounded-xl text-sm font-medium border transition-all ' +
                          (selectedPyqYears.includes(y) ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                        {y}
                      </button>
                    ))}
                    <button onClick={() => setSelectedPyqYears(selectedPyqYears.length === dbYears.length ? [] : [...dbYears])}
                      className="px-4 py-2 rounded-xl text-sm text-blue-400 border border-dashed border-blue-500/30">
                      {selectedPyqYears.length === dbYears.length ? 'Deselect All' : 'Select All Years'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Difficulty */}
          <div className="border-t border-white/5 pt-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Difficulty</p>
            <div className="flex gap-2 flex-wrap">
              {[['mixed','🎯 Mixed'],['easy','🟢 Easy'],['medium','🟡 Medium'],['hard','🔴 Hard']].map(([v,l]) => (
                <button key={v} onClick={() => setDifficulty(v)}
                  className={'px-4 py-2 rounded-xl text-xs font-medium border transition-all ' + (difficulty === v ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                  {l}
                </button>
              ))}
            </div>
          </div>

          {/* Summary */}
          {(selectedUnits.length > 0 || extraTopics.length > 0) && (
            <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-3">
              <p className="text-xs text-green-400 font-medium mb-1">✓ Ready to generate</p>
              <p className="text-xs text-slate-500">
                {selectedUnits.length} units + {extraTopics.length} extra topics
                {usePyqs && selectedPyqYears.length > 0 ? ' + PYQs from ' + selectedPyqYears.join(', ') : ''}
              </p>
            </div>
          )}

          <div className="flex gap-3">
            <button onClick={() => setStep(1)} className="px-5 py-3 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">← Back</button>
            <button onClick={() => setStep(3)} disabled={selectedUnits.length === 0 && extraTopics.length === 0}
              className="flex-1 py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600 disabled:opacity-40">
              Next: Configure Marks →
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Marks */}
      {step === 3 && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
          <h2 className="text-base font-semibold text-white mb-5">Configure Sections</h2>
          <div className="space-y-4 mb-6">
            {sections.map((sec, i) => (
              <div key={sec.name} className="bg-slate-800 rounded-xl p-4 border border-white/5">
                <div className="flex items-center gap-2 mb-3">
                  <span className={'text-xs px-2 py-0.5 rounded border font-semibold ' + sectionColors[sec.name]}>Section {sec.name}</span>
                  <span className="text-xs text-slate-500">{sec.marks}M each · attempt {sec.attempt}/{sec.total}</span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[['Total Qs','total',1,20],['Attempt','attempt',1,sec.total],['Marks Each','marks',1,25]].map(([l,f,mn,mx]) => (
                    <div key={f as string}>
                      <label className="block text-[10px] text-slate-500 uppercase mb-1">{l as string}</label>
                      <input type="number" value={sec[f as keyof Section]} onChange={e => updateSection(i, f as keyof Section, parseInt(e.target.value)||1)} min={mn as number} max={mx as number}
                        className="w-full bg-slate-700 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none" />
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
              {subject} · {selectedUnits.length + extraTopics.length} topics
              {usePyqs && selectedPyqYears.length > 0 ? ' + PYQs ' + selectedPyqYears.join(', ') : ''}
            </p>
          </div>
          {genError && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4">
              <p className="text-xs text-red-400">⚠️ {genError}</p>
            </div>
          )}
          <div className="flex gap-3">
            <button onClick={() => setStep(2)} className="px-5 py-3 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">← Back</button>
            <button onClick={generate} disabled={generating}
              className="flex-1 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-semibold rounded-xl disabled:opacity-40 flex items-center justify-center gap-2">
              {generating ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Generating from your units...</> : '🤖 Generate with AI'}
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Review */}
      {step === 4 && questions.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
            <div>
              <p className="text-sm font-semibold text-white">{selectedCount} questions</p>
              <p className="text-xs text-slate-500">Click text to edit · ✕ to delete · −/+ marks</p>
            </div>
            <div className="flex gap-2">
              <button onClick={regenerate} disabled={generating}
                className="px-4 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl border border-white/10 hover:border-white/20 disabled:opacity-40 flex items-center gap-1.5">
                {generating ? <div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> : '🔄'} Regenerate
              </button>
              <button onClick={savePaper} disabled={saving || selectedCount === 0}
                className="px-5 py-2 bg-green-500 text-white text-xs font-semibold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center gap-1.5">
                {saving ? <div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> : '💾'} Save Paper
              </button>
            </div>
          </div>

          {['A','B','C'].map(secName => {
            const secQs = questions.filter(q => q.section === secName)
            if (secQs.length === 0) return null
            const secConf = sections.find(s => s.name === secName)
            return (
              <div key={secName} className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className={'text-sm font-semibold px-3 py-1 rounded-lg border ' + sectionColors[secName]}>
                      Section {secName} — {secConf?.marks}M each
                    </span>
                    <span className="text-xs text-slate-500">{secQs.length} questions</span>
                  </div>
                  <button onClick={() => addQuestion(secName)} className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20">+ Add</button>
                </div>
                <div className="space-y-2">
                  {secQs.map((q, qi) => (
                    <div key={q.uid} className={'rounded-xl border p-4 ' + (q.selected ? 'bg-slate-900 border-white/5' : 'bg-slate-900/40 opacity-50')}>
                      <div className="flex items-start gap-3">
                        <input type="checkbox" checked={q.selected} onChange={() => toggleQ(q.uid)} className="mt-1 accent-blue-500 w-4 h-4 flex-shrink-0" />
                        <span className="text-xs text-slate-500 mt-1 flex-shrink-0">Q{qi+1}.</span>
                        <div className="flex-1 min-w-0">
                          <textarea value={q.text} onChange={e => editQ(q.uid, e.target.value)} placeholder="Question text..."
                            className="w-full bg-transparent text-sm text-white outline-none resize-none leading-relaxed"
                            rows={q.text.length > 120 ? 3 : 2} />
                          <div className="flex gap-2 mt-2 flex-wrap items-center">
                            <span className={'text-[10px] px-2 py-0.5 rounded border ' + (diffColors[q.difficulty] || 'text-slate-400 bg-slate-700 border-white/10')}>{q.difficulty}</span>
                            {q.unit && <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded border border-white/5">{q.unit}</span>}
                            <select value={q.section} onChange={e => editSection(q.uid, e.target.value)}
                              className="text-[10px] bg-slate-800 border border-white/10 rounded px-1 py-0.5 text-slate-400 outline-none">
                              <option value="A">Sec A</option><option value="B">Sec B</option><option value="C">Sec C</option>
                            </select>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <button onClick={() => editMarks(q.uid, Math.max(1, q.marks-1))} className="w-6 h-6 rounded bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center border border-white/5 text-sm">−</button>
                          <span className="text-xs font-bold text-blue-400 w-8 text-center">{q.marks}M</span>
                          <button onClick={() => editMarks(q.uid, q.marks+1)} className="w-6 h-6 rounded bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center border border-white/5 text-sm">+</button>
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
            <p className="text-sm font-semibold text-white">{selectedCount} questions · {questions.filter(q=>q.selected&&q.text.trim()).reduce((s,q)=>s+q.marks,0)} marks</p>
            <button onClick={savePaper} disabled={saving || selectedCount === 0}
              className="px-6 py-2.5 bg-green-500 text-white text-sm font-semibold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center gap-2">
              {saving ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Saving...</> : '💾 Save & Preview'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Generate page done!")

# Teacher Notifications - Alert system with class filter
os.makedirs("../frontend/app/(dashboard)/teacher/notifications", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/notifications/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type ClassSection = { id: string; name: string; section: string; branch: string; _count: { students: number } }
type Task = { id: string; title: string; classSectionId?: string | null }
type Notif = { id: string; title: string; body: string; type: string; isRead: boolean; createdAt: string }

export default function TeacherNotificationsPage() {
  const { data: session } = useSession()
  const [tab, setTab] = useState<'inbox'|'send'>('inbox')
  const [notifs, setNotifs] = useState<Notif[]>([])
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [filter, setFilter] = useState('all')
  const [sending, setSending] = useState(false)
  const [sendOk, setSendOk] = useState('')

  // Send form
  const [form, setForm] = useState({
    title: '', message: '', target: 'all_students',
    classIds: [] as string[],
    alertType: 'general', // general | task_reminder | deadline
    taskId: '',
    priority: 'normal',
  })

  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    const h = { Authorization: 'Bearer ' + token }
    Promise.all([
      fetch(API + '/notifications', { headers: h }).then(r => r.json()),
      fetch(API + '/auth/classes', { headers: h }).then(r => r.json()),
      fetch(API + '/tasks', { headers: h }).then(r => r.json()),
    ]).then(([n, c, t]) => {
      if (n.success) setNotifs(n.data || [])
      if (c.success) setClasses(c.data || [])
      if (t.success) setTasks(t.data || [])
    })
  }, [token])

  const unread = notifs.filter(n => !n.isRead).length

  const typeConf: Record<string,{icon:string;color:string;label:string}> = {
    task: { icon: '📋', color: 'text-blue-400 bg-blue-500/10 border-blue-500/20', label: 'Task' },
    result: { icon: '📊', color: 'text-green-400 bg-green-500/10 border-green-500/20', label: 'Result' },
    announcement: { icon: '📢', color: 'text-purple-400 bg-purple-500/10 border-purple-500/20', label: 'Update' },
    complaint: { icon: '💬', color: 'text-orange-400 bg-orange-500/10 border-orange-500/20', label: 'Alert' },
    system: { icon: '⚙️', color: 'text-slate-400 bg-slate-700 border-white/10', label: 'System' },
  }

  const markRead = async (id: string) => {
    await fetch(API + '/notifications/' + id + '/read', { method: 'PATCH', headers: { Authorization: 'Bearer ' + token } })
    setNotifs(p => p.map(n => n.id === id ? { ...n, isRead: true } : n))
  }

  const markAll = async () => {
    await fetch(API + '/notifications/read-all', { method: 'PATCH', headers: { Authorization: 'Bearer ' + token } })
    setNotifs(p => p.map(n => ({ ...n, isRead: true })))
  }

  const toggleClass = (id: string) => setForm(p => ({ ...p, classIds: p.classIds.includes(id) ? p.classIds.filter(c => c !== id) : [...p.classIds, id] }))

  const handleSend = async () => {
    if (!form.title || !form.message || !token) return
    setSending(true); setSendOk('')

    // Auto-fill message for task reminder
    let title = form.title
    let body = form.message
    if (form.alertType === 'task_reminder' && form.taskId) {
      const task = tasks.find(t => t.id === form.taskId)
      title = '⚠️ Reminder: ' + (task?.title || 'Task')
      body = form.message || 'Please complete "' + (task?.title || 'task') + '" before the deadline!'
    }

    const res = await fetch(API + '/notifications/send', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, body, type: 'announcement', target: form.target, classIds: form.classIds })
    })
    const d = await res.json()
    if (d.success) {
      setSendOk('✓ Alert sent to ' + d.data.sent + ' students!')
      setForm(p => ({ ...p, title: '', message: '' }))
      setTimeout(() => setSendOk(''), 3000)
    }
    setSending(false)
  }

  const filtered = filter === 'all' ? notifs : filter === 'unread' ? notifs.filter(n => !n.isRead) : notifs.filter(n => n.type === filter)

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Notifications & Alerts</h1>
          <p className="text-slate-400 text-sm">{unread} unread</p>
        </div>
      </div>

      <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-xl p-1 mb-6 w-fit">
        <button onClick={() => setTab('inbox')} className={'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ' + (tab === 'inbox' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
          📥 Inbox {unread > 0 && <span className="bg-white/20 text-xs px-1.5 rounded-full">{unread}</span>}
        </button>
        <button onClick={() => setTab('send')} className={'px-4 py-2 rounded-lg text-sm font-medium transition-all ' + (tab === 'send' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
          📢 Send Alert
        </button>
      </div>

      {tab === 'inbox' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex gap-2 flex-wrap">
              {['all','unread','task','complaint','announcement'].map(f => (
                <button key={f} onClick={() => setFilter(f)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filter === f ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>
                  {f.charAt(0).toUpperCase()+f.slice(1)}
                </button>
              ))}
            </div>
            {unread > 0 && <button onClick={markAll} className="text-xs text-blue-400 hover:text-blue-300">Mark all read</button>}
          </div>
          {filtered.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">🔕</p><p className="text-white font-medium">No notifications</p>
            </div>
          ) : (
            <div className="space-y-2">
              {filtered.map(n => {
                const tc = typeConf[n.type] || typeConf.system
                return (
                  <div key={n.id} onClick={() => !n.isRead && markRead(n.id)}
                    className={'flex items-start gap-4 p-4 rounded-2xl border cursor-pointer transition-all ' + (!n.isRead ? 'bg-slate-900 border-blue-500/20 hover:border-blue-500/30' : 'bg-slate-900 border-white/5 hover:border-white/10')}>
                    <div className={'w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0 border ' + tc.color}>{tc.icon}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-medium text-white">{n.title}</p>
                        {!n.isRead && <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />}
                        <span className={'text-[10px] px-1.5 py-0.5 rounded border font-medium ml-auto flex-shrink-0 ' + tc.color}>{tc.label}</span>
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed">{n.body}</p>
                      <p className="text-[10px] text-slate-600 mt-1">{new Date(n.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true })}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {tab === 'send' && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6 space-y-5">
          <h2 className="text-base font-semibold text-white">Send Alert to Students</h2>

          {/* Alert type */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Alert Type</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { k: 'general', i: '📢', l: 'General Update' },
                { k: 'task_reminder', i: '⚠️', l: 'Task Reminder' },
                { k: 'deadline', i: '⏰', l: 'Deadline Alert' },
              ].map(opt => (
                <button key={opt.k} onClick={() => setForm(p => ({ ...p, alertType: opt.k }))}
                  className={'p-3 rounded-xl border text-center transition-all ' + (form.alertType === opt.k ? 'border-blue-500/50 bg-blue-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                  <p className="text-xl">{opt.i}</p>
                  <p className="text-xs font-medium text-white mt-1">{opt.l}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Task selection for task reminder */}
          {form.alertType === 'task_reminder' && (
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Select Task</p>
              <select value={form.taskId} onChange={e => setForm(p => ({ ...p, taskId: e.target.value }))}
                className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none">
                <option value="">-- Select Task --</option>
                {tasks.filter(t => t).map(t => <option key={t.id} value={t.id}>{t.title}</option>)}
              </select>
            </div>
          )}

          {/* Send to */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Send To</p>
            <div className="grid grid-cols-2 gap-2 mb-3">
              {[
                { v: 'all_students', l: '👥 All Students', d: 'Every student in college' },
                { v: 'specific_classes', l: '🏫 Specific Classes', d: 'Select classes below' },
              ].map(opt => (
                <button key={opt.v} onClick={() => setForm(p => ({ ...p, target: opt.v, classIds: [] }))}
                  className={'p-3 rounded-xl border text-left transition-all ' + (form.target === opt.v ? 'border-blue-500/50 bg-blue-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                  <p className="text-sm font-medium text-white">{opt.l}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{opt.d}</p>
                </button>
              ))}
            </div>
            {form.target === 'specific_classes' && (
              <div className="flex gap-2 flex-wrap">
                {classes.map(c => (
                  <button key={c.id} onClick={() => toggleClass(c.id)}
                    className={'px-3 py-2 rounded-xl text-xs font-medium border transition-all ' + (form.classIds.includes(c.id) ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                    {c.name} {c.section} ({c._count.students})
                    {form.classIds.includes(c.id) && ' ✓'}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Title + Message */}
          <div>
            <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Alert Title</label>
            <input type="text" value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))}
              placeholder={form.alertType === 'task_reminder' ? 'Auto-filled from task...' : 'Alert title...'}
              className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
          </div>
          <div>
            <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Message</label>
            <textarea value={form.message} onChange={e => setForm(p => ({ ...p, message: e.target.value }))}
              placeholder="Write your message..."
              rows={3}
              className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 resize-none" />
          </div>

          <div className="bg-blue-500/5 border border-blue-500/15 rounded-xl p-3">
            <p className="text-xs text-blue-400 font-medium mb-1">📱 About Phone Notifications</p>
            <p className="text-xs text-slate-400">Notifications appear in students' AIQPG app. For Outlook/email alerts, students should add their email in their profile settings.</p>
          </div>

          {sendOk && <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3 text-xs text-green-400">{sendOk}</div>}

          <button onClick={handleSend}
            disabled={!form.title || !form.message || sending || (form.target === 'specific_classes' && form.classIds.length === 0)}
            className={'w-full py-3 text-sm font-semibold rounded-xl transition-all flex items-center justify-center gap-2 ' +
              (sendOk ? 'bg-green-500 text-white' : 'bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-40')}>
            {sending ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Sending...</>
              : sendOk ? '✓ Sent!'
              : '📢 Send Alert'}
          </button>
        </div>
      )}
    </div>
  )
}
""")
print("Teacher Notifications done!")

# Student Dashboard - My Class + Alert teacher + class-specific data
with open("../frontend/app/(student)/student/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import Link from 'next/link'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type ClassSection = { id: string; name: string; section: string; branch: string; semester: number; year: number; uniqueCode: string; _count: { students: number } }

export default function StudentDashboard() {
  const { data: session, status } = useSession()
  const [myClass, setMyClass] = useState<ClassSection | null>(null)
  const [allClasses, setAllClasses] = useState<ClassSection[]>([])
  const [tasks, setTasks] = useState<any[]>([])
  const [materials, setMaterials] = useState<any[]>([])
  const [submissions, setSubmissions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [dataLoading, setDataLoading] = useState(false)
  const [showClassPicker, setShowClassPicker] = useState(false)
  const [showAlert, setShowAlert] = useState(false)
  const [alertMsg, setAlertMsg] = useState('')
  const [alertSent, setAlertSent] = useState(false)
  const [error, setError] = useState('')
  const token = session?.user?.backendToken

  // Load my class from API
  useEffect(() => {
    if (status === 'loading' || !token) return
    const h = { Authorization: 'Bearer ' + token }

    Promise.all([
      fetch(API + '/auth/me', { headers: h }).then(r => r.json()),
      fetch(API + '/auth/classes', { headers: h }).then(r => r.json()),
    ]).then(([me, cls]) => {
      if (me.success && me.data?.classSection) {
        setMyClass(me.data.classSection)
        localStorage.setItem('myClassId', me.data.classSection.id)
      }
      if (cls.success) setAllClasses(cls.data || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [token, status])

  // Load class-specific data
  useEffect(() => {
    if (!token || loading) return
    setDataLoading(true)
    const classId = myClass?.id || localStorage.getItem('myClassId') || ''
    const h = { Authorization: 'Bearer ' + token }
    const taskUrl = classId ? API + '/tasks?classId=' + classId : API + '/tasks'
    const matUrl = classId ? API + '/materials?classId=' + classId : API + '/materials'

    Promise.all([
      fetch(taskUrl, { headers: h }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
      fetch(matUrl, { headers: h }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
      fetch(API + '/submissions', { headers: h }).then(r => r.json()).catch(() => ({ success: false, data: [] })),
    ]).then(([t, m, s]) => {
      if (t.success) setTasks(t.data || [])
      if (m.success) setMaterials(m.data || [])
      if (s.success) setSubmissions(s.data || [])
      if (!t.success) setError('Could not load tasks. Backend running?')
    }).catch(e => setError('Network error: ' + e.message))
    .finally(() => setDataLoading(false))
  }, [token, loading, myClass])

  const switchClass = async (cls: ClassSection) => {
    if (!token) return
    await fetch(API + '/auth/select-class', {
      method: 'PATCH',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ classSectionId: cls.id })
    })
    setMyClass(cls)
    localStorage.setItem('myClassId', cls.id)
    setShowClassPicker(false)
    setTasks([]); setMaterials([]); setSubmissions([])
  }

  const sendAlertToTeacher = async () => {
    if (!token || !myClass) return
    const res = await fetch(API + '/notifications/student-alert', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ classSectionId: myClass.id, message: alertMsg || 'Please upload study materials for our class!' })
    })
    const d = await res.json()
    if (d.success) { setAlertSent(true); setTimeout(() => { setShowAlert(false); setAlertSent(false); setAlertMsg('') }, 2000) }
  }

  const notes = materials.filter(m => !m.isPyq)
  const pyqs = materials.filter(m => m.isPyq)
  const subIds = submissions.map(s => s.taskId)
  const pending = tasks.filter(t => !subIds.includes(t.id))
  const graded = submissions.filter(s => s.status === 'graded')
  const noData = !dataLoading && tasks.length === 0 && materials.length === 0

  const typeIcon: Record<string,string> = { assignment:'📝', class_test:'✍️', quiz:'❓', project:'🔬' }
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
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Welcome, {session?.user?.name?.split(' ')[0]} 👋</h1>
          <p className="text-slate-400 text-sm">Your academic overview</p>
        </div>
        {/* Class Switcher */}
        <div className="relative">
          <button onClick={() => setShowClassPicker(!showClassPicker)}
            className="flex items-center gap-3 bg-slate-900 border border-white/10 hover:border-green-500/30 rounded-xl px-4 py-3 transition-all">
            <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center text-green-400 font-bold text-sm">
              {myClass ? myClass.section : '?'}
            </div>
            <div className="text-left">
              <p className="text-xs font-semibold text-white">{myClass ? myClass.name + ' — Sec ' + myClass.section : 'Select My Class'}</p>
              <p className="text-[10px] text-slate-500">{myClass ? myClass.branch + ' · Sem ' + myClass.semester : 'Tap to choose'}</p>
            </div>
            <span className="text-slate-500 text-xs">{showClassPicker ? '▲' : '▼'}</span>
          </button>

          {showClassPicker && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden">
              <div className="p-3 border-b border-white/5">
                <p className="text-xs text-slate-400 font-medium">My Class</p>
                <p className="text-[10px] text-slate-500">Data will filter to selected class</p>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {allClasses.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500">No classes available</div>
                ) : allClasses.map(cls => (
                  <button key={cls.id} onClick={() => switchClass(cls)}
                    className={'w-full p-3 text-left hover:bg-slate-800 transition-all flex items-center gap-3 ' + (cls.id === myClass?.id ? 'bg-green-500/10' : '')}>
                    <div className={'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ' + (cls.id === myClass?.id ? 'bg-green-500 text-white' : 'bg-slate-800 text-slate-400')}>
                      {cls.section}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">{cls.name} — Sec {cls.section}</p>
                      <p className="text-xs text-slate-500">{cls.branch} · Sem {cls.semester} · {cls._count.students} students</p>
                    </div>
                    {cls.id === myClass?.id && <span className="text-green-400 text-xs">✓ Current</span>}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {showClassPicker && <div className="fixed inset-0 z-40" onClick={() => setShowClassPicker(false)} />}

      {/* Class info */}
      {myClass && (
        <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/20 rounded-2xl p-4 mb-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center text-xl">🏫</div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">{myClass.name} — Section {myClass.section}</p>
            <p className="text-xs text-slate-400">{myClass.branch} · Semester {myClass.semester} · Code: <span className="text-green-400 font-mono">{myClass.uniqueCode}</span></p>
          </div>
          <div className="text-right">
            <p className="text-lg font-bold text-green-400">{myClass._count.students}</p>
            <p className="text-[10px] text-slate-500">classmates</p>
          </div>
        </div>
      )}

      {/* No data alert */}
      {myClass && noData && !dataLoading && (
        <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-4 mb-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm text-yellow-400 font-medium">📭 No content in {myClass.name} — Sec {myClass.section} yet</p>
              <p className="text-xs text-slate-500 mt-1">Your teacher hasn't uploaded tasks or materials for this class yet.</p>
            </div>
            <button onClick={() => setShowAlert(true)}
              className="text-xs px-3 py-2 bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded-xl hover:bg-yellow-500/30 flex-shrink-0 whitespace-nowrap">
              🔔 Alert Teacher
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4">
          <p className="text-red-400 text-xs">⚠️ {error}</p>
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
          <p className="text-slate-500 text-xs">Loading {myClass?.name || 'your'} data...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pending Tasks */}
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">📋 Pending ({pending.length})</h2>
              <Link href="/student/assignments" className="text-xs text-blue-400">View all →</Link>
            </div>
            {pending.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-3xl mb-2">{tasks.length === 0 ? '📭' : '🎉'}</p>
                <p className="text-slate-400 text-sm">{tasks.length === 0 ? 'No tasks yet' : 'All submitted!'}</p>
              </div>
            ) : (
              <div className="space-y-2">
                {pending.slice(0,4).map(t => {
                  const dl = getDL(t.deadline)
                  return (
                    <div key={t.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                      <span className="text-xl flex-shrink-0">{typeIcon[t.taskType] || '📋'}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-white truncate">{t.title}</p>
                        <p className="text-[10px] text-slate-500">{t.subjectName || 'General'} · {t.maxMarks}M</p>
                      </div>
                      <span className={'text-[10px] font-semibold ' + dl.color}>{dl.label}</span>
                    </div>
                  )
                })}
              </div>
            )}
            {pending.length > 0 && (
              <Link href="/student/assignments">
                <button className="w-full mt-3 py-2.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-xl text-xs font-medium hover:bg-blue-500/20">📤 Submit Assignments</button>
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
              <div className="text-center py-6"><p className="text-3xl mb-2">📭</p><p className="text-slate-400 text-sm">No notes yet</p></div>
            ) : (
              <div className="space-y-2">
                {notes.slice(0,4).map(m => (
                  <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                    <span className="text-xl flex-shrink-0">📚</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{m.title}</p>
                      <div className="flex gap-2">
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
              <h2 className="text-sm font-semibold text-white">📄 PYQs ({pyqs.length})</h2>
              <Link href="/student/materials" className="text-xs text-blue-400">View all →</Link>
            </div>
            {pyqs.length === 0 ? (
              <div className="text-center py-6"><p className="text-3xl mb-2">📄</p><p className="text-slate-400 text-sm">No PYQs yet</p></div>
            ) : (
              <div className="space-y-2">
                {pyqs.slice(0,4).map(m => (
                  <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                    <span className="text-xl flex-shrink-0">📄</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{m.title}</p>
                      <div className="flex gap-2">
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
                  <p className="text-xs font-semibold text-green-400">📊 {graded.length} results available</p>
                  <span className="text-green-400 text-sm">→</span>
                </div>
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Alert Teacher Modal */}
      {showAlert && myClass && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-md p-6">
            <h2 className="text-base font-semibold text-white mb-2">🔔 Alert Teacher</h2>
            <p className="text-xs text-slate-500 mb-4">Send a notification to your teacher that data is missing in {myClass.name} — Sec {myClass.section}</p>
            <textarea value={alertMsg} onChange={e => setAlertMsg(e.target.value)}
              placeholder="Optional: Add a specific message (e.g. Please upload Unit 2 notes)"
              rows={3}
              className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-yellow-500/50 placeholder:text-slate-600 resize-none mb-4" />
            {alertSent && <p className="text-xs text-green-400 mb-3">✓ Alert sent to all teachers!</p>}
            <div className="flex gap-3">
              <button onClick={() => { setShowAlert(false); setAlertMsg('') }} className="flex-1 py-2.5 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">Cancel</button>
              <button onClick={sendAlertToTeacher} disabled={alertSent}
                className="flex-1 py-2.5 bg-yellow-500 text-white text-sm font-semibold rounded-xl hover:bg-yellow-600 disabled:opacity-40">
                {alertSent ? '✓ Sent!' : '🔔 Send Alert'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Student Dashboard done!")

print("\n=== ALL FRONTEND DONE ===")