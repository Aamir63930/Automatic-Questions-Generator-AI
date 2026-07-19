with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Fix: Use Cloudinary SDK to get proper download URL
old = """async function extractPdfText(url: string): Promise<string> {
  try {
    const pdfParse = require('pdf-parse')
    const mammoth = require('mammoth')
    const cloudinary = require('../config/cloudinary').default"""

new = """async function extractPdfText(url: string): Promise<string> {
  try {
    const pdfParse = require('pdf-parse')
    const mammoth = require('mammoth')
    const cloudinaryV2 = require('cloudinary').v2
    cloudinaryV2.config({
      cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
      api_key: process.env.CLOUDINARY_API_KEY,
      api_secret: process.env.CLOUDINARY_API_SECRET,
    })"""

content = content.replace(old, new)

# Fix download logic - generate signed URL
old2 = """      let response: any
      try {
        response = await axios.get(downloadUrl, { 
          responseType: 'arraybuffer',
          timeout: 20000,
          headers: { 'Accept': '*/*' }
        })
      } catch (err1: any) {
        // Fallback: try original URL
        console.log('Raw URL failed, trying original:', url)
        response = await axios.get(url, { 
          responseType: 'arraybuffer',
          timeout: 20000,
          headers: { 'Accept': '*/*' }
        })
      }"""

new2 = """      // Generate signed URL for authenticated access
      let signedUrl = downloadUrl
      try {
        if (downloadUrl.includes('cloudinary.com')) {
          // Extract public_id from URL
          const urlParts = downloadUrl.split('/raw/upload/')
          if (urlParts.length > 1) {
            const publicIdWithVersion = urlParts[1]
            const publicId = publicIdWithVersion.replace(/^v\\d+\\//, '')
            signedUrl = cloudinaryV2.url(publicId, {
              resource_type: 'raw',
              sign_url: true,
              type: 'upload',
            })
            console.log('Generated signed URL:', signedUrl)
          }
        }
      } catch(signErr) {
        console.log('Signed URL generation failed, using direct:', signErr)
        signedUrl = downloadUrl
      }

      let response: any
      try {
        response = await axios.get(signedUrl, { 
          responseType: 'arraybuffer',
          timeout: 25000,
          headers: { 'Accept': '*/*' }
        })
        console.log('Download successful, size:', response.data.byteLength)
      } catch (err1: any) {
        console.log('Download failed:', err1.message)
        return ''
      }"""

content = content.replace(old2, new2)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("AI extraction with signed URL done!")