with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

start = content.find("async function extractPdfText")
end = content.find("\nexport const getMaterialUnits")

new_func = '''async function extractPdfText(url: string): Promise<string> {
  try {
    const pdfParse = require('pdf-parse')
    const mammoth = require('mammoth')
    const https = require('https')
    const http = require('http')

    if (!url || url.length === 0) return ''
    console.log('Extracting from URL:', url)

    let buffer: Buffer

    if (url.startsWith('http')) {
      // Direct download - works for public Cloudinary files
      buffer = await new Promise((resolve, reject) => {
        const proto = url.startsWith('https') ? https : http
        const chunks: Buffer[] = []
        let redirectCount = 0

        const doRequest = (reqUrl: string) => {
          proto.get(reqUrl, { timeout: 20000 }, (res: any) => {
            console.log('HTTP status:', res.statusCode, 'for:', reqUrl)

            // Handle redirect
            if ((res.statusCode === 301 || res.statusCode === 302) && res.headers.location && redirectCount < 3) {
              redirectCount++
              doRequest(res.headers.location)
              return
            }

            if (res.statusCode !== 200) {
              res.resume()
              resolve(Buffer.alloc(0))
              return
            }

            res.on('data', (c: Buffer) => chunks.push(c))
            res.on('end', () => resolve(Buffer.concat(chunks)))
          }).on('error', (e: any) => {
            console.log('Request error:', e.message)
            resolve(Buffer.alloc(0))
          })
        }

        doRequest(url)
      })
    } else {
      const fs = require('fs')
      const path = require('path')
      const fp = path.join(process.cwd(), url)
      if (!require('fs').existsSync(fp)) return ''
      buffer = require('fs').readFileSync(fp)
    }

    console.log('Buffer size:', buffer.length)
    if (buffer.length < 100) {
      console.log('File too small or empty - skipping extraction')
      return ''
    }

    const urlLower = url.toLowerCase()
    try {
      if (urlLower.includes('.docx')) {
        const r = await mammoth.extractRawText({ buffer })
        const text = (r.value || '').trim()
        console.log('DOCX extracted:', text.length, 'chars')
        return text.slice(0, 4000)
      } else {
        const d = await pdfParse(buffer)
        const text = (d.text || '').trim()
        console.log('PDF extracted:', text.length, 'chars')
        return text.slice(0, 4000)
      }
    } catch (parseErr: any) {
      console.log('Parse error:', parseErr.message)
      return ''
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
print("extractPdfText replaced with simple direct download!")