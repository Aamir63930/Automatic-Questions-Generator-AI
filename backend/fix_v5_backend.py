import os

# BACKEND SCRIPT - backend folder se chalao
os.makedirs("src/routes", exist_ok=True)
os.makedirs("src/controllers", exist_ok=True)

# Material routes
with open("src/routes/material.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { uploadMaterial, getMaterials, downloadMaterial, previewMaterial, deleteMaterial } from '../controllers/material.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'
import path from 'path'
import fs from 'fs'
import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()

const router = Router()
router.post('/upload', authenticate, authorize('teacher', 'admin'), upload.single('file'), uploadMaterial)
router.get('/', authenticate, getMaterials)
router.get('/:id/download', authenticate, downloadMaterial)
router.get('/:id/preview', authenticate, previewMaterial)
router.delete('/:id', authenticate, authorize('teacher', 'admin'), deleteMaterial)

// Public view route - no auth - opens inline in browser tab
router.get('/:id/view', async (req: any, res: any) => {
  try {
    const material = await prisma.material.findUnique({ where: { id: req.params.id } })
    if (!material) return res.status(404).send('<h2>File not found</h2>')
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return res.status(404).send('<h2>File not found on server</h2>')
    const ext = path.extname(material.fileName).toLowerCase()
    const mimes: Record<string, string> = {
      '.pdf': 'application/pdf',
      '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
      '.txt': 'text/plain',
    }
    const mime = mimes[ext] || 'application/pdf'
    res.setHeader('Content-Type', mime)
    res.setHeader('Content-Disposition', 'inline; filename="' + material.fileName + '"')
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('X-Frame-Options', 'ALLOWALL')
    return res.sendFile(path.resolve(filePath))
  } catch (e: any) { return res.status(500).send(e.message) }
})

export default router
""")
print("Material routes done!")

# AI Controller - generate ONLY from provided topics
with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import { success, error } from '../utils/response'

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
      max_tokens: maxTokens,
      temperature: 0.8,
    })
  })
  if (!res.ok) throw new Error('Groq: ' + await res.text())
  const d = await res.json() as { choices: { message: { content: string } }[] }
  return d.choices?.[0]?.message?.content || ''
}

export const generateQuestions = async (req: Request, res: Response) => {
  try {
    const { subject, units, extraTopics, sections, difficulty } = req.body

    // Combine units and extra topics - ONLY these will be used
    const allTopics = [
      ...(Array.isArray(units) ? units : []),
      ...(Array.isArray(extraTopics) ? extraTopics : [])
    ].filter(Boolean)

    if (allTopics.length === 0) {
      return error(res, 'Please select at least one unit or add a topic', 400)
    }

    const sectionsDesc = (sections || []).map((s: any) =>
      'Section ' + s.name + ': ' + s.total + ' questions, ' + s.marks + ' marks each'
    ).join('\\n')

    const seed = Date.now()

    const systemPrompt = `You are a university professor creating exam questions.
CRITICAL RULE: Generate questions ONLY from these specific topics: ${allTopics.join(', ')}
DO NOT add questions from any other topic.
Return ONLY a valid JSON array. No markdown, no explanation, no backticks.`

    const userPrompt = `Create exam questions (id:${seed}) for:
Subject: ${subject}
TOPICS TO USE (ONLY these): ${allTopics.join(', ')}
Difficulty: ${difficulty || 'mixed'}

${sectionsDesc}

For each topic, create at least one question. Distribute questions evenly.

Return JSON array ONLY:
[{"id":1,"section":"A","questionNo":1,"text":"specific question about one of the given topics","marks":2,"unit":"exact topic name from the list","difficulty":"easy","type":"short"}]

Section A: definitions, fill-blanks, 1-liners about ${allTopics.slice(0,3).join(', ')}
Section B: explanations with examples from ${allTopics.join(', ')}
Section C: long answers, case studies, design problems from ${allTopics.slice(-3).join(', ')}`

    const raw = await callGroq(systemPrompt, userPrompt)

    let questions = []
    try {
      const match = raw.match(/\\[[\\s\\S]*\\]/)
      questions = JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim())
    } catch {
      return error(res, 'AI returned invalid format. Please try again.', 500)
    }

    return success(res, { questions, metadata: { subject, topics: allTopics, totalQuestions: questions.length } })
  } catch (err: any) {
    return error(res, err.message, 500)
  }
}

export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history } = req.body
    const msgs = [
      ...(history || []).slice(-6).map((h: any) => ({ role: h.role, content: h.content })),
      { role: 'user', content: message }
    ]
    const res2 = await fetch(GROQ_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: 'system', content: 'You are an expert tutor for ' + (subject || 'all subjects') + '. Be clear and use examples.' }, ...msgs],
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
    const raw = await callGroq(
      'Grade this answer. Return ONLY valid JSON.',
      'Q: ' + question + '\\nA: ' + answer + '\\nSubject: ' + subject + '\\nMax: ' + marks + '\\nReturn: {"marksAwarded":number,"percentage":number,"grade":"A/B/C/F","feedback":"text","strengths":["s1"],"improvements":["i1"]}'
    )
    const match = raw.match(/\\{[\\s\\S]*\\}/)
    return success(res, JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim()))
  } catch (err: any) { return error(res, err.message, 500) }
}
""")
print("AI controller done - generates ONLY from given topics!")

