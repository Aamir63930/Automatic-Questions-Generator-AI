with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Remove complex signed URL logic - just use direct URL now
old = """      // Generate signed URL for authenticated access
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

new = """      // Direct download - URL is now /raw/upload/ which is publicly accessible
      console.log('Downloading from:', downloadUrl)
      let response: any
      try {
        response = await axios.get(downloadUrl, { 
          responseType: 'arraybuffer',
          timeout: 25000,
          headers: { 'Accept': '*/*' }
        })
        console.log('Download success! Size:', response.data.byteLength, 'bytes')
      } catch (err1: any) {
        console.log('Download failed:', err1.message, 'Status:', err1.response?.status)
        return ''
      }"""

content = content.replace(old, new)

# Also simplify the URL fixing logic
old2 = """      // Try raw URL first, then image URL
      let downloadUrl = url
      if (url.includes('cloudinary.com')) {
        // Always try raw/upload for non-image files
        downloadUrl = url.includes('/image/upload/') 
          ? url.replace('/image/upload/', '/raw/upload/')
          : url
        console.log('Trying URL:', downloadUrl)
      }"""

new2 = """      // Use URL directly - already fixed to /raw/upload/ in DB
      let downloadUrl = url
      // Safety: fix image/upload to raw/upload if somehow old URL
      if (url.includes('cloudinary.com') && url.includes('/image/upload/')) {
        downloadUrl = url.replace('/image/upload/', '/raw/upload/')
      }
      console.log('Extracting from:', downloadUrl)"""

content = content.replace(old2, new2)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("AI extraction simplified!")