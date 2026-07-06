import os

# Create all directories
dirs = [
    "src/config",
    "src/routes",
    "src/controllers",
    "src/middleware",
    "src/services",
    "src/utils",
    "uploads",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)
print("Directories created!")

# ── tsconfig.json ──────────────────────────────────────────
with open("tsconfig.json", "w", encoding="utf-8") as f:
    f.write("""{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": false,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
""")
print("tsconfig done!")

# ── package.json scripts update ────────────────────────────
with open("package.json", "r", encoding="utf-8") as f:
    import json
    pkg = json.load(f)

pkg["scripts"] = {
    "dev": "nodemon --exec ts-node src/app.ts",
    "build": "tsc",
    "start": "node dist/app.js",
    "prisma:migrate": "prisma migrate dev",
    "prisma:generate": "prisma generate",
    "prisma:studio": "prisma studio"
}
pkg["main"] = "dist/app.js"

with open("package.json", "w", encoding="utf-8") as f:
    json.dump(pkg, f, indent=2)
print("package.json updated!")

# ── .env ───────────────────────────────────────────────────
with open(".env", "w", encoding="utf-8") as f:
    f.write("""# Server
PORT=5000
NODE_ENV=development
FRONTEND_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/aiqpg_db

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRES_IN=7d

# Azure AD
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id

# File Upload (local for now, S3 later)
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
""")
print(".env done!")

# ── prisma/schema.prisma ───────────────────────────────────
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
}

model User {
  id           String   @id @default(uuid())
  collegeId    String
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
  isActive     Boolean  @default(true)
  lastLogin    DateTime?
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  college      College      @relation(fields: [collegeId], references: [id])
  tasks        Task[]       @relation("TaskCreator")
  submissions  Submission[]
  materials    Material[]
  complaints   Complaint[]  @relation("ComplaintRaiser")
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
  status      MaterialStatus @default(uploaded)
  isPyq       Boolean        @default(false)
  year        Int?
  createdAt   DateTime       @default(now())

  college   College  @relation(fields: [collegeId], references: [id])
  subject   Subject? @relation(fields: [subjectId], references: [id])
  uploader  User     @relation(fields: [uploadedBy], references: [id])
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
  id           String     @id @default(uuid())
  collegeId    String
  subjectId    String?
  createdBy    String
  title        String
  description  String?
  taskType     TaskType
  deadline     DateTime?
  startTime    DateTime?
  maxMarks     Int        @default(10)
  instructions String?
  attachmentUrl String?
  allowLate    Boolean    @default(false)
  latePenalty  Int        @default(0)
  status       TaskStatus @default(active)
  createdAt    DateTime   @default(now())
  updatedAt    DateTime   @updatedAt

  college     College      @relation(fields: [collegeId], references: [id])
  subject     Subject?     @relation(fields: [subjectId], references: [id])
  creator     User         @relation("TaskCreator", fields: [createdBy], references: [id])
  submissions Submission[]
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
  id          String         @id @default(uuid())
  taskId      String
  studentId   String
  fileUrl     String?
  fileName    String?
  textAnswer  String?
  status      SubmitStatus   @default(submitted)
  marksAwarded Int?
  feedback    String?
  gradedBy    String?
  gradedAt    DateTime?
  submittedAt DateTime       @default(now())

  task    Task   @relation(fields: [taskId], references: [id])
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
  id          String          @id @default(uuid())
  raisedBy    String
  subject     String
  category    String?
  status      ComplaintStatus @default(open)
  priority    String          @default("normal")
  resolvedAt  DateTime?
  createdAt   DateTime        @default(now())
  updatedAt   DateTime        @updatedAt

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
  message     String
  createdAt   DateTime @default(now())

  complaint Complaint @relation(fields: [complaintId], references: [id])
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
print("Prisma schema done!")

# ── src/config/db.ts ───────────────────────────────────────
with open("src/config/db.ts", "w", encoding="utf-8") as f:
    f.write("""import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient({
  log: process.env.NODE_ENV === 'development' ? ['query', 'error'] : ['error'],
})

export default prisma
""")
print("db.ts done!")

# ── src/utils/jwt.ts ───────────────────────────────────────
with open("src/utils/jwt.ts", "w", encoding="utf-8") as f:
    f.write("""import jwt from 'jsonwebtoken'

const SECRET = process.env.JWT_SECRET || 'fallback-secret'

export function signToken(payload: object): string {
  return jwt.sign(payload, SECRET, { expiresIn: process.env.JWT_EXPIRES_IN || '7d' })
}

export function verifyToken(token: string): any {
  return jwt.verify(token, SECRET)
}

export function getRoleFromEmail(email: string): string {
  if (!email) return 'unknown'

  // Special test accounts
  const SPECIAL: Record<string, string> = {
    'akumarjaan123@gmail.com': 'teacher',
  }
  if (SPECIAL[email]) return SPECIAL[email]

  const prefix = email.split('@')[0]
  const domain = email.split('@')[1]

  if (domain !== 'krmu.edu.in') return 'unknown'
  if (/^[0-9]/.test(prefix)) return 'student'
  if (/^[a-zA-Z]/.test(prefix)) return 'teacher'
  return 'unknown'
}
""")
print("jwt.ts done!")

# ── src/utils/response.ts ──────────────────────────────────
with open("src/utils/response.ts", "w", encoding="utf-8") as f:
    f.write("""import { Response } from 'express'

export const success = (res: Response, data: any, message = 'Success', status = 200) => {
  return res.status(status).json({ success: true, message, data })
}

export const error = (res: Response, message = 'Error', status = 500, details?: any) => {
  return res.status(status).json({ success: false, message, ...(details && { details }) })
}
""")
print("response.ts done!")

# ── src/middleware/auth.middleware.ts ──────────────────────
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
      return error(res, 'Access denied — insufficient permissions', 403)
    }
    next()
  }
}
""")
print("auth.middleware.ts done!")

# ── src/middleware/upload.middleware.ts ────────────────────
with open("src/middleware/upload.middleware.ts", "w", encoding="utf-8") as f:
    f.write("""import multer from 'multer'
