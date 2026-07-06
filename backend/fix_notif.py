with open("src/controllers/notification.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const getNotifications = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const notifications = await prisma.notification.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
      take: 50
    })
    return success(res, notifications)
  } catch (err) {
    return error(res, 'Failed to get notifications', 500)
  }
}

export const markRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    await prisma.notification.updateMany({
      where: { id, userId },
      data: { isRead: true }
    })
    return success(res, null, 'Marked as read')
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}

export const markAllRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.updateMany({
      where: { userId, isRead: false },
      data: { isRead: true }
    })
    return success(res, null, 'All marked as read')
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}

export const sendBulkNotification = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { title, body, type } = req.body
    const students = await prisma.user.findMany({
      where: { collegeId, role: 'student', isActive: true },
      select: { id: true }
    })
    await prisma.notification.createMany({
      data: students.map(s => ({
        userId: s.id,
        title,
        body,
        type: type || 'announcement'
      }))
    })
    return success(res, { sent: students.length }, 'Sent to ' + students.length + ' students')
  } catch (err) {
    return error(res, 'Failed to send', 500)
  }
}
""")
print("Done!")