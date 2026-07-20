import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'
import path from 'path'
import fs from 'fs'
import cloudinary from '../config/cloudinary'

const BACKEND_URL = process.env.BACKEND_URL || 'https://automatic-questions-generator-ai.onrender.com'

async function getCollegeId(): Promise<string> {
  const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
  return college?.id || ''
}

async function uploadToCloudinary(filePath: string, fileName: string): Promise<string> {
  const ext = require('path').extname(fileName).toLowerCase()
  const imageExts = ['.jpg','.jpeg','.png','.gif','.webp']
  const resourceType = imageExts.includes(ext) ? 'image' : 'raw'
  
  const result = await cloudinary.uploader.upload(filePath, {
    folder: 'aiqpg/materials',
    resource_type: resourceType,
    type: 'upload',
    access_mode: 'public',
    public_id: Date.now() + '_' + fileName.replace(/[^a-zA-Z0-9._-]/g, '_'),
    invalidate: true,
  })
  
  console.log('Cloudinary upload result:', {
    url: result.secure_url,
    resource_type: result.resource_type,
    type: result.type,
    access_mode: result.access_mode
  })
  
  return result.secure_url
}

export const uploadMaterial = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const collegeId = await getCollegeId()
    const file = req.file
    if (!file) return error(res, 'No file uploaded', 400)

    const { title, fileType, isPyq, year, subject, unit, examType, classSectionId } = req.body

    // Upload to Cloudinary
    let fileUrl = ''
    try {
      fileUrl = await uploadToCloudinary(file.path, file.originalname)
      // Delete local file after Cloudinary upload
      if (fs.existsSync(file.path)) fs.unlinkSync(file.path)
      console.log('Uploaded to Cloudinary:', fileUrl)
    } catch (cloudErr) {
      console.error('Cloudinary upload failed, using local:', cloudErr)
      // Fallback to local if Cloudinary fails
      fileUrl = '/uploads/' + collegeId + '/' + file.filename
    }

    const material = await prisma.material.create({
      data: {
        collegeId,
        uploadedBy: userId,
        title: title || file.originalname.replace(/\.[^.]+$/, ''),
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
    const f: any = { collegeId, role: 'student', isActive: true }
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
      }).catch(() => {})
    }

    return success(res, material, 'Uploaded!', 201)
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
      include: {
        uploader: { select: { name: true } },
        classSection: { select: { name: true, section: true } }
      },
      orderBy: { createdAt: 'desc' }
    })

    return success(res, materials)
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const downloadMaterial = async (req: Request, res: Response) => {
  try {
    const material = await prisma.material.findUnique({ where: { id: req.params.id as string } })
    if (!material) return error(res, 'Not found', 404)

    // Cloudinary URL - redirect
    if (material.fileUrl.startsWith('http')) {
      let downloadUrl = material.fileUrl
      if (downloadUrl.includes('cloudinary.com') && downloadUrl.includes('/image/upload/')) {
        const ext = require('path').extname(material.fileName).toLowerCase()
        const imageExts = ['.jpg','.jpeg','.png','.gif','.webp']
        if (!imageExts.includes(ext)) {
          downloadUrl = downloadUrl.replace('/image/upload/', '/raw/upload/')
        }
      }
      return res.redirect(downloadUrl)
    }

    // Local file fallback
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

    // Cloudinary URL - fix raw URL for PDF
    if (material.fileUrl.startsWith('http')) {
      let viewUrl = material.fileUrl
      // Fix: PDF/doc files need /raw/upload/ not /image/upload/
      if (viewUrl.includes('cloudinary.com') && viewUrl.includes('/image/upload/')) {
        const ext = require('path').extname(material.fileName).toLowerCase()
        const imageExts = ['.jpg','.jpeg','.png','.gif','.webp']
        if (!imageExts.includes(ext)) {
          viewUrl = viewUrl.replace('/image/upload/', '/raw/upload/')
        }
      }
      res.setHeader('Access-Control-Allow-Origin', '*')
      return res.redirect(viewUrl)
    }

    // Local file fallback
    const filePath = path.join(process.cwd(), material.fileUrl)
    if (!fs.existsSync(filePath)) return error(res, 'File not found. Please re-upload.', 404)
    const ext = path.extname(material.fileName).toLowerCase()
    const mimes: Record<string, string> = {
      '.pdf': 'application/pdf', '.png': 'image/png',
      '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.txt': 'text/plain'
    }
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

    // Delete from Cloudinary if it's a Cloudinary URL
    if (material.fileUrl.startsWith('http') && material.fileUrl.includes('cloudinary')) {
      try {
        const publicId = 'aiqpg/materials/' + material.fileUrl.split('/').pop()?.split('.')[0]
        await cloudinary.uploader.destroy(publicId, { resource_type: 'raw' })
      } catch (e) { console.error('Cloudinary delete error:', e) }
    } else if (!material.fileUrl.startsWith('http')) {
      // Delete local file
      const fp = path.join(process.cwd(), material.fileUrl)
      if (fs.existsSync(fp)) fs.unlinkSync(fp)
    }

    await prisma.material.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch (err) { return error(res, 'Failed', 500) }
}
