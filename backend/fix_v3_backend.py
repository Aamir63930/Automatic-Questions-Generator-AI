import os

# ═══════════════════════════════════════
# FIX 1: Material preview - inline open (not download)
# ═══════════════════════════════════════
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
    const { title, fileType, isPyq, year, subject, unit, examType, classSectionId } = req.body

    const material = await prisma.material.create({
      data: {
        collegeId, uploadedBy: userId,
        title: title || file.originalname.replace(/\\.[^.]+$/, ''),
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
        classSectionId: classSectionId || null,
      },
      include: { uploader: { select: { name: true } } }
    })
    return success(res, material, 'Uploaded!', 201)
  } catch (err: any) {
    return error(res, 'Upload failed: ' + err.message, 500)
  }
}

export const getMaterials = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { isPyq, year, subject, unit, examType, search, classId } = req.query
    const where: any = { collegeId }
    if (isPyq !== undefined) where.isPyq = isPyq === 'true'
    if (year) where.year = parseInt(year as string)
    if (subject) where.subject = { contains: subject as string, mode: 'insensitive' }
    if (unit) where.unit = { contains: unit as string, mode: 'insensitive' }
    if (examType) where.examType = examType as string
    if (search) where.title = { contains: search as string, mode: 'insensitive' }
    if (classId) where.OR = [{ classSectionId: classId as string }, { classSectionId: null }]

    const materials = await prisma.material.findMany({
      where, include: { uploader: { select: { name: true } }, classSection: { select: { name: true, section: true } } },
      orderBy: { createdAt: 'desc' }
    })
    return success(res, materials)
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const downloadMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const material = await prisma.material.findFirst({ where: { id: req.params.id as string, collegeId } })
    if (!material) return error(res, 'Not found', 404)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return success(res, { fileUrl: material.fileUrl, fileName: material.fileName })
    res.setHeader('Content-Disposition', 'attachment; filename="' + material.fileName + '"')
    res.setHeader('Access-Control-Allow-Origin', '*')
    return res.download(filePath, material.fileName)
  } catch (err) { return error(res, 'Failed', 500) }
}

// View inline - opens directly in browser, no download
export const previewMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const material = await prisma.material.findFirst({ where: { id: req.params.id as string, collegeId } })
    if (!material) return error(res, 'Not found', 404)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return error(res, 'File not found', 404)

    const ext = path.extname(material.fileName).toLowerCase()
    const mimeMap: Record<string, string> = {
      '.pdf': 'application/pdf',
      '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
      '.txt': 'text/plain',
    }
    const mime = mimeMap[ext] || 'application/octet-stream'

    res.setHeader('Content-Type', mime)
    res.setHeader('Content-Disposition', 'inline; filename="' + material.fileName + '"')
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('Cache-Control', 'no-cache')
    return res.sendFile(filePath)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const deleteMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const material = await prisma.material.findFirst({ where: { id: req.params.id as string, collegeId } })
    if (!material) return error(res, 'Not found', 404)
    const fp = path.join(process.cwd(), material.fileUrl)
    if (fs.existsSync(fp)) fs.unlinkSync(fp)
    await prisma.material.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch (err) { return error(res, 'Failed', 500) }
}
""")
print("Material controller done!")

# ═══════════════════════════════════════
# FIX 2: Material routes - download via /preview not /download for view
# ═══════════════════════════════════════
with open("src/routes/material.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { uploadMaterial, getMaterials, downloadMaterial, previewMaterial, deleteMaterial } from '../controllers/material.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'

const router = Router()
router.post('/upload', authenticate, authorize('teacher', 'admin'), upload.single('file'), uploadMaterial)
router.get('/', authenticate, getMaterials)
router.get('/:id/download', authenticate, downloadMaterial)
router.get('/:id/preview', authenticate, previewMaterial)
router.delete('/:id', authenticate, authorize('teacher', 'admin'), deleteMaterial)

export default router
""")
print("Material routes done!")

