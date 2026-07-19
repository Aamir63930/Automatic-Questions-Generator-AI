with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Replace extractPdfText function completely
import re

new_extract = '''async function extractPdfText(url: string): Promise<string> {
  try {
    const pdfParse = require('pdf-parse')
    const mammoth = require('mammoth')
    const https = require('https')
    const http = require('http')

    let buffer: Buffer

    if (url.includes('cloudinary.com')) {
      // Use Cloudinary Admin API to download with auth
      const cloudName = process.env.CLOUDINARY_CLOUD_NAME || ''
      const apiKey = process.env.CLOUDINARY_API_KEY || ''
      const apiSecret = process.env.CLOUDINARY_API_SECRET || ''

      // Extract public_id from URL
      const match = url.match(/\\/raw\\/upload\\/(?:v\\d+\\/)?(.+)$/) ||
                    url.match(/\\/image\\/upload\\/(?:v\\d+\\/)?(.+)$/)
      if (!match) {
        console.log('Cannot extract public_id from:', url)
        return ''
      }
      const publicId = match[1]
      console.log('Public ID:', publicId)

      // Generate signed URL using Cloudinary
      const crypto = require('crypto')
      const timestamp = Math.floor(Date.now() / 1000)
      const toSign = 'public_id=' + publicId + '&timestamp=' + timestamp + apiSecret
      const signature = crypto.createHash('sha256').update(toSign).digest('hex')

      // Use delivery URL with auth
      const authUrl = 'https://api.cloudinary.com/v1_1/' + cloudName + '/raw/download?public_id=' +
        encodeURIComponent(publicId) + '&api_key=' + apiKey +
        '&timestamp=' + timestamp + '&signature=' + signature

      console.log('Downloading with auth:', authUrl.split('?')[0])

      buffer = await new Promise((resolve, reject) => {
        const protocol = authUrl.startsWith('https') ? https : http
        const chunks: Buffer[] = []
        const req = protocol.get(authUrl, (res: any) => {
          console.log('Auth download status:', res.statusCode)
          if (res.statusCode !== 200) {
            reject(new Error('Status: ' + res.statusCode))
            return
          }
          res.on('data', (chunk: Buffer) => chunks.push(chunk))
          res.on('end', () => resolve(Buffer.concat(chunks)))
        })
        req.on('error', reject)
        req.setTimeout(20000, () => { req.destroy(); reject(new Error('Timeout')) })
      })

    } else if (url.startsWith('http')) {
      const https = require('https')
      const http = require('http')
      buffer = await new Promise((resolve, reject) => {
        const protocol = url.startsWith('https') ? https : http
        const chunks: Buffer[] = []
        protocol.get(url, (res: any) => {
          res.on('data', (chunk: Buffer) => chunks.push(chunk))
          res.on('end', () => resolve(Buffer.concat(chunks)))
        }).on('error', reject)
      })
    } else {
      const fs = require('fs')
      const path = require('path')
      const filePath = path.join(process.cwd(), url)
      if (!fs.existsSync(filePath)) return ''
      buffer = fs.readFileSync(filePath)
    }

    console.log('Downloaded buffer size:', buffer.length)
    if (buffer.length === 0) return ''

    const urlLower = url.toLowerCase()
    if (urlLower.includes('.docx')) {
      const result = await mammoth.extractRawText({ buffer })
      const text = result.value?.trim() || ''
      console.log('Extracted DOCX text length:', text.length)
      return text.slice(0, 4000)
    } else {
      const data = await pdfParse(buffer)
      const text = data.text?.trim() || ''
      console.log('Extracted PDF text length:', text.length)
      return text.slice(0, 4000)
    }

  } catch (e: any) {
    console.log('PDF extract error:', e.message)
    return ''
  }
}'''

# Replace the entire extractPdfText function
content = re.sub(
    r'async function extractPdfText\(url: string\): Promise<string> \{.*?^}',
    new_extract,
    content,
    flags=re.DOTALL | re.MULTILINE
)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("Done!")