import path from 'path'
import fs from 'fs'

// Ensure uploads folder exists
const uploadDir = process.env.UPLOAD_DIR || 'uploads'
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true })

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const folder = path.join(uploadDir, (req as any).user?.collegeId || 'general')
    if (!fs.existsSync(folder)) fs.mkdirSync(folder, { recursive: true })
    cb(null, folder)
  },
  filename: (req, file, cb) => {
    const unique = Date.now() + '-' + Math.round(Math.random() * 1e9)
    const ext = path.extname(file.originalname)
    cb(null, unique + ext)
  }
})

const fileFilter = (req: any, file: any, cb: any) => {
  const allowed = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.zip']
  const ext = path.extname(file.originalname).toLowerCase()
  if (allowed.includes(ext)) cb(null, true)
  else cb(new Error('File type not allowed'), false)
}

export const upload = multer({
  storage,
  fileFilter,
  limits: { fileSize: parseInt(process.env.MAX_FILE_SIZE || '10485760') }
})
""")
print("upload.middleware.ts done!")

# ── src/middleware/error.middleware.ts ─────────────────────
with open("src/middleware/error.middleware.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response, NextFunction } from 'express'

export const errorHandler = (err: any, req: Request, res: Response, next: NextFunction) => {
  console.error('Error:', err.message)
  const status = err.status || err.statusCode || 500
  res.status(status).json({
    success: false,
    message: err.message || 'Internal server error',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  })
}
""")
print("error.middleware.ts done!")

