import os

# ══════════════════════════════════════════
# FIX 1: app.ts - AI route properly register
# ══════════════════════════════════════════
with open("src/app.ts", "w", encoding="utf-8") as f:
    f.write("""import express from 'express'
import cors from 'cors'
import path from 'path'
import dotenv from 'dotenv'
dotenv.config()

import authRoutes         from './routes/auth.routes'
import materialRoutes     from './routes/material.routes'
import taskRoutes         from './routes/task.routes'
import submissionRoutes   from './routes/submission.routes'
import notificationRoutes from './routes/notification.routes'
import complaintRoutes    from './routes/complaint.routes'
import aiRoutes           from './routes/ai.routes'
import paperRoutes        from './routes/paper.routes'

const app = express()
const PORT = process.env.PORT || 5000

app.use(cors({ origin: '*', credentials: true }))
app.use(express.json({ limit: '50mb' }))
app.use(express.urlencoded({ extended: true, limit: '50mb' }))
app.use('/uploads', express.static(path.join(process.cwd(), 'uploads')))

app.get('/health', (_req, res) => res.json({ status: 'OK', time: new Date() }))

app.use('/api/v1/auth',          authRoutes)
app.use('/api/v1/materials',     materialRoutes)
app.use('/api/v1/tasks',         taskRoutes)
app.use('/api/v1/submissions',   submissionRoutes)
app.use('/api/v1/notifications', notificationRoutes)
app.use('/api/v1/complaints',    complaintRoutes)
app.use('/api/v1/ai',            aiRoutes)
app.use('/api/v1/papers',        paperRoutes)

app.listen(PORT, () => {
  console.log('Backend running on http://localhost:' + PORT)
  console.log('Frontend URL: http://localhost:3000')
})

export default app
""")
print("app.ts done!")