# Teacher Results - class wise + student name wise
with open("src/controllers/submission.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createSubmission = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { taskId, textAnswer } = req.body
    const file = req.file
    const task = await prisma.task.findFirst({ where: { id: taskId as string, collegeId } })
    if (!task) return error(res, 'Task not found', 404)
    if (task.status !== 'active') return error(res, 'Task is closed', 400)
    const existing = await prisma.submission.findUnique({ where: { taskId_studentId: { taskId: taskId as string, studentId: userId } } })
    if (existing) return error(res, 'Already submitted', 400)
    const isLate = task.deadline && new Date() > task.deadline
    if (isLate && !task.allowLate) return error(res, 'Deadline has passed', 400)
    const submission = await prisma.submission.create({
      data: { taskId: taskId as string, studentId: userId, textAnswer: textAnswer || null, fileUrl: file ? '/uploads/' + collegeId + '/' + file.filename : null, fileName: file?.originalname || null, status: (isLate ? 'late' : 'submitted') as any },
      include: { student: { select: { name: true } }, task: { select: { title: true, maxMarks: true } } }
    })
    const student = await prisma.user.findUnique({ where: { id: userId }, select: { name: true } })
    await prisma.notification.create({ data: { userId: task.createdBy, title: '📥 New Submission', body: (student?.name || 'Student') + ' submitted "' + task.title + '"', type: 'task', refId: taskId as string } })
    const submCount = await prisma.submission.count({ where: { taskId: taskId as string } })
    const f2: any = { collegeId, role: 'student', isActive: true }
    if (task.classSectionId) f2.classSectionId = task.classSectionId
    const totalStudents = await prisma.user.count({ where: f2 })
    if (submCount === totalStudents && totalStudents > 0) {
      await prisma.notification.create({ data: { userId: task.createdBy, title: '✅ All Submitted!', body: 'All ' + totalStudents + ' students submitted "' + task.title + '"', type: 'task', refId: taskId as string } })
    }
    return success(res, submission, 'Submitted!', 201)
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const getSubmissions = async (req: Request, res: Response) => {
  try {
    const { userId, role } = (req as any).user
    const { taskId } = req.query
    const submissions = await prisma.submission.findMany({
      where: { ...(taskId && { taskId: taskId as string }), ...(role === 'student' && { studentId: userId }) },
      include: { student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true, classSectionId: true, classSection: { select: { name: true, section: true } } } }, task: { select: { title: true, maxMarks: true, taskType: true, subjectName: true } } },
      orderBy: { submittedAt: 'desc' }
    })
    return success(res, submissions)
  } catch (err) { return error(res, 'Failed', 500) }
}

// Teacher: class-wise + student-wise result summary
export const getResultsSummary = async (req: Request, res: Response) => {
  try {
    const { collegeId, userId } = (req as any).user
    const { classId } = req.query

    // Get all submissions with student + task info
    const subs = await prisma.submission.findMany({
      where: {
        task: { collegeId, createdBy: userId, ...(classId && { classSectionId: classId as string }) }
      },
      include: {
        student: { select: { id: true, name: true, email: true, rollNumber: true, classSectionId: true, classSection: { select: { id: true, name: true, section: true, branch: true } } } },
        task: { select: { id: true, title: true, maxMarks: true, taskType: true, subjectName: true, classSectionId: true } }
      },
      orderBy: { submittedAt: 'desc' }
    })

    // Group by class
    const byClass: Record<string, any> = {}
    for (const sub of subs) {
      const cls = sub.student.classSection
      const classKey = cls ? cls.id : 'no_class'
      const className = cls ? cls.name + ' ' + cls.section : 'No Class'
      if (!byClass[classKey]) byClass[classKey] = { classId: classKey, className, branch: cls?.branch || '', students: {}, submissions: [] }

      byClass[classKey].submissions.push(sub)

      const sid = sub.student.id
      if (!byClass[classKey].students[sid]) {
        byClass[classKey].students[sid] = { id: sid, name: sub.student.name, email: sub.student.email, rollNumber: sub.student.rollNumber, tasks: [], totalObtained: 0, totalMax: 0, avgPct: 0 }
      }
      byClass[classKey].students[sid].tasks.push({
        taskId: sub.task.id, title: sub.task.title, maxMarks: sub.task.maxMarks,
        marksAwarded: sub.marksAwarded, status: sub.status, submittedAt: sub.submittedAt, feedback: sub.feedback
      })
      if (sub.marksAwarded !== null) {
        byClass[classKey].students[sid].totalObtained += sub.marksAwarded
        byClass[classKey].students[sid].totalMax += sub.task.maxMarks
      }
    }

    // Calculate averages
    const result = Object.values(byClass).map((cls: any) => {
      const students = Object.values(cls.students).map((s: any) => ({
        ...s, avgPct: s.totalMax > 0 ? Math.round((s.totalObtained / s.totalMax) * 100) : null,
        grade: s.totalMax > 0 ? (s.totalObtained / s.totalMax >= 0.8 ? 'A' : s.totalObtained / s.totalMax >= 0.6 ? 'B' : s.totalObtained / s.totalMax >= 0.4 ? 'C' : 'F') : '-'
      })).sort((a: any, b: any) => (b.totalObtained || 0) - (a.totalObtained || 0))
      return { ...cls, students, studentCount: students.length }
    })

    return success(res, result)
  } catch (err: any) { return error(res, err.message, 500) }
}