# ── src/controllers/auth.controller.ts ────────────────────
with open("src/controllers/auth.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { signToken, getRoleFromEmail } from '../utils/jwt'
import { success, error } from '../utils/response'

// POST /api/v1/auth/azure
// Called from Next.js after Azure AD login
export const azureLogin = async (req: Request, res: Response) => {
  try {
    const { email, name, azureOid, avatarUrl } = req.body

    if (!email || !azureOid) {
      return error(res, 'Email and Azure OID required', 400)
    }

    const role = getRoleFromEmail(email)
    if (role === 'unknown') {
      return error(res, 'Access denied. Only KRMU accounts allowed.', 403)
    }

    // Find or create college from email domain
    const domain = email.includes('@') ? email.split('@')[1] : 'krmu.edu.in'
    let college = await prisma.college.findUnique({ where: { domain } })
    if (!college) {
      college = await prisma.college.create({
        data: { name: 'K.R Mangalam University', domain }
      })
    }

    // Find or create user
    let user = await prisma.user.findUnique({ where: { email } })
    if (!user) {
      user = await prisma.user.create({
        data: {
          collegeId: college.id,
          name: name || email.split('@')[0],
          email,
          role: role as any,
          azureOid,
          avatarUrl: avatarUrl || null,
        }
      })
    } else {
      user = await prisma.user.update({
        where: { id: user.id },
        data: { lastLogin: new Date(), avatarUrl: avatarUrl || user.avatarUrl }
      })
    }

    // Generate JWT
    const token = signToken({
      userId: user.id,
      email: user.email,
      role: user.role,
      name: user.name,
      collegeId: user.collegeId,
    })

    return success(res, { token, user: { id: user.id, name: user.name, email: user.email, role: user.role, avatarUrl: user.avatarUrl } })
  } catch (err: any) {
    console.error('Azure login error:', err)
    return error(res, 'Login failed', 500)
  }
}

// GET /api/v1/auth/me
export const getMe = async (req: Request, res: Response) => {
  try {
    const userId = (req as any).user.userId
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { id: true, name: true, email: true, role: true, avatarUrl: true, department: true, rollNumber: true, college: { select: { name: true, logoUrl: true } } }
    })
    if (!user) return error(res, 'User not found', 404)
    return success(res, user)
  } catch (err) {
    return error(res, 'Failed to get user', 500)
  }
}

// GET /api/v1/auth/users (teacher: list students, admin: all users)
export const getUsers = async (req: Request, res: Response) => {
  try {
    const { collegeId, role: myRole } = (req as any).user
    const { role, search } = req.query

    const users = await prisma.user.findMany({
      where: {
        collegeId,
        ...(role && { role: role as any }),
        ...(search && {
          OR: [
            { name: { contains: search as string, mode: 'insensitive' } },
            { email: { contains: search as string, mode: 'insensitive' } },
          ]
        }),
        isActive: true,
      },
      select: { id: true, name: true, email: true, role: true, avatarUrl: true, rollNumber: true, department: true, createdAt: true },
      orderBy: { createdAt: 'desc' }
    })

    return success(res, users)
  } catch (err) {
    return error(res, 'Failed to get users', 500)
  }
}
""")
print("auth.controller.ts done!")

# ── src/controllers/material.controller.ts ────────────────
with open("src/controllers/material.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'
import path from 'path'
import fs from 'fs'

// POST /api/v1/materials/upload
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
        fileType: fileType || 'other',
        fileSizeKb: Math.round(file.size / 1024),
        status: 'ready',
        isPyq: isPyq === 'true',
        year: year ? parseInt(year) : null,
      }
    })

    return success(res, material, 'Material uploaded successfully', 201)
  } catch (err: any) {
    return error(res, 'Upload failed: ' + err.message, 500)
  }
}

// GET /api/v1/materials
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
        ...(search && {
          OR: [
            { title: { contains: search as string, mode: 'insensitive' } },
          ]
        })
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

// GET /api/v1/materials/:id/download
export const downloadMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const material = await prisma.material.findFirst({
      where: { id: req.params.id, collegeId }
    })

    if (!material) return error(res, 'Material not found', 404)

    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return error(res, 'File not found on server', 404)

    res.download(filePath, material.fileName)
  } catch (err) {
    return error(res, 'Download failed', 500)
  }
}

// DELETE /api/v1/materials/:id
export const deleteMaterial = async (req: Request, res: Response) => {
  try {
    const { collegeId, userId } = (req as any).user
    const material = await prisma.material.findFirst({
      where: { id: req.params.id, collegeId }
    })
    if (!material) return error(res, 'Material not found', 404)

    // Delete file
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath)

    await prisma.material.delete({ where: { id: req.params.id } })
    return success(res, null, 'Material deleted')
  } catch (err) {
    return error(res, 'Delete failed', 500)
  }
}
""")
print("material.controller.ts done!")

# ── src/controllers/task.controller.ts ────────────────────
with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

// POST /api/v1/tasks
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
        taskType,
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

    // Notify all students in college
    const students = await prisma.user.findMany({
      where: { collegeId, role: 'student', isActive: true },
      select: { id: true }
    })

    await prisma.notification.createMany({
      data: students.map(s => ({
        userId: s.id,
        title: 'New ' + taskType + ' Assigned',
        body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleDateString('en-IN') : ''),
        type: 'task',
        refId: task.id,
      }))
    })

    return success(res, task, 'Task created successfully', 201)
  } catch (err: any) {
    return error(res, 'Failed to create task: ' + err.message, 500)
  }
}

