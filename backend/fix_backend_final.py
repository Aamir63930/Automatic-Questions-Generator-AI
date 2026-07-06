import os

# ══════════════════════════════════════════
# BACKEND: Free AI using Groq (Llama 3)
# ══════════════════════════════════════════
with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import { success, error } from '../utils/response'

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions'
const GROQ_KEY = process.env.GROQ_API_KEY || ''
const MODEL ="llama-3.1-8b-instant" // Free Groq model

async function callGroq(systemPrompt: string, messages: {role: string; content: string}[]): Promise<string> {
  const res = await fetch(GROQ_API, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + GROQ_KEY,
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: 'system', content: systemPrompt },
        ...messages
      ],
      max_tokens: 1024,
      temperature: 0.7,
    })
  })
  if (!res.ok) {
    const errText = await res.text()
    throw new Error('Groq API error: ' + errText)
  }
  const data = await res.json()
  return data.choices?.[0]?.message?.content || 'No response'
}

export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history } = req.body
    const systemPrompt = `You are an expert academic tutor for K.R Mangalam University students.
Subject: ${subject || 'General'}
Your role: Help students understand concepts, solve doubts, generate practice questions, and prepare for exams.
Be clear, concise, and educational. Use examples. If asked for questions, give numbered questions with answers.`

    const msgs = [
      ...(history || []).slice(-6).map((h: any) => ({ role: h.role, content: h.content })),
      { role: 'user', content: message }
    ]

    const reply = await callGroq(systemPrompt, msgs)
    return success(res, { reply })
  } catch (err: any) {
    console.error('AI chat error:', err.message)
    return error(res, 'AI unavailable: ' + err.message, 500)
  }
}

export const generateQuestions = async (req: Request, res: Response) => {
  try {
    const { subject, units, sections, difficulty, pyqYears, source } = req.body

    const systemPrompt = `You are a university professor creating exam questions. Return ONLY a valid JSON array. No markdown, no extra text.`

    const sectionsDesc = (sections || []).map((s: any) =>
      `Section ${s.name}: ${s.total} questions of ${s.marks} marks each, student attempts ${s.attempt}`
    ).join('\\n')

    const userMsg = `Create exam questions for:
Subject: ${subject}
Topics/Units: ${(units || [subject]).join(', ')}
${source === 'pyq' ? 'Based on PYQ years: ' + (pyqYears || []).join(', ') : ''}
Difficulty: ${difficulty || 'mixed'}

Sections:
${sectionsDesc}

Return JSON array:
[{"id":1,"section":"A","questionNo":1,"text":"question text","marks":2,"unit":"unit name","difficulty":"easy","type":"descriptive"}]`

    const raw = await callGroq(systemPrompt, [{ role: 'user', content: userMsg }])

    let questions = []
    try {
      const match = raw.match(/\\[.*\\]/s)
      questions = JSON.parse(match ? match[0] : raw.replace(/\`\`\`json|\`\`\`/g, '').trim())
    } catch {
      questions = JSON.parse(raw.replace(/\`\`\`json|\`\`\`/g, '').trim())
    }

    return success(res, { questions })
  } catch (err: any) {
    return error(res, 'Question generation failed: ' + err.message, 500)
  }
}

export const checkAnswer = async (req: Request, res: Response) => {
  try {
    const { question, answer, subject, marks } = req.body
    const systemPrompt = `You are a university professor grading answers. Return ONLY valid JSON, no extra text.`
    const userMsg = `Grade this:
Question: ${question}
Answer: ${answer}
Subject: ${subject}
Max Marks: ${marks}

Return: {"marksAwarded":number,"percentage":number,"grade":"A/B/C/D/F","feedback":"feedback text","strengths":["point"],"improvements":["point"]}`

    const raw = await callGroq(systemPrompt, [{ role: 'user', content: userMsg }])
    const match = raw.match(/\\{.*\\}/s)
    const result = JSON.parse(match ? match[0] : raw.replace(/\`\`\`json|\`\`\`/g, '').trim())
    return success(res, result)
  } catch (err: any) {
    return error(res, 'Check failed: ' + err.message, 500)
  }
}
""")
print("AI controller (Groq) done!")

# Update .env
with open(".env", "r", encoding="utf-8") as f:
    env = f.read()
if "GROQ_API_KEY" not in env:
    with open(".env", "a", encoding="utf-8") as f:
        f.write("\n# Groq AI (FREE - get key from console.groq.com)\nGROQ_API_KEY=your-groq-api-key-here\n")
print(".env updated!")

# Fix submission controller - teacher sees all submissions with student details
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

    const existing = await prisma.submission.findUnique({
      where: { taskId_studentId: { taskId: taskId as string, studentId: userId } }
    })
    if (existing) return error(res, 'Already submitted', 400)

    const isLate = task.deadline && new Date() > task.deadline
    if (isLate && !task.allowLate) return error(res, 'Deadline has passed', 400)

    const submission = await prisma.submission.create({
      data: {
        taskId: taskId as string,
        studentId: userId,
        textAnswer: textAnswer || null,
        fileUrl: file ? '/uploads/' + collegeId + '/' + file.filename : null,
        fileName: file?.originalname || null,
        status: (isLate ? 'late' : 'submitted') as any,
      },
      include: { student: { select: { name: true, email: true, rollNumber: true } }, task: { select: { title: true, maxMarks: true } } }
    })

    // Notify teacher
    const student = await prisma.user.findUnique({ where: { id: userId }, select: { name: true } })
    await prisma.notification.create({
      data: {
        userId: task.createdBy,
        title: 'New Submission',
        body: (student?.name || 'Student') + ' submitted "' + task.title + '"',
        type: 'task',
        refId: taskId as string,
      }
    })

    return success(res, submission, 'Submitted successfully!', 201)
  } catch (err: any) {
    return error(res, 'Submission failed: ' + err.message, 500)
  }
}

export const getSubmissions = async (req: Request, res: Response) => {
  try {
    const { userId, role } = (req as any).user
    const { taskId } = req.query

    const submissions = await prisma.submission.findMany({
      where: {
        ...(taskId && { taskId: taskId as string }),
        ...(role === 'student' && { studentId: userId }),
      },
      include: {
        student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } },
        task: { select: { title: true, maxMarks: true, taskType: true, subjectName: true } }
      },
      orderBy: { submittedAt: 'desc' }
    })
    return success(res, submissions)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const gradeSubmission = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    const { marks, feedback } = req.body

    const submission = await prisma.submission.update({
      where: { id },
      data: {
        marksAwarded: parseInt(marks),
        feedback: feedback || null,
        gradedBy: userId,
        gradedAt: new Date(),
        status: 'graded' as any,
      },
      include: { task: { select: { title: true, maxMarks: true } }, student: { select: { name: true } } }
    })

    // Notify student
    await prisma.notification.create({
      data: {
        userId: submission.studentId,
        title: '📊 Result Published!',
        body: '"' + submission.task.title + '" graded: ' + marks + '/' + submission.task.maxMarks + (feedback ? ' — ' + feedback : ''),
        type: 'result',
        refId: submission.taskId,
      }
    })

    return success(res, submission, 'Graded!')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}
""")
print("Submission controller done!")

print("\nBackend fixes done!")