# ══════════════════════════════════════════
# FIX 2: Paper routes (was missing!)
# ══════════════════════════════════════════
os.makedirs("src/routes", exist_ok=True)
with open("src/routes/paper.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { authenticate } from '../middleware/auth.middleware'
import prisma from '../config/db'

const router = Router()

router.post('/', authenticate, async (req: any, res: any) => {
  try {
    const { userId, collegeId } = req.user
    const { title, subject, examType, totalMarks, duration, questions } = req.body
    const paper = await prisma.paper.create({
      data: { collegeId, createdBy: userId, title, subject, examType: examType || 'end_term', totalMarks, duration: duration || 180, questions: questions || [] }
    })
    return res.json({ success: true, data: paper })
  } catch (e: any) { return res.status(500).json({ success: false, message: e.message }) }
})

router.get('/', authenticate, async (req: any, res: any) => {
  try {
    const { collegeId } = req.user
    const papers = await prisma.paper.findMany({ where: { collegeId }, orderBy: { createdAt: 'desc' } })
    return res.json({ success: true, data: papers })
  } catch (e: any) { return res.status(500).json({ success: false, message: e.message }) }
})

router.get('/:id', authenticate, async (req: any, res: any) => {
  try {
    const paper = await prisma.paper.findUnique({ where: { id: req.params.id } })
    return res.json({ success: true, data: paper })
  } catch (e: any) { return res.status(500).json({ success: false, message: e.message }) }
})

export default router
""")
print("Paper routes done!")

# ══════════════════════════════════════════
# FIX 3: AI Controller
# ══════════════════════════════════════════
os.makedirs("src/controllers", exist_ok=True)
with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import { success, error } from '../utils/response'

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions'
const GROQ_KEY = process.env.GROQ_API_KEY || ''

async function callGroq(system: string, user: string, maxTokens = 2048): Promise<string> {
  if (!GROQ_KEY || GROQ_KEY === 'your-groq-api-key-here') {
    throw new Error('GROQ_API_KEY not set. Get free key at console.groq.com')
  }
  const res = await fetch(GROQ_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
    body: JSON.stringify({
      model: "llama-3.1-8b-instant",
      messages: [{ role: 'system', content: system }, { role: 'user', content: user }],
      max_tokens: maxTokens,
      temperature: 0.85,
    })
  })
  if (!res.ok) throw new Error('Groq API: ' + await res.text())
  const d = await res.json()
  return d.choices?.[0]?.message?.content || ''
}

export const generateQuestions = async (req: Request, res: Response) => {
  try {
    const { subject, units, sections, difficulty } = req.body
    const seed = Date.now()
    const unitsList = Array.isArray(units) && units.length > 0 ? units.join(', ') : subject
    const sectionsDesc = (sections || []).map((s: any) =>
      `Section ${s.name}: Exactly ${s.total} questions, ${s.marks} marks each`
    ).join('\\n')

    const raw = await callGroq(
      'You are a university professor. Return ONLY a valid JSON array. No markdown, no explanation.',
      `Generate UNIQUE exam questions for (id:${seed}):
Subject: ${subject}
Topics: ${unitsList}
Difficulty: ${difficulty || 'mixed'}

${sectionsDesc}

Each question object:
{"id":number,"section":"A","questionNo":number,"text":"question","marks":number,"unit":"unit name","difficulty":"easy/medium/hard","type":"short/descriptive"}

Rules:
- Section A: definitions, fill blanks, MCQ-style short answers
- Section B: explain with examples, compare/contrast
- Section C: long essays, case studies, design problems
- Every question MUST be different
- Cover different topics from: ${unitsList}
- Return ONLY JSON array, nothing else`,
      3000
    )

    let questions = []
    try {
      const match = raw.match(/\[[\s\S]*\]/)
      questions = JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim())
    } catch {
      return error(res, 'AI returned invalid format. Please try again.', 500)
    }

    return success(res, { questions, metadata: { subject, totalQuestions: questions.length } })
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
        model: "llama-3.1-8b-instant",
        messages: [
          { role: 'system', content: `You are an expert tutor for ${subject || 'all subjects'} at K.R Mangalam University. Be clear, concise, use examples. Format: Definition → Explanation → Example.` },
          ...msgs
        ],
        max_tokens: 1024, temperature: 0.7,
      })
    })
    const d = await res2.json()
    return success(res, { reply: d.choices?.[0]?.message?.content || 'No response' })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const checkAnswer = async (req: Request, res: Response) => {
  try {
    const { question, answer, subject, marks } = req.body
    const raw = await callGroq(
      'Grade this answer. Return ONLY valid JSON.',
      `Question: ${question}\\nAnswer: ${answer}\\nSubject: ${subject}\\nMax: ${marks}\\nReturn: {"marksAwarded":number,"percentage":number,"grade":"A/B/C/F","feedback":"text","strengths":["s1"],"improvements":["i1"]}`
    )
    const match = raw.match(/\{[\s\S]*\}/)
    return success(res, JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim()))
  } catch (err: any) { return error(res, err.message, 500) }
}
""")
print("AI controller done!")

