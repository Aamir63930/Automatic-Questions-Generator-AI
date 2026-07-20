with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

start = content.find("async function extractPdfText")
end = content.find("\nexport const getMaterialUnits")

new_func = '''async function extractPdfText(url: string): Promise<string> {
  try {
    if (!url) return ''
    console.log('Extracting from:', url.slice(0, 80))

    const pdfParse = require('pdf-parse')
    const mammoth = require('mammoth')

    let buffer: Buffer | null = null

    if (url.startsWith('http')) {
      // For Cloudinary - try multiple approaches
      const urlsToTry: string[] = [url]

      // If raw/upload URL - also try image/upload as fallback
      if (url.includes('/raw/upload/')) {
        urlsToTry.push(url.replace('/raw/upload/', '/image/upload/'))
      }
      // If image/upload - also try raw/upload
      if (url.includes('/image/upload/')) {
        urlsToTry.push(url.replace('/image/upload/', '/raw/upload/'))
      }

      for (const tryUrl of urlsToTry) {
        try {
          const response = await fetch(tryUrl, {
            headers: { 'Accept': '*/*' },
            signal: AbortSignal.timeout(15000)
          })
          console.log('Fetch status:', response.status, 'URL:', tryUrl.slice(0, 60))

          if (response.ok) {
            const arrayBuf = await response.arrayBuffer()
            buffer = Buffer.from(arrayBuf)
            console.log('Downloaded:', buffer.length, 'bytes')
            if (buffer.length > 100) break
          }
        } catch (fetchErr: any) {
          console.log('Fetch attempt failed:', fetchErr.message)
        }
      }
    } else {
      // Local file
      const fs = require('fs')
      const path = require('path')
      const fp = path.join(process.cwd(), url)
      if (fs.existsSync(fp)) {
        buffer = fs.readFileSync(fp)
      }
    }

    if (!buffer || buffer.length < 100) {
      console.log('Could not download file or file too small')
      return ''
    }

    const urlLower = url.toLowerCase()
    if (urlLower.includes('.docx')) {
      const r = await mammoth.extractRawText({ buffer })
      const text = (r.value || '').trim()
      console.log('DOCX text extracted:', text.length, 'chars')
      return text.slice(0, 4000)
    } else {
      const d = await pdfParse(buffer)
      const text = (d.text || '').trim()
      console.log('PDF text extracted:', text.length, 'chars')
      return text.slice(0, 4000)
    }

  } catch (e: any) {
    console.log('Extract error:', e.message)
    return ''
  }
}

'''

new_content = content[:start] + new_func + content[end:]
with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(new_content)
print("AI extraction fixed!")