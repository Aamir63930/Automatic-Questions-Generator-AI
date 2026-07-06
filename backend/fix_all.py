import os

# ── 1. Prisma Schema Update - Class/Section add karo ──────
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
  themeColor String   @default("#4f7fff")
  isActive   Boolean  @default(true)
  createdAt  DateTime @default(now())

  users      User[]
  subjects   Subject[]
  tasks      Task[]
  materials  Material[]
  papers     Paper[]
  classes    ClassSection[]
}

model ClassSection {
  id        String   @id @default(uuid())
  collegeId String
  name      String
  section   String
  semester  Int
  branch    String
  year      Int
  isActive  Boolean  @default(true)
  createdAt DateTime @default(now())

  college  College  @relation(fields: [collegeId], references: [id])
  students User[]   @relation("StudentClass")
  tasks    Task[]   @relation("TaskClass")
}

model User {
  id           String   @id @default(uuid())
  collegeId    String
  classSectionId String?
  name         String
  email        String   @unique
  role         Role
  azureOid     String?  @unique
  avatarUrl    String?
  department   String?
  employeeId   String?
  rollNumber   String?
  semester     Int?
  branch       String?
  section      String?
  isActive     Boolean  @default(true)
  lastLogin    DateTime?
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

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

model Subject {
  id        String   @id @default(uuid())
  collegeId String
  name      String
  code      String
  semester  Int?
  branch    String?
  isActive  Boolean  @default(true)
  createdAt DateTime @default(now())

  college   College    @relation(fields: [collegeId], references: [id])
  tasks     Task[]
  materials Material[]
}

model Material {
  id          String         @id @default(uuid())
  collegeId   String
  subjectId   String?
  uploadedBy  String
  title       String
  fileName    String
  fileUrl     String
  fileType    MaterialType
  fileSizeKb  Int?
  status      MaterialStatus @default(ready)
  isPyq       Boolean        @default(false)
  year        Int?
  createdAt   DateTime       @default(now())

  college  College  @relation(fields: [collegeId], references: [id])
  subject  Subject? @relation(fields: [subjectId], references: [id])
  uploader User     @relation(fields: [uploadedBy], references: [id])
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
  subjectId      String?
  classSectionId String?
  createdBy      String
  title          String
  description    String?
  taskType       TaskType
  deadline       DateTime?
  startTime      DateTime?
  maxMarks       Int        @default(10)
  instructions   String?
  attachmentUrl  String?
  allowLate      Boolean    @default(false)
  latePenalty    Int        @default(0)
  status         TaskStatus @default(active)
  createdAt      DateTime   @default(now())
  updatedAt      DateTime   @updatedAt

  college      College       @relation(fields: [collegeId], references: [id])
  subject      Subject?      @relation(fields: [subjectId], references: [id])
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

  task    Task   @relation(fields: [taskId], references: [id], onDelete: Cascade)
  student User   @relation(fields: [studentId], references: [id])

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
print("Schema updated!")

# ── 2. Fix Auth Controller ─────────────────────────────────
with open("src/controllers/auth.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { signToken, getRoleFromEmail } from '../utils/jwt'
import { success, error } from '../utils/response'

export const azureLogin = async (req: Request, res: Response) => {
  try {
    const { email, name, azureOid, avatarUrl } = req.body
    if (!email) return error(res, 'Email required', 400)

    const role = getRoleFromEmail(email)
    if (role === 'unknown') return error(res, 'Access denied. Only KRMU accounts allowed.', 403)

    const domain = email.includes('@') ? email.split('@')[1] : 'krmu.edu.in'
    let college = await prisma.college.findUnique({ where: { domain } })
    if (!college) {
      college = await prisma.college.create({
        data: { name: 'K.R Mangalam University', domain }
      })
    }

    let user = await prisma.user.findUnique({ where: { email } })
    if (!user) {
      // Extract roll number for students
      const prefix = email.split('@')[0]
      const isStudent = /^[0-9]/.test(prefix)
      user = await prisma.user.create({
        data: {
          collegeId: college.id,
          name: name || prefix,
          email,
          role: role as any,
          azureOid: azureOid || null,
          avatarUrl: avatarUrl || null,
          rollNumber: isStudent ? prefix : null,
        }
      })
    } else {
      user = await prisma.user.update({
        where: { id: user.id },
        data: {
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
      collegeId: user.collegeId,
      classSectionId: user.classSectionId,
    })

    return success(res, {
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role,
        avatarUrl: user.avatarUrl,
        rollNumber: user.rollNumber,
        classSectionId: user.classSectionId,
      }
    })
  } catch (err: any) {
    console.error('Login error:', err)
    return error(res, 'Login failed: ' + err.message, 500)
  }
}

export const getMe = async (req: Request, res: Response) => {
  try {
    const userId = (req as any).user.userId
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true, name: true, email: true, role: true,
        avatarUrl: true, department: true, rollNumber: true,
        semester: true, branch: true, section: true,
        classSection: { select: { name: true, section: true, branch: true, semester: true } },
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
        ...(search && {
          OR: [
            { name: { contains: search as string, mode: 'insensitive' as any } },
            { email: { contains: search as string, mode: 'insensitive' as any } },
          ]
        }),
        isActive: true,
      },
      select: {
        id: true, name: true, email: true, role: true,
        avatarUrl: true, rollNumber: true, department: true,
        semester: true, branch: true, section: true, createdAt: true,
        classSection: { select: { name: true, section: true } }
      },
      orderBy: { name: 'asc' }
    })
    return success(res, users)
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}

// GET /api/v1/auth/classes
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

// POST /api/v1/auth/classes
export const createClass = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { name, section, semester, branch, year } = req.body
    const cls = await prisma.classSection.create({
      data: { collegeId, name, section, semester: parseInt(semester), branch, year: parseInt(year) }
    })
    return success(res, cls, 'Class created', 201)
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

// PATCH /api/v1/auth/assign-class
export const assignClass = async (req: Request, res: Response) => {
  try {
    const { studentId, classSectionId } = req.body
    const user = await prisma.user.update({
      where: { id: studentId },
      data: { classSectionId }
    })
    return success(res, user, 'Class assigned')
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

// PATCH /api/v1/auth/select-class (student selects own class)
export const selectClass = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { classSectionId } = req.body
    const user = await prisma.user.update({
      where: { id: userId },
      data: { classSectionId },
      include: { classSection: true }
    })
    return success(res, user, 'Class selected')
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}
""")
print("auth.controller done!")

# ── 3. Fix Task Controller ─────────────────────────────────
with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createTask = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const {
      title, description, taskType, subjectId,
      classSectionId, deadline, startTime,
      maxMarks, instructions, allowLate, latePenalty
    } = req.body

    const task = await prisma.task.create({
      data: {
        collegeId,
        createdBy: userId,
        title,
        description: description || null,
        taskType: taskType as any,
        subjectId: subjectId || null,
        classSectionId: classSectionId || null,
        deadline: deadline ? new Date(deadline) : null,
        startTime: startTime ? new Date(startTime) : null,
        maxMarks: parseInt(maxMarks) || 10,
        instructions: instructions || null,
        allowLate: allowLate === 'true' || allowLate === true,
        latePenalty: parseInt(latePenalty) || 0,
        attachmentUrl: req.file
          ? '/uploads/' + collegeId + '/' + req.file.filename
          : null,
      },
      include: {
        creator: { select: { name: true } },
        subject: { select: { name: true } },
        classSection: { select: { name: true, section: true } }
      }
    })

    // Notify students - by class if specified, else all students
    const studentFilter: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId) studentFilter.classSectionId = classSectionId

    const students = await prisma.user.findMany({
      where: studentFilter,
      select: { id: true }
    })

    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: 'New ' + taskType.replace('_', ' ') + ' Assigned',
          body: title + (deadline
            ? ' — Due: ' + new Date(deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
            : ''),
          type: 'task',
          refId: task.id,
        }))
      })
    }

    return success(res, task, 'Task created successfully', 201)
  } catch (err: any) {
    console.error('Create task error:', err)
    return error(res, 'Failed to create task: ' + err.message, 500)
  }
}

export const getTasks = async (req: Request, res: Response) => {
  try {
    const { collegeId, role, userId, classSectionId } = (req as any).user
    const { status, type, subjectId, classId } = req.query

    let whereClause: any = {
      collegeId,
      ...(status && role !== 'student' && { status: status as any }),
      ...(type && { taskType: type as any }),
      ...(subjectId && { subjectId: subjectId as string }),
    }

    if (role === 'student') {
      whereClause.status = 'active'
      // Show tasks for student's class OR tasks for all (no class specified)
      if (classSectionId) {
        whereClause.OR = [
          { classSectionId: classSectionId },
          { classSectionId: null },
        ]
      }
    }

    if (role === 'teacher' && classId) {
      whereClause.classSectionId = classId as string
    }

    const tasks = await prisma.task.findMany({
      where: whereClause,
      include: {
        creator: { select: { name: true, email: true } },
        subject: { select: { name: true, code: true } },
        classSection: { select: { name: true, section: true, branch: true } },
        _count: { select: { submissions: true } }
      },
      orderBy: { createdAt: 'desc' }
    })

    return success(res, tasks)
  } catch (err: any) {
    console.error('Get tasks error:', err)
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
        classSection: { select: { name: true, section: true } },
        submissions: {
          include: {
            student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } }
          }
        }
      }
    })
    if (!task) return error(res, 'Task not found', 404)
    return success(res, task)
  } catch (err) {
    return error(res, 'Failed', 500)
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
    return error(res, 'Failed', 500)
  }
}

export const deleteTask = async (req: Request, res: Response) => {
  try {
    const id = req.params.id as string
    await prisma.task.delete({ where: { id } })
    return success(res, null, 'Task deleted')
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}
""")
print("task.controller done!")

# ── 4. Fix Complaint Controller ────────────────────────────
with open("src/controllers/complaint.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createComplaint = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { subject, category, description } = req.body

    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { name: true, role: true }
    })

    const complaint = await prisma.complaint.create({
      data: {
        raisedBy: userId,
        subject,
        category: category || 'General',
        messages: {
          create: {
            sentBy: userId,
            senderName: user?.name || 'Student',
            senderRole: user?.role || 'student',
            message: description
          }
        }
      },
      include: {
        raiser: { select: { name: true, email: true } },
        messages: true
      }
    })

    // Notify ALL teachers in college
    const teachers = await prisma.user.findMany({
      where: { collegeId, role: 'teacher', isActive: true },
      select: { id: true }
    })

    if (teachers.length > 0) {
      await prisma.notification.createMany({
        data: teachers.map(t => ({
          userId: t.id,
          title: 'New Complaint from ' + (user?.name || 'Student'),
          body: subject + ' — Category: ' + (category || 'General'),
          type: 'complaint',
          refId: complaint.id,
        }))
      })
    }

    return success(res, complaint, 'Complaint raised successfully', 201)
  } catch (err: any) {
    console.error('Complaint error:', err)
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
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}

