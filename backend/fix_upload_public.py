with open("src/controllers/material.controller.ts", "r", encoding="utf-8") as f:
    c = f.read()

# Fix upload to use 'upload' type (public) not authenticated
old = """  const result = await cloudinary.uploader.upload(filePath, {
    folder: 'aiqpg/materials',
    resource_type: resourceType,
    public_id: Date.now() + '_' + fileName.replace(/[^a-zA-Z0-9._-]/g, '_'),
    use_filename: false,
  })"""

new = """  const result = await cloudinary.uploader.upload(filePath, {
    folder: 'aiqpg/materials',
    resource_type: resourceType,
    type: 'upload',  // public access
    public_id: Date.now() + '_' + fileName.replace(/[^a-zA-Z0-9._-]/g, '_'),
    use_filename: false,
    access_mode: 'public',  // ensure public access
  })"""

c = c.replace(old, new)

with open("src/controllers/material.controller.ts", "w", encoding="utf-8") as f:
    f.write(c)
print("Upload type fixed to public!")