# ═══════════════════════════════════════
# FIX 3: Submission controller - class wise summary with submitted/not-submitted
# ═══════════════════════════════════════
with open("src/controllers/submission.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createSubmission = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { taskId, textAnswer } = req.body
    const file = req.file

    const task = await prisma.task.findFirst({ where: { id: taskId as string, collegeId } })
    if (!task) return error(res, 'Task not found', 404)
    if (task.status !== 'active') return error(res, 'Task is closed', 400)

    const existing = await prisma.submission.findUnique({ where: { taskId_studentId: { taskId: taskId as string, studentId: userId } } })
    if (existing) return error(res, 'Already submitted', 400)

    const isLate = task.deadline && new Date() > task.deadline
    if (isLate && !task.allowLate) return error(res, 'Deadline has passed', 400)

    const submission = await prisma.submission.create({
      data: {
        taskId: taskId as string, studentId: userId,
        textAnswer: textAnswer || null,
        fileUrl: file ? '/uploads/' + collegeId + '/' + file.filename : null,
        fileName: file?.originalname || null,
        status: (isLate ? 'late' : 'submitted') as any,
      },
      include: { student: { select: { name: true } }, task: { select: { title: true, maxMarks: true } } }
    })

    const student = await prisma.user.findUnique({ where: { id: userId }, select: { name: true } })
    await prisma.notification.create({
      data: { userId: task.createdBy, title: 'New Submission', body: (student?.name || 'Student') + ' submitted "' + task.title + '"', type: 'task', refId: taskId as string }
    })

    // Check if all students in class have submitted - notify teacher with summary
    const submCount = await prisma.submission.count({ where: { taskId: taskId as string } })
    const studentFilter: any = { collegeId, role: 'student', isActive: true }
    if (task.classSectionId) studentFilter.classSectionId = task.classSectionId
    const totalStudents = await prisma.user.count({ where: studentFilter })

    if (submCount === totalStudents && totalStudents > 0) {
      await prisma.notification.create({
        data: { userId: task.createdBy, title: '✅ All Submitted!', body: 'All ' + totalStudents + ' students have submitted "' + task.title + '"', type: 'task', refId: taskId as string }
      })
    }

    return success(res, submission, 'Submitted successfully!', 201)
  } catch (err: any) { return error(res, 'Submission failed: ' + err.message, 500) }
}

export const getSubmissions = async (req: Request, res: Response) => {
  try {
    const { userId, role } = (req as any).user
    const { taskId } = req.query
    const submissions = await prisma.submission.findMany({
      where: { ...(taskId && { taskId: taskId as string }), ...(role === 'student' && { studentId: userId }) },
      include: {
        student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true, classSectionId: true, classSection: { select: { name: true, section: true } } } },
        task: { select: { title: true, maxMarks: true, taskType: true, subjectName: true, classSectionId: true } }
      },
      orderBy: { submittedAt: 'desc' }
    })
    return success(res, submissions)
  } catch (err) { return error(res, 'Failed', 500) }
}