# ══════════════════════════════════════════
# FIX 4: AI Routes
# ══════════════════════════════════════════
with open("src/routes/ai.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { generateQuestions, aiChat, checkAnswer } from '../controllers/ai.controller'
import { authenticate } from '../middleware/auth.middleware'

const router = Router()
router.post('/generate-questions', authenticate, generateQuestions)
router.post('/chat', authenticate, aiChat)
router.post('/check-answer', authenticate, checkAnswer)
export default router
""")
print("AI routes done!")

# ══════════════════════════════════════════
# FIX 5: Task Controller - Student data FIX
# The real issue: classSectionId is in JWT but
# student sees no tasks. Fix: show ALL tasks
# if student has no class, or class-filtered tasks
# ══════════════════════════════════════════
with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createTask = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { title, description, taskType, subjectName, classSectionId, deadline, maxMarks, instructions, allowLate } = req.body

    const task = await prisma.task.create({
      data: {
        collegeId, createdBy: userId, title,
        description: description || null,
        taskType: taskType as any,
        subjectName: subjectName || null,
        classSectionId: classSectionId || null,
        deadline: deadline ? new Date(deadline) : null,
        maxMarks: parseInt(maxMarks) || 10,
        instructions: instructions || null,
        allowLate: allowLate === 'true' || allowLate === true,
        attachmentUrl: req.file ? '/uploads/' + collegeId + '/' + req.file.filename : null,
      },
      include: {
        creator: { select: { name: true } },
        classSection: { select: { name: true, section: true, branch: true } }
      }
    })

    // Notify relevant students
    const filter: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId) filter.classSectionId = classSectionId
    const students = await prisma.user.findMany({ where: filter, select: { id: true } })
    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: 'New ' + (taskType || 'assignment').replace('_', ' '),
          body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : ''),
          type: 'task', refId: task.id,
        }))
      })
    }
    return success(res, task, 'Task created', 201)
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const createBulkTasks = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { tasks } = req.body
    const created = []
    for (const t of tasks) {
      const task = await prisma.task.create({
        data: { collegeId, createdBy: userId, title: t.title, taskType: t.taskType as any, subjectName: t.subjectName || null, classSectionId: t.classSectionId || null, deadline: t.deadline ? new Date(t.deadline) : null, maxMarks: parseInt(t.maxMarks) || 10 }
      })
      created.push(task)
    }
    return success(res, created, created.length + ' tasks created', 201)
  } catch (err: any) { return error(res, err.message, 500) }
}

export const getTasks = async (req: Request, res: Response) => {
  try {
    const { collegeId, role, classSectionId, userId } = (req as any).user
    const { classId } = req.query

    let where: any = { collegeId }

    if (role === 'student') {
      where.status = 'active'
      // IMPORTANT: Student sees tasks for their class OR tasks with no class (all students)
      if (classSectionId) {
        where.OR = [
          { classSectionId: classSectionId },
          { classSectionId: null }
        ]
      }
      // If no class: show all active tasks in college
    } else if (role === 'teacher') {
      if (classId) where.classSectionId = classId as string
    }

    const tasks = await prisma.task.findMany({
      where,
      include: {
        creator: { select: { name: true, email: true } },
        classSection: { select: { name: true, section: true, branch: true } },
        _count: { select: { submissions: true } }
      },
      orderBy: { createdAt: 'desc' }
    })

    return success(res, tasks)
  } catch (err: any) {
    console.error('getTasks error:', err.message)
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const getTask = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const task = await prisma.task.findFirst({
      where: { id: req.params.id as string, collegeId },
      include: {
        creator: { select: { name: true } },
        classSection: { select: { name: true, section: true } },
        submissions: { include: { student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } } } }
      }
    })
    if (!task) return error(res, 'Not found', 404)
    return success(res, task)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const updateTaskStatus = async (req: Request, res: Response) => {
  try {
    const task = await prisma.task.update({ where: { id: req.params.id as string }, data: { status: req.body.status as any } })
    return success(res, task)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const deleteTask = async (req: Request, res: Response) => {
  try {
    await prisma.task.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch (err) { return error(res, 'Failed', 500) }
}
""")
print("Task controller done!")

# ══════════════════════════════════════════
# FIX 6: Material Controller - proper field names
# ══════════════════════════════════════════
with open("src/controllers/material.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'
import path from 'path'
import fs from 'fs'

export const uploadMaterial = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const file = req.file
    if (!file) return error(res, 'No file uploaded', 400)

    const { title, fileType, isPyq, year, subject, unit, examType } = req.body

    const material = await prisma.material.create({
      data: {
        collegeId, uploadedBy: userId,
        title: title || file.originalname.replace(/\\.[^.]+$/, ''),
        fileName: file.originalname,
        fileUrl: '/uploads/' + collegeId + '/' + file.filename,
        fileType: (isPyq === 'true' ? 'pyq' : fileType || 'notes') as any,
        fileSizeKb: Math.round(file.size / 1024),
        status: 'ready' as any,
        isPyq: isPyq === 'true',
        subject: subject || null,
        unit: unit || null,
        year: year ? parseInt(year) : null,
        examType: examType || null,
      },
      include: { uploader: { select: { name: true } } }
    })
    return success(res, material, 'Uploaded!', 201)
  } catch (err: any) {
    return error(res, 'Upload failed: ' + err.message, 500)
  }
}

