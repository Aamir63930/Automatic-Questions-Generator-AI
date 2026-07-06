import { Request, Response } from 'express'
import { success, error } from '../utils/response'
import prisma from '../config/db'

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions'
const GROQ_KEY = process.env.GROQ_API_KEY || ''
const MODEL = 'llama-3.1-8b-instant'

async function callGroq(system: string, user: string, maxTokens = 3000): Promise<string> {
  if (!GROQ_KEY || GROQ_KEY === 'your-groq-api-key-here') {
    throw new Error('GROQ_API_KEY not set. Get free key at console.groq.com')
  }
  const res = await fetch(GROQ_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'system', content: system }, { role: 'user', content: user }],
      max_tokens: maxTokens, temperature: 0.7,
    })
  })
  if (!res.ok) throw new Error('Groq: ' + await res.text())
  const d = await res.json() as { choices: { message: { content: string } }[] }
  return d.choices?.[0]?.message?.content || ''
}

// GET /api/v1/ai/material-units?subject=DSA - fetch units from uploaded materials
export const getMaterialUnits = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { subject } = req.query

    const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
    const cid = college?.id || collegeId

    const materials = await prisma.material.findMany({
      where: {
        collegeId: cid,
        isPyq: false,
        ...(subject && { subject: { contains: subject as string, mode: 'insensitive' as any } })
      },
      select: { unit: true, subject: true, title: true, createdAt: true },
      orderBy: { createdAt: 'asc' }
    })

    const pyqYears = await prisma.material.findMany({
      where: {
        collegeId: cid,
        isPyq: true,
        ...(subject && { subject: { contains: subject as string, mode: 'insensitive' as any } })
      },
      select: { year: true, examType: true, subject: true },
      orderBy: { year: 'desc' }
    })

    const units = Array.from(new Set(materials.map(m => m.unit).filter(Boolean))) as string[]
    const years = Array.from(new Set(pyqYears.map(m => m.year?.toString()).filter(Boolean))) as string[]
    const subjects = Array.from(new Set([...materials, ...pyqYears].map(m => m.subject).filter(Boolean))) as string[]

    return success(res, { units, years, subjects, hasMaterials: materials.length > 0, hasPyqs: pyqYears.length > 0 })
  } catch (err: any) {
    return error(res, err.message, 500)
  }
}

export const generateQuestions = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { subject, units, extraTopics, sections, difficulty, pyqYears, usePyqs } = req.body

    const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
    const cid = college?.id || collegeId

    // Fetch actual uploaded materials for context
    const uploadedMaterials = await prisma.material.findMany({
      where: {
        collegeId: cid, isPyq: false,
        ...(subject && { subject: { contains: subject, mode: 'insensitive' as any } }),
        ...(units?.length > 0 && { unit: { in: units } })
      },
      select: { title: true, unit: true, subject: true },
      orderBy: { createdAt: 'asc' }
    })

    // Fetch PYQ context if years selected
    let pyqContext = ''
    if (usePyqs && pyqYears?.length > 0) {
      const pyqs = await prisma.material.findMany({
        where: {
          collegeId: cid, isPyq: true,
          ...(subject && { subject: { contains: subject, mode: 'insensitive' as any } }),
          year: { in: pyqYears.map((y: string) => parseInt(y)) }
        },
        select: { title: true, year: true, examType: true }
      })
      if (pyqs.length > 0) {
        pyqContext = '\nPYQ Reference (use similar difficulty/style from these years): ' + 
          pyqs.map(p => p.year + ' ' + (p.examType || '') + ' - ' + p.title).join(', ')
      }
    }

    // Build topic list from selected units + extra topics
    const selectedTopics = [
      ...(Array.isArray(units) ? units.filter(Boolean) : []),
      ...(Array.isArray(extraTopics) ? extraTopics.filter(Boolean) : [])
    ]

    if (selectedTopics.length === 0) {
      return error(res, 'Please select at least one unit or topic', 400)
    }

    // Build material context
    const materialContext = uploadedMaterials.length > 0
      ? '\nUploaded materials in these units: ' + uploadedMaterials.map(m => m.title + ' (' + m.unit + ')').join(', ')
      : ''

    const sectionsDesc = (sections || []).map((s: any) =>
      'Section ' + s.name + ': ' + s.total + ' questions of ' + s.marks + ' marks each'
    ).join('\n')

    const topicList = selectedTopics.map((t, i) => (i+1) + '. ' + t).join('\n')

    const systemPrompt = `You are a university exam paper setter for K.R Mangalam University.
CRITICAL: Generate questions ONLY from the specific topics/units provided below.
DO NOT add questions from topics not in the list.
Questions should align with uploaded study materials context.
Return ONLY valid JSON array, no markdown, no explanation.`

    const userPrompt = `Create exam paper for:
Subject: ${subject}
Difficulty: ${difficulty || 'mixed'}
${pyqContext}
${materialContext}

TOPICS TO USE (STRICTLY ONLY THESE):
${topicList}

Sections:
${sectionsDesc}

Rules:
- Every question must be from the topic list above
- Cover ALL provided topics, at least 1 question per topic
- Section A: definitions, fill blanks, one-liners from: ${selectedTopics.slice(0,3).join(', ')}
- Section B: explanations, comparisons from: ${selectedTopics.join(', ')}
- Section C: long essays, case studies from: ${selectedTopics.slice(-2).join(', ')}
${usePyqs && pyqYears?.length > 0 ? '- Style questions similar to PYQs from years: ' + pyqYears.join(', ') : ''}

Return ONLY JSON:
[{"id":1,"section":"A","questionNo":1,"text":"specific question about ${selectedTopics[0]}","marks":${sections?.[0]?.marks || 2},"unit":"${selectedTopics[0]}","difficulty":"easy","type":"short"}]`

    const raw = await callGroq(systemPrompt, userPrompt)

    let questions = []
    try {
      const match = raw.match(/\[[\s\S]*\]/)
      questions = JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim())
    } catch {
      return error(res, 'AI format error. Please try again.', 500)
    }

    return success(res, { questions, metadata: { subject, topics: selectedTopics, pyqYears: pyqYears || [], totalQuestions: questions.length } })
  } catch (err: any) {
    return error(res, err.message, 500)
  }
}

export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history } = req.body
    if (!GROQ_KEY || GROQ_KEY === 'your-groq-api-key-here') {
      return error(res, 'GROQ_API_KEY not set', 500)
    }
    const msgs = [
      ...(history || []).slice(-6).map((h: any) => ({ role: h.role, content: h.content })),
      { role: 'user', content: message }
    ]
    const res2 = await fetch(GROQ_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: 'system', content: 'You are an expert academic tutor for ' + (subject || 'all subjects') + ' at K.R Mangalam University. Be clear and educational.' }, ...msgs],
        max_tokens: 1024, temperature: 0.7,
      })
    })
    const d = await res2.json() as { choices: { message: { content: string } }[] }
    return success(res, { reply: d.choices?.[0]?.message?.content || 'No response' })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const checkAnswer = async (req: Request, res: Response) => {
  try {
    const { question, answer, subject, marks } = req.body
    const raw = await callGroq('Grade this. Return ONLY valid JSON.',
      'Q: ' + question + '\nA: ' + answer + '\nSubject: ' + subject + '\nMax: ' + marks + '\nReturn: {"marksAwarded":number,"percentage":number,"grade":"A/B/C/F","feedback":"text"}')
    const match = raw.match(/\{[\s\S]*\}/)
    return success(res, JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim()))
  } catch (err: any) { return error(res, err.message, 500) }
}
