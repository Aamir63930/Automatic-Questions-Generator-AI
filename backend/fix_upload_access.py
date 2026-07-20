with open("src/controllers/material.controller.ts", "r", encoding="utf-8") as f:
    c = f.read()

old = """async function uploadToCloudinary(filePath: string, fileName: string): Promise<string> {
  const ext = require('path').extname(fileName).toLowerCase()
  // PDFs and docs must be uploaded as 'raw', images as 'image'
  const imageExts = ['.jpg','.jpeg','.png','.gif','.webp']
  const resourceType = imageExts.includes(ext) ? 'image' : 'raw'
  
  const result = await cloudinary.uploader.upload(filePath, {
    folder: 'aiqpg/materials',
    resource_type: resourceType,
    type: 'upload',  // public access
    public_id: Date.now() + '_' + fileName.replace(/[^a-zA-Z0-9._-]/g, '_'),
    use_filename: false,
    access_mode: 'public',  // ensure public access
  })
  return result.secure_url
}"""

new = """async function uploadToCloudinary(filePath: string, fileName: string): Promise<string> {
  const ext = require('path').extname(fileName).toLowerCase()
  const imageExts = ['.jpg','.jpeg','.png','.gif','.webp']
  const resourceType = imageExts.includes(ext) ? 'image' : 'raw'
  
  const result = await cloudinary.uploader.upload(filePath, {
    folder: 'aiqpg/materials',
    resource_type: resourceType,
    type: 'upload',
    access_mode: 'public',
    public_id: Date.now() + '_' + fileName.replace(/[^a-zA-Z0-9._-]/g, '_'),
    invalidate: true,
  })
  
  console.log('Cloudinary upload result:', {
    url: result.secure_url,
    resource_type: result.resource_type,
    type: result.type,
    access_mode: result.access_mode
  })
  
  return result.secure_url
}"""

c = c.replace(old, new)
with open("src/controllers/material.controller.ts", "w", encoding="utf-8") as f:
    f.write(c)
print("Upload fixed!")