import os

# Teacher Results - class-wise + student-name-wise
os.makedirs("../frontend/app/(dashboard)/teacher/results", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/results/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect, useCallback } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Student = { id: string; name: string; email: string; rollNumber?: string | null; totalObtained: number; totalMax: number; avgPct: number | null; grade: string; tasks: any[] }
type ClassGroup = { classId: string; className: string; branch: string; students: Student[]; studentCount: number }

export default function TeacherResultsPage() {
  const { data: session } = useSession()
  const [view, setView] = useState<'overview'|'classwise'|'pending'|'grade'>('overview')
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([])
  const [pendingSummary, setPendingSummary] = useState<{ totalPending: number; tasks: any[] }>({ totalPending: 0, tasks: [] })
  const [tasks, setTasks] = useState<any[]>([])
  const [selTask, setSelTask] = useState<any>(null)
  const [taskStatus, setTaskStatus] = useState<any>(null)
  const [subs, setSubs] = useState<any[]>([])
  const [editId, setEditId] = useState<string|null>(null)
  const [editMarks, setEditMarks] = useState('')
  const [editFeedback, setEditFeedback] = useState('')
  const [saving, setSaving] = useState(false)
  const [expandedStudent, setExpandedStudent] = useState<string|null>(null)
  const [expandedClass, setExpandedClass] = useState<string|null>(null)
  const [searchStudent, setSearchStudent] = useState('')
  const token = session?.user?.backendToken

  const load = useCallback(async () => {
    if (!token) return
    const h = { Authorization: 'Bearer ' + token }
    const [r, p, t] = await Promise.all([
      fetch(API + '/submissions/results-summary', { headers: h }).then(x => x.json()),
      fetch(API + '/submissions/pending-summary', { headers: h }).then(x => x.json()),
      fetch(API + '/tasks', { headers: h }).then(x => x.json()),
    ])
    if (r.success) setClassGroups(r.data)
    if (p.success) setPendingSummary(p.data)
    if (t.success) setTasks(t.data)
  }, [token])

  useEffect(() => { load() }, [load])

  const loadTaskSubs = async (taskId: string) => {
    if (!token) return
    const [s, ts] = await Promise.all([
      fetch(API + '/submissions?taskId=' + taskId, { headers: { Authorization: 'Bearer ' + token } }).then(r => r.json()),
      fetch(API + '/submissions/task/' + taskId + '/status', { headers: { Authorization: 'Bearer ' + token } }).then(r => r.json()),
    ])
    if (s.success) setSubs(s.data)
    if (ts.success) setTaskStatus(ts.data)
  }

  const selectTask = (t: any) => { setSelTask(t); setView('grade'); setEditId(null); loadTaskSubs(t.id) }

  const saveGrade = async (sub: any) => {
    if (!token || !editMarks) return
    setSaving(true)
    const res = await fetch(API + '/submissions/' + sub.id + '/grade', {
      method: 'PATCH', headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ marks: editMarks, feedback: editFeedback })
    })
    if ((await res.json()).success) { await load(); await loadTaskSubs(sub.taskId); setEditId(null) }
    setSaving(false)
  }

  const gc = (m: number, max: number) => { const p = (m/max)*100; return p>=80?'text-green-400':p>=60?'text-blue-400':p>=40?'text-yellow-400':'text-red-400' }
  const gradeLabel = (g: string) => ({ A: 'text-green-400', B: 'text-blue-400', C: 'text-yellow-400', F: 'text-red-400', '-': 'text-slate-500' }[g] || 'text-slate-400')

  const allStudents = classGroups.flatMap(c => c.students.map(s => ({ ...s, className: c.className })))
  const filteredStudents = searchStudent ? allStudents.filter(s => s.name.toLowerCase().includes(searchStudent.toLowerCase()) || (s.rollNumber || '').includes(searchStudent)) : allStudents

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Results & Grading</h1>
          <p className="text-slate-400 text-sm">Class-wise and student-wise performance tracking</p>
        </div>
        {pendingSummary.totalPending > 0 && (
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl px-4 py-2.5 flex items-center gap-2 cursor-pointer" onClick={() => setView('pending')}>
            <span className="text-yellow-400 text-lg">⏳</span>
            <div>
              <p className="text-sm font-semibold text-yellow-400">{pendingSummary.totalPending} pending</p>
              <p className="text-xs text-slate-500">Click to grade</p>
            </div>
          </div>
        )}
      </div>

      {/* View tabs */}
      <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-2xl p-1.5 mb-6">
        {[
          { k: 'overview', l: '📊 Overview', count: null },
          { k: 'classwise', l: '🏫 Class-wise', count: classGroups.length },
          { k: 'pending', l: '⏳ Grade', count: pendingSummary.totalPending || null },
        ].map(tab => (
          <button key={tab.k} onClick={() => setView(tab.k as any)} className={'flex-1 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2 ' + (view === tab.k ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
            {tab.l}
            {tab.count !== null && tab.count > 0 && <span className={'text-xs px-1.5 rounded-full ' + (view === tab.k ? 'bg-white/20' : 'bg-blue-500/20 text-blue-400')}>{tab.count}</span>}
          </button>
        ))}
      </div>

      {/* OVERVIEW - Student name search + all results */}
      {view === 'overview' && (
        <div>
          <input type="text" value={searchStudent} onChange={e => setSearchStudent(e.target.value)} placeholder="Search student by name or roll number..." className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 mb-4" />
          {allStudents.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">📊</p>
              <p className="text-white font-medium">No submissions yet</p>
              <p className="text-slate-500 text-sm mt-1">Students will appear here after they submit tasks</p>
            </div>
          ) : (
            <div className="bg-slate-900 rounded-2xl border border-white/5 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/5 bg-slate-800/50">
                      {['Student', 'Class', 'Roll No', 'Total Marks', 'Percentage', 'Grade', 'Tasks'].map(h => (
                        <th key={h} className="text-left px-4 py-3 text-[10px] text-slate-400 uppercase tracking-wider font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredStudents.map((s, i) => (
                      <>
                        <tr key={s.id} onClick={() => setExpandedStudent(expandedStudent === s.id ? null : s.id)} className={'border-b border-white/5 cursor-pointer hover:bg-slate-800/30 transition-all ' + (i%2===0?'':'bg-slate-800/10')}>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold flex-shrink-0">{s.name.charAt(0)}</div>
                              <span className="text-sm font-medium text-white">{s.name}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-xs text-slate-400">{(s as any).className}</td>
                          <td className="px-4 py-3 text-xs text-slate-400">{s.rollNumber || '-'}</td>
                          <td className="px-4 py-3">
                            <span className={'text-sm font-bold ' + (s.totalMax > 0 ? gc(s.totalObtained, s.totalMax) : 'text-slate-500')}>
                              {s.totalObtained}/{s.totalMax}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            {s.avgPct !== null ? (
                              <div className="flex items-center gap-2">
                                <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                  <div className={'h-full rounded-full ' + gc(s.totalObtained, s.totalMax).replace('text-','bg-')} style={{ width: s.avgPct + '%' }} />
                                </div>
                                <span className={'text-sm font-semibold ' + gc(s.totalObtained, s.totalMax)}>{s.avgPct}%</span>
                              </div>
                            ) : <span className="text-slate-500 text-xs">Pending</span>}
                          </td>
                          <td className="px-4 py-3"><span className={'text-base font-bold ' + gradeLabel(s.grade)}>{s.grade}</span></td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-slate-400">{s.tasks.length} tasks</span>
                              <span className="text-slate-600 text-xs">{expandedStudent === s.id ? '▲' : '▼'}</span>
                            </div>
                          </td>
                        </tr>
                        {expandedStudent === s.id && (
                          <tr key={s.id + '_expanded'}>
                            <td colSpan={7} className="px-4 py-3 bg-slate-800/30">
                              <div className="space-y-2">
                                {s.tasks.map((t: any, ti: number) => (
                                  <div key={ti} className="flex items-center gap-4 bg-slate-900 rounded-xl p-3 border border-white/5">
                                    <div className="flex-1">
                                      <p className="text-xs font-medium text-white">{t.title}</p>
                                      {t.feedback && <p className="text-[10px] text-slate-500 mt-0.5">💬 {t.feedback}</p>}
                                    </div>
                                    <span className={'text-sm font-bold ' + (t.marksAwarded !== null ? gc(t.marksAwarded, t.maxMarks) : 'text-slate-500')}>
                                      {t.marksAwarded !== null ? t.marksAwarded + '/' + t.maxMarks : 'Not graded'}
                                    </span>
                                    <span className={'text-[10px] px-2 py-0.5 rounded border ' + (t.marksAwarded !== null ? 'text-green-400 bg-green-500/10 border-green-500/20' : t.status === 'submitted' ? 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' : 'text-slate-500 bg-slate-700 border-white/5')}>
                                      {t.marksAwarded !== null ? 'Graded' : t.status}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* CLASS-WISE view */}
      {view === 'classwise' && (
        <div className="space-y-4">
          {classGroups.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">🏫</p>
              <p className="text-white font-medium">No class data yet</p>
            </div>
          ) : classGroups.map(cls => {
            const isExpanded = expandedClass === cls.classId
            const classAvg = cls.students.filter(s => s.totalMax > 0).reduce((sum, s) => sum + (s.avgPct || 0), 0) / (cls.students.filter(s => s.totalMax > 0).length || 1)
            return (
              <div key={cls.classId} className="bg-slate-900 rounded-2xl border border-white/5 overflow-hidden">
                <button onClick={() => setExpandedClass(isExpanded ? null : cls.classId)} className="w-full p-5 text-left hover:bg-slate-800/30 transition-all">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 font-bold">{cls.className.charAt(0)}</div>
                      <div>
                        <p className="text-sm font-semibold text-white">🏫 {cls.className}</p>
                        <p className="text-xs text-slate-500">{cls.branch} · {cls.studentCount} students</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className={'text-lg font-bold ' + gc(classAvg, 100)}>{Math.round(classAvg)}%</p>
                        <p className="text-[10px] text-slate-500">Class avg</p>
                      </div>
                      <span className="text-slate-500">{isExpanded ? '▲' : '▼'}</span>
                    </div>
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-white/5 overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-white/5 bg-slate-800/50">
                          <th className="text-left px-4 py-2.5 text-[10px] text-slate-400 uppercase">Rank</th>
                          <th className="text-left px-4 py-2.5 text-[10px] text-slate-400 uppercase">Student</th>
                          <th className="text-left px-4 py-2.5 text-[10px] text-slate-400 uppercase">Roll No</th>
                          <th className="text-left px-4 py-2.5 text-[10px] text-slate-400 uppercase">Total Marks</th>
                          <th className="text-left px-4 py-2.5 text-[10px] text-slate-400 uppercase">%</th>
                          <th className="text-left px-4 py-2.5 text-[10px] text-slate-400 uppercase">Grade</th>
                        </tr>
                      </thead>
                      <tbody>
                        {cls.students.map((s, i) => (
                          <tr key={s.id} className={'border-b border-white/5 ' + (i%2===0?'':'bg-slate-800/10')}>
                            <td className="px-4 py-3">
                              <span className={'text-sm font-bold ' + (i===0?'text-yellow-400':i===1?'text-slate-300':i===2?'text-orange-400':'text-slate-600')}>
                                {i===0?'🥇':i===1?'🥈':i===2?'🥉':'#'+(i+1)}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-7 h-7 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-xs font-bold">{s.name.charAt(0)}</div>
                                <span className="text-sm text-white">{s.name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-xs text-slate-400">{s.rollNumber || '-'}</td>
                            <td className="px-4 py-3">
                              <span className={'text-sm font-bold ' + (s.totalMax > 0 ? gc(s.totalObtained, s.totalMax) : 'text-slate-500')}>
                                {s.totalObtained}/{s.totalMax}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                  <div className={'h-full rounded-full ' + (s.totalMax > 0 ? gc(s.totalObtained, s.totalMax).replace('text-','bg-') : 'bg-slate-600')} style={{ width: (s.avgPct || 0) + '%' }} />
                                </div>
                                <span className={'text-xs font-semibold ' + (s.totalMax > 0 ? gc(s.totalObtained, s.totalMax) : 'text-slate-500')}>
                                  {s.avgPct !== null ? s.avgPct + '%' : '-'}
                                </span>
                              </div>
                            </td>
                            <td className="px-4 py-3"><span className={'text-base font-bold ' + gradeLabel(s.grade)}>{s.grade}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* PENDING GRADING */}
      {view === 'pending' && (
        <div>
          {pendingSummary.tasks.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">🎉</p>
              <p className="text-white font-medium">All caught up! No pending grading.</p>
            </div>
          ) : (
            <>
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4 mb-4">
                <p className="text-sm text-yellow-400 font-semibold">⚠️ {pendingSummary.totalPending} submissions waiting · {pendingSummary.tasks.filter(t => t.notSubmittedCount > 0).reduce((s: number, t: any) => s + t.notSubmittedCount, 0)} students haven't submitted yet</p>
              </div>
              <div className="space-y-3 mb-6">
                {pendingSummary.tasks.map((t: any) => (
                  <button key={t.taskId} onClick={() => { const ft = tasks.find(x => x.id === t.taskId); if (ft) selectTask(ft) }} className="w-full bg-slate-900 rounded-xl border border-white/5 hover:border-yellow-500/30 p-4 text-left transition-all">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div>
                        <p className="text-sm font-medium text-white">{t.title}</p>
                        <p className="text-xs text-slate-500">{t.className}</p>
                        <div className="flex gap-3 mt-1">
                          <span className="text-xs text-green-400">✓ {t.submittedCount}/{t.totalStudents} submitted</span>
                          {t.notSubmittedCount > 0 && <span className="text-xs text-red-400">✗ {t.notSubmittedCount} not submitted</span>}
                          {t.graded > 0 && <span className="text-xs text-blue-400">📊 {t.graded} graded</span>}
                        </div>
                      </div>
                      <span className="text-xs px-3 py-1.5 bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded-full font-semibold">
                        {t.pending > 0 ? t.pending + ' to grade →' : '✓ All graded'}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* GRADE individual task */}
      {view === 'grade' && selTask && (
        <div>
          <button onClick={() => setView('pending')} className="text-xs text-blue-400 mb-4 hover:text-blue-300 flex items-center gap-1">← Back</button>
          <div className="bg-slate-900 rounded-xl border border-white/5 p-4 mb-4">
            <p className="text-sm font-semibold text-white">{selTask.title}</p>
            {taskStatus && (
              <div className="flex gap-4 mt-2">
                <span className="text-xs text-green-400">✓ {taskStatus.submittedCount} submitted</span>
                <span className="text-xs text-red-400">✗ {taskStatus.notSubmittedCount} not submitted</span>
                <span className="text-xs text-blue-400">📊 {subs.filter(s => s.marksAwarded !== null).length} graded</span>
              </div>
            )}
          </div>

          {/* Not submitted students */}
          {taskStatus?.notSubmitted?.length > 0 && (
            <div className="mb-4 bg-red-500/5 border border-red-500/15 rounded-xl p-4">
              <p className="text-xs text-red-400 font-semibold mb-2">✗ Not submitted ({taskStatus.notSubmitted.length} students):</p>
              <div className="flex gap-2 flex-wrap">
                {taskStatus.notSubmitted.map((s: any) => (
                  <span key={s.id} className="text-xs text-slate-400 bg-slate-800 px-2 py-1 rounded-lg border border-white/5">{s.name}</span>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-3">
            {subs.map(sub => {
              const isEditing = editId === sub.id
              return (
                <div key={sub.id} className={'bg-slate-900 rounded-xl border p-4 ' + (isEditing ? 'border-blue-500/30' : 'border-white/5')}>
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-semibold flex-shrink-0">{sub.student.name.charAt(0)}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white">{sub.student.name}</p>
                      <p className="text-xs text-slate-500">{sub.student.rollNumber ? 'Roll: ' + sub.student.rollNumber + ' · ' : ''}{sub.student.email}</p>
                      {sub.textAnswer && <div className="mt-2 p-2.5 bg-slate-800 rounded-lg border border-white/5 max-h-32 overflow-y-auto"><p className="text-xs text-slate-300 leading-relaxed">{sub.textAnswer}</p></div>}
                      {sub.fileUrl && <a href={'http://localhost:5000' + sub.fileUrl} target="_blank" className="mt-2 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300">📎 {sub.fileName}</a>}
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {sub.marksAwarded !== null && !isEditing && (
                        <div className="text-right">
                          <p className={'text-lg font-bold ' + gc(sub.marksAwarded, selTask.maxMarks)}>{sub.marksAwarded}<span className="text-slate-500 text-sm">/{selTask.maxMarks}</span></p>
                          <p className="text-[10px] text-slate-500">{Math.round((sub.marksAwarded/selTask.maxMarks)*100)}%</p>
                        </div>
                      )}
                      {!isEditing && (
                        <button onClick={() => { setEditId(sub.id); setEditMarks(sub.marksAwarded?.toString() || ''); setEditFeedback(sub.feedback || '') }} className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20">
                          {sub.marksAwarded !== null ? '✏ Edit' : '+ Grade'}
                        </button>
                      )}
                    </div>
                  </div>
                  {sub.feedback && !isEditing && <div className="mt-2 flex gap-2 ml-13 p-2 bg-slate-800 rounded-lg"><span className="text-purple-400 text-xs">💬</span><p className="text-xs text-slate-400">{sub.feedback}</p></div>}
                  {isEditing && (
                    <div className="mt-3 pt-3 border-t border-white/5 space-y-3">
                      <div className="flex gap-3 items-end">
                        <div>
                          <label className="block text-[10px] text-slate-500 uppercase mb-1">Marks / {selTask.maxMarks}</label>
                          <input type="number" value={editMarks} onChange={e => setEditMarks(e.target.value)} min={0} max={selTask.maxMarks} autoFocus className="w-24 bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500/50" />
                        </div>
                        <div className="flex-1">
                          <label className="block text-[10px] text-slate-500 uppercase mb-1">Feedback</label>
                          <input type="text" value={editFeedback} onChange={e => setEditFeedback(e.target.value)} placeholder="Feedback for student..." className="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => saveGrade(sub)} disabled={!editMarks || saving} className="px-4 py-2 bg-blue-500 text-white text-xs font-semibold rounded-lg disabled:opacity-40 flex items-center gap-1.5">
                          {saving ? <div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /> : '✓'} Save & Notify Student
                        </button>
                        <button onClick={() => setEditId(null)} className="px-4 py-2 bg-slate-800 text-slate-400 text-xs rounded-lg border border-white/5">Cancel</button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Teacher Results done!")

# Fix notification - student dashboard view link
with open("../frontend/app/(student)/student/page.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Fix material view URL if needed
content = content.replace("'http://localhost:5000' + preview.fileUrl", "'http://localhost:5000/api/v1/materials/' + preview.id + '/view'")

with open("../frontend/app/(student)/student/page.tsx", "w", encoding="utf-8") as f:
    f.write(content)
print("Student dashboard done!")

print("\n=== ALL FRONTEND DONE ===")