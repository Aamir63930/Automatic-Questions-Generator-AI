import os

# ═══════════════════════════════════════════
# FIX 1: Single College for everyone (merge domains)
# ═══════════════════════════════════════════
with open("src/controllers/auth.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { signToken, getRoleFromEmail } from '../utils/jwt'
import { success, error } from '../utils/response'
import crypto from 'crypto'

const FIXED_DOMAIN = 'krmu.edu.in' // Everyone belongs to ONE college regardless of login email

function genCode(branch: string, sem: string, section: string): string {
  const base = (branch.slice(0,3) + sem + section).toUpperCase().replace(/[^A-Z0-9]/g, '')
  const hash = crypto.randomBytes(2).toString('hex').toUpperCase()
  return base + '-' + hash
}

async function getOrCreateCollege() {
  let college = await prisma.college.findUnique({ where: { domain: FIXED_DOMAIN } })
  if (!college) {
    college = await prisma.college.create({ data: { name: 'K.R Mangalam University', domain: FIXED_DOMAIN } })
  }
  return college
}

export const azureLogin = async (req: Request, res: Response) => {
  try {
    const { email, name, azureOid, avatarUrl } = req.body
    if (!email) return error(res, 'Email required', 400)
    const role = getRoleFromEmail(email)
    if (role === 'unknown') return error(res, 'Access denied', 403)

    // ALWAYS use the same fixed college, regardless of login domain
    const college = await getOrCreateCollege()

    let user = await prisma.user.findUnique({ where: { email } })
    if (!user) {
      const prefix = email.split('@')[0]
      user = await prisma.user.create({
        data: { collegeId: college.id, name: name || prefix, email, role: role as any, azureOid: azureOid || null, avatarUrl: avatarUrl || null, rollNumber: /^[0-9]/.test(prefix) ? prefix : null }
      })
    } else {
      // Migrate old users to fixed college if they were in a different one
      user = await prisma.user.update({ where: { id: user.id }, data: { lastLogin: new Date(), avatarUrl: avatarUrl || user.avatarUrl, name: name || user.name, collegeId: college.id } })
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
    // Always use fixed college so everyone sees the same classes
    const college = await getOrCreateCollege()
    const classes = await prisma.classSection.findMany({
      where: { collegeId: college.id, isActive: true },
      include: { _count: { select: { students: true } } },
      orderBy: [{ semester: 'asc' }, { branch: 'asc' }]
    })
    return success(res, classes)
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const createClass = async (req: Request, res: Response) => {
  try {
    const college = await getOrCreateCollege()
    const { name, section, semester, branch, year } = req.body
    let uniqueCode = genCode(branch, semester, section)
    while (await prisma.classSection.findUnique({ where: { uniqueCode } })) {
      uniqueCode = genCode(branch, semester, section)
    }
    const cls = await prisma.classSection.create({
      data: { collegeId: college.id, name, section, semester: parseInt(semester), branch, year: parseInt(year), uniqueCode }
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
    const { userId } = (req as any).user
    const { code } = req.body
    if (!code) return error(res, 'Code required', 400)
    const cls = await prisma.classSection.findUnique({ where: { uniqueCode: code.toUpperCase().trim() } })
    if (!cls) return error(res, 'Invalid code: ' + code.toUpperCase().trim(), 404)
    if (!cls.isActive) return error(res, 'Class is inactive', 400)
    await prisma.user.update({ where: { id: userId }, data: { classSectionId: cls.id } })
    const user = await prisma.user.findUnique({ where: { id: userId } })
    const newToken = signToken({ userId: user!.id, email: user!.email, role: user!.role, name: user!.name, collegeId: user!.collegeId, classSectionId: cls.id })
    return success(res, { class: cls, token: newToken }, 'Joined class!')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const selectClass = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { classSectionId } = req.body
    await prisma.user.update({ where: { id: userId }, data: { classSectionId } })
    const user = await prisma.user.findUnique({ where: { id: userId } })
    const newToken = signToken({ userId: user!.id, email: user!.email, role: user!.role, name: user!.name, collegeId: user!.collegeId, classSectionId })
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
print("Auth controller fixed - single college for everyone!")

# ═══════════════════════════════════════════
# FIX 2: Groq model - use the CURRENT working model
# ═══════════════════════════════════════════
with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import { success, error } from '../utils/response'

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions'
const GROQ_KEY = process.env.GROQ_API_KEY || ''
const MODEL = 'llama-3.1-8b-instant' // Current active free Groq model

async function callGroq(system: string, user: string, maxTokens = 2048): Promise<string> {
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
      temperature: 0.85,
    })
  })
  if (!res.ok) {
    const errText = await res.text()
    throw new Error('Groq API error: ' + errText)
  }
  const d = await res.json() as { choices: { message: { content: string } }[] }
  return d.choices?.[0]?.message?.content || ''
}

export const generateQuestions = async (req: Request, res: Response) => {
  try {
    const { subject, units, sections, difficulty } = req.body
    const seed = Date.now()
    const unitsList = Array.isArray(units) && units.length > 0 ? units.join(', ') : subject
    const sectionsDesc = (sections || []).map((s: any) =>
      'Section ' + s.name + ': Exactly ' + s.total + ' questions, ' + s.marks + ' marks each'
    ).join('\\n')

    const raw = await callGroq(
      'You are a university professor. Return ONLY a valid JSON array. No markdown, no explanation, no backticks.',
      'Generate UNIQUE exam questions (id:' + seed + ') for:\\nSubject: ' + subject + '\\nTopics: ' + unitsList + '\\nDifficulty: ' + (difficulty || 'mixed') + '\\n\\n' + sectionsDesc + '\\n\\nRules:\\n- Section A: short definitions, fill blanks, one-liners\\n- Section B: explain with examples, compare/contrast\\n- Section C: long essays, case studies, design\\n- All questions MUST be different\\n- Cover: ' + unitsList + '\\n\\nReturn JSON array:\\n[{"id":1,"section":"A","questionNo":1,"text":"question text","marks":2,"unit":"unit name","difficulty":"easy","type":"short"}]',
      3000
    )

    let questions = []
    try {
      const match = raw.match(/\\[[\\s\\S]*\\]/)
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
    if (!GROQ_KEY || GROQ_KEY === 'your-groq-api-key-here') {
      return error(res, 'GROQ_API_KEY not set. Get free key at console.groq.com', 500)
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
        messages: [
          { role: 'system', content: 'You are an expert tutor for ' + (subject || 'all subjects') + ' at K.R Mangalam University. Be clear, concise, use examples.' },
          ...msgs
        ],
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
      'Question: ' + question + '\\nAnswer: ' + answer + '\\nSubject: ' + subject + '\\nMax: ' + marks + '\\nReturn: {"marksAwarded":number,"percentage":number,"grade":"A/B/C/F","feedback":"text","strengths":["s1"],"improvements":["i1"]}'
    )
    const match = raw.match(/\\{[\\s\\S]*\\}/)
    return success(res, JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim()))
  } catch (err: any) { return error(res, err.message, 500) }
}
""")
print("AI controller fixed - model updated!")

# ═══════════════════════════════════════════
# FIX 3: Task Controller (was missing from FileNotFoundError)
# ═══════════════════════════════════════════
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
    const filter: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId) filter.classSectionId = classSectionId
    const students = await prisma.user.findMany({ where: filter, select: { id: true } })
    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: 'New ' + (taskType || 'assignment').replace('_', ' '),
          body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleDateString('en-IN') : ''),
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
    const { collegeId, role } = (req as any).user
    const { classId } = req.query
    let where: any = { collegeId }

    if (role === 'student') {
      where.status = 'active'
      if (classId) {
        where.OR = [{ classSectionId: classId as string }, { classSectionId: null }]
      }
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
  } catch { return error(res, 'Failed', 500) }
}

export const updateTaskStatus = async (req: Request, res: Response) => {
  try {
    const task = await prisma.task.update({ where: { id: req.params.id as string }, data: { status: req.body.status as any } })
    return success(res, task)
  } catch { return error(res, 'Failed', 500) }
}

export const deleteTask = async (req: Request, res: Response) => {
  try {
    await prisma.task.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch { return error(res, 'Failed', 500) }
}
""")
print("Task controller created!")

print("\n" + "="*50)
print("ALL BACKEND FIXES DONE!")
print("="*50)
with open("../frontend/components/ui/Sidebar.tsx", "r", encoding="utf-8") as f:
    pass  # just checking - skip, real fix is below