# Debug + Fix all student data issues

# Fix 1: JWT token mein classSectionId update karo after class join
with open("src/controllers/auth.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Fix joinClassByCode to return new token
old = """    const user = await prisma.user.update({ where: { id: userId }, data: { classSectionId: cls.id }, include: { classSection: true } })
    return success(res, { user, class: cls }, 'Joined class successfully!')"""

new = """    const user = await prisma.user.update({ where: { id: userId }, data: { classSectionId: cls.id }, include: { classSection: true } })
    // Generate new token with updated classSectionId
    const { signToken } = require('../utils/jwt')
    const newToken = signToken({
      userId: user.id, email: user.email, role: user.role,
      name: user.name, collegeId: user.collegeId, classSectionId: cls.id,
    })
    return success(res, { user, class: cls, token: newToken }, 'Joined class successfully!')"""

content = content.replace(old, new)

with open("src/controllers/auth.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("Auth controller fixed!")

# Fix 2: Task controller - student without class sees ALL tasks
with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createTask = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { title, description, taskType, subjectName, classSectionId, deadline, maxMarks, instructions, allowLate, latePenalty } = req.body

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
        latePenalty: parseInt(latePenalty) || 0,
        attachmentUrl: req.file ? '/uploads/' + collegeId + '/' + req.file.filename : null,
      },
      include: {
        creator: { select: { name: true } },
        classSection: { select: { name: true, section: true, branch: true } }
      }
    })

    // Notify students
    const studentFilter: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId) studentFilter.classSectionId = classSectionId
    const students = await prisma.user.findMany({ where: studentFilter, select: { id: true } })

    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: 'New ' + (taskType || 'assignment').replace('_', ' ') + ' Assigned',
          body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''),
          type: 'task', refId: task.id,
        }))
      })
    }

    return success(res, task, 'Task created', 201)
  } catch (err: any) {
    console.error('Create task error:', err)
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const createBulkTasks = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { tasks } = req.body
    const created = []
    for (const t of tasks) {
      const task = await prisma.task.create({
        data: {
          collegeId, createdBy: userId,
          title: t.title, taskType: t.taskType as any,
          subjectName: t.subjectName || null,
          classSectionId: t.classSectionId || null,
          deadline: t.deadline ? new Date(t.deadline) : null,
          maxMarks: parseInt(t.maxMarks) || 10,
          instructions: t.instructions || null,
          allowLate: t.allowLate || false,
        }
      })
      created.push(task)
      const f: any = { collegeId, role: 'student', isActive: true }
      if (t.classSectionId) f.classSectionId = t.classSectionId
      const students = await prisma.user.findMany({ where: f, select: { id: true } })
      if (students.length > 0) {
        await prisma.notification.createMany({
          data: students.map(s => ({ userId: s.id, title: 'New ' + t.taskType.replace('_', ' '), body: t.title, type: 'task', refId: task.id }))
        })
      }
    }
    return success(res, created, created.length + ' tasks created', 201)
  } catch (err: any) {
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const getTasks = async (req: Request, res: Response) => {
  try {
    const { collegeId, role, userId, classSectionId } = (req as any).user
    const { classId } = req.query

    let where: any = { collegeId }

    if (role === 'student') {
      where.status = 'active'
      if (classSectionId) {
        // Student sees: tasks for their class + tasks for all students (no class set)
        where.OR = [
          { classSectionId: classSectionId },
          { classSectionId: null },
        ]
      }
      // If student has no class, show all active tasks in college
    } else if (role === 'teacher') {
      if (classId) where.classSectionId = classId as string
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
  } catch (err: any) {
    console.error('Get tasks error:', err)
    return error(res, 'Failed: ' + err.message, 500)
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
        classSection: { select: { name: true, section: true } },
        submissions: { include: { student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } } } }
      }
    })
    if (!task) return error(res, 'Not found', 404)
    return success(res, task)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const updateTaskStatus = async (req: Request, res: Response) => {
  try {
    const id = req.params.id as string
    const task = await prisma.task.update({ where: { id }, data: { status: req.body.status as any } })
    return success(res, task, 'Updated')
  } catch (err) { return error(res, 'Failed', 500) }
}

export const deleteTask = async (req: Request, res: Response) => {
  try {
    await prisma.task.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch (err) { return error(res, 'Failed', 500) }
}
""")
print("Task controller fixed!")

print("Backend fixes done!")