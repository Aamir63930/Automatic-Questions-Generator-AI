import { Router } from 'express'
import { azureLogin, getMe, getUsers, updateSubjects, getClasses, createClass, deleteClass, joinClassByCode, selectClass, assignClass } from '../controllers/auth.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'

const router = Router()

router.post('/azure', azureLogin)
router.get('/me', authenticate, getMe)
router.get('/users', authenticate, getUsers)
router.patch('/subjects', authenticate, updateSubjects)
router.get('/classes', authenticate, getClasses)
router.post('/classes', authenticate, authorize('teacher', 'admin'), createClass)
router.delete('/classes/:id', authenticate, authorize('teacher', 'admin'), deleteClass)
router.post('/join-class', authenticate, authorize('student'), joinClassByCode)
router.patch('/select-class', authenticate, selectClass)
router.patch('/assign-class', authenticate, authorize('teacher', 'admin'), assignClass)

// ONE TIME FIX - fixes cloudinary URLs
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

export default router