// GET /api/v1/tasks
export const getTasks = async (req: Request, res: Response) => {
  try {
    const { collegeId, role, userId } = (req as any).user
    const { status, type, subjectId } = req.query

    const tasks = await prisma.task.findMany({
      where: {
        collegeId,
        ...(status && { status: status as any }),
        ...(type && { taskType: type as any }),
        ...(subjectId && { subjectId: subjectId as string }),
        // Students see only active tasks
        ...(role === 'student' && { status: 'active' }),
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

// GET /api/v1/tasks/:id
export const getTask = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const task = await prisma.task.findFirst({
      where: { id: req.params.id, collegeId },
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

// PATCH /api/v1/tasks/:id/status
export const updateTaskStatus = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const { status } = req.body

    const task = await prisma.task.update({
      where: { id: req.params.id },
      data: { status }
    })
    return success(res, task, 'Task status updated')
  } catch (err) {
    return error(res, 'Failed to update task', 500)
  }
}

// DELETE /api/v1/tasks/:id
export const deleteTask = async (req: Request, res: Response) => {
  try {
    await prisma.task.delete({ where: { id: req.params.id } })
    return success(res, null, 'Task deleted')
  } catch (err) {
    return error(res, 'Failed to delete task', 500)
  }
}
""")
print("task.controller.ts done!")

# ── src/controllers/submission.controller.ts ──────────────
with open("src/controllers/submission.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

// POST /api/v1/submissions
export const createSubmission = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { taskId, textAnswer } = req.body
    const file = req.file

    // Check task exists and is active
    const task = await prisma.task.findFirst({ where: { id: taskId, collegeId, status: 'active' } })
    if (!task) return error(res, 'Task not found or closed', 404)

    // Check if already submitted
    const existing = await prisma.submission.findUnique({
      where: { taskId_studentId: { taskId, studentId: userId } }
    })
    if (existing) return error(res, 'Already submitted', 400)

    // Check if late
    const isLate = task.deadline && new Date() > task.deadline
    if (isLate && !task.allowLate) return error(res, 'Submission deadline has passed', 400)

    const submission = await prisma.submission.create({
      data: {
        taskId,
        studentId: userId,
        textAnswer: textAnswer || null,
        fileUrl: file ? '/uploads/' + collegeId + '/' + file.filename : null,
        fileName: file?.originalname || null,
        status: isLate ? 'late' : 'submitted',
      }
    })

    // Notify teacher
    const teacher = await prisma.user.findFirst({ where: { id: task.createdBy } })
    if (teacher) {
      const student = await prisma.user.findUnique({ where: { id: userId }, select: { name: true } })
      await prisma.notification.create({
        data: {
          userId: teacher.id,
          title: 'New Submission',
          body: (student?.name || 'A student') + ' submitted ' + task.title,
          type: 'task',
          refId: taskId,
        }
      })
    }

    return success(res, submission, 'Submitted successfully', 201)
  } catch (err: any) {
    return error(res, 'Submission failed: ' + err.message, 500)
  }
}

// GET /api/v1/submissions?taskId=xxx (teacher sees all, student sees own)
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

// PATCH /api/v1/submissions/:id/grade (teacher only)
export const gradeSubmission = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { marks, feedback } = req.body

    const submission = await prisma.submission.update({
      where: { id: req.params.id },
      data: {
        marksAwarded: parseInt(marks),
        feedback,
        gradedBy: userId,
        gradedAt: new Date(),
        status: 'graded',
      },
      include: { task: { select: { title: true, maxMarks: true } } }
    })

    // Notify student
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
print("submission.controller.ts done!")

# ── src/controllers/notification.controller.ts ────────────
with open("src/controllers/notification.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

// GET /api/v1/notifications
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

// PATCH /api/v1/notifications/:id/read
export const markRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.updateMany({
      where: { id: req.params.id, userId },
      data: { isRead: true }
    })
    return success(res, null, 'Marked as read')
  } catch (err) {
    return error(res, 'Failed to mark read', 500)
  }
}

// PATCH /api/v1/notifications/read-all
export const markAllRead = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    await prisma.notification.updateMany({
      where: { userId, isRead: false },
      data: { isRead: true }
    })
    return success(res, null, 'All marked as read')
  } catch (err) {
    return error(res, 'Failed to mark all read', 500)
  }
}

// POST /api/v1/notifications/send (teacher sends bulk to students)
export const sendBulkNotification = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { title, body, type } = req.body

    const students = await prisma.user.findMany({
      where: { collegeId, role: 'student', isActive: true },
      select: { id: true }
    })

    await prisma.notification.createMany({
      data: students.map(s => ({ userId: s.id, title, body, type: type || 'announcement' }))
    })

    return success(res, { sent: students.length }, 'Notification sent to ' + students.length + ' students')
  } catch (err) {
    return error(res, 'Failed to send notification', 500)
  }
}
""")
print("notification.controller.ts done!")

# ── src/controllers/complaint.controller.ts ───────────────
with open("src/controllers/complaint.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

// POST /api/v1/complaints
export const createComplaint = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { subject, category, description } = req.body

    const complaint = await prisma.complaint.create({
      data: {
        raisedBy: userId,
        subject,
        category,
        messages: {
          create: { sentBy: userId, message: description }
        }
      },
      include: { messages: true }
    })

    // Notify teachers
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
    return error(res, 'Failed to raise complaint: ' + err.message, 500)
  }
}

// GET /api/v1/complaints
export const getComplaints = async (req: Request, res: Response) => {
  try {
    const { userId, role } = (req as any).user
    const complaints = await prisma.complaint.findMany({
      where: role === 'student' ? { raisedBy: userId } : {},
      include: {
        raiser: { select: { name: true, email: true, rollNumber: true } },
        messages: { include: { }, orderBy: { createdAt: 'asc' } }
      },
      orderBy: { createdAt: 'desc' }
    })
    return success(res, complaints)
  } catch (err) {
    return error(res, 'Failed to get complaints', 500)
  }
}

// POST /api/v1/complaints/:id/reply
export const replyComplaint = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const { message } = req.body

    const msg = await prisma.complaintMessage.create({
      data: { complaintId: req.params.id, sentBy: userId, message }
    })

    await prisma.complaint.update({
      where: { id: req.params.id },
      data: { status: 'in_progress' }
    })

    // Notify the other party
    const complaint = await prisma.complaint.findUnique({ where: { id: req.params.id } })
    if (complaint && complaint.raisedBy !== userId) {
      await prisma.notification.create({
        data: {
          userId: complaint.raisedBy,
          title: 'Complaint Reply',
          body: 'Your complaint has a new reply: ' + message.slice(0, 50),
          type: 'complaint',
          refId: req.params.id,
        }
      })
    }

    return success(res, msg, 'Reply sent')
  } catch (err) {
    return error(res, 'Failed to reply', 500)
  }
}

// PATCH /api/v1/complaints/:id/status
export const updateComplaintStatus = async (req: Request, res: Response) => {
  try {
    const { status } = req.body
    const complaint = await prisma.complaint.update({
      where: { id: req.params.id },
      data: { status, ...(status === 'resolved' && { resolvedAt: new Date() }) }
    })

    // Notify student
    await prisma.notification.create({
      data: {
        userId: complaint.raisedBy,
        title: 'Complaint ' + status.replace('_', ' '),
        body: 'Your complaint "' + complaint.subject + '" has been ' + status.replace('_', ' '),
        type: 'complaint',
        refId: complaint.id,
      }
    })

    return success(res, complaint, 'Status updated')
  } catch (err) {
    return error(res, 'Failed to update status', 500)
  }
}
""")
print("complaint.controller.ts done!")

# ── src/routes/auth.routes.ts ──────────────────────────────
with open("src/routes/auth.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { azureLogin, getMe, getUsers } from '../controllers/auth.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'

const router = Router()

router.post('/azure', azureLogin)
router.get('/me', authenticate, getMe)
router.get('/users', authenticate, authorize('teacher', 'admin', 'hod'), getUsers)

export default router
""")

