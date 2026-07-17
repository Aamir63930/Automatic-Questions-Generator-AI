# In Cloudinary, raw files URL is different
# Fix view/download redirect to use raw URL

with open("src/controllers/material.controller.ts", "r", encoding="utf-8") as f:
    c = f.read()

# Fix previewMaterial to fix URL
old = """    // Cloudinary URL - redirect directly (opens in browser)
    if (material.fileUrl.startsWith('http')) {
      res.setHeader('Access-Control-Allow-Origin', '*')
      return res.redirect(material.fileUrl)
    }"""

new = """    // Cloudinary URL - fix raw URL for PDF
    if (material.fileUrl.startsWith('http')) {
      let viewUrl = material.fileUrl
      // Fix: PDF/doc files need /raw/upload/ not /image/upload/
      if (viewUrl.includes('cloudinary.com') && viewUrl.includes('/image/upload/')) {
        const ext = require('path').extname(material.fileName).toLowerCase()
        const imageExts = ['.jpg','.jpeg','.png','.gif','.webp']
        if (!imageExts.includes(ext)) {
          viewUrl = viewUrl.replace('/image/upload/', '/raw/upload/')
        }
      }
      res.setHeader('Access-Control-Allow-Origin', '*')
      return res.redirect(viewUrl)
    }"""

c = c.replace(old, new)

# Fix downloadMaterial too
old2 = """    // Cloudinary URL - redirect directly
    if (material.fileUrl.startsWith('http')) {
      return res.redirect(material.fileUrl)
    }"""

new2 = """    // Cloudinary URL - redirect
    if (material.fileUrl.startsWith('http')) {
      let downloadUrl = material.fileUrl
      if (downloadUrl.includes('cloudinary.com') && downloadUrl.includes('/image/upload/')) {
        const ext = require('path').extname(material.fileName).toLowerCase()
        const imageExts = ['.jpg','.jpeg','.png','.gif','.webp']
        if (!imageExts.includes(ext)) {
          downloadUrl = downloadUrl.replace('/image/upload/', '/raw/upload/')
        }
      }
      return res.redirect(downloadUrl)
    }"""

c = c.replace(old2, new2)

with open("src/controllers/material.controller.ts", "w", encoding="utf-8") as f:
    f.write(c)
print("View/Download URL fixed!")