import os

# ═══════════════════════════════════════════════════════
# FIX 1: Submission Controller - TypeScript errors fix
# ═══════════════════════════════════════════════════════
with open("src/controllers/submission.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

async function getMainCollegeId(): Promise<string> {
  const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
  return college?.id || ''
}

export const createSubmission = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const { taskId, textAnswer } = req.body
    const file = req.file
    const tid = taskId as string

    const task = await prisma.task.findFirst({ where: { id: tid, collegeId } })
    if (!task) return error(res, 'Task not found', 404)
    if (task.status !== 'active') return error(res, 'Task is closed', 400)

    const existing = await prisma.submission.findUnique({
      where: { taskId_studentId: { taskId: tid, studentId: userId } }
    })
    if (existing) return error(res, 'Already submitted', 400)

    const isLate = task.deadline && new Date() > task.deadline
    if (isLate && !task.allowLate) return error(res, 'Deadline has passed', 400)

    const submission = await prisma.submission.create({
      data: {
        taskId: tid, studentId: userId,
        textAnswer: textAnswer || null,
        fileUrl: file ? '/uploads/' + collegeId + '/' + file.filename : null,
        fileName: file?.originalname || null,
        status: (isLate ? 'late' : 'submitted') as any,
      },
      include: {
        student: { select: { name: true } },
        task: { select: { title: true, maxMarks: true } }
      }
    })

    await prisma.notification.create({
      data: {
        userId: task.createdBy,
        title: '📥 New Submission',
        body: (submission.student.name || 'Student') + ' submitted "' + task.title + '"',
        type: 'task', refId: tid
      }
    })

    return success(res, submission, 'Submitted!', 201)
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}

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
        student: {
          select: {
            name: true, email: true, rollNumber: true, avatarUrl: true,
            classSectionId: true,
            classSection: { select: { name: true, section: true, branch: true } }
          }
        },
        task: { select: { title: true, maxMarks: true, taskType: true, subjectName: true } }
      },
      orderBy: { submittedAt: 'desc' }
    })
    return success(res, submissions)
  } catch (err) { return error(res, 'Failed', 500) }
}

export const getResultsSummary = async (req: Request, res: Response) => {
  try {
    const { collegeId, userId } = (req as any).user
    const { classId } = req.query
    const subs = await prisma.submission.findMany({
      where: {
        task: {
          collegeId,
          createdBy: userId,
          ...(classId && classId !== 'undefined' && { classSectionId: classId as string })
        }
      },
      include: {
        student: {
          select: {
            id: true, name: true, email: true, rollNumber: true, classSectionId: true,
            classSection: { select: { id: true, name: true, section: true, branch: true } }
          }
        },
        task: { select: { id: true, title: true, maxMarks: true, taskType: true, subjectName: true } }
      },
      orderBy: { submittedAt: 'desc' }
    })

    const byClass: Record<string, any> = {}
    for (const sub of subs) {
      const cls = sub.student.classSection
      const classKey = cls ? cls.id : 'no_class'
      const className = cls ? cls.name + ' ' + cls.section : 'No Class'
      if (!byClass[classKey]) {
        byClass[classKey] = { classId: classKey, className, branch: cls?.branch || '', students: {}, submissions: [] }
      }
      byClass[classKey].submissions.push(sub)
      const sid = sub.student.id
      if (!byClass[classKey].students[sid]) {
        byClass[classKey].students[sid] = {
          id: sid, name: sub.student.name, email: sub.student.email,
          rollNumber: sub.student.rollNumber, tasks: [], totalObtained: 0, totalMax: 0
        }
      }
      byClass[classKey].students[sid].tasks.push({
        taskId: sub.task.id, title: sub.task.title, maxMarks: sub.task.maxMarks,
        subjectName: sub.task.subjectName, marksAwarded: sub.marksAwarded,
        status: sub.status, submittedAt: sub.submittedAt, feedback: sub.feedback,
        submissionId: sub.id
      })
      if (sub.marksAwarded !== null) {
        byClass[classKey].students[sid].totalObtained += sub.marksAwarded
        byClass[classKey].students[sid].totalMax += sub.task.maxMarks
      }
    }

    const result = Object.values(byClass).map((cls: any) => {
      const students = Object.values(cls.students).map((s: any) => ({
        ...s,
        avgPct: s.totalMax > 0 ? Math.round((s.totalObtained / s.totalMax) * 100) : null,
        grade: s.totalMax > 0 ? (s.totalObtained/s.totalMax >= 0.8 ? 'A' : s.totalObtained/s.totalMax >= 0.6 ? 'B' : s.totalObtained/s.totalMax >= 0.4 ? 'C' : 'F') : '-'
      })).sort((a: any, b: any) => (b.totalObtained || 0) - (a.totalObtained || 0))
      return { ...cls, students, studentCount: students.length }
    })

    return success(res, result)
  } catch (err: any) { return error(res, err.message, 500) }
}