export const getMaterials = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { isPyq, year, subject, unit, examType, search } = req.query

    const where: any = { collegeId }
    if (isPyq !== undefined) where.isPyq = isPyq === 'true'
    if (year) where.year = parseInt(year as string)
    if (subject) where.subject = { contains: subject as string, mode: 'insensitive' }
    if (unit) where.unit = { contains: unit as string, mode: 'insensitive' }
    if (examType) where.examType = examType as string
    if (search) where.title = { contains: search as string, mode: 'insensitive' }

    const materials = await prisma.material.findMany({
      where,
      include: { uploader: { select: { name: true } } },
      orderBy: { createdAt: 'desc' }
    })
    return success(res, materials)
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const downloadMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const material = await prisma.material.findFirst({ where: { id: req.params.id as string, collegeId } })
    if (!material) return error(res, 'Not found', 404)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return success(res, { fileUrl: material.fileUrl, fileName: material.fileName })
    res.setHeader('Content-Disposition', 'attachment; filename="' + material.fileName + '"')
    res.setHeader('Access-Control-Allow-Origin', '*')
    return res.download(filePath, material.fileName)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const previewMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const material = await prisma.material.findFirst({ where: { id: req.params.id as string, collegeId } })
    if (!material) return error(res, 'Not found', 404)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return error(res, 'File not found', 404)
    res.setHeader('Content-Type', 'application/pdf')
    res.setHeader('Content-Disposition', 'inline')
    res.setHeader('Access-Control-Allow-Origin', '*')
    return res.sendFile(filePath)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const deleteMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const material = await prisma.material.findFirst({ where: { id: req.params.id as string, collegeId } })
    if (!material) return error(res, 'Not found', 404)
    const fp = path.join(process.cwd(), material.fileUrl)
    if (fs.existsSync(fp)) fs.unlinkSync(fp)
    await prisma.material.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch (err) { return error(res, 'Failed', 500) }
}
""")
print("Material controller done!")

# ══════════════════════════════════════════
# FIX 7: Auth Controller - classSectionId in token
# ══════════════════════════════════════════
with open("src/controllers/auth.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { signToken, getRoleFromEmail } from '../utils/jwt'
import { success, error } from '../utils/response'
import crypto from 'crypto'

function genCode(branch: string, sem: string, section: string): string {
  const base = (branch.slice(0,3) + sem + section).toUpperCase().replace(/[^A-Z0-9]/g, '')
  const hash = crypto.randomBytes(2).toString('hex').toUpperCase()
  return base + '-' + hash
}

export const azureLogin = async (req: Request, res: Response) => {
  try {
    const { email, name, azureOid, avatarUrl } = req.body
    if (!email) return error(res, 'Email required', 400)
    const role = getRoleFromEmail(email)
    if (role === 'unknown') return error(res, 'Access denied', 403)

    const domain = email.split('@')[1] || 'krmu.edu.in'
    let college = await prisma.college.findUnique({ where: { domain } })
    if (!college) college = await prisma.college.create({ data: { name: 'K.R Mangalam University', domain } })

    let user = await prisma.user.findUnique({ where: { email } })
    if (!user) {
      const prefix = email.split('@')[0]
      user = await prisma.user.create({
        data: { collegeId: college.id, name: name || prefix, email, role: role as any, azureOid: azureOid || null, avatarUrl: avatarUrl || null, rollNumber: /^[0-9]/.test(prefix) ? prefix : null }
      })
    } else {
      user = await prisma.user.update({ where: { id: user.id }, data: { lastLogin: new Date(), avatarUrl: avatarUrl || user.avatarUrl, name: name || user.name } })
    }

    const token = signToken({ userId: user.id, email: user.email, role: user.role, name: user.name, collegeId: user.collegeId, classSectionId: user.classSectionId })
    return success(res, { token, user: { id: user.id, name: user.name, email: user.email, role: user.role, avatarUrl: user.avatarUrl, rollNumber: user.rollNumber, classSectionId: user.classSectionId } })
  } catch (err: any) { return error(res, 'Login failed: ' + err.message, 500) }
}

export const getMe = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { id: true, name: true, email: true, role: true, avatarUrl: true, rollNumber: true, subjects: true, classSectionId: true,
        classSection: { select: { id: true, name: true, section: true, branch: true, semester: true, uniqueCode: true } },
        college: { select: { name: true } }
      }
    })
    if (!user) return error(res, 'Not found', 404)
    return success(res, user)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const getUsers = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { role, classSectionId } = req.query
    const users = await prisma.user.findMany({
      where: { collegeId, ...(role && { role: role as any }), ...(classSectionId && { classSectionId: classSectionId as string }), isActive: true },
      select: { id: true, name: true, email: true, role: true, avatarUrl: true, rollNumber: true, classSectionId: true, classSection: { select: { name: true, section: true } } },
      orderBy: { name: 'asc' }
    })
    return success(res, users)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const updateSubjects = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { subjects } = req.body
    const user = await prisma.user.update({ where: { id: userId }, data: { subjects } })
    return success(res, { subjects: user.subjects })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const getClasses = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const classes = await prisma.classSection.findMany({
      where: { collegeId, isActive: true },
      include: { _count: { select: { students: true } } },
      orderBy: [{ semester: 'asc' }, { branch: 'asc' }]
    })
    return success(res, classes)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const createClass = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { name, section, semester, branch, year } = req.body
    let uniqueCode = genCode(branch, semester, section)
    while (await prisma.classSection.findUnique({ where: { uniqueCode } })) {
      uniqueCode = genCode(branch, semester, section)
    }
    const cls = await prisma.classSection.create({
      data: { collegeId, name, section, semester: parseInt(semester), branch, year: parseInt(year), uniqueCode }
    })
    return success(res, cls, 'Created', 201)
  } catch (err: any) { return error(res, err.message, 500) }
}

export const deleteClass = async (req: Request, res: Response) => {
  try {
    await prisma.classSection.update({ where: { id: req.params.id as string }, data: { isActive: false } })
    return success(res, null, 'Deleted')
  } catch (err: any) { return error(res, err.message, 500) }
}

export const joinClassByCode = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { code } = req.body
    if (!code) return error(res, 'Code required', 400)

    const cls = await prisma.classSection.findUnique({ where: { uniqueCode: code.toUpperCase().trim() } })
    if (!cls) return error(res, 'Invalid code: ' + code.toUpperCase().trim(), 404)
    if (!cls.isActive) return error(res, 'Class is inactive', 400)

    await prisma.user.update({ where: { id: userId }, data: { classSectionId: cls.id } })

    // Generate NEW token with classSectionId
    const user = await prisma.user.findUnique({ where: { id: userId } })
    const newToken = signToken({
      userId: user!.id, email: user!.email, role: user!.role,
      name: user!.name, collegeId: user!.collegeId, classSectionId: cls.id
    })

    return success(res, { class: cls, token: newToken }, 'Joined class!')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const selectClass = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { classSectionId } = req.body
    await prisma.user.update({ where: { id: userId }, data: { classSectionId } })
    const user = await prisma.user.findUnique({ where: { id: userId } })
    const newToken = signToken({
      userId: user!.id, email: user!.email, role: user!.role,
      name: user!.name, collegeId: user!.collegeId, classSectionId
    })
    return success(res, { token: newToken }, 'Class selected')
  } catch (err: any) { return error(res, err.message, 500) }
}

export const assignClass = async (req: Request, res: Response) => {
  try {
    const { studentId, classSectionId } = req.body
    await prisma.user.update({ where: { id: studentId }, data: { classSectionId } })
    return success(res, null, 'Assigned')
  } catch (err: any) { return error(res, err.message, 500) }
}
""")
print("Auth controller done!")

print("\n" + "="*50)
print("ALL BACKEND FIXES DONE!")
print("="*50)