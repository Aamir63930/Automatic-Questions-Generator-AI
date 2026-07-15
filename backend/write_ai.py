with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(r"""import { Request, Response } from 'express'
import { success, error } from '../utils/response'
import prisma from '../config/db'

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions'
const GROQ_KEY = process.env.GROQ_API_KEY || ''
const MODEL = 'llama-3.1-8b-instant'

async function callGroq(system: string, user: string, maxTokens = 3500): Promise<string> {
  if (!GROQ_KEY) throw new Error('GROQ_API_KEY not set')
  const res = await fetch(GROQ_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'system', content: system }, { role: 'user', content: user }],
      max_tokens: maxTokens,
      temperature: 0.7,
    })
  })
  if (!res.ok) throw new Error('Groq error: ' + res.status)
  const d = await res.json() as { choices: { message: { content: string } }[] }
  return d.choices?.[0]?.message?.content || ''
}

export const getMaterialUnits = async (req: Request, res: Response) => {
  try {
    const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
    const cid = college?.id || ''
    const { subject } = req.query
    const materials = await prisma.material.findMany({
      where: { collegeId: cid, isPyq: false, ...(subject && { subject: { contains: subject as string, mode: 'insensitive' } }) },
      select: { unit: true, subject: true, title: true }
    })
    const pyqs = await prisma.material.findMany({
      where: { collegeId: cid, isPyq: true, ...(subject && { subject: { contains: subject as string, mode: 'insensitive' } }) },
      select: { year: true, examType: true }
    })
    const units = Array.from(new Set(materials.map(m => m.unit).filter(Boolean))) as string[]
    const years = Array.from(new Set(pyqs.map(m => m.year?.toString()).filter(Boolean))) as string[]
    return success(res, { units, years, hasMaterials: materials.length > 0, hasPyqs: pyqs.length > 0 })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const generateQuestions = async (req: Request, res: Response) => {
  try {
    const { subject, units, extraTopics, sections, difficulty, pyqYears, usePyqs } = req.body

    const selectedTopics: string[] = [
      ...(Array.isArray(units) ? units.filter(Boolean) : []),
      ...(Array.isArray(extraTopics) ? extraTopics.filter(Boolean) : [])
    ]

    if (selectedTopics.length === 0) {
      return error(res, 'Please select at least one unit or topic', 400)
    }

    const topicList = selectedTopics.map((t, i) => (i+1) + '. ' + t).join('\n')
    const sectionsDesc = (sections || []).map((s: any) =>
      'Section ' + s.name + ': ' + s.total + ' questions of ' + s.marks + ' marks each'
    ).join('\n')

    const pyqNote = (usePyqs && pyqYears?.length > 0)
      ? 'Style questions like previous year papers from: ' + pyqYears.join(', ')
      : ''

    const systemPrompt = 'You are a strict exam paper setter. ONLY use the given topics. Return ONLY valid JSON array, nothing else.'

    const userPrompt = 'Create exam questions for subject: ' + subject + '\n' +
      'Difficulty: ' + (difficulty || 'mixed') + '\n' +
      (pyqNote ? pyqNote + '\n' : '') +
      '\nTOPICS - USE ONLY THESE (no other topics allowed):\n' + topicList +
      '\n\nSections needed:\n' + sectionsDesc +
      '\n\nRules:\n' +
      '- Every question must relate to one of the ' + selectedTopics.length + ' topics above\n' +
      '- "unit" field = exact topic name from list\n' +
      '- Cover ALL topics evenly\n' +
      '\nReturn ONLY JSON array:\n' +
      '[{"id":1,"section":"A","questionNo":1,"text":"question here","marks":' + (sections?.[0]?.marks || 2) + ',"unit":"' + (selectedTopics[0] || subject) + '","difficulty":"easy","type":"short"}]'

    const raw = await callGroq(systemPrompt, userPrompt)

    let questions = []
    try {
      const cleaned = raw.replace(/```json|```/g, '').trim()
      const match = cleaned.match(/\[[\s\S]*\]/)
      questions = JSON.parse(match ? match[0] : cleaned)
    } catch {
      return error(res, 'AI format error. Try again.', 500)
    }

    return success(res, {
      questions,
      metadata: { subject, topics: selectedTopics, totalQuestions: questions.length }
    })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history, image } = req.body
    if (!GROQ_KEY) return error(res, 'GROQ_API_KEY not configured', 500)

    const userContent = image
      ? (message || 'Analyze and solve this problem') + '\n[Student shared an image about ' + (subject || 'their subject') + '. Provide detailed step-by-step solution.]'
      : message

    if (!userContent) return error(res, 'Message required', 400)

    const msgs = [
      ...(history || []).slice(-6).map((h: any) => ({ role: h.role, content: h.content })),
      { role: 'user', content: userContent }
    ]

    const res2 = await fetch(GROQ_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          { role: 'system', content: 'You are HAYAT, an expert AI tutor for ' + (subject || 'all subjects') + ' at K.R Mangalam University. Be helpful and educational.' },
          ...msgs
        ],
        max_tokens: 2048,
        temperature: 0.7,
      })
    })

    if (!res2.ok) return error(res, 'AI service error: ' + res2.status, 500)

    const d = await res2.json() as { choices: { message: { content: string } }[] }
    const reply = d.choices?.[0]?.message?.content
    if (!reply) return error(res, 'No response from AI', 500)

    return success(res, { reply })
  } catch (err: any) { return error(res, 'AI unavailable: ' + err.message, 500) }
}

export const checkAnswer = async (req: Request, res: Response) => {
  try {
    const { question, answer, subject, marks } = req.body
    const raw = await callGroq(
      'Grade this answer. Return ONLY valid JSON.',
      'Q: ' + question + '\nA: ' + answer + '\nSubject: ' + subject + '\nMax: ' + marks + '\nReturn: {"marksAwarded":0,"percentage":0,"grade":"A","feedback":"text"}'
    )
    const match = raw.match(/\{[\s\S]*\}/)
    return success(res, JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim()))
  } catch (err: any) { return error(res, err.message, 500) }
}
""")
print("AI controller written successfully!")