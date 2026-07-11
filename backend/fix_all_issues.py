# Run from BACKEND folder
import os

# ═══════════════════════════════════════
# FIX 1: Prisma - PostgreSQL connection error (Neon needs pooling)
# ═══════════════════════════════════════
with open("src/config/db.ts", "r", encoding="utf-8") as f:
    db = f.read()

if "datasourceUrl" not in db:
    new_db = """import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient }

const prisma = globalForPrisma.prisma || new PrismaClient({
  datasourceUrl: process.env.DATABASE_URL,
  log: ['error'],
})

// Prevent multiple instances in development
if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma

// Handle connection errors gracefully
prisma.$connect().catch((e) => {
  console.error('DB connection error:', e)
})

export default prisma
"""
    with open("src/config/db.ts", "w", encoding="utf-8") as f:
        f.write(new_db)
    print("DB config fixed!")

# Fix prisma schema - add connection pooling
with open("prisma/schema.prisma", "r", encoding="utf-8") as f:
    schema = f.read()

if "?pgbouncer=true" not in schema:
    schema = schema.replace(
        'provider = "postgresql"',
        'provider = "postgresql"\n  directUrl = env("DIRECT_URL")'
    )
    with open("prisma/schema.prisma", "w", encoding="utf-8") as f:
        f.write(schema)
    print("Schema updated - add DIRECT_URL to Render env vars!")
    print("DIRECT_URL = same as DATABASE_URL but without ?pgbouncer=true")

# ═══════════════════════════════════════
# FIX 2: Material file URLs - use Render URL not localhost
# ═══════════════════════════════════════
with open("src/controllers/material.controller.ts", "r", encoding="utf-8") as f:
    mat = f.read()

# Store files properly - for production use absolute URL
old_upload = "fileUrl: '/uploads/' + collegeId + '/' + file.filename,"
new_upload = """fileUrl: '/uploads/' + collegeId + '/' + file.filename,
        filePublicUrl: (process.env.BACKEND_URL || 'http://localhost:5000') + '/uploads/' + collegeId + '/' + file.filename,"""

if "filePublicUrl" not in mat:
    mat = mat.replace(old_upload, new_upload)
    with open("src/controllers/material.controller.ts", "w", encoding="utf-8") as f:
        f.write(mat)
    print("Material controller updated!")