with open("src/routes/material.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { uploadMaterial, getMaterials, downloadMaterial, deleteMaterial } from '../controllers/material.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'

const router = Router()

router.post('/upload', authenticate, authorize('teacher', 'admin'), upload.single('file'), uploadMaterial)
router.get('/', authenticate, getMaterials)
router.get('/:id/download', authenticate, downloadMaterial)
router.delete('/:id', authenticate, authorize('teacher', 'admin'), deleteMaterial)

export default router
""")

with open("src/routes/task.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { createTask, getTasks, getTask, updateTaskStatus, deleteTask } from '../controllers/task.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'

const router = Router()

router.post('/', authenticate, authorize('teacher', 'admin'), upload.single('attachment'), createTask)
router.get('/', authenticate, getTasks)
router.get('/:id', authenticate, getTask)
router.patch('/:id/status', authenticate, authorize('teacher', 'admin'), updateTaskStatus)
router.delete('/:id', authenticate, authorize('teacher', 'admin'), deleteTask)

export default router
""")

with open("src/routes/submission.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { createSubmission, getSubmissions, gradeSubmission } from '../controllers/submission.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'

const router = Router()

router.post('/', authenticate, authorize('student'), upload.single('file'), createSubmission)
router.get('/', authenticate, getSubmissions)
router.patch('/:id/grade', authenticate, authorize('teacher', 'admin'), gradeSubmission)

export default router
""")

with open("src/routes/notification.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { getNotifications, markRead, markAllRead, sendBulkNotification } from '../controllers/notification.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'

const router = Router()

router.get('/', authenticate, getNotifications)
router.patch('/read-all', authenticate, markAllRead)
router.patch('/:id/read', authenticate, markRead)
router.post('/send', authenticate, authorize('teacher', 'admin'), sendBulkNotification)

export default router
""")

