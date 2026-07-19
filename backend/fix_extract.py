# Read current file, find function start and end, replace it
with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Find the function and replace it
start = content.find("async function extractPdfText")
end = content.find("\nexport const getMaterialUnits")

if start == -1 or end == -1:
    print("Could not find function boundaries")
    print("Start:", start, "End:", end)
else:
    new_func = '''async function extractPdfText(url: string): Promise<string> {
  try {
    const pdfParse = require('pdf-parse')
    const mammoth = require('mammoth')
    const https = require('https')
    const http = require('http')

    let buffer: Buffer

    if (url.includes('cloudinary.com')) {
      const cloudName = process.env.CLOUDINARY_CLOUD_NAME || ''
      const apiKey = process.env.CLOUDINARY_API_KEY || ''
      const apiSecret = process.env.CLOUDINARY_API_SECRET || ''
      const crypto = require('crypto')

      // Extract public_id
      let publicId = ''
      const rawMatch = url.split('/raw/upload/').pop() || ''
      const imgMatch = url.split('/image/upload/').pop() || ''
      const raw = rawMatch || imgMatch
      // Remove version prefix v1234567/
      publicId = raw.replace(/^v[0-9]+\\//, '')
      console.log('Public ID:', publicId)

      // Generate signed download URL
      const timestamp = Math.floor(Date.now() / 1000)
      const str = 'public_id=' + publicId + '&timestamp=' + timestamp + apiSecret
      const sig = crypto.createHash('sha256').update(str).digest('hex')

      const downloadUrl = 'https://api.cloudinary.com/v1_1/' + cloudName +
        '/raw/download?public_id=' + encodeURIComponent(publicId) +
        '&api_key=' + apiKey + '&timestamp=' + timestamp + '&signature=' + sig

      console.log('Auth URL base:', downloadUrl.split('?')[0])

      buffer = await new Promise((resolve, reject) => {
        const chunks: Buffer[] = []
        https.get(downloadUrl, (res: any) => {
          console.log('Status:', res.statusCode)
          if (res.statusCode !== 200) {
            let body = ''
            res.on('data', (d: any) => body += d)
            res.on('end', () => {
              console.log('Error body:', body.slice(0, 200))
              reject(new Error('HTTP ' + res.statusCode))
            })
            return
          }
          res.on('data', (c: Buffer) => chunks.push(c))
          res.on('end', () => resolve(Buffer.concat(chunks)))
        }).on('error', (e: any) => {
          console.log('Request error:', e.message)
          reject(e)
        }).setTimeout(20000, function(this: any) {
          this.destroy()
          reject(new Error('Timeout'))
        })
      })

    } else if (url.startsWith('http')) {
      buffer = await new Promise((resolve, reject) => {
        const proto = url.startsWith('https') ? https : http
        const chunks: Buffer[] = []
        proto.get(url, (res: any) => {
          res.on('data', (c: Buffer) => chunks.push(c))
          res.on('end', () => resolve(Buffer.concat(chunks)))
        }).on('error', reject)
      })
    } else {
      const fs = require('fs')
      const path = require('path')
      const fp = path.join(process.cwd(), url)
      if (!require('fs').existsSync(fp)) return ''
      buffer = require('fs').readFileSync(fp)
    }

    console.log('Buffer size:', buffer.length)
    if (buffer.length === 0) return ''

    if (url.toLowerCase().includes('.docx')) {
      const r = await mammoth.extractRawText({ buffer })
      console.log('DOCX text length:', r.value?.length || 0)
      return (r.value || '').slice(0, 4000)
    } else {
      const d = await pdfParse(buffer)
      console.log('PDF text length:', d.text?.length || 0)
      return (d.text || '').slice(0, 4000)
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
    print("Function replaced successfully!")
    print("Function starts at:", start)
    print("Function ends at:", end)