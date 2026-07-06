import os

# ═══════════════════════════════════════════════════════
# THE REAL FIX: Single College + Open Data for Everyone
# ═══════════════════════════════════════════════════════

# 1. JWT Utils - classSectionId properly
with open("src/utils/jwt.ts", "w", encoding="utf-8") as f:
    f.write("""import jwt from 'jsonwebtoken'

const SECRET = process.env.JWT_SECRET || 'aiqpg-secret-key-krmu-2024'
const EXPIRES = process.env.JWT_EXPIRES_IN || '30d'

const SPECIAL_TEACHERS = ['akumarjaan123@gmail.com']

export function getRoleFromEmail(email: string): string {
  if (!email) return 'unknown'
  if (SPECIAL_TEACHERS.includes(email.toLowerCase())) return 'teacher'
  const prefix = email.split('@')[0]
  const domain = email.split('@')[1]
  // Accept any domain for now (college-wide access)
  if (!domain) return 'unknown'
  // Numbers = student, letters = teacher
  if (/^[0-9]/.test(prefix)) return 'student'
  if (/^[a-zA-Z]/.test(prefix)) return 'teacher'
  return 'unknown'
}

export function signToken(payload: object): string {
  return (jwt as any).sign(payload, SECRET, { expiresIn: EXPIRES })
}

export function verifyToken(token: string): any {
  return (jwt as any).verify(token, SECRET)
}
""")
print("JWT utils done!")

