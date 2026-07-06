import { Router } from 'express'
import { uploadMaterial, getMaterials, downloadMaterial, previewMaterial, deleteMaterial } from '../controllers/material.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'
import path from 'path'
import fs from 'fs'
import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()

const router = Router()
router.post('/upload', authenticate, authorize('teacher','admin'), upload.single('file'), uploadMaterial)
router.get('/', authenticate, getMaterials)
router.get('/:id/download', authenticate, downloadMaterial)
router.get('/:id/preview', authenticate, previewMaterial)
router.delete('/:id', authenticate, authorize('teacher','admin'), deleteMaterial)

// Public inline view - no auth - opens PDF directly in browser
router.get('/:id/view', async (req: any, res: any) => {
  try {
    const material = await prisma.material.findUnique({ where: { id: req.params.id } })
    if (!material) return res.status(404).send('File not found')
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return res.status(404).send('File not on server')
    const ext = path.extname(material.fileName).toLowerCase()
    const mimes: Record<string,string> = { '.pdf':'application/pdf', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.txt':'text/plain' }
    res.setHeader('Content-Type', mimes[ext] || 'application/pdf')
    res.setHeader('Content-Disposition', 'inline; filename="' + material.fileName + '"')
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('X-Frame-Options', 'SAMEORIGIN')
    return res.sendFile(path.resolve(filePath))
  } catch (e: any) { return res.status(500).send(e.message) }
})

export default router
