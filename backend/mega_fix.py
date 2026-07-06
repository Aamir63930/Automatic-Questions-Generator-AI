import os, json

# ═══════════════════════════════════════════════════
# BACKEND FIX 1: Final Prisma Schema
# ═══════════════════════════════════════════════════
with open("prisma/schema.prisma", "w", encoding="utf-8") as f:
    f.write("""generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model College {
  id         String   @id @default(uuid())
  name       String
  domain     String   @unique
  logoUrl    String?
  isActive   Boolean  @default(true)
  createdAt  DateTime @default(now())

  users      User[]
  tasks      Task[]
  materials  Material[]
  papers     Paper[]
  classes    ClassSection[]
}

model ClassSection {
  id         String   @id @default(uuid())
  collegeId  String
  name       String
  section    String
  semester   Int
  branch     String
  year       Int
  uniqueCode String   @unique
  isActive   Boolean  @default(true)
  createdAt  DateTime @default(now())

  college  College @relation(fields: [collegeId], references: [id])
  students User[]  @relation("StudentClass")
  tasks    Task[]  @relation("TaskClass")
}

model User {
  id             String   @id @default(uuid())
  collegeId      String
  classSectionId String?
  name           String
  email          String   @unique
  role           Role
  azureOid       String?  @unique
  avatarUrl      String?
  department     String?
  rollNumber     String?
  subjects       String[] @default([])
  isActive       Boolean  @default(true)
  lastLogin      DateTime?
  createdAt      DateTime @default(now())
  updatedAt      DateTime @updatedAt

  college       College       @relation(fields: [collegeId], references: [id])
  classSection  ClassSection? @relation("StudentClass", fields: [classSectionId], references: [id])
  tasks         Task[]        @relation("TaskCreator")
  submissions   Submission[]
  materials     Material[]
  complaints    Complaint[]   @relation("ComplaintRaiser")
  notifications Notification[]
}

enum Role {
  admin
  hod
  teacher
  student
}

model Material {
  id          String         @id @default(uuid())
  collegeId   String
  uploadedBy  String
  title       String
  fileName    String
  fileUrl     String
  fileType    MaterialType
  fileSizeKb  Int?
  status      MaterialStatus @default(ready)
  isPyq       Boolean        @default(false)
  subject     String?
  unit        String?
  year        Int?
  examType    String?
  createdAt   DateTime       @default(now())

  college  College @relation(fields: [collegeId], references: [id])
  uploader User    @relation(fields: [uploadedBy], references: [id])
}

enum MaterialType {
  notes
  pyq
  textbook
  other
}

enum MaterialStatus {
  uploaded
  processing
  ready
  failed
}

model Task {
  id             String     @id @default(uuid())
  collegeId      String
  classSectionId String?
  createdBy      String
  title          String
  description    String?
  taskType       TaskType
  subjectName    String?
  deadline       DateTime?
  maxMarks       Int        @default(10)
  instructions   String?
  attachmentUrl  String?
  allowLate      Boolean    @default(false)
  latePenalty    Int        @default(0)
  status         TaskStatus @default(active)
  createdAt      DateTime   @default(now())
  updatedAt      DateTime   @updatedAt

  college      College       @relation(fields: [collegeId], references: [id])
  creator      User          @relation("TaskCreator", fields: [createdBy], references: [id])
  classSection ClassSection? @relation("TaskClass", fields: [classSectionId], references: [id])
  submissions  Submission[]
}

enum TaskType {
  assignment
  class_test
  quiz
  project
}

enum TaskStatus {
  active
  closed
  draft
}

model Submission {
  id           String       @id @default(uuid())
  taskId       String
  studentId    String
  fileUrl      String?
  fileName     String?
  textAnswer   String?
  status       SubmitStatus @default(submitted)
  marksAwarded Int?
  feedback     String?
  gradedBy     String?
  gradedAt     DateTime?
  submittedAt  DateTime     @default(now())

  task    Task @relation(fields: [taskId], references: [id], onDelete: Cascade)
  student User @relation(fields: [studentId], references: [id])

  @@unique([taskId, studentId])
}

enum SubmitStatus {
  submitted
  late
  missing
  graded
}

model Notification {
  id        String   @id @default(uuid())
  userId    String
  title     String
  body      String
  type      String   @default("system")
  refId     String?
  isRead    Boolean  @default(false)
  createdAt DateTime @default(now())

  user User @relation(fields: [userId], references: [id])
}

model Complaint {
  id         String          @id @default(uuid())
  raisedBy   String
  subject    String
  category   String?
  status     ComplaintStatus @default(open)
  priority   String          @default("normal")
  resolvedAt DateTime?
  createdAt  DateTime        @default(now())
  updatedAt  DateTime        @updatedAt

  raiser   User               @relation("ComplaintRaiser", fields: [raisedBy], references: [id])
  messages ComplaintMessage[]
}

enum ComplaintStatus {
  open
  in_progress
  resolved
  closed
}

model ComplaintMessage {
  id          String   @id @default(uuid())
  complaintId String
  sentBy      String
  senderName  String   @default("User")
  senderRole  String   @default("student")
  message     String
  createdAt   DateTime @default(now())

  complaint Complaint @relation(fields: [complaintId], references: [id], onDelete: Cascade)
}

model Paper {
  id         String   @id @default(uuid())
  collegeId  String
  createdBy  String
  title      String
  subject    String
  examType   String
  totalMarks Int
  duration   Int      @default(180)
  pdfUrl     String?
  status     String   @default("draft")
  questions  Json     @default("[]")
  createdAt  DateTime @default(now())

  college College @relation(fields: [collegeId], references: [id])
}
""")
print("Schema done!")

