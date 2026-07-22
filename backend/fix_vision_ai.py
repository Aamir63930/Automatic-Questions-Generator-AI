# BACKEND - Fix HAYAT to use vision-capable model
with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Use llama-3.2-11b-vision-preview for image support
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

    const VISION_MODEL = 'llama-3.2-11b-vision-preview'
    const TEXT_MODEL = MODEL

    let messages: any[]
    let modelToUse = TEXT_MODEL

    if (image) {
      // Use vision model with image
      modelToUse = VISION_MODEL
      messages = [
        {
          role: 'system',
          content: 'You are HAYAT, an expert AI tutor for ' + (subject || 'all subjects') +
            ' at K.R Mangalam University. Analyze the image carefully and provide detailed step-by-step solution.'
        },
        {
          role: 'user',
          content: [
            {
              type: 'image_url',
              image_url: { url: image }  // base64 data URL
            },
            {
              type: 'text',
              text: message || 'Please analyze this image and solve the problem shown. Provide detailed step-by-step solution.'
            }
          ]
        }
      ]
    } else {
      // Text only
      const histMsgs = (history || []).slice(-6).map((h: any) => ({ role: h.role, content: h.content }))
      messages = [
        {
          role: 'system',
          content: 'You are HAYAT, an expert AI tutor for ' + (subject || 'all subjects') +
            ' at K.R Mangalam University. Be helpful, clear and educational.'
        },
        ...histMsgs,
        { role: 'user', content: message }
      ]
    }

    const res2 = await fetch(GROQ_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
      body: JSON.stringify({
        model: modelToUse,
        messages,
        max_tokens: 2048,
        temperature: 0.7,
      })
    })

    if (!res2.ok) {
      const errText = await res2.text()
      console.error('AI error:', res2.status, errText)
      return error(res, 'AI service error: ' + res2.status, 500)
    }

    const d = await res2.json() as { choices: { message: { content: string } }[] }
    const reply = d.choices?.[0]?.message?.content
    if (!reply) return error(res, 'No response from AI', 500)
    return success(res, { reply })
  } catch (err: any) {
    console.error('aiChat error:', err)
    return error(res, 'AI unavailable: ' + err.message, 500)
  }
}"""

content = content.replace(old, new)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("Vision AI fixed!")