# ═══════════════════════════════════════
# FIX 3: AI Controller - STRICT unit scanning
# ═══════════════════════════════════════
with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write('''import { Request, Response } from \'express\'
import { success, error } from \'../utils/response\'
import prisma from \'../config/db\'

const GROQ_API = \'https://api.groq.com/openai/v1/chat/completions\'
const GROQ_KEY = process.env.GROQ_API_KEY || \'\'
const MODEL = \'llama-3.1-8b-instant\'

async function callGroq(system: string, user: string, maxTokens = 3000): Promise<string> {
  if (!GROQ_KEY) throw new Error(\'GROQ_API_KEY not set\')
  const res = await fetch(GROQ_API, {
    method: \'POST\',
    headers: { \'Content-Type\': \'application/json\', \'Authorization\': \'Bearer \' + GROQ_KEY },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: \'system\', content: system }, { role: \'user\', content: user }],
      max_tokens: maxTokens, temperature: 0.7,
    })
  })
  if (!res.ok) throw new Error(\'Groq API error: \' + res.status)
  const d = await res.json() as { choices: { message: { content: string } }[] }
  return d.choices?.[0]?.message?.content || \'\'
}

export const getMaterialUnits = async (req: Request, res: Response) => {
  try {
    const college = await prisma.college.findFirst({ orderBy: { createdAt: \'asc\' } })
    const cid = college?.id || \'\'
    const { subject } = req.query

    const materials = await prisma.material.findMany({
      where: {
        collegeId: cid, isPyq: false,
        ...(subject && { subject: { contains: subject as string, mode: \'insensitive\' as any } })
      },
      select: { unit: true, subject: true, title: true }
    })

    const pyqs = await prisma.material.findMany({
      where: {
        collegeId: cid, isPyq: true,
        ...(subject && { subject: { contains: subject as string, mode: \'insensitive\' as any } })
      },
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

    const selectedTopics = [
      ...(Array.isArray(units) ? units.filter(Boolean) : []),
      ...(Array.isArray(extraTopics) ? extraTopics.filter(Boolean) : [])
    ]

    if (selectedTopics.length === 0) {
      return error(res, \'Please select at least one unit or topic\', 400)
    }

    const sectionsDesc = (sections || []).map((s: any) =>
      `Section ${s.name}: generate exactly ${s.total} questions worth ${s.marks} marks each`
    ).join(\'\\n\')

    const topicList = selectedTopics.map((t, i) => `${i+1}. ${t}`).join(\'\\n\')

    const pyqNote = (usePyqs && pyqYears?.length > 0)
      ? `\\nIMPORTANT: Style questions similar to previous year papers from: ${pyqYears.join(\', \')}`
      : \'\'

    const systemPrompt = `You are a strict university exam paper setter.
ABSOLUTE RULE: You MUST ONLY create questions from these EXACT topics: ${selectedTopics.join(\', \')}
DO NOT use any other topics. DO NOT add general knowledge questions.
Every single question text must clearly mention or relate to one of the given topics.
Return ONLY valid JSON array. No markdown. No explanation. No text before or after the JSON.`

    const userPrompt = `Create exam questions for subject: ${subject}
Difficulty: ${difficulty || \'mixed\'}${pyqNote}

TOPICS LIST (USE ONLY THESE - NO EXCEPTIONS):
${topicList}

Required sections:
${sectionsDesc}

STRICT RULES:
- EVERY question must be about one of the ${selectedTopics.length} topics listed above
- Distribute questions across ALL topics equally
- Section A: short definitions/one-liners FROM the topics
- Section B: explanation with examples FROM the topics
- Section C: detailed analysis/case studies FROM the topics
- "unit" field = exact topic name from list above

Return JSON array ONLY (no other text):
[{"id":1,"section":"A","questionNo":1,"text":"Define ${selectedTopics[0]} and its importance","marks":${sections?.[0]?.marks || 2},"unit":"${selectedTopics[0]}","difficulty":"easy","type":"short"}]`

    const raw = await callGroq(systemPrompt, userPrompt, 3500)

    let questions = []
    try {
      const cleaned = raw.replace(/```json|```/g, \'\').trim()
      const match = cleaned.match(/\\[[\\s\\S]*\\]/)
      questions = JSON.parse(match ? match[0] : cleaned)
    } catch {
      return error(res, \'AI format error. Please try again.\', 500)
    }

    // VERIFY questions are from given topics
    const verifiedQuestions = questions.filter((q: any) => {
      const text = (q.text || \'\').toLowerCase()
      const unit = (q.unit || \'\').toLowerCase()
      return selectedTopics.some(t =>
        text.includes(t.toLowerCase().split(\' \')[0]) ||
        unit.includes(t.toLowerCase().split(\' \')[0])
      )
    })

    return success(res, {
      questions: verifiedQuestions.length > 0 ? verifiedQuestions : questions,
      metadata: { subject, topics: selectedTopics, totalQuestions: questions.length }
    })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history, image } = req.body

    if (!GROQ_KEY) return error(res, \'GROQ_API_KEY not configured on server\', 500)

    const userContent = image
      ? `${message || \'Please analyze and solve this problem from the image\'}\\n[Student shared an image related to ${subject || \'their subject\'}. Based on the subject context, provide a detailed step-by-step solution.]`
      : message

    if (!userContent) return error(res, \'Message required\', 400)

    const msgs = [
      ...(history || []).slice(-6).map((h: any) => ({ role: h.role, content: h.content })),
      { role: \'user\', content: userContent }
    ]

    const res2 = await fetch(GROQ_API, {
      method: \'POST\',
      headers: { \'Content-Type\': \'application/json\', \'Authorization\': \'Bearer \' + GROQ_KEY },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          {
            role: \'system\',
            content: `You are HAYAT, an expert AI tutor for ${subject || \'all subjects\'} at K.R Mangalam University, India. ${image ? \'The student has shared an image of their problem. Provide detailed step-by-step solution.\' : \'Be clear, concise and use examples.\'} Always respond in a helpful, educational manner.`
          },
          ...msgs
        ],
        max_tokens: 2048, temperature: 0.7,
      })
    })

    if (!res2.ok) {
      const errText = await res2.text()
      return error(res, \'AI service error: \' + errText, 500)
    }

    const d = await res2.json() as { choices: { message: { content: string } }[] }
    const reply = d.choices?.[0]?.message?.content
    if (!reply) return error(res, \'No response from AI\', 500)

    return success(res, { reply })
  } catch (err: any) {
    console.error(\'aiChat error:\', err)
    return error(res, \'AI service unavailable: \' + err.message, 500)
  }
}

export const checkAnswer = async (req: Request, res: Response) => {
  try {
    const { question, answer, subject, marks } = req.body
    const raw = await callGroq(\'Grade this answer. Return ONLY valid JSON.\',
      `Q: ${question}\\nA: ${answer}\\nSubject: ${subject}\\nMax: ${marks}\\nReturn: {"marksAwarded":number,"percentage":number,"grade":"A/B/C/F","feedback":"text"}`)
    const match = raw.match(/\\{[\\s\\S]*\\}/)
    return success(res, JSON.parse(match ? match[0] : raw.replace(/```json|```/g, \'\').trim()))
  } catch (err: any) { return error(res, err.message, 500) }
}
''')
print("AI controller done!")

