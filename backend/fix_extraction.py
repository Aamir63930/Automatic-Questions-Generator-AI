with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

old = """      // Fix Cloudinary URL - change image/upload to raw/upload for PDFs
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
      })"""

new = """      // Try raw URL first, then image URL
      let downloadUrl = url
      if (url.includes('cloudinary.com')) {
        // Always try raw/upload for non-image files
        downloadUrl = url.includes('/image/upload/') 
          ? url.replace('/image/upload/', '/raw/upload/')
          : url
        console.log('Trying URL:', downloadUrl)
      }
      
      let response: any
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

content = content.replace(old, new)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("AI extraction fixed!")