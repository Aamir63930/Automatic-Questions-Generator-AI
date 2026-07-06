import { Router } from 'express'
import { authenticate } from '../middleware/auth.middleware'
import prisma from '../config/db'

const router = Router()

router.post('/', authenticate, async (req: any, res: any) => {
  try {
    const { userId, collegeId } = req.user
    const { title, subject, examType, totalMarks, duration, questions } = req.body
    const paper = await prisma.paper.create({
      data: { collegeId, createdBy: userId, title, subject, examType: examType || 'end_term', totalMarks, duration: duration || 180, questions: questions || [] }
    })
    return res.json({ success: true, data: paper })
  } catch (e: any) { return res.status(500).json({ success: false, message: e.message }) }
})

router.get('/', authenticate, async (req: any, res: any) => {
  try {
    const { collegeId } = req.user
    const papers = await prisma.paper.findMany({ where: { collegeId }, orderBy: { createdAt: 'desc' } })
    return res.json({ success: true, data: papers })
  } catch (e: any) { return res.status(500).json({ success: false, message: e.message }) }
})

router.get('/:id', authenticate, async (req: any, res: any) => {
  try {
    const paper = await prisma.paper.findUnique({ where: { id: req.params.id } })
    return res.json({ success: true, data: paper })
  } catch (e: any) { return res.status(500).json({ success: false, message: e.message }) }
})

export default router