export const getPendingSummary = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const tasks = await prisma.task.findMany({
      where: { collegeId, createdBy: userId },
      include: { classSection: { select: { name: true, section: true } }, submissions: { select: { id: true, marksAwarded: true } } }
    })
    const summary = await Promise.all(tasks.map(async t => {
      const total = t.submissions.length
      const graded = t.submissions.filter(s => s.marksAwarded !== null).length
      const f: any = { collegeId, role: 'student', isActive: true }
      if (t.classSectionId) f.classSectionId = t.classSectionId
      const totalStudents = await prisma.user.count({ where: f })
      return { taskId: t.id, title: t.title, maxMarks: t.maxMarks, className: t.classSection ? t.classSection.name + ' ' + t.classSection.section : 'All', totalStudents, submittedCount: total, notSubmittedCount: totalStudents - total, graded, pending: total - graded }
    }))
    return success(res, { totalPending: summary.reduce((s, x) => s + x.pending, 0), tasks: summary })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const getTaskSubmissionStatus = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const task = await prisma.task.findFirst({ where: { id: req.params.taskId, collegeId } })
    if (!task) return error(res, 'Not found', 404)
    const f: any = { collegeId, role: 'student', isActive: true }
    if (task.classSectionId) f.classSectionId = task.classSectionId
    const allStudents = await prisma.user.findMany({ where: f, select: { id: true, name: true, rollNumber: true, avatarUrl: true } })
    const subs = await prisma.submission.findMany({ where: { taskId: req.params.taskId }, select: { studentId: true, status: true, marksAwarded: true, submittedAt: true } })
    const subMap = new Map(subs.map(s => [s.studentId, s]))
    return success(res, { total: allStudents.length, submittedCount: subs.length, notSubmittedCount: allStudents.length - subs.length, submitted: allStudents.filter(s => subMap.has(s.id)).map(s => ({ ...s, ...subMap.get(s.id) })), notSubmitted: allStudents.filter(s => !subMap.has(s.id)) })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const gradeSubmission = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { marks, feedback } = req.body
    const submission = await prisma.submission.update({
      where: { id: req.params.id as string },
      data: { marksAwarded: parseInt(marks), feedback: feedback || null, gradedBy: userId, gradedAt: new Date(), status: 'graded' as any },
      include: { task: { select: { title: true, maxMarks: true } } }
    })
    await prisma.notification.create({ data: { userId: submission.studentId, title: '📊 Result Published!', body: '"' + submission.task.title + '" graded: ' + marks + '/' + submission.task.maxMarks + (feedback ? ' — ' + feedback : ''), type: 'result', refId: submission.taskId } })
    return success(res, submission, 'Graded!')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}
""")
print("Submission controller done!")

with open("src/routes/submission.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { createSubmission, getSubmissions, gradeSubmission, getPendingSummary, getTaskSubmissionStatus, getResultsSummary } from '../controllers/submission.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'

const router = Router()
router.post('/', authenticate, authorize('student'), upload.single('file'), createSubmission)
router.get('/', authenticate, getSubmissions)
router.get('/pending-summary', authenticate, authorize('teacher', 'admin'), getPendingSummary)
router.get('/results-summary', authenticate, authorize('teacher', 'admin'), getResultsSummary)
router.get('/task/:taskId/status', authenticate, authorize('teacher', 'admin'), getTaskSubmissionStatus)
router.patch('/:id/grade', authenticate, authorize('teacher', 'admin'), gradeSubmission)
export default router
""")
print("Submission routes done!")

print("\n=== BACKEND DONE ===")