# ═══════════════════════════════════════
# FIX 4: Auth controller - notify unassigned students
# ═══════════════════════════════════════
with open("src/controllers/auth.controller.ts", "r", encoding="utf-8") as f:
    auth = f.read()

# After user creation, send notification if no class
old_create = """    return success(res, {
      token,
      user: {
        id: user.id, name: user.name, email: user.email,
        role: user.role, avatarUrl: user.avatarUrl,
        rollNumber: user.rollNumber, classSectionId: user.classSectionId,
        collegeId: college.id,
      }
    })"""

new_create = """    // If student has no class, create a self-reminder notification
    if (user.role === 'student' && !user.classSectionId) {
      const existingNotif = await prisma.notification.findFirst({
        where: { userId: user.id, type: 'system', title: { contains: 'class' } }
      })
      if (!existingNotif) {
        await prisma.notification.create({
          data: {
            userId: user.id,
            title: '⚠️ Please Join Your Class!',
            body: 'You have not enrolled in any class yet. Go to Dashboard and select your class to access tasks, materials and results.',
            type: 'system'
          }
        }).catch(() => {})
      }
    }

    return success(res, {
      token,
      user: {
        id: user.id, name: user.name, email: user.email,
        role: user.role, avatarUrl: user.avatarUrl,
        rollNumber: user.rollNumber, classSectionId: user.classSectionId,
        collegeId: college.id,
      }
    })"""

if "Please Join Your Class" not in auth:
    auth = auth.replace(old_create, new_create)
    with open("src/controllers/auth.controller.ts", "w", encoding="utf-8") as f:
        f.write(auth)
    print("Auth controller - student notification added!")
else:
    print("Auth already has class notification")

print("\n=== BACKEND DONE ===")
print("\nIMPORTANT: Add these to Render Environment Variables:")
print("BACKEND_URL = https://aiqpg-backend.onrender.com")
print("DIRECT_URL = (same as DATABASE_URL from neon.tech)")