export const replyComplaint = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    const { message } = req.body

    const sender = await prisma.user.findUnique({
      where: { id: userId },
      select: { name: true, role: true }
    })

    const msg = await prisma.complaintMessage.create({
      data: {
        complaintId: id,
        sentBy: userId,
        senderName: sender?.name || 'User',
        senderRole: sender?.role || 'student',
        message
      }
    })

    await prisma.complaint.update({
      where: { id },
      data: { status: 'in_progress', updatedAt: new Date() }
    })

    // Notify the other party
    const complaint = await prisma.complaint.findUnique({ where: { id } })
    if (complaint) {
      const notifyUserId = complaint.raisedBy === userId
        ? null // teacher replied - need to find teacher to notify student
        : complaint.raisedBy // student replied - notify raiser... wait

      // If teacher replied -> notify student (raiser)
      // If student replied -> notify teacher (but we don't know which teacher)
      if (sender?.role === 'teacher') {
        await prisma.notification.create({
          data: {
            userId: complaint.raisedBy,
            title: 'Complaint Reply from Teacher',
            body: message.slice(0, 80),
            type: 'complaint',
            refId: id,
          }
        })
      }
    }

    return success(res, msg, 'Reply sent')
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const updateComplaintStatus = async (req: Request, res: Response) => {
  try {
    const id = req.params.id as string
    const { status } = req.body
    const complaint = await prisma.complaint.update({
      where: { id },
      data: {
        status: status as any,
        ...(status === 'resolved' && { resolvedAt: new Date() })
      }
    })
    await prisma.notification.create({
      data: {
        userId: complaint.raisedBy,
        title: 'Complaint ' + status.replace('_', ' '),
        body: '"' + complaint.subject + '" status: ' + status.replace('_', ' '),
        type: 'complaint',
        refId: id,
      }
    })
    return success(res, complaint, 'Status updated')
  } catch (err) {
    return error(res, 'Failed', 500)
  }
}
""")
print("complaint.controller done!")

# ── 5. Update Auth Routes ──────────────────────────────────
with open("src/routes/auth.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import {
  azureLogin, getMe, getUsers,
  getClasses, createClass, assignClass, selectClass
} from '../controllers/auth.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'

const router = Router()

router.post('/azure', azureLogin)
router.get('/me', authenticate, getMe)
router.get('/users', authenticate, getUsers)
router.get('/classes', authenticate, getClasses)
router.post('/classes', authenticate, authorize('teacher', 'admin'), createClass)
router.patch('/assign-class', authenticate, authorize('teacher', 'admin'), assignClass)
router.patch('/select-class', authenticate, selectClass)

export default router
""")
print("auth.routes done!")

# ── 6. Update JWT middleware to include classSectionId ─────
with open("src/middleware/auth.middleware.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response, NextFunction } from 'express'
import { verifyToken } from '../utils/jwt'
import { error } from '../utils/response'

export const authenticate = (req: Request, res: Response, next: NextFunction) => {
  try {
    const authHeader = req.headers.authorization
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return error(res, 'No token provided', 401)
    }
    const token = authHeader.split(' ')[1]
    const decoded = verifyToken(token)
    ;(req as any).user = decoded
    next()
  } catch (err) {
    return error(res, 'Invalid or expired token', 401)
  }
}

export const authorize = (...roles: string[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = (req as any).user
    if (!user || !roles.includes(user.role)) {
      return error(res, 'Access denied', 403)
    }
    next()
  }
}
""")
print("auth.middleware done!")

print("\n" + "="*50)
print("ALL BACKEND FIXES DONE!")
print("="*50)