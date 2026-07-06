import os

# ═══════════════════════════════════════════
# FIX 1: Student Layout - FORCE class selection
# ═══════════════════════════════════════════
with open("../frontend/app/(student)/layout.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter, usePathname } from 'next/navigation'
import StudentSidebar from '@/components/student/StudentSidebar'
import StudentNavbar from '@/components/student/StudentNavbar'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

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

    // Check if student has joined a class via API
    const token = session.user.backendToken
    if (!token) { setReady(true); return }

    fetch(API + '/auth/me', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(data => {
        const hasClass = data.data?.classSection !== null && data.data?.classSection !== undefined
        const skipped = localStorage.getItem('studentClassSelected')
        if (!hasClass && !skipped) {
          router.push('/student/select-class')
        } else {
          setReady(true)
        }
      })
      .catch(() => setReady(true))
  }, [session, status, pathname])

  if (!ready) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Loading...</p>
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
print("Student layout fixed!")

# ═══════════════════════════════════════════
# FIX 2: Generate Questions - Real AI with unique questions
# ═══════════════════════════════════════════
with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import { success, error } from '../utils/response'

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions'
const GROQ_KEY = process.env.GROQ_API_KEY || ''

async function callGroq(systemPrompt: string, userMsg: string, maxTokens = 2048): Promise<string> {
  const res = await fetch(GROQ_API, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + GROQ_KEY,
    },
    body: JSON.stringify({
      model: "llama-3.1-8b-instant",
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMsg }
      ],
      max_tokens: maxTokens,
      temperature: 0.9,
    })
  })
  if (!res.ok) throw new Error('Groq error: ' + await res.text())
  const data = await res.json()
  return data.choices?.[0]?.message?.content || ''
}

export const generateQuestions = async (req: Request, res: Response) => {
  try {
    const { subject, units, sections, difficulty } = req.body

    const systemPrompt = `You are a senior university professor at K.R Mangalam University with 20+ years of experience creating exam papers.
Your questions must be:
- UNIQUE and DIFFERENT from each other
- SPECIFIC to the exact topic/unit asked
- Academically rigorous and university-level
- Varied in approach (definitions, applications, comparisons, problem-solving, diagrams)
Return ONLY a valid JSON array. No markdown, no extra text, no backticks.`

    // Build detailed sections description
    const sectionsDesc = (sections || []).map((s: any) =>
      `Section ${s.name}: Generate exactly ${s.total} UNIQUE questions of ${s.marks} marks each. Student will attempt ${s.attempt}.`
    ).join('\n')

    const unitsList = (units || [subject]).join(', ')
    const randomSeed = Math.random().toString(36).substring(7)

    const userMsg = `Create a UNIQUE exam question paper (seed:${randomSeed}) for:

Subject: ${subject}
Topics to cover: ${unitsList}
Difficulty: ${difficulty || 'mixed (30% easy, 50% medium, 20% hard)'}

${sectionsDesc}

IMPORTANT RULES:
1. Every question must be DIFFERENT - no repetition
2. Cover DIFFERENT aspects of ${subject} in each question
3. For Section A (short): definitions, fill-in-blanks style, one-line answers
4. For Section B (medium): explain with examples, compare and contrast, list with explanation
5. For Section C (long): detailed essays, case studies, design problems, critical analysis
6. Reference these specific topics: ${unitsList}
7. Include variety: theory, application, analysis, design

Return JSON array:
[
  {
    "id": 1,
    "section": "A",
    "questionNo": 1,
    "text": "UNIQUE specific question text here",
    "marks": 2,
    "unit": "specific unit name",
    "difficulty": "easy",
    "type": "short"
  }
]`

    const raw = await callGroq(systemPrompt, userMsg, 3000)

    let questions = []
    try {
      // Extract JSON array from response
      const match = raw.match(/\\[\\s*\\{.*\\}\\s*\\]/s)
      if (match) {
        questions = JSON.parse(match[0])
      } else {
        const cleaned = raw.replace(/```json|```/g, '').trim()
        questions = JSON.parse(cleaned)
      }
    } catch (parseErr) {
      console.error('Parse error, raw:', raw.substring(0, 200))
      return error(res, 'AI response parse failed. Please try again.', 500)
    }

    return success(res, { questions, metadata: { subject, totalQuestions: questions.length, units: unitsList } })
  } catch (err: any) {
    console.error('Generate error:', err.message)
    return error(res, 'Generation failed: ' + err.message, 500)
  }
}

