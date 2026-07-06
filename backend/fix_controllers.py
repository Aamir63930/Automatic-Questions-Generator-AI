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
    const { title, subjectId, fileType, isPyq, year } = req.body
    const material = await prisma.material.create({
      data: {
        collegeId,
        subjectId: subjectId || null,
        uploadedBy: userId,
        title: title || file.originalname,
        fileName: file.originalname,
        fileUrl: '/uploads/' + collegeId + '/' + file.filename,
        fileType: (fileType || 'other') as any,
        fileSizeKb: Math.round(file.size / 1024),
        status: 'ready' as any,
        isPyq: isPyq === 'true',
        year: year ? parseInt(year) : null,
      }
    })
    return success(res, material, 'Material uploaded successfully', 201)
  } catch (err: any) {
    return error(res, 'Upload failed: ' + err.message, 500)
  }
}

export const getMaterials = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { subjectId, type, isPyq, year, search } = req.query
    const materials = await prisma.material.findMany({
      where: {
        collegeId,
        ...(subjectId && { subjectId: subjectId as string }),
        ...(type && { fileType: type as any }),
        ...(isPyq && { isPyq: isPyq === 'true' }),
        ...(year && { year: parseInt(year as string) }),
        ...(search && { title: { contains: search as string, mode: 'insensitive' as any } })
      },
      include: {
        uploader: { select: { name: true } },
        subject: { select: { name: true, code: true } }
      },
      orderBy: { createdAt: 'desc' }
    })
    return success(res, materials)
  } catch (err) {
    return error(res, 'Failed to get materials', 500)
  }
}

export const downloadMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const id = req.params.id as string
    const material = await prisma.material.findFirst({
      where: { id, collegeId }
    })
    if (!material) return error(res, 'Material not found', 404)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return error(res, 'File not found on server', 404)
    res.download(filePath, material.fileName)
  } catch (err) {
    return error(res, 'Download failed', 500)
  }
}

export const deleteMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const id = req.params.id as string
    const material = await prisma.material.findFirst({
      where: { id, collegeId }
    })
    if (!material) return error(res, 'Material not found', 404)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath)
    await prisma.material.delete({ where: { id } })
    return success(res, null, 'Material deleted')
  } catch (err) {
    return error(res, 'Delete failed', 500)
  }
}
""")
print("material.controller fixed!")

# Fix submission controller too
with open("src/controllers/submission.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createSubmission = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { taskId, textAnswer } = req.body
    const file = req.file

    const task = await prisma.task.findFirst({
      where: { id: taskId as string, collegeId, status: 'active' }
    })
    if (!task) return error(res, 'Task not found or closed', 404)

    const existing = await prisma.submission.findUnique({
      where: { taskId_studentId: { taskId: taskId as string, studentId: userId } }
    })
    if (existing) return error(res, 'Already submitted', 400)

    const isLate = task.deadline && new Date() > task.deadline
    if (isLate && !task.allowLate) return error(res, 'Deadline has passed', 400)

    const submission = await prisma.submission.create({
      data: {
        taskId: taskId as string,
        studentId: userId,
        textAnswer: textAnswer || null,
        fileUrl: file ? '/uploads/' + collegeId + '/' + file.filename : null,
        fileName: file?.originalname || null,
        status: (isLate ? 'late' : 'submitted') as any,
      }
    })

    // Notify teacher
    const student = await prisma.user.findUnique({ where: { id: userId }, select: { name: true } })
    await prisma.notification.create({
      data: {
        userId: task.createdBy,
        title: 'New Submission',
        body: (student?.name || 'A student') + ' submitted ' + task.title,
        type: 'task',
        refId: taskId as string,
      }
    })

    return success(res, submission, 'Submitted successfully', 201)
  } catch (err: any) {
    return error(res, 'Submission failed: ' + err.message, 500)
  }
}

export const getSubmissions = async (req: Request, res: Response) => {
  try {
    const { userId, role } = (req as any).user
    const { taskId } = req.query
    const submissions = await prisma.submission.findMany({
      where: {
        ...(taskId && { taskId: taskId as string }),
        ...(role === 'student' && { studentId: userId }),
      },
      include: {
        student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } },
        task: { select: { title: true, maxMarks: true, taskType: true } }
      },
      orderBy: { submittedAt: 'desc' }
    })
    return success(res, submissions)
  } catch (err) {
    return error(res, 'Failed to get submissions', 500)
  }
}

export const gradeSubmission = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    const { marks, feedback } = req.body

    const submission = await prisma.submission.update({
      where: { id },
      data: {
        marksAwarded: parseInt(marks),
        feedback,
        gradedBy: userId,
        gradedAt: new Date(),
        status: 'graded' as any,
      },
      include: { task: { select: { title: true, maxMarks: true } } }
    })

    await prisma.notification.create({
      data: {
        userId: submission.studentId,
        title: 'Result Published',
        body: submission.task.title + ' graded: ' + marks + '/' + submission.task.maxMarks + (feedback ? ' — ' + feedback : ''),
        type: 'result',
        refId: submission.taskId,
      }
    })

    return success(res, submission, 'Graded successfully')
  } catch (err: any) {
    return error(res, 'Grading failed: ' + err.message, 500)
  }
}
""")
print("submission.controller fixed!")

