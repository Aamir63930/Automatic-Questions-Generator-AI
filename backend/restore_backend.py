import os

# ══════════════════════════════════════
# RESTORE: Remove cloudinary dependency
# Use simple multer disk storage
# ══════════════════════════════════════

# FIX 1: Upload middleware - back to simple disk
with open("src/middleware/upload.middleware.ts", "w", encoding="utf-8") as f:
    f.write("""import multer from 'multer'
import path from 'path'
import fs from 'fs'

const uploadDir = path.join(process.cwd(), 'uploads')
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true })

const storage = multer.diskStorage({
  destination: (req: any, file, cb) => {
    const dir = path.join(uploadDir, req.user?.collegeId || 'general')
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
    cb(null, dir)
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + '-' + Math.round(Math.random() * 1e9) + path.extname(file.originalname))
  }
})

export const upload = multer({
  storage,
  limits: { fileSize: 20 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowed = ['.pdf','.doc','.docx','.ppt','.pptx','.jpg','.jpeg','.png','.txt']
    if (allowed.includes(path.extname(file.originalname).toLowerCase())) cb(null, true)
    else cb(new Error('File type not allowed'))
  }
})
""")
print("Upload middleware restored!")

# FIX 2: app.ts - clean version
with open("src/app.ts", "r", encoding="utf-8") as f:
    app = f.read()

# Fix CORS properly
import re
# Remove any broken cors config
app = re.sub(
    r"app\.use\(cors\(\{[\s\S]*?\}\)\)\napp\.options.*?\n",
    "",
    app
)
app = re.sub(r"app\.use\(cors\(\)\)", "", app)
app = re.sub(r"app\.use\(cors\(.*?\)\)", "", app, flags=re.DOTALL)

# Add clean CORS after imports
if "cors({" not in app:
    # Find where app is defined
    app = app.replace(
        "const app = express()",
        """const app = express()

// CORS - allow all vercel deployments
app.use(require('cors')({
  origin: function(origin: any, callback: any) {
    // Allow all origins in production (Vercel, etc)
    callback(null, true)
  },
  credentials: true,
  methods: ['GET','POST','PUT','PATCH','DELETE','OPTIONS'],
  allowedHeaders: ['Content-Type','Authorization'],
}))
app.options('*', require('cors')())"""
    )

# Add health check if not present
if "'/health'" not in app:
    app = app.replace(
        "app.use('/api/v1'",
        """app.get('/health', (req: any, res: any) => res.json({ status: 'OK', time: new Date() }))
app.get('/', (req: any, res: any) => res.json({ message: 'AIQPG Backend Live!' }))

// Serve uploaded files
app.use('/uploads', require('express').static(require('path').join(process.cwd(), 'uploads')))

app.use('/api/v1'"""
    )

with open("src/app.ts", "w", encoding="utf-8") as f:
    f.write(app)
print("app.ts fixed!")

# FIX 3: Material controller - simple version
with open("src/controllers/material.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'
import path from 'path'
import fs from 'fs'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:5000'

async function getCollegeId(): Promise<string> {
  const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
  return college?.id || ''
}

export const uploadMaterial = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const collegeId = await getCollegeId()
    const file = req.file
    if (!file) return error(res, 'No file uploaded', 400)
    const { title, fileType, isPyq, year, subject, unit, examType, classSectionId } = req.body

    const fileUrl = '/uploads/' + collegeId + '/' + file.filename

    const material = await prisma.material.create({
      data: {
        collegeId, uploadedBy: userId,
        title: title || file.originalname.replace(/\\.[^.]+$/, ''),
        fileName: file.originalname,
        fileUrl,
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

    // Notify students
    let f: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId) f.classSectionId = classSectionId
    const students = await prisma.user.findMany({ where: f, select: { id: true } })
    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: isPyq === 'true' ? '📋 New PYQ Available' : '📚 New Study Material',
          body: (title || file.originalname) + (subject ? ' — ' + subject : '') + (unit ? ' (' + unit + ')' : ''),
          type: 'announcement', refId: material.id,
        }))
      }).catch(() => {})
    }

    return success(res, { ...material, viewUrl: BACKEND_URL + fileUrl }, 'Uploaded!', 201)
  } catch (err: any) {
    return error(res, 'Upload failed: ' + err.message, 500)
  }
}

export const getMaterials = async (req: Request, res: Response) => {
  try {
    const collegeId = await getCollegeId()
    const { isPyq, year, subject, unit, examType, search, classId } = req.query
    const where: any = { collegeId }
    if (isPyq !== undefined) where.isPyq = isPyq === 'true'
    if (year) where.year = parseInt(year as string)
    if (subject) where.subject = { contains: subject as string, mode: 'insensitive' }
    if (unit) where.unit = { contains: unit as string, mode: 'insensitive' }
    if (examType) where.examType = examType as string
    if (search) where.title = { contains: search as string, mode: 'insensitive' }
    if (classId && classId !== 'undefined' && classId !== '') {
      where.OR = [{ classSectionId: classId as string }, { classSectionId: null }]
    }
    const materials = await prisma.material.findMany({
      where,
      include: { uploader: { select: { name: true } }, classSection: { select: { name: true, section: true } } },
      orderBy: { createdAt: 'desc' }
    })
    // Add full URL to each material
    const withUrls = materials.map(m => ({
      ...m,
      viewUrl: m.fileUrl.startsWith('http') ? m.fileUrl : BACKEND_URL + m.fileUrl
    }))
    return success(res, withUrls)
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const downloadMaterial = async (req: Request, res: Response) => {
  try {
    const material = await prisma.material.findUnique({ where: { id: req.params.id as string } })
    if (!material) return error(res, 'Not found', 404)
    if (material.fileUrl.startsWith('http')) return res.redirect(material.fileUrl)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return error(res, 'File not found. Please re-upload.', 404)
    res.setHeader('Content-Disposition', 'attachment; filename="' + material.fileName + '"')
    res.setHeader('Access-Control-Allow-Origin', '*')
    return res.download(filePath, material.fileName)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const previewMaterial = async (req: Request, res: Response) => {
  try {
    const material = await prisma.material.findUnique({ where: { id: req.params.id as string } })
    if (!material) return error(res, 'Not found', 404)
    if (material.fileUrl.startsWith('http')) return res.redirect(material.fileUrl)
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return error(res, 'File not found. Please re-upload.', 404)
    const ext = path.extname(material.fileName).toLowerCase()
    const mimes: Record<string,string> = {'.pdf':'application/pdf','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.txt':'text/plain'}
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
    if (!material.fileUrl.startsWith('http')) {
      const fp = path.join(process.cwd(), material.fileUrl)
      if (fs.existsSync(fp)) fs.unlinkSync(fp)
    }
    await prisma.material.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch (err) { return error(res, 'Failed', 500) }
}
""")
print("Material controller done!")

# FIX 4: package.json - remove cloudinary if added
with open("package.json", "r", encoding="utf-8") as f:
    pkg = f.read()

pkg = pkg.replace('"cloudinary": "^2.0.0",', '')
pkg = pkg.replace('"multer-storage-cloudinary": "^4.0.0",', '')
pkg = pkg.replace('"cloudinary":', '#"cloudinary":')
pkg = pkg.replace('"multer-storage-cloudinary":', '#"multer-storage-cloudinary":')

with open("package.json", "w", encoding="utf-8") as f:
    f.write(pkg)
print("package.json cleaned!")

print("\n=== BACKEND RESTORED ===")
print("\nAdd to Render Environment Variables:")
print("BACKEND_URL = https://aiqpg-backend.onrender.com")