with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    c = f.read()

old = """async function extractPdfText(url: string): Promise<string> {
  try {
    const pdfParse = require('pdf-parse')"""

new = """async function extractPdfText(url: string): Promise<string> {
  try {
    const pdfParse = require('pdf-parse')
    const mammoth = require('mammoth')"""

c = c.replace(old, new)

# Add docx support
old2 = """    const response = await axios.get(url, { 
        responseType: 'arraybuffer',
        timeout: 15000,
        headers: { 'User-Agent': 'Mozilla/5.0' }
      })
      const buffer = Buffer.from(response.data)
      const data = await pdfParse(buffer)
      return data.text?.slice(0, 4000) || ''"""

new2 = """    const response = await axios.get(url, { 
        responseType: 'arraybuffer',
        timeout: 15000,
        headers: { 'User-Agent': 'Mozilla/5.0' }
      })
      const buffer = Buffer.from(response.data)
      
      // Check if docx or pdf
      const urlLower = url.toLowerCase()
      if (urlLower.includes('.docx') || urlLower.includes('docx') || urlLower.includes('officedocument')) {
        const result = await mammoth.extractRawText({ buffer })
        return result.value?.slice(0, 4000) || ''
      } else {
        const data = await pdfParse(buffer)
        return data.text?.slice(0, 4000) || ''
      }"""

c = c.replace(old2, new2)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(c)
print("DOCX support added!")