# Fix complaint controller
with open("src/controllers/complaint.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createComplaint = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { subject, category, description } = req.body

    const complaint = await prisma.complaint.create({
      data: {
        raisedBy: userId,
        subject,
        category,
        messages: { create: { sentBy: userId, message: description } }
      },
      include: { messages: true }
    })

    const teachers = await prisma.user.findMany({
      where: { collegeId, role: 'teacher', isActive: true },
      select: { id: true }
    })
    await prisma.notification.createMany({
      data: teachers.map(t => ({
        userId: t.id,
        title: 'New Complaint',
        body: subject,
        type: 'complaint',
        refId: complaint.id,
      }))
    })

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
        raiser: { select: { name: true, email: true, rollNumber: true } },
        messages: { orderBy: { createdAt: 'asc' } }
      },
      orderBy: { createdAt: 'desc' }
    })
    return success(res, complaints)
  } catch (err) {
    return error(res, 'Failed to get complaints', 500)
  }
}

export const replyComplaint = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    const { message } = req.body

    const msg = await prisma.complaintMessage.create({
      data: { complaintId: id, sentBy: userId, message }
    })

    await prisma.complaint.update({
      where: { id },
      data: { status: 'in_progress' as any }
    })

    const complaint = await prisma.complaint.findUnique({ where: { id } })
    if (complaint && complaint.raisedBy !== userId) {
      await prisma.notification.create({
        data: {
          userId: complaint.raisedBy,
          title: 'Complaint Reply',
          body: 'New reply: ' + message.slice(0, 60),
          type: 'complaint',
          refId: id,
        }
      })
    }

    return success(res, msg, 'Reply sent')
  } catch (err) {
    return error(res, 'Failed to reply', 500)
  }
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
      data: {
        userId: complaint.raisedBy,
        title: 'Complaint ' + status,
        body: '"' + complaint.subject + '" has been ' + status,
        type: 'complaint',
        refId: id,
      }
    })
    return success(res, complaint, 'Status updated')
  } catch (err) {
    return error(res, 'Failed to update status', 500)
  }
}
""")
print("complaint.controller fixed!")

# Fix task controller
with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createTask = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { title, description, taskType, subjectId, deadline, startTime, maxMarks, instructions, allowLate, latePenalty } = req.body

    const task = await prisma.task.create({
      data: {
        collegeId,
        createdBy: userId,
        title,
        description,
        taskType: taskType as any,
        subjectId: subjectId || null,
        deadline: deadline ? new Date(deadline) : null,
        startTime: startTime ? new Date(startTime) : null,
        maxMarks: parseInt(maxMarks) || 10,
        instructions,
        allowLate: allowLate === true || allowLate === 'true',
        latePenalty: parseInt(latePenalty) || 0,
        attachmentUrl: req.file ? '/uploads/' + collegeId + '/' + req.file.filename : null,
      },
      include: { creator: { select: { name: true } }, subject: { select: { name: true } } }
    })

    const students = await prisma.user.findMany({
      where: { collegeId, role: 'student', isActive: true },
      select: { id: true }
    })

    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: 'New ' + taskType + ' Assigned',
          body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleDateString('en-IN') : ''),
          type: 'task',
          refId: task.id,
        }))
      })
    }

    return success(res, task, 'Task created', 201)
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const getTasks = async (req: Request, res: Response) => {
  try {
    const { collegeId, role } = (req as any).user
    const { status, type, subjectId } = req.query

    const tasks = await prisma.task.findMany({
      where: {
        collegeId,
        ...(status && { status: status as any }),
        ...(type && { taskType: type as any }),
        ...(subjectId && { subjectId: subjectId as string }),
        ...(role === 'student' && { status: 'active' as any }),
      },
      include: {
        creator: { select: { name: true, email: true } },
        subject: { select: { name: true, code: true } },
        _count: { select: { submissions: true } }
      },
      orderBy: { createdAt: 'desc' }
    })

    return success(res, tasks)
  } catch (err) {
    return error(res, 'Failed to get tasks', 500)
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
        subject: { select: { name: true } },
        submissions: {
          include: { student: { select: { name: true, email: true, rollNumber: true } } }
        }
      }
    })
    if (!task) return error(res, 'Task not found', 404)
    return success(res, task)
  } catch (err) {
    return error(res, 'Failed to get task', 500)
  }
}

export const updateTaskStatus = async (req: Request, res: Response) => {
  try {
    const id = req.params.id as string
    const { status } = req.body
    const task = await prisma.task.update({
      where: { id },
      data: { status: status as any }
    })
    return success(res, task, 'Status updated')
  } catch (err) {
    return error(res, 'Failed to update', 500)
  }
}

export const deleteTask = async (req: Request, res: Response) => {
  try {
    const id = req.params.id as string
    await prisma.task.delete({ where: { id } })
    return success(res, null, 'Task deleted')
  } catch (err) {
    return error(res, 'Failed to delete', 500)
  }
}
""")
print("task.controller fixed!")

print("\nAll controllers fixed!")