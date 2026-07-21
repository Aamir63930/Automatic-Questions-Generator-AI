with open("src/controllers/submission.controller.ts", "r", encoding="utf-8") as f:
    c = f.read()

old = """        fileUrl: file ? '/uploads/' + collegeId + '/' + file.filename : null,
        fileName: file?.originalname || null,"""

new = """        fileUrl: await (async () => {
          if (!file) return null
          try {
            const cloudinary = require('../config/cloudinary').default
            const ext = require('path').extname(file.originalname).toLowerCase()
            const imageExts = ['.jpg','.jpeg','.png','.gif','.webp']
            const resourceType = imageExts.includes(ext) ? 'image' : 'raw'
            const result = await cloudinary.uploader.upload(file.path, {
              folder: 'aiqpg/submissions',
              resource_type: resourceType,
              type: 'upload',
              access_mode: 'public',
            })
            const fs = require('fs')
            if (fs.existsSync(file.path)) fs.unlinkSync(file.path)
            return result.secure_url
          } catch(e) {
            console.error('Submission upload error:', e)
            return '/uploads/' + collegeId + '/' + file.filename
          }
        })(),
        fileName: file?.originalname || null,"""

if old in c:
    c = c.replace(old, new)
    with open("src/controllers/submission.controller.ts", "w", encoding="utf-8") as f:
        f.write(c)
    print("Submission controller - Cloudinary upload added!")
else:
    print("Pattern not found")