# ═══════════════════════════════════════════════════
# BACKEND FIX 2: Notification Controller - multi target
# ═══════════════════════════════════════════════════
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
    return error(res, 'Failed', 500)
  }
}

export const markRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    await prisma.notification.updateMany({ where: { id, userId }, data: { isRead: true } })
    return success(res, null, 'Marked as read')
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}

export const markAllRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.updateMany({ where: { userId, isRead: false }, data: { isRead: true } })
    return success(res, null, 'All marked as read')
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}

export const deleteNotification = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    await prisma.notification.deleteMany({ where: { id, userId } })
    return success(res, null, 'Deleted')
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}

// POST /api/v1/notifications/send
// target: 'all' | classSectionId[] | 'teachers'
export const sendBulkNotification = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { title, body, type, target, classIds } = req.body
    // target: 'all_students' | 'specific_classes' | 'all'
    let userFilter: any = { collegeId, isActive: true }

    if (target === 'all_students') {
      userFilter.role = 'student'
    } else if (target === 'specific_classes' && classIds?.length > 0) {
      userFilter.role = 'student'
      userFilter.classSectionId = { in: classIds }
    } else if (target === 'teachers') {
      userFilter.role = 'teacher'
    }
    // else 'all' = everyone

    const users = await prisma.user.findMany({ where: userFilter, select: { id: true } })

    if (users.length > 0) {
      await prisma.notification.createMany({
        data: users.map(u => ({
          userId: u.id,
          title,
          body,
          type: type || 'announcement',
        }))
      })
    }

    return success(res, { sent: users.length }, 'Sent to ' + users.length + ' users')
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}
""")
print("notification.controller done!")

# ═══════════════════════════════════════════════════
# BACKEND FIX 3: Auth - subject management
# ═══════════════════════════════════════════════════
with open("src/controllers/auth.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { signToken, getRoleFromEmail } from '../utils/jwt'
import { success, error } from '../utils/response'
import crypto from 'crypto'

function generateClassCode(branch: string, name: string, section: string, semester: string): string {
  const base = (branch.slice(0,3) + semester + section).toUpperCase()
  const hash = crypto.randomBytes(2).toString('hex').toUpperCase()
  return base + '-' + hash
}

export const azureLogin = async (req: Request, res: Response) => {
  try {
    const { email, name, azureOid, avatarUrl } = req.body
    if (!email) return error(res, 'Email required', 400)
    const role = getRoleFromEmail(email)
    if (role === 'unknown') return error(res, 'Access denied. Only KRMU accounts allowed.', 403)

    const domain = email.includes('@') ? email.split('@')[1] : 'krmu.edu.in'
    let college = await prisma.college.findUnique({ where: { domain } })
    if (!college) {
      college = await prisma.college.create({ data: { name: 'K.R Mangalam University', domain } })
    }

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
      user = await prisma.user.update({
        where: { id: user.id },
        data: { lastLogin: new Date(), avatarUrl: avatarUrl || user.avatarUrl, name: name || user.name }
      })
    }

    const token = signToken({
      userId: user.id, email: user.email, role: user.role,
      name: user.name, collegeId: user.collegeId, classSectionId: user.classSectionId,
    })

    return success(res, {
      token,
      user: { id: user.id, name: user.name, email: user.email, role: user.role, avatarUrl: user.avatarUrl, rollNumber: user.rollNumber, classSectionId: user.classSectionId, subjects: user.subjects }
    })
  } catch (err: any) {
    return error(res, 'Login failed: ' + err.message, 500)
  }
}

export const getMe = async (req: Request, res: Response) => {
  try {
    const userId = (req as any).user.userId
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true, name: true, email: true, role: true, avatarUrl: true,
        rollNumber: true, subjects: true,
        classSection: { select: { id: true, name: true, section: true, branch: true, semester: true, uniqueCode: true } },
        college: { select: { name: true, logoUrl: true } }
      }
    })
    if (!user) return error(res, 'User not found', 404)
    return success(res, user)
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}

export const getUsers = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { role, search, classSectionId } = req.query
    const users = await prisma.user.findMany({
      where: {
        collegeId,
        ...(role && { role: role as any }),
        ...(classSectionId && { classSectionId: classSectionId as string }),
        ...(search && { OR: [{ name: { contains: search as string, mode: 'insensitive' as any } }, { email: { contains: search as string, mode: 'insensitive' as any } }] }),
        isActive: true,
      },
      select: { id: true, name: true, email: true, role: true, avatarUrl: true, rollNumber: true, subjects: true, createdAt: true, classSection: { select: { name: true, section: true, uniqueCode: true } } },
      orderBy: { name: 'asc' }
    })
    return success(res, users)
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}

export const updateSubjects = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { subjects } = req.body
    const user = await prisma.user.update({ where: { id: userId }, data: { subjects } })
    return success(res, { subjects: user.subjects }, 'Subjects updated')
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const getClasses = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const classes = await prisma.classSection.findMany({
      where: { collegeId, isActive: true },
      include: { _count: { select: { students: true } } },
      orderBy: [{ semester: 'asc' }, { branch: 'asc' }, { section: 'asc' }]
    })
    return success(res, classes)
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}

export const createClass = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { name, section, semester, branch, year } = req.body
    let uniqueCode = generateClassCode(branch, name, section, semester)
    let exists = await prisma.classSection.findUnique({ where: { uniqueCode } })
    while (exists) {
      uniqueCode = generateClassCode(branch, name, section, semester)
      exists = await prisma.classSection.findUnique({ where: { uniqueCode } })
    }
    const cls = await prisma.classSection.create({
      data: { collegeId, name, section, semester: parseInt(semester), branch, year: parseInt(year), uniqueCode }
    })
    return success(res, cls, 'Class created', 201)
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const deleteClass = async (req: Request, res: Response) => {
  try {
    const id = req.params.id as string
    await prisma.classSection.update({ where: { id }, data: { isActive: false } })
    return success(res, null, 'Class deleted')
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const joinClassByCode = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { code } = req.body
    const cls = await prisma.classSection.findUnique({ where: { uniqueCode: code.toUpperCase().trim() } })
    if (!cls) return error(res, 'Invalid class code. Please check and try again.', 404)
    if (!cls.isActive) return error(res, 'This class is no longer active.', 400)
    const user = await prisma.user.update({ where: { id: userId }, data: { classSectionId: cls.id }, include: { classSection: true } })
    return success(res, { user, class: cls }, 'Joined class successfully!')
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const selectClass = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { classSectionId } = req.body
    const user = await prisma.user.update({ where: { id: userId }, data: { classSectionId }, include: { classSection: true } })
    return success(res, user, 'Class selected')
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const assignClass = async (req: Request, res: Response) => {
  try {
    const { studentId, classSectionId } = req.body
    const user = await prisma.user.update({ where: { id: studentId }, data: { classSectionId } })
    return success(res, user, 'Class assigned')
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}
""")
print("auth.controller done!")