// Summary of submitted vs not-submitted per task (for teacher)
export const getTaskSubmissionStatus = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const taskId = req.params.taskId as string
    const task = await prisma.task.findFirst({ where: { id: taskId, collegeId } })
    if (!task) return error(res, 'Not found', 404)

    const studentFilter: any = { collegeId, role: 'student', isActive: true }
    if (task.classSectionId) studentFilter.classSectionId = task.classSectionId

    const allStudents = await prisma.user.findMany({
      where: studentFilter,
      select: { id: true, name: true, rollNumber: true, avatarUrl: true }
    })

    const submissions = await prisma.submission.findMany({
      where: { taskId },
      select: { studentId: true, status: true, marksAwarded: true, submittedAt: true }
    })
    const subMap = new Map(submissions.map(s => [s.studentId, s]))

    const submitted = allStudents.filter(s => subMap.has(s.id)).map(s => ({ ...s, ...subMap.get(s.id) }))
    const notSubmitted = allStudents.filter(s => !subMap.has(s.id))

    return success(res, {
      total: allStudents.length,
      submittedCount: submitted.length,
      notSubmittedCount: notSubmitted.length,
      submitted, notSubmitted,
    })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const getPendingSummary = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const tasks = await prisma.task.findMany({
      where: { collegeId, createdBy: userId },
      include: {
        classSection: { select: { name: true, section: true } },
        submissions: { select: { id: true, marksAwarded: true } }
      }
    })

    const summary = await Promise.all(tasks.map(async t => {
      const total = t.submissions.length
      const graded = t.submissions.filter(s => s.marksAwarded !== null).length
      const pending = total - graded

      const studentFilter: any = { collegeId, role: 'student', isActive: true }
      if (t.classSectionId) studentFilter.classSectionId = t.classSectionId
      const totalStudents = await prisma.user.count({ where: studentFilter })

      return {
        taskId: t.id, title: t.title, maxMarks: t.maxMarks,
        className: t.classSection ? t.classSection.name + ' ' + t.classSection.section : 'All Students',
        totalStudents, submittedCount: total, notSubmittedCount: totalStudents - total,
        graded, pending
      }
    }))

    const totalPending = summary.reduce((sum, s) => sum + s.pending, 0)
    return success(res, { totalPending, tasks: summary })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const gradeSubmission = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    const { marks, feedback } = req.body
    const submission = await prisma.submission.update({
      where: { id },
      data: { marksAwarded: parseInt(marks), feedback: feedback || null, gradedBy: userId, gradedAt: new Date(), status: 'graded' as any },
      include: { task: { select: { title: true, maxMarks: true } } }
    })
    await prisma.notification.create({
      data: { userId: submission.studentId, title: '📊 Result Published!', body: '"' + submission.task.title + '" graded: ' + marks + '/' + submission.task.maxMarks + (feedback ? ' — ' + feedback : ''), type: 'result', refId: submission.taskId }
    })
    return success(res, submission, 'Graded!')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}
""")
print("Submission controller done!")

with open("src/routes/submission.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { createSubmission, getSubmissions, gradeSubmission, getPendingSummary, getTaskSubmissionStatus } from '../controllers/submission.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'

const router = Router()
router.post('/', authenticate, authorize('student'), upload.single('file'), createSubmission)
router.get('/', authenticate, getSubmissions)
router.get('/pending-summary', authenticate, authorize('teacher', 'admin'), getPendingSummary)
router.get('/task/:taskId/status', authenticate, authorize('teacher', 'admin'), getTaskSubmissionStatus)
router.patch('/:id/grade', authenticate, authorize('teacher', 'admin'), gradeSubmission)

export default router
""")
print("Submission routes done!")

# ═══════════════════════════════════════
# FIX 4: Task controller - extendedDeadline field for extend feature
# ═══════════════════════════════════════
with open("prisma/schema.prisma", "r", encoding="utf-8") as f:
    schema = f.read()

if "extendedDeadline" not in schema:
    schema = schema.replace(
        "  deadline       DateTime?",
        "  deadline       DateTime?\n  extendedDeadline DateTime?"
    )
    with open("prisma/schema.prisma", "w", encoding="utf-8") as f:
        f.write(schema)
    print("Schema: extendedDeadline added!")
else:
    print("Schema already has extendedDeadline")

