import os

# Student Dashboard - Class selector + filtered data
os.makedirs("../frontend/app/(student)/student", exist_ok=True)
with open("../frontend/app/(student)/student/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect, useCallback } from 'react'
import { useSession } from 'next-auth/react'
import Link from 'next/link'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type ClassSection = {
  id: string; name: string; section: string; branch: string
  semester: number; year: number; uniqueCode: string
  _count: { students: number }
}

export default function StudentDashboard() {
  const { data: session, status } = useSession()
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [selectedClass, setSelectedClass] = useState<ClassSection | null>(null)
  const [tasks, setTasks] = useState<any[]>([])
  const [materials, setMaterials] = useState<any[]>([])
  const [submissions, setSubmissions] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [classLoading, setClassLoading] = useState(true)
  const [showClassPicker, setShowClassPicker] = useState(false)

  const token = session?.user?.backendToken

  // Step 1: Load all available classes
  useEffect(() => {
    if (!token || status === 'loading') return
    setClassLoading(true)
    fetch(API + '/auth/classes', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(d => {
        if (d.success && d.data.length > 0) {
          setClasses(d.data)
          // Check if student already has a class saved
          const savedId = localStorage.getItem('myClassId')
          const found = d.data.find((c: ClassSection) => c.id === savedId)
          if (found) {
            setSelectedClass(found)
          }
          // If only 1 class exists, auto-select it
          else if (d.data.length === 1) {
            setSelectedClass(d.data[0])
            localStorage.setItem('myClassId', d.data[0].id)
          }
        }
        setClassLoading(false)
      })
      .catch(() => setClassLoading(false))
  }, [token, status])

  // Step 2: Load data when class is selected
  const loadClassData = useCallback(async (cls: ClassSection) => {
    if (!token) return
    setLoading(true)
    try {
      const headers = { Authorization: 'Bearer ' + token }
      const [t, m, s] = await Promise.all([
        fetch(API + '/tasks?classId=' + cls.id, { headers }).then(r => r.json()),
        fetch(API + '/materials', { headers }).then(r => r.json()),
        fetch(API + '/submissions', { headers }).then(r => r.json()),
      ])
      if (t.success) setTasks(t.data || [])
      if (m.success) setMaterials(m.data || [])
      if (s.success) setSubmissions(s.data || [])
    } catch {}
    setLoading(false)
  }, [token])

  useEffect(() => {
    if (selectedClass) loadClassData(selectedClass)
  }, [selectedClass, loadClassData])

  const switchClass = (cls: ClassSection) => {
    setSelectedClass(cls)
    localStorage.setItem('myClassId', cls.id)
    setShowClassPicker(false)
    // Clear old data
    setTasks([]); setMaterials([]); setSubmissions([])
  }

  const notes = materials.filter(m => !m.isPyq)
  const pyqs = materials.filter(m => m.isPyq)
  const subIds = submissions.map((s: any) => s.taskId)
  const pending = tasks.filter(t => !subIds.includes(t.id))
  const graded = submissions.filter(s => s.status === 'graded')

  const typeIcon: Record<string, string> = { assignment: '📝', class_test: '✍️', quiz: '❓', project: '🔬' }

  const getDL = (d?: string) => {
    if (!d) return { label: 'No deadline', color: 'text-slate-400' }
    const diff = new Date(d).getTime() - Date.now()
    const days = Math.ceil(diff / 86400000)
    if (diff < 0) return { label: 'Overdue!', color: 'text-red-400' }
    if (days === 0) return { label: 'Due Today!', color: 'text-red-400' }
    if (days <= 2) return { label: days + 'd left', color: 'text-yellow-400' }
    return { label: days + 'd left', color: 'text-green-400' }
  }

  if (status === 'loading' || classLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Loading...</p>
      </div>
    </div>
  )

  // No classes created by teacher yet
  if (classes.length === 0) return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">Welcome, {session?.user?.name?.split(' ')[0]} 👋</h1>
      </div>
      <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
        <p className="text-5xl mb-4">⏳</p>
        <p className="text-white font-semibold text-lg mb-2">No Classes Available Yet</p>
        <p className="text-slate-400 text-sm mb-6">Your teacher hasn't created any classes yet. Once they do, you'll be able to select your class and access all materials.</p>
        <button onClick={() => window.location.reload()} className="px-6 py-2.5 bg-green-500 text-white text-sm font-medium rounded-xl hover:bg-green-600">
          🔄 Refresh
        </button>
      </div>
    </div>
  )

  // Class not selected yet
  if (!selectedClass) return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">Welcome, {session?.user?.name?.split(' ')[0]} 👋</h1>
        <p className="text-slate-400 text-sm">Select your class to get started</p>
      </div>
      <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
        <h2 className="text-base font-semibold text-white mb-4">🏫 Select Your Class</h2>
        <div className="space-y-3">
          {classes.map(cls => (
            <button key={cls.id} onClick={() => switchClass(cls)}
              className="w-full p-4 bg-slate-800 rounded-xl border border-white/5 hover:border-green-500/40 hover:bg-green-500/5 transition-all text-left group">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-white group-hover:text-green-400 transition-colors">
                    {cls.name} — Section {cls.section}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">{cls.branch} · Semester {cls.semester} · {cls.year}</p>
                  <p className="text-xs text-slate-600 mt-0.5">{cls._count.students} students enrolled</p>
                </div>
                <div className="text-right">
                  <span className="text-xs font-mono text-green-400 bg-green-500/10 px-2 py-1 rounded-lg border border-green-500/20 block mb-1">{cls.uniqueCode}</span>
                  <span className="text-xs text-green-400 opacity-0 group-hover:opacity-100 transition-opacity">Select →</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header with class switcher */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">
            Welcome, {session?.user?.name?.split(' ')[0]} 👋
          </h1>
          <p className="text-slate-400 text-sm">Your class dashboard</p>
        </div>

        {/* Class Switcher */}
        <div className="relative">
          <button onClick={() => setShowClassPicker(!showClassPicker)}
            className="flex items-center gap-3 bg-slate-900 border border-white/10 hover:border-green-500/30 rounded-xl px-4 py-3 transition-all">
            <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center text-green-400 font-bold text-sm">
              {selectedClass.section}
            </div>
            <div className="text-left">
              <p className="text-xs font-semibold text-white">{selectedClass.name} — Sec {selectedClass.section}</p>
              <p className="text-[10px] text-slate-500">{selectedClass.branch} · Sem {selectedClass.semester}</p>
            </div>
            <span className="text-slate-500 text-xs ml-1">{showClassPicker ? '▲' : '▼'}</span>
          </button>

          {showClassPicker && classes.length > 1 && (
            <div className="absolute right-0 top-full mt-2 w-72 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden">
              <div className="p-3 border-b border-white/5">
                <p className="text-xs text-slate-500 uppercase tracking-wider">Switch Class</p>
              </div>
              {classes.map(cls => (
                <button key={cls.id} onClick={() => switchClass(cls)}
                  className={'w-full p-3 text-left hover:bg-slate-800 transition-all flex items-center gap-3 ' + (cls.id === selectedClass.id ? 'bg-green-500/10' : '')}>
                  <div className={'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ' + (cls.id === selectedClass.id ? 'bg-green-500 text-white' : 'bg-slate-800 text-slate-400')}>
                    {cls.section}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white">{cls.name} — Sec {cls.section}</p>
                    <p className="text-xs text-slate-500">{cls.branch} · Sem {cls.semester} · {cls._count.students} students</p>
                  </div>
                  {cls.id === selectedClass.id && <span className="text-green-400 text-xs">✓ Current</span>}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Click outside to close */}
      {showClassPicker && (
        <div className="fixed inset-0 z-40" onClick={() => setShowClassPicker(false)} />
      )}

      {/* Class Info Banner */}
      <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/20 rounded-2xl p-4 mb-6 flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center text-2xl">🏫</div>
        <div>
          <p className="text-sm font-semibold text-white">{selectedClass.name} — Section {selectedClass.section}</p>
          <p className="text-xs text-slate-400">{selectedClass.branch} · Semester {selectedClass.semester} · {selectedClass.year} · Code: <span className="text-green-400 font-mono">{selectedClass.uniqueCode}</span></p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-lg font-bold text-green-400">{selectedClass._count.students}</p>
          <p className="text-xs text-slate-500">classmates</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { l: 'Pending Tasks', v: pending.length, i: '📋', c: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20', h: '/student/assignments' },
          { l: 'Submitted', v: submissions.length, i: '✅', c: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20', h: '/student/assignments' },
          { l: 'Study Notes', v: notes.length, i: '📚', c: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20', h: '/student/materials' },
          { l: 'PYQs', v: pyqs.length, i: '📄', c: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20', h: '/student/materials' },
        ].map(s => (
          <Link key={s.l} href={s.h}>
            <div className={'bg-slate-900 rounded-2xl border p-5 cursor-pointer hover:scale-[1.02] transition-all ' + s.bg}>
              <div className={'w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-3 border ' + s.bg}>{s.i}</div>
              <p className={'text-2xl font-bold mb-1 ' + s.c}>{loading ? '...' : s.v}</p>
              <p className="text-xs text-slate-500">{s.l}</p>
            </div>
          </Link>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Loading {selectedClass.name} data...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pending Tasks */}
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">📋 Pending Tasks ({pending.length})</h2>
              <Link href="/student/assignments" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
            </div>
            {tasks.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-2">📭</p>
                <p className="text-slate-400 text-sm">No tasks for {selectedClass.name} yet</p>
                <p className="text-slate-600 text-xs mt-1">Your teacher will assign tasks soon</p>
              </div>
            ) : pending.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-2">🎉</p>
                <p className="text-slate-400 text-sm">All tasks submitted!</p>
              </div>
            ) : (
              <div className="space-y-2">
                {pending.slice(0,5).map((t: any) => {
                  const dl = getDL(t.deadline)
                  return (
                    <div key={t.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                      <span className="text-xl flex-shrink-0">{typeIcon[t.taskType] || '📋'}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-white truncate">{t.title}</p>
                        <p className="text-[10px] text-slate-500">{t.subjectName || 'General'} · {t.maxMarks}M</p>
                      </div>
                      <span className={'text-[10px] font-semibold flex-shrink-0 ' + dl.color}>{dl.label}</span>
                    </div>
                  )
                })}
              </div>
            )}
            {pending.length > 0 && (
              <Link href="/student/assignments">
                <button className="w-full mt-3 py-2.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-xl text-xs font-medium hover:bg-blue-500/20">📤 Submit Assignments</button>
              </Link>
            )}
          </div>

          {/* Recent Notes */}
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">📚 Study Notes ({notes.length})</h2>
              <Link href="/student/materials" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
            </div>
            {notes.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-2">📭</p>
                <p className="text-slate-400 text-sm">No notes uploaded yet</p>
                <p className="text-slate-600 text-xs mt-1">Ask your teacher to upload notes</p>
              </div>
            ) : (
              <div className="space-y-2">
                {notes.slice(0,5).map((m: any) => (
                  <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                    <span className="text-xl flex-shrink-0">📚</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{m.title}</p>
                      <div className="flex gap-2 mt-0.5">
                        {m.subject && <span className="text-[10px] text-green-400 truncate max-w-[120px]">{m.subject}</span>}
                        {m.unit && <span className="text-[10px] text-slate-500">· {m.unit}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* PYQs */}
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">📄 Previous Year Papers ({pyqs.length})</h2>
              <Link href="/student/materials" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
            </div>
            {pyqs.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-2">📄</p>
                <p className="text-slate-400 text-sm">No PYQs uploaded yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {pyqs.slice(0,5).map((m: any) => (
                  <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                    <span className="text-xl flex-shrink-0">📄</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{m.title}</p>
                      <div className="flex gap-2 mt-0.5">
                        {m.subject && <span className="text-[10px] text-blue-400 truncate max-w-[120px]">{m.subject}</span>}
                        {m.year && <span className="text-[10px] text-slate-500">· {m.year}</span>}
                        {m.examType && <span className="text-[10px] text-orange-400">· {m.examType.replace('_',' ')}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Results */}
          <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">📊 Recent Results ({graded.length})</h2>
              <Link href="/student/results" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
            </div>
            {graded.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-2">📊</p>
                <p className="text-slate-400 text-sm">No grades yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {graded.slice(0,4).map((s: any) => {
                  const pct = s.task?.maxMarks ? Math.round((s.marksAwarded / s.task.maxMarks) * 100) : 0
                  const grade = pct >= 80 ? { g: 'A', c: 'text-green-400' } : pct >= 60 ? { g: 'B', c: 'text-blue-400' } : pct >= 40 ? { g: 'C', c: 'text-yellow-400' } : { g: 'F', c: 'text-red-400' }
                  return (
                    <div key={s.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                      <div className={'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ' + grade.c + ' bg-current/10'}>{grade.g}</div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-white truncate">{s.task?.title}</p>
                        <p className="text-[10px] text-slate-500">{s.task?.subjectName || 'General'}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className={'text-sm font-bold ' + grade.c}>{s.marksAwarded}<span className="text-slate-600 text-xs">/{s.task?.maxMarks}</span></p>
                        <p className="text-[10px] text-slate-500">{pct}%</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Quick Actions */}
            <div className="mt-4 pt-4 border-t border-white/5 grid grid-cols-2 gap-2">
              <Link href="/student/assignments">
                <div className="p-2.5 bg-slate-800 rounded-xl border border-white/5 hover:border-blue-500/30 transition-all cursor-pointer text-center">
                  <p className="text-base">📤</p>
                  <p className="text-[10px] text-slate-400 mt-1">Submit Task</p>
                </div>
              </Link>
              <Link href="/student/chatbot">
                <div className="p-2.5 bg-slate-800 rounded-xl border border-white/5 hover:border-purple-500/30 transition-all cursor-pointer text-center">
                  <p className="text-base">🤖</p>
                  <p className="text-[10px] text-slate-400 mt-1">AI Assistant</p>
                </div>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Student Dashboard done!")

# Fix Student Layout - remove API check, use simple localStorage
with open("../frontend/app/(student)/layout.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter, usePathname } from 'next/navigation'
import StudentSidebar from '@/components/student/StudentSidebar'
import StudentNavbar from '@/components/student/StudentNavbar'

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const pathname = usePathname()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (status === 'loading') return
    if (!session) { router.push('/login'); return }
    if (session.user.role !== 'student') { router.push('/teacher'); return }
    // Always allow student in - class selection handled in dashboard
    setReady(true)
  }, [session, status, pathname])

  if (!ready) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="w-10 h-10 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (pathname === '/student/select-class') return <>{children}</>

  return (
    <div className="flex min-h-screen bg-slate-950">
      <StudentSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <StudentNavbar />
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  )
}
""")
print("Student layout done!")

# Fix Task Controller - student with classId filter
with open("src/controllers/task.controller.ts", "w", encoding="utf-8") as f:
    f.write("""import { Request, Response } from 'express'
import prisma from '../config/db'
import { success, error } from '../utils/response'

export const createTask = async (req: Request, res: Response) => {
  try {
    const { userId, collegeId } = (req as any).user
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
    // Notify students
    const filter: any = { collegeId, role: 'student', isActive: true }
    if (classSectionId) filter.classSectionId = classSectionId
    const students = await prisma.user.findMany({ where: filter, select: { id: true } })
    if (students.length > 0) {
      await prisma.notification.createMany({
        data: students.map(s => ({
          userId: s.id,
          title: 'New ' + (taskType || 'assignment').replace('_', ' '),
          body: title + (deadline ? ' — Due: ' + new Date(deadline).toLocaleDateString('en-IN') : ''),
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
    const { userId, collegeId } = (req as any).user
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
    const { collegeId, role } = (req as any).user
    const { classId } = req.query

    let where: any = { collegeId }

    if (role === 'student') {
      where.status = 'active'
      if (classId) {
        // Show tasks for this specific class + tasks for all (no class set)
        where.OR = [
          { classSectionId: classId as string },
          { classSectionId: null }
        ]
      }
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
    return error(res, 'Failed: ' + err.message, 500)
  }
}

export const getTask = async (req: Request, res: Response) => {
  try {
    const { collegeId } = (req as any).user
    const task = await prisma.task.findFirst({
      where: { id: req.params.id as string, collegeId },
      include: {
        creator: { select: { name: true } },
        classSection: { select: { name: true, section: true } },
        submissions: { include: { student: { select: { name: true, email: true, rollNumber: true, avatarUrl: true } } } }
      }
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

export const deleteTask = async (req: Request, res: Response) => {
  try {
    await prisma.task.delete({ where: { id: req.params.id as string } })
    return success(res, null, 'Deleted')
  } catch { return error(res, 'Failed', 500) }
}
""")
print("Task controller done!")

# Fix Student Assignments - pass classId in API call
with open("../frontend/app/(student)/student/assignments/page.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Replace task fetch to include classId
old_fetch = "fetch(API + '/tasks', { headers: { Authorization: 'Bearer ' + token } }).then(r => r.json()),"
new_fetch = """fetch(API + '/tasks?classId=' + (localStorage.getItem('myClassId') || ''), { headers: { Authorization: 'Bearer ' + token } }).then(r => r.json()),"""

if old_fetch in content:
    content = content.replace(old_fetch, new_fetch)
    with open("../frontend/app/(student)/student/assignments/page.tsx", "w", encoding="utf-8") as f:
        f.write(content)
    print("Assignments classId fix done!")
else:
    print("Assignments - already updated or different format")

print("\n" + "="*50)
print("ALL DONE!")
print("="*50)