# Update auth routes
with open("src/routes/auth.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { azureLogin, getMe, getUsers, updateSubjects, getClasses, createClass, deleteClass, joinClassByCode, selectClass, assignClass } from '../controllers/auth.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'

const router = Router()

router.post('/azure', azureLogin)
router.get('/me', authenticate, getMe)
router.get('/users', authenticate, getUsers)
router.patch('/subjects', authenticate, updateSubjects)
router.get('/classes', authenticate, getClasses)
router.post('/classes', authenticate, authorize('teacher', 'admin'), createClass)
router.delete('/classes/:id', authenticate, authorize('teacher', 'admin'), deleteClass)
router.post('/join-class', authenticate, authorize('student'), joinClassByCode)
router.patch('/select-class', authenticate, selectClass)
router.patch('/assign-class', authenticate, authorize('teacher', 'admin'), assignClass)

export default router
""")

# Update notification routes
with open("src/routes/notification.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { getNotifications, markRead, markAllRead, deleteNotification, sendBulkNotification } from '../controllers/notification.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'

const router = Router()

router.get('/', authenticate, getNotifications)
router.patch('/read-all', authenticate, markAllRead)
router.patch('/:id/read', authenticate, markRead)
router.delete('/:id', authenticate, deleteNotification)
router.post('/send', authenticate, authorize('teacher', 'admin'), sendBulkNotification)

export default router
""")
print("Routes done!")

print("\n=== BACKEND DONE ===")