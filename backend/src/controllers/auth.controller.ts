import { Request, Response } from 'express'
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
    // For students without class, also send available classes
    let availableClasses: any[] = []
    if (user.role === 'student' && !user.classSectionId) {
      availableClasses = await prisma.classSection.findMany({
        where: { isActive: true },
        include: { _count: { select: { students: true } } },
        orderBy: [{ semester: 'asc' }, { branch: 'asc' }]
      })
    }
    return success(res, { ...user, availableClasses })
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
      select: { id: true, name: true, email: true, role: true, avatarUrl: true, rollNumber: true, classSectionId: true, classSection: { select: { id: true, name: true, section: true, branch: true, semester: true } } },
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
