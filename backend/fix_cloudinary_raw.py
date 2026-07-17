# Fix Cloudinary config - PDF ko raw type se upload karo
with open("src/config/cloudinary.ts", "w", encoding="utf-8") as f:
    f.write("""import { v2 as cloudinary } from 'cloudinary'

cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME || '',
  api_key: process.env.CLOUDINARY_API_KEY || '',
  api_secret: process.env.CLOUDINARY_API_SECRET || '',
})

export default cloudinary
""")

# Fix material controller - use raw upload + signed URL for download
with open("src/controllers/material.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Fix uploadToCloudinary function
old = """async function uploadToCloudinary(filePath: string, fileName: string): Promise<string> {
  const result = await cloudinary.uploader.upload(filePath, {
    folder: 'aiqpg/materials',
    resource_type: 'auto',
    public_id: Date.now() + '_' + fileName.replace(/[^a-zA-Z0-9]/g, '_'),
    use_filename: true,
  })
  return result.secure_url
}"""

new = """async function uploadToCloudinary(filePath: string, fileName: string): Promise<string> {
  const ext = require('path').extname(fileName).toLowerCase()
  // PDFs and docs must be uploaded as 'raw', images as 'image'
  const imageExts = ['.jpg','.jpeg','.png','.gif','.webp']
  const resourceType = imageExts.includes(ext) ? 'image' : 'raw'
  
  const result = await cloudinary.uploader.upload(filePath, {
    folder: 'aiqpg/materials',
    resource_type: resourceType,
    public_id: Date.now() + '_' + fileName.replace(/[^a-zA-Z0-9._-]/g, '_'),
    use_filename: false,
  })
  return result.secure_url
}"""

content = content.replace(old, new)

with open("src/controllers/material.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("Material controller fixed!")

# Fix AI controller - use Cloudinary SDK to download with auth
with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    ai = f.read()

old_extract = """async function extractPdfText(url: string): Promise<string> {
  try {
    const pdfParse = require('pdf-parse')
    const mammoth = require('mammoth')
    
    if (url.startsWith('http')) {
      // Download from Cloudinary
      const response = await axios.get(url, { 
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

new_extract = """async function extractPdfText(url: string): Promise<string> {
  try {
    const pdfParse = require('pdf-parse')
    const mammoth = require('mammoth')
    const cloudinary = require('../config/cloudinary').default
    
    if (url.startsWith('http')) {
      // Fix Cloudinary URL - change image/upload to raw/upload for PDFs
      let downloadUrl = url
      if (url.includes('cloudinary.com') && url.includes('/image/upload/')) {
        const urlLower = url.toLowerCase()
        if (urlLower.includes('.pdf') || urlLower.includes('.doc') || 
            urlLower.includes('.ppt') || urlLower.includes('.txt')) {
          downloadUrl = url.replace('/image/upload/', '/raw/upload/')
          console.log('Fixed Cloudinary URL:', downloadUrl)
        }
      }
      
      const response = await axios.get(downloadUrl, { 
        responseType: 'arraybuffer',
        timeout: 20000,
        headers: { 
          'User-Agent': 'Mozilla/5.0',
          'Accept': '*/*'
        }
      })
      const buffer = Buffer.from(response.data)
      
      const urlLower = url.toLowerCase()
      if (urlLower.includes('.docx') || urlLower.includes('docx')) {
        const result = await mammoth.extractRawText({ buffer })
        return result.value?.slice(0, 4000) || ''
      } else {
        const data = await pdfParse(buffer)
        return data.text?.slice(0, 4000) || ''
      }"""

ai = ai.replace(old_extract, new_extract)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(ai)
print("AI controller - Cloudinary URL fix done!")
print("Done!")