# Run from BACKEND
with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: pdfParse import
content = content.replace(
    "const pdfParse = require('pdf-parse').default || require('pdf-parse')",
    "let pdfParse: any; try { pdfParse = require('pdf-parse'); if (pdfParse.default) pdfParse = pdfParse.default; } catch(e) { pdfParse = null; }"
)

# Fix 2: Use pdfParse safely
content = content.replace(
    "const d = await pdfParse(buffer)",
    "if (!pdfParse) { console.log('pdf-parse not available'); return '' }\n      const d = await pdfParse(buffer)"
)

# Fix 3: Groq 429 - add retry with delay
old_groq = """  const res = await fetch(GROQ_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'system', content: system }, { role: 'user', content: user }],
      max_tokens: maxTokens,
      temperature: 0.7,
    })
  })
  if (!res.ok) throw new Error('Groq error: ' + res.status)"""

new_groq = """  // Retry logic for rate limits
  let res: any
  for (let attempt = 0; attempt < 3; attempt++) {
    res = await fetch(GROQ_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: 'system', content: system }, { role: 'user', content: user }],
        max_tokens: maxTokens,
        temperature: 0.7,
      })
    })
    if (res.status === 429) {
      console.log('Rate limited, waiting 10s... attempt', attempt + 1)
      await new Promise(r => setTimeout(r, 10000))
      continue
    }
    break
  }
  if (!res.ok) throw new Error('Groq error: ' + res.status)"""

content = content.replace(old_groq, new_groq)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("Backend fixes done!")