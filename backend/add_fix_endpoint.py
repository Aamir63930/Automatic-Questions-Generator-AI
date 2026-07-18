with open("src/routes/auth.routes.ts", "r", encoding="utf-8") as f:
    routes = f.read()

# Add one-time fix endpoint
if "fix-cloudinary" not in routes:
    routes = routes.replace(
        "export default router",
        """// ONE TIME FIX - fixes cloudinary URLs
router.get('/fix-cloudinary', async (req: any, res: any) => {
  try {
    const materials = await prisma.findMany ? [] : []
    const { PrismaClient } = require('@prisma/client')
    const p = new PrismaClient()
    const mats = await p.material.findMany({ select: { id: true, fileUrl: true, fileName: true } })
    let fixed = 0
    for (const m of mats) {
      if (m.fileUrl?.includes('/image/upload/')) {
        const ext = (m.fileName || '').split('.').pop()?.toLowerCase()
        if (['pdf','doc','docx','ppt','pptx','txt'].includes(ext || '')) {
          const newUrl = m.fileUrl.replace('/image/upload/', '/raw/upload/')
          await p.material.update({ where: { id: m.id }, data: { fileUrl: newUrl } })
          fixed++
        }
      }
    }
    return res.json({ success: true, fixed, total: mats.length })
  } catch(e: any) { return res.json({ error: e.message }) }
})

export default router"""
    )
    with open("src/routes/auth.routes.ts", "w", encoding="utf-8") as f:
        f.write(routes)
    print("Fix endpoint added!")