import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createComplaint = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId, role } = (req as any).user
    const { subject, category, description, targetRole } = req.body

    const user = await prisma.user.findUnique({ where: { id: userId }, select: { name: true, role: true } })

    const complaint = await prisma.complaint.create({
      data: {
        raisedBy: userId, subject,
        category: category || 'General',
        messages: {
          create: { sentBy: userId, senderName: user?.name || 'User', senderRole: user?.role || role, message: description }
        }
      },
      include: { raiser: { select: { name: true, email: true } }, messages: true }
    })

    // Notify relevant users
    // Students notify teachers; teachers notify admins or other teachers
    const notifyFilter: any = { collegeId, isActive: true }
    if (role === 'student') {
      notifyFilter.role = 'teacher'
    } else {
      // Teacher complaint - notify all teachers
      notifyFilter.role = 'teacher'
    }

    const toNotify = await prisma.user.findMany({ where: notifyFilter, select: { id: true } })
    const filtered = toNotify.filter(u => u.id !== userId) // don't notify self

    if (filtered.length > 0) {
      await prisma.notification.createMany({
        data: filtered.map(u => ({
          userId: u.id,
          title: 'New Complaint from ' + (user?.name || 'User'),
          body: subject + ' — ' + (category || 'General'),
          type: 'complaint', refId: complaint.id,
        }))
      })
    }

    return success(res, complaint, 'Complaint raised', 201)
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const getComplaints = async (req: Request, res: Response) => {
  try {
    const { userId, role } = (req as any).user
    const complaints = await prisma.complaint.findMany({
      where: role === 'student' ? { raisedBy: userId } : {},
      include: {
        raiser: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } },
        messages: { orderBy: { createdAt: 'asc' } }
      },
      orderBy: { createdAt: 'desc' }
    })
    return success(res, complaints)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const replyComplaint = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    const { message } = req.body
    const sender = await prisma.user.findUnique({ where: { id: userId }, select: { name: true, role: true } })

    const msg = await prisma.complaintMessage.create({
      data: { complaintId: id, sentBy: userId, senderName: sender?.name || 'User', senderRole: sender?.role || 'student', message }
    })

    await prisma.complaint.update({ where: { id }, data: { status: 'in_progress' as any, updatedAt: new Date() } })

    const complaint = await prisma.complaint.findUnique({ where: { id } })
    if (complaint && sender?.role === 'teacher') {
      await prisma.notification.create({
        data: { userId: complaint.raisedBy, title: 'Reply from Teacher', body: message.slice(0, 80), type: 'complaint', refId: id }
      })
    } else if (complaint && sender?.role === 'student') {
      // Find teachers to notify
      const teachers = await prisma.user.findMany({ where: { role: 'teacher', isActive: true }, select: { id: true }, take: 3 })
      if (teachers.length > 0) {
        await prisma.notification.createMany({
          data: teachers.map(t => ({ userId: t.id, title: 'New Reply on Complaint', body: message.slice(0, 80), type: 'complaint', refId: id }))
        })
      }
    }

    return success(res, msg, 'Reply sent')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const updateComplaintStatus = async (req: Request, res: Response) => {
  try {
    const id = req.params.id as string
    const { status } = req.body
    const complaint = await prisma.complaint.update({
      where: { id },
      data: { status: status as any, ...(status === 'resolved' && { resolvedAt: new Date() }) }
    })
    await prisma.notification.create({
      data: { userId: complaint.raisedBy, title: 'Complaint ' + status.replace('_', ' '), body: '"' + complaint.subject + '" is now ' + status.replace('_', ' '), type: 'complaint', refId: id }
    })
    return success(res, complaint, 'Updated')
  } catch (err) { return error(res, 'Failed', 500) }
}
