import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

async function getMainCollegeId(): Promise<string> {
  const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
  return college?.id || ''
}

export const getNotifications = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const notifications = await prisma.notification.findMany({
      where: { userId }, orderBy: { createdAt: 'desc' }, take: 50
    })
    return success(res, notifications)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const markRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.updateMany({ where: { id: req.params.id as string, userId }, data: { isRead: true } })
    return success(res, null)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const markAllRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.updateMany({ where: { userId, isRead: false }, data: { isRead: true } })
    return success(res, null)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const deleteNotification = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.deleteMany({ where: { id: req.params.id as string, userId } })
    return success(res, null)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const sendBulkNotification = async (req: Request, res: Response) => {
  try {
    const { title, body, type, target, classIds } = req.body
    const collegeId = await getMainCollegeId()

    let userFilter: any = { collegeId, isActive: true }
    if (target === 'all_students') {
      userFilter.role = 'student'
    } else if (target === 'specific_classes' && classIds?.length > 0) {
      userFilter.role = 'student'
      userFilter.classSectionId = { in: classIds }
    } else if (target === 'teachers') {
      userFilter.role = 'teacher'
    } else if (target === 'no_submission' && classIds?.length > 0) {
      // Send to students who haven't submitted a specific task
      userFilter.role = 'student'
      userFilter.classSectionId = { in: classIds }
    }

    const users = await prisma.user.findMany({ where: userFilter, select: { id: true, email: true, name: true } })

    if (users.length > 0) {
      await prisma.notification.createMany({
        data: users.map(u => ({ userId: u.id, title, body, type: type || 'announcement' }))
      })
    }

    return success(res, { sent: users.length, recipients: users.map(u => ({ name: u.name, email: u.email })) }, 'Sent to ' + users.length + ' users')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

// Student alerts teacher that no data in class
export const studentAlertTeacher = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { classSectionId, message } = req.body

    const student = await prisma.user.findUnique({ where: { id: userId }, select: { name: true, email: true } })
    const cls = await prisma.classSection.findUnique({ where: { id: classSectionId }, select: { name: true, section: true } })
    const collegeId = await getMainCollegeId()

    // Notify all teachers
    const teachers = await prisma.user.findMany({ where: { collegeId, role: 'teacher', isActive: true }, select: { id: true } })

    if (teachers.length > 0) {
      await prisma.notification.createMany({
        data: teachers.map(t => ({
          userId: t.id,
          title: '📢 Student Alert from ' + (student?.name || 'Student'),
          body: 'Class: ' + (cls?.name || '') + ' ' + (cls?.section || '') + ' — ' + (message || 'Please upload study materials for our class!'),
          type: 'complaint',
        }))
      })
    }

    return success(res, null, 'Alert sent to teachers!')
  } catch (err: any) { return error(res, err.message, 500) }
}

export const getUnreadCount = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const count = await prisma.notification.count({
      where: { userId, isRead: false }
    })
    return success(res, { count })
  } catch (err) { return error(res, 'Failed', 500) }
}