export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history } = req.body
    const systemPrompt = `You are an expert academic tutor for K.R Mangalam University students.
Subject expertise: ${subject || 'all subjects'}
Style: Clear, concise, use examples. For code use proper formatting. For math use clear notation.
When asked for questions, give numbered questions with model answers.
When explaining concepts, use: Definition → Explanation → Example → Application`

    const msgs = [
      ...(history || []).slice(-6).map((h: any) => ({ role: h.role, content: h.content })),
      { role: 'user', content: message }
    ]

    const res2 = await fetch(GROQ_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
      body: JSON.stringify({
        model: "llama-3.1-8b-instant",
        messages: [{ role: 'system', content: systemPrompt }, ...msgs],
        max_tokens: 1024,
        temperature: 0.7,
      })
    })
    const data = await res2.json()
    const reply = data.choices?.[0]?.message?.content || 'Sorry, could not generate response.'
    return success(res, { reply })
  } catch (err: any) {
    return error(res, 'Chat failed: ' + err.message, 500)
  }
}

export const checkAnswer = async (req: Request, res: Response) => {
  try {
    const { question, answer, subject, marks } = req.body
    const raw = await callGroq(
      'You are a strict university professor. Return ONLY valid JSON.',
      `Grade this answer:
Question: ${question}
Student Answer: ${answer}
Subject: ${subject}
Max Marks: ${marks}

Return: {"marksAwarded":number,"percentage":number,"grade":"A/B/C/D/F","feedback":"detailed feedback","strengths":["point1"],"improvements":["area1"]}`
    )
    const match = raw.match(/\\{.*\\}/s)
    const result = JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim())
    return success(res, result)
  } catch (err: any) {
    return error(res, 'Check failed: ' + err.message, 500)
  }
}
""")
print("AI controller fixed!")

# ═══════════════════════════════════════════
# FIX 3: Generate Questions Frontend
# ═══════════════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/generate", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/generate/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

const SUBJECTS = [
  'Data Structures and Algorithms', 'Operating Systems', 'Computer Networks',
  'Database Management Systems', 'Software Engineering', 'Artificial Intelligence',
  'Machine Learning', 'Web Technologies', 'Object Oriented Programming',
  'Discrete Mathematics', 'Computer Organization and Architecture',
  'Theory of Computation', 'Compiler Design', 'Digital Electronics',
  'Mathematics', 'Physics', 'Chemistry', 'English', 'Management',
]

const ALL_UNITS: Record<string, string[]> = {
  'Data Structures and Algorithms': ['Unit 1: Arrays, Linked Lists, Stacks, Queues', 'Unit 2: Trees, BST, AVL Trees, Heap', 'Unit 3: Graphs, BFS, DFS, Shortest Path', 'Unit 4: Sorting and Searching Algorithms', 'Unit 5: Dynamic Programming, Greedy Algorithms, Backtracking'],
  'Operating Systems': ['Unit 1: Process Management and Scheduling', 'Unit 2: Memory Management, Paging, Segmentation', 'Unit 3: File Systems and I/O Management', 'Unit 4: Deadlocks Detection and Prevention', 'Unit 5: Synchronization, Semaphores, Monitors'],
  'Computer Networks': ['Unit 1: Network Models, OSI, TCP/IP', 'Unit 2: Data Link Layer, Framing, Error Control', 'Unit 3: Network Layer, IP, Routing Protocols', 'Unit 4: Transport Layer, TCP, UDP, Flow Control', 'Unit 5: Application Layer, HTTP, DNS, SMTP'],
  'Database Management Systems': ['Unit 1: ER Model, Relational Model', 'Unit 2: SQL and Relational Algebra', 'Unit 3: Normalization, Functional Dependencies', 'Unit 4: Transaction Management, ACID Properties', 'Unit 5: Concurrency Control, Recovery'],
  'Software Engineering': ['Unit 1: SDLC Models, Agile, Scrum', 'Unit 2: Requirements Engineering', 'Unit 3: Software Design, UML Diagrams', 'Unit 4: Software Testing, Test Cases', 'Unit 5: Project Management, Risk Analysis'],
  'Artificial Intelligence': ['Unit 1: Search Algorithms, BFS, DFS, A*', 'Unit 2: Knowledge Representation, Logic', 'Unit 3: Planning and Expert Systems', 'Unit 4: Machine Learning Basics', 'Unit 5: Neural Networks, NLP Basics'],
  'Machine Learning': ['Unit 1: Supervised Learning, Regression', 'Unit 2: Classification, Decision Trees, SVM', 'Unit 3: Unsupervised Learning, Clustering', 'Unit 4: Neural Networks, Deep Learning', 'Unit 5: Evaluation Metrics, Model Selection'],
  'Web Technologies': ['Unit 1: HTML5, CSS3, Responsive Design', 'Unit 2: JavaScript, DOM, ES6+', 'Unit 3: React.js, Angular, Vue.js', 'Unit 4: Node.js, Express, REST APIs', 'Unit 5: Databases, MongoDB, Deployment'],
  'Object Oriented Programming': ['Unit 1: Classes, Objects, Encapsulation', 'Unit 2: Inheritance, Polymorphism', 'Unit 3: Abstraction, Interfaces, Abstract Classes', 'Unit 4: Exception Handling, Generics', 'Unit 5: Design Patterns, SOLID Principles'],
  'Discrete Mathematics': ['Unit 1: Sets, Relations, Functions', 'Unit 2: Logic, Propositional Calculus', 'Unit 3: Graph Theory', 'Unit 4: Combinatorics and Probability', 'Unit 5: Algebraic Structures, Groups'],
}

type Section = { name: string; total: number; attempt: number; marks: number }
type Question = { id: number; section: string; questionNo: number; text: string; marks: number; unit: string; difficulty: string; type: string; selected?: boolean }

export default function GeneratePage() {
  const { data: session } = useSession()
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [subject, setSubject] = useState('')
  const [selectedUnits, setSelectedUnits] = useState<string[]>([])
  const [difficulty, setDifficulty] = useState('mixed')
  const [sections, setSections] = useState<Section[]>([
    { name: 'A', total: 5, attempt: 5, marks: 2 },
    { name: 'B', total: 3, attempt: 3, marks: 5 },
    { name: 'C', total: 2, attempt: 2, marks: 10 },
  ])
  const [questions, setQuestions] = useState<Question[]>([])
  const [generating, setGenerating] = useState(false)
  const [genError, setGenError] = useState('')
  const [saving, setSaving] = useState(false)
  const token = session?.user?.backendToken

  const units = ALL_UNITS[subject] || ['Unit 1', 'Unit 2', 'Unit 3', 'Unit 4', 'Unit 5']

  const toggleUnit = (u: string) => {
    setSelectedUnits(prev => prev.includes(u) ? prev.filter(x => x !== u) : [...prev, u])
  }

  const updateSection = (idx: number, field: keyof Section, val: number) => {
    setSections(prev => prev.map((s, i) => i === idx ? { ...s, [field]: val } : s))
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
          units: selectedUnits.length > 0 ? selectedUnits : units,
          sections,
          difficulty,
        })
      })
      const data = await res.json()
      if (data.success && data.data.questions?.length > 0) {
        setQuestions(data.data.questions.map((q: Question) => ({ ...q, selected: true })))
        setStep(4)
      } else {
        setGenError(data.message || 'No questions generated. Check if GROQ_API_KEY is set in backend .env')
      }
    } catch (e: any) {
      setGenError('Connection error: ' + e.message)
    }
    setGenerating(false)
  }

  const regenerate = () => {
    setQuestions([])
    generate()
  }

  const toggleQ = (id: number) => {
    setQuestions(prev => prev.map(q => q.id === id ? { ...q, selected: !q.selected } : q))
  }

  const editQ = (id: number, text: string) => {
    setQuestions(prev => prev.map(q => q.id === id ? { ...q, text } : q))
  }

  const deleteQ = (id: number) => {
    setQuestions(prev => prev.filter(q => q.id !== id))
  }

  const savePaper = async () => {
    if (!token) return
    setSaving(true)
    const selected = questions.filter(q => q.selected !== false)
    const totalMarks = selected.reduce((s, q) => s + q.marks, 0)
    const res = await fetch(API + '/papers', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: subject + ' — ' + new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
        subject, examType: 'end_term', totalMarks, duration: 180,
        questions: selected,
      })
    })
    const data = await res.json()
    if (data.success) router.push('/teacher/generate/preview?id=' + data.data.id)
    setSaving(false)
  }

  const diffColors: Record<string, string> = {
    easy: 'text-green-400 bg-green-500/10 border-green-500/20',
    medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    hard: 'text-red-400 bg-red-500/10 border-red-500/20',
  }

  const sectionColors: Record<string, string> = {
    A: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    B: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
    C: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  }

  const totalMarks = sections.reduce((s, sec) => s + sec.attempt * sec.marks, 0)

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">Generate Question Paper</h1>
        <p className="text-slate-400 text-sm">AI-powered unique question generation</p>
      </div>

      {/* Step indicator */}
      <div className="flex gap-2 mb-8">
        {['Subject', 'Units', 'Marks', 'Review'].map((label, i) => (
          <div key={i} className="flex items-center gap-2 flex-1">
            <div className={'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0 border ' +
              (step > i+1 ? 'bg-green-500 border-green-500 text-white' :
               step === i+1 ? 'bg-blue-500 border-blue-500 text-white' :
               'bg-slate-800 border-white/10 text-slate-500')}>
              {step > i+1 ? '✓' : i+1}
            </div>
            <div className="flex-1 min-w-0">
              <p className={'text-xs font-medium ' + (step === i+1 ? 'text-white' : step > i+1 ? 'text-green-400' : 'text-slate-600')}>{label}</p>
            </div>
            {i < 3 && <div className={'h-px flex-1 ' + (step > i+1 ? 'bg-green-500' : 'bg-slate-700')} />}
          </div>
        ))}
      </div>

      {/* Step 1: Subject */}
      {step === 1 && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
          <h2 className="text-base font-semibold text-white mb-5">Select Subject</h2>
          <div className="grid grid-cols-2 gap-2 mb-6">
            {SUBJECTS.map(s => (
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

      {/* Step 2: Units */}
      {step === 2 && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-semibold text-white">Select Units for {subject}</h2>
            <button onClick={() => {
              if (selectedUnits.length === units.length) setSelectedUnits([])
              else setSelectedUnits([...units])
            }} className="text-xs text-blue-400 hover:text-blue-300">
              {selectedUnits.length === units.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          <div className="mb-4">
            <p className="text-xs text-slate-500 mb-2">Difficulty Mix</p>
            <div className="flex gap-2">
              {[['mixed', '🎯 Mixed (Recommended)'], ['easy', '🟢 Easy'], ['medium', '🟡 Medium'], ['hard', '🔴 Hard']].map(([v, l]) => (
                <button key={v} onClick={() => setDifficulty(v)} className={'px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ' + (difficulty === v ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                  {l}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2 mb-6">
            {units.map(u => (
              <button key={u} onClick={() => toggleUnit(u)} className={'w-full p-4 rounded-xl border text-left transition-all flex items-center gap-3 ' + (selectedUnits.includes(u) ? 'border-blue-500/40 bg-blue-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                <div className={'w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 ' + (selectedUnits.includes(u) ? 'bg-blue-500 border-blue-500' : 'border-white/20')}>
                  {selectedUnits.includes(u) && <span className="text-white text-xs font-bold">✓</span>}
                </div>
                <p className="text-sm text-white">{u}</p>
              </button>
            ))}
          </div>

          <div className="flex gap-3">
            <button onClick={() => setStep(1)} className="px-5 py-3 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">← Back</button>
            <button onClick={() => setStep(3)} className="flex-1 py-3 bg-blue-500 text-white text-sm font-semibold rounded-xl hover:bg-blue-600">
              Next: Configure Marks → {selectedUnits.length > 0 ? '(' + selectedUnits.length + ' units selected)' : '(all units)'}
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
                  <span className={'text-xs px-2 py-0.5 rounded border font-semibold ' + (sectionColors[sec.name] || 'text-white border-white/10 bg-white/5')}>Section {sec.name}</span>
                  <span className="text-xs text-slate-500">{sec.marks} marks each · {sec.attempt} to attempt out of {sec.total}</span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[10px] text-slate-500 uppercase mb-1">Total Questions</label>
                    <input type="number" value={sec.total} onChange={e => updateSection(i, 'total', parseInt(e.target.value))} min={1} max={20} className="w-full bg-slate-700 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50" />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-500 uppercase mb-1">To Attempt</label>
                    <input type="number" value={sec.attempt} onChange={e => updateSection(i, 'attempt', parseInt(e.target.value))} min={1} max={sec.total} className="w-full bg-slate-700 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50" />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-500 uppercase mb-1">Marks Each</label>
                    <input type="number" value={sec.marks} onChange={e => updateSection(i, 'marks', parseInt(e.target.value))} min={1} max={25} className="w-full bg-slate-700 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50" />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 mb-6">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Total Marks</span>
              <span className="text-blue-400 font-bold text-lg">{totalMarks}</span>
            </div>
            <div className="flex items-center justify-between text-xs mt-1">
              <span className="text-slate-500">Subject</span>
              <span className="text-slate-400">{subject}</span>
            </div>
            {selectedUnits.length > 0 && (
              <div className="flex items-center justify-between text-xs mt-1">
                <span className="text-slate-500">Units selected</span>
                <span className="text-slate-400">{selectedUnits.length}</span>
              </div>
            )}
          </div>

          {genError && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4">
              <p className="text-xs text-red-400">⚠️ {genError}</p>
              <p className="text-xs text-slate-500 mt-1">Tip: Get free key at console.groq.com and add GROQ_API_KEY to backend .env</p>
            </div>
          )}

          <div className="flex gap-3">
            <button onClick={() => setStep(2)} className="px-5 py-3 bg-slate-800 text-slate-300 text-sm rounded-xl border border-white/5">← Back</button>
            <button onClick={generate} disabled={generating} className="flex-1 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-semibold rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-40 flex items-center justify-center gap-2">
              {generating ? (
                <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Generating unique questions with AI...</>
              ) : '🤖 Generate Questions with AI'}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Review */}
      {step === 4 && questions.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-5">
            <div>
              <p className="text-sm font-semibold text-white">{questions.filter(q => q.selected !== false).length} questions generated</p>
              <p className="text-xs text-slate-500">{subject} · Click to edit · Deselect to remove</p>
            </div>
            <div className="flex gap-2">
              <button onClick={regenerate} disabled={generating} className="px-4 py-2 bg-slate-800 text-slate-300 text-xs font-medium rounded-xl border border-white/10 hover:border-white/20 disabled:opacity-40 flex items-center gap-1.5">
                {generating ? <div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> : '🔄'} Regenerate
              </button>
              <button onClick={savePaper} disabled={saving || questions.filter(q => q.selected !== false).length === 0} className="px-4 py-2 bg-green-500 text-white text-xs font-semibold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center gap-1.5">
                {saving ? <div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> : '💾'} Save as Paper
              </button>
            </div>
          </div>

          {['A', 'B', 'C'].map(secName => {
            const secQs = questions.filter(q => q.section === secName)
            if (secQs.length === 0) return null
            const secConf = sections.find(s => s.name === secName)
            return (
              <div key={secName} className="mb-6">
                <div className="flex items-center gap-3 mb-3">
                  <span className={'text-sm font-semibold px-3 py-1 rounded-lg border ' + (sectionColors[secName] || 'text-white')}>
                    Section {secName} — {secConf?.marks || 0} Marks Each
                  </span>
                  <span className="text-xs text-slate-500">Attempt {secConf?.attempt} of {secQs.length}</span>
                </div>
                <div className="space-y-2">
                  {secQs.map(q => (
                    <div key={q.id} className={'rounded-xl border p-4 transition-all ' + (q.selected !== false ? 'bg-slate-900 border-white/5' : 'bg-slate-900/50 border-white/3 opacity-50')}>
                      <div className="flex items-start gap-3">
                        <input type="checkbox" checked={q.selected !== false} onChange={() => toggleQ(q.id)} className="mt-1 flex-shrink-0 accent-blue-500" />
                        <div className="flex-1 min-w-0">
                          <textarea
                            value={q.text}
                            onChange={e => editQ(q.id, e.target.value)}
                            className="w-full bg-transparent text-sm text-white outline-none resize-none leading-relaxed"
                            rows={q.text.length > 100 ? 3 : 2}
                          />
                          <div className="flex gap-2 mt-2 flex-wrap">
                            <span className={'text-[10px] px-2 py-0.5 rounded border font-medium ' + (diffColors[q.difficulty] || 'text-slate-400 bg-slate-700 border-white/10')}>{q.difficulty}</span>
                            {q.unit && <span className="text-[10px] text-slate-500 px-2 py-0.5 rounded border border-white/5">{q.unit}</span>}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-xs font-semibold text-blue-400">[{q.marks}M]</span>
                          <button onClick={() => deleteQ(q.id)} className="text-slate-600 hover:text-red-400 w-6 h-6 flex items-center justify-center text-sm">✕</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}

          <div className="bg-slate-900 rounded-xl border border-white/5 p-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-white">Total: {questions.filter(q => q.selected !== false).reduce((s, q) => s + q.marks, 0)} marks</p>
              <p className="text-xs text-slate-500">{questions.filter(q => q.selected !== false).length} questions selected</p>
            </div>
            <button onClick={savePaper} disabled={saving} className="px-6 py-2.5 bg-green-500 text-white text-sm font-semibold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center gap-2">
              {saving ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Saving...</> : '💾 Save & Preview Paper'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Generate questions page done!")

# Clear student class selection for testing
print("\nAll fixes done!")