# 2. Auth Controller - FORCE single college, fix notifications
with open("src/controllers/auth.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { signToken, getRoleFromEmail } from '../utils/jwt'
import { success, error } from '../utils/response'
import crypto from 'crypto'

// SINGLE FIXED COLLEGE - everyone belongs to KRMU
const COLLEGE_NAME = 'K.R Mangalam University'
const COLLEGE_DOMAIN = 'krmu.edu.in'

async function getMainCollege() {
  // Always use the FIRST college created - everyone shares it
  let college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
  if (!college) {
    college = await prisma.college.create({
      data: { name: COLLEGE_NAME, domain: COLLEGE_DOMAIN }
    })
  }
  return college
}

function genCode(branch: string, sem: string, section: string): string {
  const base = (branch.slice(0,3) + sem + section).toUpperCase().replace(/[^A-Z0-9]/g,'')
  const hash = crypto.randomBytes(2).toString('hex').toUpperCase()
  return base + '-' + hash
}

export const azureLogin = async (req: Request, res: Response) => {
  try {
    const { email, name, azureOid, avatarUrl } = req.body
    if (!email) return error(res, 'Email required', 400)

    const role = getRoleFromEmail(email)
    if (role === 'unknown') return error(res, 'Access denied', 403)

    // EVERYONE goes to the SAME college
    const college = await getMainCollege()

    let user = await prisma.user.findUnique({ where: { email } })

    if (!user) {
      const prefix = email.split('@')[0]
      user = await prisma.user.create({
        data: {
          collegeId: college.id,
          name: name || prefix,
          email,
          role: role as any,
          azureOid: azureOid || null,
          avatarUrl: avatarUrl || null,
          rollNumber: /^[0-9]/.test(prefix) ? prefix : null,
        }
      })
    } else {
      // Always update to main college (fixes old users in wrong college)
      user = await prisma.user.update({
        where: { id: user.id },
        data: {
          collegeId: college.id,  // Force correct college
          lastLogin: new Date(),
          avatarUrl: avatarUrl || user.avatarUrl,
          name: name || user.name,
        }
      })
    }

    const token = signToken({
      userId: user.id,
      email: user.email,
      role: user.role,
      name: user.name,
      collegeId: college.id,  // Always main college
      classSectionId: user.classSectionId,
    })

    return success(res, {
      token,
      user: {
        id: user.id, name: user.name, email: user.email,
        role: user.role, avatarUrl: user.avatarUrl,
        rollNumber: user.rollNumber, classSectionId: user.classSectionId,
        collegeId: college.id,
      }
    })
  } catch (err: any) {
    console.error('Login error:', err)
    return error(res, 'Login failed: ' + err.message, 500)
  }
}

export const getMe = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true, name: true, email: true, role: true,
        avatarUrl: true, rollNumber: true, subjects: true, classSectionId: true,
        classSection: { select: { id: true, name: true, section: true, branch: true, semester: true, uniqueCode: true } },
        college: { select: { name: true } }
      }
    })
    if (!user) return error(res, 'Not found', 404)
    return success(res, user)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const getUsers = async (req: Request, res: Response) => {
  try {
    const college = await getMainCollege()
    const { role, classSectionId } = req.query
    const users = await prisma.user.findMany({
      where: {
        collegeId: college.id,
        ...(role && { role: role as any }),
        ...(classSectionId && { classSectionId: classSectionId as string }),
        isActive: true,
      },
      select: { id: true, name: true, email: true, role: true, avatarUrl: true, rollNumber: true, classSectionId: true, classSection: { select: { name: true, section: true } } },
      orderBy: { name: 'asc' }
    })
    return success(res, users)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const updateSubjects = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { subjects } = req.body
    const user = await prisma.user.update({ where: { id: userId }, data: { subjects } })
    return success(res, { subjects: user.subjects })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const getClasses = async (req: Request, res: Response) => {
  try {
    const college = await getMainCollege()
    const classes = await prisma.classSection.findMany({
      where: { collegeId: college.id, isActive: true },
      include: { _count: { select: { students: true } } },
      orderBy: [{ semester: 'asc' }, { branch: 'asc' }]
    })
    return success(res, classes)
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const createClass = async (req: Request, res: Response) => {
  try {
    const college = await getMainCollege()
    const { name, section, semester, branch, year } = req.body
    let uniqueCode = genCode(branch, semester, section)
    while (await prisma.classSection.findUnique({ where: { uniqueCode } })) {
      uniqueCode = genCode(branch, semester, section)
    }
    const cls = await prisma.classSection.create({
      data: { collegeId: college.id, name, section, semester: parseInt(semester), branch, year: parseInt(year), uniqueCode }
    })
    return success(res, cls, 'Created', 201)
  } catch (err: any) { return error(res, err.message, 500) }
}

export const deleteClass = async (req: Request, res: Response) => {
  try {
    await prisma.classSection.update({ where: { id: req.params.id as string }, data: { isActive: false } })
    return success(res, null, 'Deleted')
  } catch (err: any) { return error(res, err.message, 500) }
}

export const joinClassByCode = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { code } = req.body
    if (!code) return error(res, 'Code required', 400)
    const cls = await prisma.classSection.findUnique({ where: { uniqueCode: code.toUpperCase().trim() } })
    if (!cls) return error(res, 'Invalid code: ' + code.toUpperCase().trim(), 404)
    if (!cls.isActive) return error(res, 'Class is inactive', 400)
    await prisma.user.update({ where: { id: userId }, data: { classSectionId: cls.id } })
    const user = await prisma.user.findUnique({ where: { id: userId } })
    const newToken = signToken({
      userId: user!.id, email: user!.email, role: user!.role,
      name: user!.name, collegeId: user!.collegeId, classSectionId: cls.id
    })
    return success(res, { class: cls, token: newToken }, 'Joined class!')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const selectClass = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { classSectionId } = req.body
    await prisma.user.update({ where: { id: userId }, data: { classSectionId } })
    const user = await prisma.user.findUnique({ where: { id: userId } })
    const newToken = signToken({
      userId: user!.id, email: user!.email, role: user!.role,
      name: user!.name, collegeId: user!.collegeId, classSectionId
    })
    return success(res, { token: newToken }, 'Class selected')
  } catch (err: any) { return error(res, err.message, 500) }
}

export const assignClass = async (req: Request, res: Response) => {
  try {
    const { studentId, classSectionId } = req.body
    await prisma.user.update({ where: { id: studentId }, data: { classSectionId } })
    return success(res, null, 'Assigned')
  } catch (err: any) { return error(res, err.message, 500) }
}
""")
print("Auth controller done - single college!")

# 3. Task Controller - ALL students see ALL tasks by default
with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

async function getMainCollegeId(): Promise<string> {
  const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
  return college?.id || ''
}

export const createTask = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const collegeId = await getMainCollegeId()
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
      include: {
        creator: { select: { name: true } },
        classSection: { select: { name: true, section: true, branch: true } }
      }
    })

    // Notify students - class-specific OR all students
    let studentFilter: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId) {
      studentFilter.classSectionId = classSectionId
    }
    const students = await prisma.user.findMany({ where: studentFilter, select: { id: true } })

    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: '📋 New ' + (taskType || 'assignment').replace('_', ' '),
          body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true }) : ''),
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

export const createBulkTasks = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const collegeId = await getMainCollegeId()
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
    const { role } = (req as any).user
    const collegeId = await getMainCollegeId()
    const { classId } = req.query

    let where: any = { collegeId }

    if (role === 'student') {
      where.status = 'active'
      if (classId && classId !== 'undefined' && classId !== '') {
        // Student sees: their class tasks + college-wide tasks (no class set)
        where.OR = [
          { classSectionId: classId as string },
          { classSectionId: null }
        ]
      }
      // If no classId: show ALL active tasks in college
    } else if (role === 'teacher') {
      if (classId && classId !== 'undefined' && classId !== '') {
        where.classSectionId = classId as string
      }
    }

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
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const getTask = async (req: Request, res: Response) => {
  try {
    const collegeId = await getMainCollegeId()
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

export const extendDeadline = async (req: Request, res: Response) => {
  try {
    const collegeId = await getMainCollegeId()
    const { newDeadline } = req.body
    const task = await prisma.task.update({
      where: { id: req.params.id as string },
      data: { deadline: new Date(newDeadline), allowLate: true }
    })
    const f: any = { collegeId, role: 'student', isActive: true }
    if (task.classSectionId) f.classSectionId = task.classSectionId
    const students = await prisma.user.findMany({ where: f, select: { id: true } })
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

# 4. Material Controller - ALL students see ALL materials
with open("src/controllers/material.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'
import path from 'path'
import fs from 'fs'

async function getMainCollegeId(): Promise<string> {
  const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
  return college?.id || ''
}

export const uploadMaterial = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const collegeId = await getMainCollegeId()
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

    // Notify ALL students in college (or class if specified)
    let f: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId) f.classSectionId = classSectionId
    const students = await prisma.user.findMany({ where: f, select: { id: true } })
    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: isPyq === 'true' ? '📋 New PYQ Available' : '📚 New Study Material',
          body: (title || file.originalname) + (subject ? ' — ' + subject : '') + (unit ? ' (' + unit + ')' : ''),
          type: 'announcement',
          refId: material.id,
        }))
      })
    }

    return success(res, material, 'Uploaded!', 201)
  } catch (err: any) {
    return error(res, 'Upload failed: ' + err.message, 500)
  }
}

export const getMaterials = async (req: Request, res: Response) => {
  try {
    const collegeId = await getMainCollegeId()
    const { isPyq, year, subject, unit, examType, search, classId } = req.query

    const where: any = { collegeId }
    if (isPyq !== undefined) where.isPyq = isPyq === 'true'
    if (year) where.year = parseInt(year as string)
    if (subject) where.subject = { contains: subject as string, mode: 'insensitive' }
    if (unit) where.unit = { contains: unit as string, mode: 'insensitive' }
    if (examType) where.examType = examType as string
    if (search) where.title = { contains: search as string, mode: 'insensitive' }

    // If classId given: show class materials + general materials
    // Otherwise: show ALL materials (for all students)
    if (classId && classId !== 'undefined' && classId !== '') {
      where.OR = [
        { classSectionId: classId as string },
        { classSectionId: null }
      ]
    }

    const materials = await prisma.material.findMany({
      where,
      include: {
        uploader: { select: { name: true } },
        classSection: { select: { name: true, section: true } }
      },
      orderBy: { createdAt: 'desc' }
    })
    return success(res, materials)
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const downloadMaterial = async (req: Request, res: Response) => {
  try {
    const material = await prisma.material.findUnique({ where: { id: req.params.id as string } })
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
    const material = await prisma.material.findUnique({ where: { id: req.params.id as string } })
    if (!material) return error(res, 'Not found', 404)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return error(res, 'File not found', 404)
    const ext = path.extname(material.fileName).toLowerCase()
    const mimes: Record<string, string> = { '.pdf': 'application/pdf', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.txt': 'text/plain' }
    res.setHeader('Content-Type', mimes[ext] || 'application/pdf')
    res.setHeader('Content-Disposition', 'inline; filename="' + material.fileName + '"')
    res.setHeader('Access-Control-Allow-Origin', '*')
    return res.sendFile(path.resolve(filePath))
  } catch (err) { return error(res, 'Failed', 500) }
}

export const deleteMaterial = async (req: Request, res: Response) => {
  try {
    const material = await prisma.material.findUnique({ where: { id: req.params.id as string } })
    if (!material) return error(res, 'Not found', 404)
    const fp = path.join(process.cwd(), material.fileUrl)
    if (fs.existsSync(fp)) fs.unlinkSync(fp)
    await prisma.material.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch (err) { return error(res, 'Failed', 500) }
}
""")
print("Material controller done!")

# 5. Material Routes with view endpoint
with open("src/routes/material.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { uploadMaterial, getMaterials, downloadMaterial, previewMaterial, deleteMaterial } from '../controllers/material.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'
import path from 'path'
import fs from 'fs'
import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()

const router = Router()
router.post('/upload', authenticate, authorize('teacher','admin'), upload.single('file'), uploadMaterial)
router.get('/', authenticate, getMaterials)
router.get('/:id/download', authenticate, downloadMaterial)
router.get('/:id/preview', authenticate, previewMaterial)
router.delete('/:id', authenticate, authorize('teacher','admin'), deleteMaterial)

// Public inline view - no auth - opens PDF directly in browser
router.get('/:id/view', async (req: any, res: any) => {
  try {
    const material = await prisma.material.findUnique({ where: { id: req.params.id } })
    if (!material) return res.status(404).send('File not found')
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return res.status(404).send('File not on server')
    const ext = path.extname(material.fileName).toLowerCase()
    const mimes: Record<string,string> = { '.pdf':'application/pdf', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.txt':'text/plain' }
    res.setHeader('Content-Type', mimes[ext] || 'application/pdf')
    res.setHeader('Content-Disposition', 'inline; filename="' + material.fileName + '"')
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('X-Frame-Options', 'SAMEORIGIN')
    return res.sendFile(path.resolve(filePath))
  } catch (e: any) { return res.status(500).send(e.message) }
})

export default router
""")
print("Material routes done!")

# 6. Notification Controller fix
with open("src/controllers/notification.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
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
      where: { userId },
      orderBy: { createdAt: 'desc' },
      take: 50
    })
    return success(res, notifications)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const markRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    await prisma.notification.updateMany({ where: { id, userId }, data: { isRead: true } })
    return success(res, null, 'Marked as read')
  } catch (err) { return error(res, 'Failed', 500) }
}

export const markAllRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.updateMany({ where: { userId, isRead: false }, data: { isRead: true } })
    return success(res, null, 'All marked as read')
  } catch (err) { return error(res, 'Failed', 500) }
}

export const deleteNotification = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    await prisma.notification.deleteMany({ where: { id, userId } })
    return success(res, null, 'Deleted')
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
    }

    const users = await prisma.user.findMany({ where: userFilter, select: { id: true } })
    if (users.length > 0) {
      await prisma.notification.createMany({
        data: users.map(u => ({ userId: u.id, title, body, type: type || 'announcement' }))
      })
    }
    return success(res, { sent: users.length }, 'Sent to ' + users.length + ' users')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}
""")
print("Notification controller done!")

# 7. DB MERGE SCRIPT - merge all colleges into one
with open("merge_db.ts", "w", encoding="utf-8") as f:
    f.write("""import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()

async function main() {
  console.log('Starting database merge...')

  // Get the first/main college
  const colleges = await prisma.college.findMany({ orderBy: { createdAt: 'asc' } })
  console.log('Found colleges:', colleges.map(c => c.id + ' - ' + c.domain))

  if (colleges.length <= 1) {
    console.log('Only one college - no merge needed!')
    return
  }

  const mainCollege = colleges[0]
  const otherIds = colleges.slice(1).map(c => c.id)

  console.log('Main college:', mainCollege.id, mainCollege.domain)
  console.log('Merging colleges:', otherIds)

  // Move all data to main college
  await prisma.user.updateMany({ where: { collegeId: { in: otherIds } }, data: { collegeId: mainCollege.id } })
  await prisma.classSection.updateMany({ where: { collegeId: { in: otherIds } }, data: { collegeId: mainCollege.id } })
  await prisma.task.updateMany({ where: { collegeId: { in: otherIds } }, data: { collegeId: mainCollege.id } })
  await prisma.material.updateMany({ where: { collegeId: { in: otherIds } }, data: { collegeId: mainCollege.id } })

  // Delete other colleges
  await prisma.college.deleteMany({ where: { id: { in: otherIds } } })

  console.log('DONE! All data merged into single college:', mainCollege.id)
  const counts = {
    users: await prisma.user.count({ where: { collegeId: mainCollege.id } }),
    classes: await prisma.classSection.count({ where: { collegeId: mainCollege.id } }),
    tasks: await prisma.task.count({ where: { collegeId: mainCollege.id } }),
    materials: await prisma.material.count({ where: { collegeId: mainCollege.id } }),
  }
  console.log('Data counts:', counts)
}

main().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1) })
""")
print("DB merge script created!")

print("\n" + "="*60)
print("ALL BACKEND DONE!")
print("="*60)