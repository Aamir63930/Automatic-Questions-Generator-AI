import { Request, Response } from 'express'
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

    // IMPORTANT: Only notify students in the specific class
    // If no class selected, notify ALL students
    let studentFilter: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId && classSectionId !== '' && classSectionId !== 'null') {
      // Only this class
      studentFilter.classSectionId = classSectionId
    }
    // else: all students

    const students = await prisma.user.findMany({ where: studentFilter, select: { id: true } })

    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: '📋 New ' + (taskType || 'assignment').replace('_', ' '),
          body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true }) : ''),
          type: 'task', refId: task.id,
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
    const { role, userId } = (req as any).user
    const collegeId = await getMainCollegeId()
    const { classId } = req.query

    let where: any = { collegeId }

    if (role === 'student') {
      where.status = 'active'
      const classIdStr = classId as string
      if (classIdStr && classIdStr !== 'undefined' && classIdStr !== '') {
        // Student sees: tasks for THEIR class + tasks with NO class (college-wide)
        where.OR = [
          { classSectionId: classIdStr },
          { classSectionId: null }
        ]
      }
      // If no classId: show only college-wide tasks (no class assigned)
    } else if (role === 'teacher') {
      const classIdStr = classId as string
      if (classIdStr && classIdStr !== 'undefined' && classIdStr !== '') {
        where.classSectionId = classIdStr
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
        data: students.map(s => ({ userId: s.id, title: '⏰ Deadline Extended', body: '"' + task.title + '" extended to ' + new Date(newDeadline).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true }), type: 'task', refId: task.id }))
      })
    }
    return success(res, task, 'Extended')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

export const deleteTask = async (req: Request, res: Response) => {
  try {
    await prisma.task.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch { return error(res, 'Failed', 500) }
}
