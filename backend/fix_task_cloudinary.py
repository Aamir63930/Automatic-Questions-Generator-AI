with open("src/controllers/task.controller.ts", "r", encoding="utf-8") as f:
    c = f.read()

# Add Cloudinary upload for task attachment
old = """        attachmentUrl: req.file ? '/uploads/' + collegeId + '/' + req.file.filename : null,"""

new = """        attachmentUrl: await (async () => {
          if (!req.file) return null
          try {
            const cloudinary = require('../config/cloudinary').default
            const ext = require('path').extname(req.file.originalname).toLowerCase()
            const imageExts = ['.jpg','.jpeg','.png','.gif','.webp']
            const resourceType = imageExts.includes(ext) ? 'image' : 'raw'
            const result = await cloudinary.uploader.upload(req.file.path, {
              folder: 'aiqpg/tasks',
              resource_type: resourceType,
              type: 'upload',
              access_mode: 'public',
            })
            const fs = require('fs')
            if (fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path)
            return result.secure_url
          } catch(e) {
            console.error('Task attachment upload error:', e)
            return '/uploads/' + collegeId + '/' + req.file.filename
          }
        })(),"""

if old in c:
    c = c.replace(old, new)
    with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
        f.write(c)
    print("Task controller - Cloudinary upload added!")
else:
    print("Pattern not found in task controller")