with open("src/routes/complaint.routes.ts", "w", encoding="utf-8") as f:
    f.write("""import { Router } from 'express'
import { createComplaint, getComplaints, replyComplaint, updateComplaintStatus } from '../controllers/complaint.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'

const router = Router()

router.post('/', authenticate, createComplaint)
router.get('/', authenticate, getComplaints)
router.post('/:id/reply', authenticate, replyComplaint)
router.patch('/:id/status', authenticate, authorize('teacher', 'admin'), updateComplaintStatus)

export default router
""")
print("All routes done!")

# ── src/app.ts ─────────────────────────────────────────────
with open("src/app.ts", "w", encoding="utf-8") as f:
    f.write("""import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import morgan from 'morgan'
import path from 'path'
import { rateLimit } from 'express-rate-limit'
import dotenv from 'dotenv'
dotenv.config()

import authRoutes         from './routes/auth.routes'
import materialRoutes     from './routes/material.routes'
import taskRoutes         from './routes/task.routes'
import submissionRoutes   from './routes/submission.routes'
import notificationRoutes from './routes/notification.routes'
import complaintRoutes    from './routes/complaint.routes'
import { errorHandler }   from './middleware/error.middleware'

const app = express()
const PORT = process.env.PORT || 5000

// ── Security ─────────────────────────────────────────────
app.use(helmet({ crossOriginResourcePolicy: { policy: 'cross-origin' } }))
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
}))

// ── Rate Limiting ─────────────────────────────────────────
app.use(rateLimit({ windowMs: 15 * 60 * 1000, max: 200, message: 'Too many requests' }))

// ── Parsing ───────────────────────────────────────────────
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true }))
app.use(morgan('dev'))

// ── Static files (uploaded files) ─────────────────────────
app.use('/uploads', express.static(path.join(process.cwd(), 'uploads')))

// ── Health check ──────────────────────────────────────────
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() })
})

// ── API Routes ────────────────────────────────────────────
app.use('/api/v1/auth',          authRoutes)
app.use('/api/v1/materials',     materialRoutes)
app.use('/api/v1/tasks',         taskRoutes)
app.use('/api/v1/submissions',   submissionRoutes)
app.use('/api/v1/notifications', notificationRoutes)
app.use('/api/v1/complaints',    complaintRoutes)

// ── Error Handler ─────────────────────────────────────────
app.use(errorHandler)

// ── Start ─────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log('Backend running on http://localhost:' + PORT)
  console.log('Frontend URL:', process.env.FRONTEND_URL)
})

export default app
""")
print("app.ts done!")

# ── nodemon.json ───────────────────────────────────────────
with open("nodemon.json", "w", encoding="utf-8") as f:
    f.write("""{
  "watch": ["src"],
  "ext": "ts,json",
  "ignore": ["src/**/*.spec.ts"],
  "exec": "ts-node src/app.ts"
}
""")
print("nodemon.json done!")

print("\\n" + "="*50)
print("BACKEND SETUP COMPLETE!")
print("="*50)
print("Next steps:")
print("1. Setup PostgreSQL database")
print("2. Update .env with real DATABASE_URL")
print("3. Run: npx prisma migrate dev")
print("4. Run: npm run dev")