# BACKEND - Complete ai.controller.ts rewrite with proper pdf-parse
with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Find and fix extractPdfText function
start = content.find("async function extractPdfText")
end = content.find("\nexport const getMaterialUnits")

new_func = '''async function extractPdfText(url: string): Promise<string> {
  try {
    if (!url) return ''
    console.log('Extracting from:', url.slice(0, 80))

    // Import pdf-parse correctly
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const pdfParseModule = require('pdf-parse')
    const pdfParse = typeof pdfParseModule === 'function'
      ? pdfParseModule
      : (pdfParseModule.default || pdfParseModule)

    if (typeof pdfParse !== 'function') {
      console.log('pdf-parse not loaded correctly, type:', typeof pdfParse)
      return ''
    }

    let buffer: Buffer | null = null

    if (url.startsWith('http')) {
      try {
        const response = await fetch(url, {
          headers: { 'Accept': '*/*' },
          signal: AbortSignal.timeout(20000)
        })
        console.log('Fetch status:', response.status)
        if (response.ok) {
          const ab = await response.arrayBuffer()
          buffer = Buffer.from(ab)
          console.log('Downloaded:', buffer.length, 'bytes')
        }
      } catch (fe: any) {
        console.log('Fetch error:', fe.message)
      }
    } else {
      const fs = require('fs'), path = require('path')
      const fp = path.join(process.cwd(), url)
      if (fs.existsSync(fp)) buffer = fs.readFileSync(fp)
    }

    if (!buffer || buffer.length < 100) {
      console.log('No buffer or too small:', buffer?.length)
      return ''
    }

    const urlLower = url.toLowerCase()
    if (urlLower.includes('.docx')) {
      const mammoth = require('mammoth')
      const r = await mammoth.extractRawText({ buffer })
      const text = (r.value || '').trim()
      console.log('DOCX text:', text.length, 'chars')
      return text.slice(0, 4000)
    } else {
      // PDF parse with options to avoid issues
      const data = await pdfParse(buffer, {
        max: 0,  // parse all pages
      })
      const text = (data.text || '').trim()
      console.log('PDF text:', text.length, 'chars - SAMPLE:', text.slice(0, 100))
      return text.slice(0, 4000)
    }

  } catch (e: any) {
    console.log('Extract error:', e.message)
    return ''
  }
}

'''

if start != -1 and end != -1:
    new_content = content[:start] + new_func + content[end:]
    with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("extractPdfText fixed!")
else:
    print("ERROR: Could not find function boundaries")
    print("start:", start, "end:", end)