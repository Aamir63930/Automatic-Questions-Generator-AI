import re

with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Rewrite generateQuestions function with STRICT topic enforcement
old_system = content[content.find('const systemPrompt'):content.find('const userPrompt')]

new_generate = '''export const generateQuestions = async (req: Request, res: Response) => {
  try {
    const { subject, units, extraTopics, sections, difficulty, pyqYears, usePyqs } = req.body

    const selectedTopics = [
      ...(Array.isArray(units) ? units.filter(Boolean) : []),
      ...(Array.isArray(extraTopics) ? extraTopics.filter(Boolean) : [])
    ]

    if (selectedTopics.length === 0) {
      return error(res, 'Please select at least one unit or topic', 400)
    }

    const sectionsDesc = (sections || []).map((s: any) =>
      `Section ${s.name}: ${s.total} questions of ${s.marks} marks each`
    ).join('\\n')

    const topicList = selectedTopics.map((t: string, i: number) => `${i+1}. ${t}`).join('\\n')
    const pyqNote = (usePyqs && pyqYears?.length > 0)
      ? `Style similar to PYQ papers from years: ${pyqYears.join(', ')}` : ''

    const prompt = `Create exam questions for: ${subject}
Difficulty: ${difficulty || 'mixed'}
${pyqNote}

TOPICS (USE ONLY THESE ${selectedTopics.length} TOPICS - NO OTHERS):
${topicList}

${sectionsDesc}

RULES:
- Every question MUST be about one of the ${selectedTopics.length} topics above
- "unit" field must be EXACT topic name from the list
- Cover ALL topics with at least 1 question each
- Section A: short 1-liners about the topics
- Section B: explain with examples from the topics
- Section C: detailed analysis from the topics

Return ONLY this JSON (no text before/after):
[{"id":1,"section":"A","questionNo":1,"text":"question about ${selectedTopics[0] || subject}","marks":${sections?.[0]?.marks || 2},"unit":"${selectedTopics[0] || subject}","difficulty":"easy","type":"short"}]`

    const raw = await callGroq(
      `You are an exam paper setter. ONLY use topics from the given list. Return ONLY valid JSON array.`,
      prompt,
      3500
    )

    let questions = []
    try {
      const cleaned = raw.replace(/\`\`\`json|\`\`\`/g, '').trim()
      const match = cleaned.match(/\\[[\\s\\S]*\\]/)
      questions = JSON.parse(match ? match[0] : cleaned)
    } catch {
      return error(res, 'AI format error. Try again.', 500)
    }

    return success(res, {
      questions,
      metadata: { subject, topics: selectedTopics, totalQuestions: questions.length }
    })
  } catch (err: any) { return error(res, err.message, 500) }
}'''

# Replace the entire generateQuestions function
content = re.sub(
    r'export const generateQuestions = async.*?^\}',
    new_generate,
    content,
    flags=re.DOTALL | re.MULTILINE
)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("AI controller fixed!")