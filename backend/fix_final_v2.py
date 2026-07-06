import os

os.makedirs("src/routes", exist_ok=True)

# Notification routes
with open("src/routes/notification.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { getNotifications, markRead, markAllRead, deleteNotification, sendBulkNotification } from '../controllers/notification.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import prisma from '../config/db'

const router = Router()
router.get('/', authenticate, getNotifications)
router.patch('/read-all', authenticate, markAllRead)
router.patch('/:id/read', authenticate, markRead)
router.delete('/:id', authenticate, deleteNotification)
router.post('/send', authenticate, authorize('teacher','admin'), sendBulkNotification)
router.post('/', authenticate, authorize('teacher','admin'), async (req: any, res: any) => {
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

# AI Controller - STRICT topic-based generation
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
      max_tokens: maxTokens, temperature: 0.7,
    })
  })
  if (!res.ok) throw new Error('Groq: ' + await res.text())
  const d = await res.json() as { choices: { message: { content: string } }[] }
  return d.choices?.[0]?.message?.content || ''
}

export const generateQuestions = async (req: Request, res: Response) => {
  try {
    const { subject, units, extraTopics, sections, difficulty } = req.body

    const selectedTopics = [
      ...(Array.isArray(units) ? units.filter(Boolean) : []),
      ...(Array.isArray(extraTopics) ? extraTopics.filter(Boolean) : [])
    ]

    if (selectedTopics.length === 0) {
      return error(res, 'Please select at least one unit or topic', 400)
    }

    const sectionsDesc = (sections || []).map((s: any) =>
      'Section ' + s.name + ': ' + s.total + ' questions of ' + s.marks + ' marks each'
    ).join('\\n')

    // Create strict per-topic distribution
    const topicDist = selectedTopics.map((t, i) => (i + 1) + '. ' + t).join('\\n')

    const systemPrompt = `You are a university exam paper setter.
STRICT RULE: You MUST create questions ONLY from these specific topics provided by the teacher.
DO NOT add questions from any other topic.
DO NOT use your general knowledge to add unrelated topics.
Every question text must clearly reference one of the given topics.
Return ONLY valid JSON array, no markdown, no explanation.`

    const userPrompt = `Create exam questions for:
Subject: ${subject}
Difficulty: ${difficulty || 'mixed'}

TOPICS PROVIDED (use ONLY these - no others):
${topicDist}

Sections required:
${sectionsDesc}

STRICT RULES:
- ONLY use topics from the list above
- Distribute questions evenly across ALL topics
- Each question must be about a specific topic from the list
- Section A: short answers, definitions from the topics
- Section B: explanations with examples from the topics  
- Section C: long answers, analysis from the topics
- "unit" field must be EXACT topic name from the list

Return JSON ONLY:
[{"id":1,"section":"A","questionNo":1,"text":"question about ${selectedTopics[0] || subject}","marks":${(sections && sections[0]) ? sections[0].marks : 2},"unit":"${selectedTopics[0] || subject}","difficulty":"easy","type":"short"}]`

    const raw = await callGroq(systemPrompt, userPrompt)

    let questions = []
    try {
      const match = raw.match(/\\[[\\s\\S]*\\]/)
      questions = JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim())
    } catch {
      return error(res, 'AI format error. Please try again.', 500)
    }

    return success(res, { questions, metadata: { subject, topics: selectedTopics, totalQuestions: questions.length } })
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
        messages: [
          { role: 'system', content: 'You are an expert academic tutor for ' + (subject || 'all subjects') + ' at K.R Mangalam University. Be clear, concise and educational. Use examples.' },
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
      'Q: ' + question + '\\nA: ' + answer + '\\nSubject: ' + subject + '\\nMax: ' + marks + '\\nReturn: {"marksAwarded":number,"percentage":number,"grade":"A/B/C/F","feedback":"text","strengths":["s1"],"improvements":["i1"]}'
    )
    const match = raw.match(/\\{[\\s\\S]*\\}/)
    return success(res, JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim()))
  } catch (err: any) { return error(res, err.message, 500) }
}
""")
print("AI controller done - strict topic usage!")

# Task Controller - Fix: tasks only go to selected class
with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

async function getMainCollegeId(): Promise<string> {
  const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
  return college?.id || ''
}

export const createTask = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const collegeId = await getMainCollegeId()
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

    // IMPORTANT: Only notify students in the specific class
    // If no class selected, notify ALL students
    let studentFilter: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId && classSectionId !== '' && classSectionId !== 'null') {
      // Only this class
      studentFilter.classSectionId = classSectionId
    }
    // else: all students

    const students = await prisma.user.findMany({ where: studentFilter, select: { id: true } })

    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: '📋 New ' + (taskType || 'assignment').replace('_', ' '),
          body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true }) : ''),
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
    const { userId } = (req as any).user
    const collegeId = await getMainCollegeId()
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
    const { role, userId } = (req as any).user
    const collegeId = await getMainCollegeId()
    const { classId } = req.query

    let where: any = { collegeId }

    if (role === 'student') {
      where.status = 'active'
      const classIdStr = classId as string
      if (classIdStr && classIdStr !== 'undefined' && classIdStr !== '') {
        // Student sees: tasks for THEIR class + tasks with NO class (college-wide)
        where.OR = [
          { classSectionId: classIdStr },
          { classSectionId: null }
        ]
      }
      // If no classId: show only college-wide tasks (no class assigned)
    } else if (role === 'teacher') {
      const classIdStr = classId as string
      if (classIdStr && classIdStr !== 'undefined' && classIdStr !== '') {
        where.classSectionId = classIdStr
      }
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
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const getTask = async (req: Request, res: Response) => {
  try {
    const collegeId = await getMainCollegeId()
    const task = await prisma.task.findFirst({
      where: { id: req.params.id as string, collegeId },
      include: { creator: { select: { name: true } }, classSection: { select: { name: true, section: true } }, submissions: { include: { student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } } } } }
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

export const extendDeadline = async (req: Request, res: Response) => {
  try {
    const collegeId = await getMainCollegeId()
    const { newDeadline } = req.body
    const task = await prisma.task.update({
      where: { id: req.params.id as string },
      data: { deadline: new Date(newDeadline), allowLate: true }
    })
    const f: any = { collegeId, role: 'student', isActive: true }
    if (task.classSectionId) f.classSectionId = task.classSectionId
    const students = await prisma.user.findMany({ where: f, select: { id: true } })
    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({ userId: s.id, title: '⏰ Deadline Extended', body: '"' + task.title + '" extended to ' + new Date(newDeadline).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true }), type: 'task', refId: task.id }))
      })
    }
    return success(res, task, 'Extended')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const deleteTask = async (req: Request, res: Response) => {
  try {
    await prisma.task.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch { return error(res, 'Failed', 500) }
}
""")
print("Task controller done - class-specific!")

# Fix auth - student class shown correctly in teacher dashboard
with open("src/controllers/auth.controller.ts", "r", encoding="utf-8") as f:
    auth_content = f.read()

# Make sure getUsers returns classSectionId properly
if "classSection: { select: { name: true, section: true } }" in auth_content:
    auth_content = auth_content.replace(
        "classSection: { select: { name: true, section: true } }",
        "classSection: { select: { id: true, name: true, section: true, branch: true, semester: true } }"
    )
    with open("src/controllers/auth.controller.ts", "w", encoding="utf-8") as f:
        f.write(auth_content)
    print("Auth controller updated!")
else:
    print("Auth controller - already updated")

print("\n=== BACKEND DONE ===")