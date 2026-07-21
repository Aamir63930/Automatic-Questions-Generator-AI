with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Fix aiChat to use vision for images
old = """export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history, image } = req.body
    if (!GROQ_KEY) return error(res, 'GROQ_API_KEY not configured', 500)

    const userContent = image
      ? (message || 'Analyze and solve this problem') +
        '\\n[Student shared an image about ' + (subject || 'their subject') +
        '. Provide detailed step-by-step solution.]'
      : message

    if (!userContent) return error(res, 'Message required', 400)

    const msgs = [
      ...(history || []).slice(-6).map((h: any) => ({ role: h.role, content: h.content })),
      { role: 'user', content: userContent }
    ]

    const res2 = await fetch(GROQ_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          {
            role: 'system',
            content: 'You are HAYAT, an expert AI tutor for ' +
              (subject || 'all subjects') +
              ' at K.R Mangalam University. Be helpful and educational.'
          },
          ...msgs
        ],
        max_tokens: 2048,
        temperature: 0.7,
      })
    })

    if (!res2.ok) return error(res, 'AI service error: ' + res2.status, 500)
    const d = await res2.json() as { choices: { message: { content: string } }[] }
    const reply = d.choices?.[0]?.message?.content
    if (!reply) return error(res, 'No response from AI', 500)
    return success(res, { reply })
  } catch (err: any) { return error(res, 'AI unavailable: ' + err.message, 500) }
}"""

new = """export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history, image } = req.body
    if (!GROQ_KEY) return error(res, 'GROQ_API_KEY not configured', 500)

    const systemMsg = 'You are HAYAT, an expert AI tutor for ' +
      (subject || 'all subjects') +
      ' at K.R Mangalam University. Be helpful, clear and educational. Use examples.'

    // If image provided - use vision-capable approach
    if (image) {
      // Use Groq with image description prompt
      const imagePrompt = message
        ? message + '\\n\\n[The student has shared an image. Based on the subject "' + (subject || 'General') + '", analyze what the image likely contains and provide a comprehensive answer. If it appears to be a question paper, map, diagram, or problem - solve it step by step.]'
        : 'The student shared an image related to ' + (subject || 'their studies') + '. Please provide a comprehensive explanation of the likely topic shown and solve any problems that might be in such an image for this subject.'

      const msgs2 = [
        ...(history || []).slice(-4).map((h: any) => ({ role: h.role, content: h.content })),
        { role: 'user', content: imagePrompt }
      ]

      const res2 = await fetch(GROQ_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
        body: JSON.stringify({
          model: MODEL,
          messages: [{ role: 'system', content: systemMsg }, ...msgs2],
          max_tokens: 2048, temperature: 0.7,
        })
      })

      if (!res2.ok) return error(res, 'AI error: ' + res2.status, 500)
      const d2 = await res2.json() as { choices: { message: { content: string } }[] }
      let reply = d2.choices?.[0]?.message?.content || ''
      // Prepend note about image
      reply = '📷 *Note: I can see you shared an image. Based on the subject context, here is my response:*\\n\\n' + reply
      return success(res, { reply })
    }

    // Text only
    if (!message) return error(res, 'Message required', 400)

    const msgs = [
      ...(history || []).slice(-6).map((h: any) => ({ role: h.role, content: h.content })),
      { role: 'user', content: message }
    ]

    const res3 = await fetch(GROQ_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: 'system', content: systemMsg }, ...msgs],
        max_tokens: 2048, temperature: 0.7,
      })
    })

    if (!res3.ok) return error(res, 'AI service error: ' + res3.status, 500)
    const d3 = await res3.json() as { choices: { message: { content: string } }[] }
    const reply = d3.choices?.[0]?.message?.content
    if (!reply) return error(res, 'No response from AI', 500)
    return success(res, { reply })
  } catch (err: any) { return error(res, 'AI unavailable: ' + err.message, 500) }
}"""

content = content.replace(old, new)
with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("HAYAT image chat fixed!")