with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createTask = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { title, description, taskType, subjectName, classSectionId, deadline, maxMarks, instructions, allowLate } = req.body
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
        attachmentUrl: req.file ? '/uploads/' + collegeId + '/' + req.file.filename : null,
      },
      include: { creator: { select: { name: true } }, classSection: { select: { name: true, section: true, branch: true } } }
    })
    const filter: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId) filter.classSectionId = classSectionId
    const students = await prisma.user.findMany({ where: filter, select: { id: true } })
    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id, title: 'New ' + (taskType || 'assignment').replace('_', ' '),
          body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true }) : ''),
          type: 'task', refId: task.id,
        }))
      })
    }
    return success(res, task, 'Task created', 201)
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const createBulkTasks = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { tasks } = req.body
    const created = []
    for (const t of tasks) {
      const task = await prisma.task.create({
        data: { collegeId, createdBy: userId, title: t.title, taskType: t.taskType as any, subjectName: t.subjectName || null, classSectionId: t.classSectionId || null, deadline: t.deadline ? new Date(t.deadline) : null, maxMarks: parseInt(t.maxMarks) || 10 }
      })
      created.push(task)
    }
    return success(res, created, created.length + ' tasks created', 201)
  } catch (err: any) { return error(res, err.message, 500) }
}

export const getTasks = async (req: Request, res: Response) => {
  try {
    const { collegeId, role } = (req as any).user
    const { classId } = req.query
    let where: any = { collegeId }
    if (role === 'student') {
      where.status = 'active'
      if (classId) where.OR = [{ classSectionId: classId as string }, { classSectionId: null }]
    } else if (role === 'teacher') {
      if (classId) where.classSectionId = classId as string
    }
    const tasks = await prisma.task.findMany({
      where,
      include: { creator: { select: { name: true, email: true } }, classSection: { select: { name: true, section: true, branch: true } }, _count: { select: { submissions: true } } },
      orderBy: { createdAt: 'desc' }
    })
    return success(res, tasks)
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const getTask = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const task = await prisma.task.findFirst({
      where: { id: req.params.id as string, collegeId },
      include: { creator: { select: { name: true } }, classSection: { select: { name: true, section: true } }, submissions: { include: { student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } } } } }
    })
    if (!task) return error(res, 'Not found', 404)
    return success(res, task)
  } catch { return error(res, 'Failed', 500) }
}

export const updateTaskStatus = async (req: Request, res: Response) => {
  try {
    const task = await prisma.task.update({ where: { id: req.params.id as string }, data: { status: req.body.status as any } })
    return success(res, task)
  } catch { return error(res, 'Failed', 500) }
}

// Extend deadline with date+time
export const extendDeadline = async (req: Request, res: Response) => {
  try {
    const { newDeadline } = req.body
    const task = await prisma.task.update({
      where: { id: req.params.id as string },
      data: { deadline: new Date(newDeadline), allowLate: true }
    })
    // Notify students of extension
    const students = await prisma.user.findMany({
      where: { collegeId: task.collegeId, role: 'student', isActive: true, ...(task.classSectionId && { classSectionId: task.classSectionId }) },
      select: { id: true }
    })
    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id, title: '⏰ Deadline Extended',
          body: '"' + task.title + '" deadline extended to ' + new Date(newDeadline).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true }),
          type: 'task', refId: task.id,
        }))
      })
    }
    return success(res, task, 'Deadline extended')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const deleteTask = async (req: Request, res: Response) => {
  try {
    await prisma.task.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch { return error(res, 'Failed', 500) }
}
""")
print("Task controller done!")

with open("src/routes/task.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { createTask, createBulkTasks, getTasks, getTask, updateTaskStatus, extendDeadline, deleteTask } from '../controllers/task.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'

const router = Router()
router.post('/', authenticate, authorize('teacher', 'admin'), upload.single('attachment'), createTask)
router.post('/bulk', authenticate, authorize('teacher', 'admin'), createBulkTasks)
router.get('/', authenticate, getTasks)
router.get('/:id', authenticate, getTask)
router.patch('/:id/status', authenticate, authorize('teacher', 'admin'), updateTaskStatus)
router.patch('/:id/extend-deadline', authenticate, authorize('teacher', 'admin'), extendDeadline)
router.delete('/:id', authenticate, authorize('teacher', 'admin'), deleteTask)

export default router
""")
print("Task routes done!")

print("\n=== BACKEND DONE ===")