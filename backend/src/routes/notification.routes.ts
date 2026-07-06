import { Router } from 'express'
import { getNotifications, markRead, markAllRead, deleteNotification, sendBulkNotification, studentAlertTeacher } from '../controllers/notification.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import prisma from '../config/db'

const router = Router()
router.get('/', authenticate, getNotifications)
router.patch('/read-all', authenticate, markAllRead)
router.patch('/:id/read', authenticate, markRead)
router.delete('/:id', authenticate, deleteNotification)
router.post('/send', authenticate, authorize('teacher','admin'), sendBulkNotification)
router.post('/student-alert', authenticate, authorize('student'), studentAlertTeacher)

// Direct notification to one user
router.post('/', authenticate, async (req: any, res: any) => {
  try {
    const { userId, title, body, type, refId } = req.body
    if (!userId || !title) return res.status(400).json({ success: false, message: 'userId and title required' })
    const notif = await prisma.notification.create({
      data: { userId, title, body: body || '', type: type || 'announcement', refId: refId || null }
    })
    return res.json({ success: true, data: notif })
  } catch (e: any) { return res.status(500).json({ success: false, message: e.message }) }
})

export default router
