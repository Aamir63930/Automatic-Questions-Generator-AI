import os

# ═══════════════════════════════════════════════════════
# BACKEND FIX 1: AI Generate - reads actual uploaded materials + PYQs by year
# ═══════════════════════════════════════════════════════
with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
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
        pyqContext = '\\nPYQ Reference (use similar difficulty/style from these years): ' + 
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
      ? '\\nUploaded materials in these units: ' + uploadedMaterials.map(m => m.title + ' (' + m.unit + ')').join(', ')
      : ''

    const sectionsDesc = (sections || []).map((s: any) =>
      'Section ' + s.name + ': ' + s.total + ' questions of ' + s.marks + ' marks each'
    ).join('\\n')

    const topicList = selectedTopics.map((t, i) => (i+1) + '. ' + t).join('\\n')

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
      const match = raw.match(/\\[[\\s\\S]*\\]/)
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
      'Q: ' + question + '\\nA: ' + answer + '\\nSubject: ' + subject + '\\nMax: ' + marks + '\\nReturn: {"marksAwarded":number,"percentage":number,"grade":"A/B/C/F","feedback":"text"}')
    const match = raw.match(/\\{[\\s\\S]*\\}/)
    return success(res, JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim()))
  } catch (err: any) { return error(res, err.message, 500) }
}
""")
print("AI controller done!")

# AI Routes - add material-units endpoint
with open("src/routes/ai.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { generateQuestions, getMaterialUnits, aiChat, checkAnswer } from '../controllers/ai.controller'
import { authenticate } from '../middleware/auth.middleware'

const router = Router()
router.get('/material-units', authenticate, getMaterialUnits)
router.post('/generate-questions', authenticate, generateQuestions)
router.post('/chat', authenticate, aiChat)
router.post('/check-answer', authenticate, checkAnswer)
export default router
""")
print("AI routes done!")

# Notification Controller - alert with email option
with open("src/controllers/notification.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

async function getMainCollegeId(): Promise<string> {
  const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
  return college?.id || ''
}

export const getNotifications = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const notifications = await prisma.notification.findMany({
      where: { userId }, orderBy: { createdAt: 'desc' }, take: 50
    })
    return success(res, notifications)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const markRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.updateMany({ where: { id: req.params.id as string, userId }, data: { isRead: true } })
    return success(res, null)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const markAllRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.updateMany({ where: { userId, isRead: false }, data: { isRead: true } })
    return success(res, null)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const deleteNotification = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.deleteMany({ where: { id: req.params.id as string, userId } })
    return success(res, null)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const sendBulkNotification = async (req: Request, res: Response) => {
  try {
    const { title, body, type, target, classIds } = req.body
    const collegeId = await getMainCollegeId()

    let userFilter: any = { collegeId, isActive: true }
    if (target === 'all_students') {
      userFilter.role = 'student'
    } else if (target === 'specific_classes' && classIds?.length > 0) {
      userFilter.role = 'student'
      userFilter.classSectionId = { in: classIds }
    } else if (target === 'teachers') {
      userFilter.role = 'teacher'
    } else if (target === 'no_submission' && classIds?.length > 0) {
      // Send to students who haven't submitted a specific task
      userFilter.role = 'student'
      userFilter.classSectionId = { in: classIds }
    }

    const users = await prisma.user.findMany({ where: userFilter, select: { id: true, email: true, name: true } })

    if (users.length > 0) {
      await prisma.notification.createMany({
        data: users.map(u => ({ userId: u.id, title, body, type: type || 'announcement' }))
      })
    }

    return success(res, { sent: users.length, recipients: users.map(u => ({ name: u.name, email: u.email })) }, 'Sent to ' + users.length + ' users')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

// Student alerts teacher that no data in class
export const studentAlertTeacher = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { classSectionId, message } = req.body

    const student = await prisma.user.findUnique({ where: { id: userId }, select: { name: true, email: true } })
    const cls = await prisma.classSection.findUnique({ where: { id: classSectionId }, select: { name: true, section: true } })
    const collegeId = await getMainCollegeId()

    // Notify all teachers
    const teachers = await prisma.user.findMany({ where: { collegeId, role: 'teacher', isActive: true }, select: { id: true } })

    if (teachers.length > 0) {
      await prisma.notification.createMany({
        data: teachers.map(t => ({
          userId: t.id,
          title: '📢 Student Alert from ' + (student?.name || 'Student'),
          body: 'Class: ' + (cls?.name || '') + ' ' + (cls?.section || '') + ' — ' + (message || 'Please upload study materials for our class!'),
          type: 'complaint',
        }))
      })
    }

    return success(res, null, 'Alert sent to teachers!')
  } catch (err: any) { return error(res, err.message, 500) }
}
""")
print("Notification controller done!")

with open("src/routes/notification.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { getNotifications, markRead, markAllRead, deleteNotification, sendBulkNotification, studentAlertTeacher } from '../controllers/notification.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import prisma from '../config/db'

const router = Router()
router.get('/', authenticate, getNotifications)
router.patch('/read-all', authenticate, markAllRead)
router.patch('/:id/read', authenticate, markRead)
router.delete('/:id', authenticate, deleteNotification)
router.post('/send', authenticate, authorize('teacher','admin'), sendBulkNotification)
router.post('/student-alert', authenticate, authorize('student'), studentAlertTeacher)

// Direct notification to one user
router.post('/', authenticate, async (req: any, res: any) => {
  try {
    const { userId, title, body, type, refId } = req.body
    if (!userId || !title) return res.status(400).json({ success: false, message: 'userId and title required' })
    const notif = await prisma.notification.create({
      data: { userId, title, body: body || '', type: type || 'announcement', refId: refId || null }
    })
    return res.json({ success: true, data: notif })
  } catch (e: any) { return res.status(500).json({ success: false, message: e.message }) }
})

export default router
""")
print("Notification routes done!")

print("\n=== BACKEND DONE ===")