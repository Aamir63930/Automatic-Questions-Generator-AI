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
    if (!GROQ_KEY || GROQ_KEY === 'your-groq-api-key-here') {
      return error(res, 'GROQ_API_KEY not set. Get free key at console.groq.com and add to backend .env', 500)
    }
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
          { role: 'system', content: 'You are an expert tutor for ' + (subject || 'all subjects') + ' at K.R Mangalam University. Be clear, concise, use examples.' },
          ...msgs
        ],
        max_tokens: 1024, temperature: 0.7,
      })
    })
    const d = await res2.json() as { choices: { message: { content: string } }[] }
    const reply = d.choices?.[0]?.message?.content || 'No response'
    return success(res, { reply })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const checkAnswer = async (req: Request, res: Response) => {
  try {
    const { question, answer, subject, marks } = req.body
    const raw = await callGroq(
      'Grade this answer. Return ONLY valid JSON.',
      'Question: ' + question + '\\nAnswer: ' + answer + '\\nSubject: ' + subject + '\\nMax: ' + marks + '\\nReturn: {"marksAwarded":number,"percentage":number,"grade":"A/B/C/F","feedback":"text","strengths":["s1"],"improvements":["i1"]}'
    )
    const match = raw.match(/\{[\s\S]*\}/)
    return success(res, JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim()))
  } catch (err: any) { return error(res, err.message, 500) }
}
""")
print("AI controller fixed!")