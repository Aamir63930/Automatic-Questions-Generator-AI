import os

# ═══════════════════════════════════════
# FIX 1: Material Controller - classSectionId filter add
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
    if (classId) {
      where.OR = [{ classSectionId: classId as string }, { classSectionId: null }]
    }

    const materials = await prisma.material.findMany({
      where,
      include: { uploader: { select: { name: true } }, classSection: { select: { name: true, section: true } } },
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
    if (!fs.existsSync(filePath)) return success(res, { fileUrl: material.fileUrl, fileName: material.fileName })
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
    res.setHeader('Content-Disposition', 'inline')
    res.setHeader('Access-Control-Allow-Origin', '*')
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
# FIX 2: Prisma schema - Material needs classSectionId
# ═══════════════════════════════════════
with open("prisma/schema.prisma", "r", encoding="utf-8") as f:
    schema = f.read()

if "classSectionId" not in schema.split("model Material")[1].split("model")[0]:
    schema = schema.replace(
        """model Material {
  id          String         @id @default(uuid())
  collegeId   String
  uploadedBy  String""",
        """model Material {
  id          String         @id @default(uuid())
  collegeId   String
  classSectionId String?
  uploadedBy  String"""
    )
    schema = schema.replace(
        """  college  College @relation(fields: [collegeId], references: [id])
  uploader User    @relation(fields: [uploadedBy], references: [id])
}

enum MaterialType {""",
        """  college  College @relation(fields: [collegeId], references: [id])
  uploader User    @relation(fields: [uploadedBy], references: [id])
  classSection ClassSection? @relation(fields: [classSectionId], references: [id])
}

enum MaterialType {"""
    )
    # Add relation on ClassSection
    schema = schema.replace(
        """  students User[]  @relation("StudentClass")
  tasks    Task[]  @relation("TaskClass")
}""",
        """  students User[]  @relation("StudentClass")
  tasks    Task[]  @relation("TaskClass")
  materials Material[]
}"""
    )
    with open("prisma/schema.prisma", "w", encoding="utf-8") as f:
        f.write(schema)
    print("Schema updated with Material.classSectionId!")
else:
    print("Schema already has classSectionId on Material")

# ═══════════════════════════════════════
# FIX 3: Submission Controller - notify + summary for teacher
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

    const existing = await prisma.submission.findUnique({
      where: { taskId_studentId: { taskId: taskId as string, studentId: userId } }
    })
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

    return success(res, submission, 'Submitted successfully!', 201)
  } catch (err: any) {
    return error(res, 'Submission failed: ' + err.message, 500)
  }
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

// GET /api/v1/submissions/pending-summary - for teacher dashboard
export const getPendingSummary = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const tasks = await prisma.task.findMany({
      where: { collegeId, createdBy: userId },
      include: {
        classSection: { select: { name: true, section: true } },
        _count: { select: { submissions: true } },
        submissions: { select: { id: true, marksAwarded: true } }
      }
    })

    const summary = tasks.map(t => {
      const total = t.submissions.length
      const graded = t.submissions.filter(s => s.marksAwarded !== null).length
      const pending = total - graded
      return {
        taskId: t.id, title: t.title, maxMarks: t.maxMarks,
        className: t.classSection ? t.classSection.name + ' ' + t.classSection.section : 'All Students',
        totalSubmissions: total, graded, pending
      }
    }).filter(s => s.pending > 0)

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

# ═══════════════════════════════════════
# FIX 4: Submission routes - add pending-summary
# ═══════════════════════════════════════
with open("src/routes/submission.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { createSubmission, getSubmissions, gradeSubmission, getPendingSummary } from '../controllers/submission.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'

const router = Router()
router.post('/', authenticate, authorize('student'), upload.single('file'), createSubmission)
router.get('/', authenticate, getSubmissions)
router.get('/pending-summary', authenticate, authorize('teacher', 'admin'), getPendingSummary)
router.patch('/:id/grade', authenticate, authorize('teacher', 'admin'), gradeSubmission)

export default router
""")
print("Submission routes done!")

print("\n=== BACKEND DONE ===")