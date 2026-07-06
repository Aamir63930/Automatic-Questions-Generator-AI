# Fix task + material controllers
with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createTask = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { title, description, taskType, subjectName, classSectionId, deadline, maxMarks, instructions, allowLate, latePenalty } = req.body

    const task = await prisma.task.create({
      data: {
        collegeId, createdBy: userId, title,
        description: description || null,
        taskType: taskType as any,
        subjectName: subjectName || null,
        classSectionId: classSectionId || null,
        deadline: deadline ? new Date(deadline) : null,
        maxMarks: parseInt(maxMarks) || 10,
        instructions: instructions || null,
        allowLate: allowLate === 'true' || allowLate === true,
        latePenalty: parseInt(latePenalty) || 0,
        attachmentUrl: req.file ? '/uploads/' + collegeId + '/' + req.file.filename : null,
      },
      include: {
        creator: { select: { name: true } },
        classSection: { select: { name: true, section: true, branch: true } }
      }
    })

    const studentFilter: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId) studentFilter.classSectionId = classSectionId
    const students = await prisma.user.findMany({ where: studentFilter, select: { id: true } })
    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: 'New ' + (taskType || 'assignment').replace('_', ' ') + ' Assigned',
          body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''),
          type: 'task', refId: task.id,
        }))
      })
    }

    return success(res, task, 'Task created', 201)
  } catch (err: any) {
    console.error('Create task error:', err)
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const createBulkTasks = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { tasks } = req.body
    const created = []
    for (const t of tasks) {
      const task = await prisma.task.create({
        data: {
          collegeId, createdBy: userId,
          title: t.title, taskType: t.taskType as any,
          subjectName: t.subjectName || null,
          classSectionId: t.classSectionId || null,
          deadline: t.deadline ? new Date(t.deadline) : null,
          maxMarks: parseInt(t.maxMarks) || 10,
          instructions: t.instructions || null,
          allowLate: t.allowLate || false,
        }
      })
      created.push(task)
      const studentFilter: any = { collegeId, role: 'student', isActive: true }
      if (t.classSectionId) studentFilter.classSectionId = t.classSectionId
      const students = await prisma.user.findMany({ where: studentFilter, select: { id: true } })
      if (students.length > 0) {
        await prisma.notification.createMany({
          data: students.map(s => ({ userId: s.id, title: 'New ' + t.taskType.replace('_', ' '), body: t.title, type: 'task', refId: task.id }))
        })
      }
    }
    return success(res, created, created.length + ' tasks created', 201)
  } catch (err: any) {
    return error(res, 'Bulk failed: ' + err.message, 500)
  }
}

export const getTasks = async (req: Request, res: Response) => {
  try {
    const { collegeId, role, classSectionId } = (req as any).user
    const { status, type, classId } = req.query
    let where: any = {
      collegeId,
      ...(status && role !== 'student' && { status: status as any }),
      ...(type && { taskType: type as any }),
    }
    if (role === 'student') {
      where.status = 'active'
      if (classSectionId) {
        where.OR = [{ classSectionId }, { classSectionId: null }]
      }
    }
    if (role === 'teacher' && classId) where.classSectionId = classId as string

    const tasks = await prisma.task.findMany({
      where,
      include: {
        creator: { select: { name: true, email: true } },
        classSection: { select: { name: true, section: true, branch: true } },
        _count: { select: { submissions: true } }
      },
      orderBy: { createdAt: 'desc' }
    })
    return success(res, tasks)
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const getTask = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const id = req.params.id as string
    const task = await prisma.task.findFirst({
      where: { id, collegeId },
      include: {
        creator: { select: { name: true } },
        classSection: { select: { name: true, section: true } },
        submissions: { include: { student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } } } }
      }
    })
    if (!task) return error(res, 'Task not found', 404)
    return success(res, task)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const updateTaskStatus = async (req: Request, res: Response) => {
  try {
    const id = req.params.id as string
    const task = await prisma.task.update({ where: { id }, data: { status: req.body.status as any } })
    return success(res, task, 'Updated')
  } catch (err) { return error(res, 'Failed', 500) }
}

export const deleteTask = async (req: Request, res: Response) => {
  try {
    await prisma.task.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch (err) { return error(res, 'Failed', 500) }
}
""")
print("task.controller fixed!")

with open("src/controllers/material.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'
import path from 'path'
import fs from 'fs'

export const uploadMaterial = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const file = req.file
    if (!file) return error(res, 'No file uploaded', 400)
    const { title, fileType, isPyq, year, subject, unit, examType } = req.body

    const material = await prisma.material.create({
      data: {
        collegeId, uploadedBy: userId,
        title: title || file.originalname,
        fileName: file.originalname,
        fileUrl: '/uploads/' + collegeId + '/' + file.filename,
        fileType: (isPyq === 'true' ? 'pyq' : fileType || 'notes') as any,
        fileSizeKb: Math.round(file.size / 1024),
        status: 'ready' as any,
        isPyq: isPyq === 'true',
        subject: subject || null,
        unit: unit || null,
        year: year ? parseInt(year) : null,
        examType: examType || null,
      }
    })
    return success(res, material, 'Uploaded', 201)
  } catch (err: any) {
    return error(res, 'Upload failed: ' + err.message, 500)
  }
}

export const getMaterials = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { type, isPyq, year, subject, search } = req.query
    const materials = await prisma.material.findMany({
      where: {
        collegeId,
        ...(type && { fileType: type as any }),
        ...(isPyq !== undefined && { isPyq: isPyq === 'true' }),
        ...(year && { year: parseInt(year as string) }),
        ...(subject && { subject: { contains: subject as string, mode: 'insensitive' as any } }),
        ...(search && { title: { contains: search as string, mode: 'insensitive' as any } })
      },
      include: { uploader: { select: { name: true } } },
      orderBy: { createdAt: 'desc' }
    })
    return success(res, materials)
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const downloadMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const material = await prisma.material.findFirst({ where: { id: req.params.id as string, collegeId } })
    if (!material) return error(res, 'Not found', 404)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) {
      return success(res, { fileUrl: material.fileUrl, fileName: material.fileName })
    }
    res.setHeader('Content-Disposition', 'attachment; filename="' + material.fileName + '"')
    res.setHeader('Access-Control-Allow-Origin', '*')
    return res.download(filePath, material.fileName)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const previewMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const material = await prisma.material.findFirst({ where: { id: req.params.id as string, collegeId } })
    if (!material) return error(res, 'Not found', 404)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return error(res, 'File not found', 404)
    res.setHeader('Content-Type', 'application/pdf')
    res.setHeader('Content-Disposition', 'inline; filename="' + material.fileName + '"')
    res.setHeader('Access-Control-Allow-Origin', '*')
    return res.sendFile(filePath)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const deleteMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const material = await prisma.material.findFirst({ where: { id: req.params.id as string, collegeId } })
    if (!material) return error(res, 'Not found', 404)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath)
    await prisma.material.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch (err) { return error(res, 'Failed', 500) }
}
""")
print("material.controller fixed!")

# Teacher complaints - allow teacher to raise complaint too
with open("src/controllers/complaint.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
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
""")
print("complaint.controller fixed!")

print("\nAll backend fixes done!")