export const getPendingSummary = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
    const tasks = await prisma.task.findMany({
      where: { collegeId, createdBy: userId },
      include: {
        classSection: { select: { name: true, section: true, branch: true } },
        submissions: { select: { id: true, marksAwarded: true, studentId: true } }
      }
    })

    const summary = await Promise.all(tasks.map(async t => {
      const total = t.submissions.length
      const graded = t.submissions.filter(s => s.marksAwarded !== null).length
      const f: any = { collegeId, role: 'student', isActive: true }
      if (t.classSectionId) f.classSectionId = t.classSectionId
      const totalStudents = await prisma.user.count({ where: f })
      const submittedIds = t.submissions.map(s => s.studentId)
      const notSubmitted = await prisma.user.findMany({
        where: { ...f, id: { notIn: submittedIds } },
        select: { id: true, name: true, email: true, rollNumber: true }
      })
      return {
        taskId: t.id, title: t.title, maxMarks: t.maxMarks,
        className: t.classSection ? t.classSection.name + ' ' + t.classSection.section : 'All Students',
        totalStudents, submittedCount: total, notSubmittedCount: totalStudents - total,
        graded, pending: total - graded, notSubmitted
      }
    }))

    return success(res, { totalPending: summary.reduce((s, x) => s + x.pending, 0), tasks: summary })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const getTaskSubmissionStatus = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const taskId = req.params.taskId as string
    const task = await prisma.task.findFirst({ where: { id: taskId, collegeId } })
    if (!task) return error(res, 'Not found', 404)
    const f: any = { collegeId, role: 'student', isActive: true }
    if (task.classSectionId) f.classSectionId = task.classSectionId
    const allStudents = await prisma.user.findMany({ where: f, select: { id: true, name: true, rollNumber: true, avatarUrl: true } })
    const subs = await prisma.submission.findMany({
      where: { taskId },
      select: { studentId: true, status: true, marksAwarded: true, submittedAt: true }
    })
    const subMap = new Map(subs.map(s => [s.studentId, s]))
    return success(res, {
      total: allStudents.length, submittedCount: subs.length,
      notSubmittedCount: allStudents.length - subs.length,
      submitted: allStudents.filter(s => subMap.has(s.id)).map(s => ({ ...s, ...subMap.get(s.id) })),
      notSubmitted: allStudents.filter(s => !subMap.has(s.id))
    })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const gradeSubmission = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const id = req.params.id as string
    const { marks, feedback } = req.body
    const submission = await prisma.submission.update({
      where: { id },
      data: {
        marksAwarded: parseInt(marks), feedback: feedback || null,
        gradedBy: userId, gradedAt: new Date(), status: 'graded' as any
      },
      include: { task: { select: { title: true, maxMarks: true } } }
    })
    await prisma.notification.create({
      data: {
        userId: submission.studentId,
        title: '📊 Result Published!',
        body: '"' + submission.task.title + '" graded: ' + marks + '/' + submission.task.maxMarks + (feedback ? ' — ' + feedback : ''),
        type: 'result', refId: submission.taskId
      }
    })
    return success(res, submission, 'Graded!')
  } catch (err: any) { return error(res, 'Failed: ' + err.message, 500) }
}
""")
print("Submission controller fixed!")

print("Backend done!")