import os

# Student Results - total marks aggregate
os.makedirs("../frontend/app/(student)/student/results", exist_ok=True)
with open("../frontend/app/(student)/student/results/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Submission = {
  id: string; taskId: string; status: string
  marksAwarded?: number | null; feedback?: string | null
  submittedAt: string
  task: { title: string; maxMarks: number; taskType: string; subjectName?: string | null }
}

export default function StudentResultsPage() {
  const { data: session } = useSession()
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    fetch(API + '/submissions', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json()).then(d => { if (d.success) setSubmissions(d.data); setLoading(false) })
  }, [token])

  const graded = submissions.filter(s => s.status === 'graded' && s.marksAwarded !== null)
  const pending = submissions.filter(s => s.status !== 'graded')
  const totalMarksObtained = graded.reduce((sum, s) => sum + (s.marksAwarded || 0), 0)
  const totalMaxMarks = graded.reduce((sum, s) => sum + s.task.maxMarks, 0)
  const overallPct = totalMaxMarks > 0 ? Math.round((totalMarksObtained / totalMaxMarks) * 100) : 0

  const getGrade = (m: number, max: number) => {
    const p = (m/max)*100
    return p >= 80 ? { grade: 'A', color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' }
      : p >= 60 ? { grade: 'B', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' }
      : p >= 40 ? { grade: 'C', color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' }
      : { grade: 'F', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' }
  }

  const typeIcon: Record<string, string> = { assignment: '📝', class_test: '✍️', quiz: '❓', project: '🔬' }
  const filtered = filter === 'graded' ? graded : filter === 'pending' ? pending : submissions

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">My Results</h1>
        <p className="text-slate-400 text-sm">View your marks and total performance</p>
      </div>

      {/* TOTAL MARKS SUMMARY - prominent card */}
      {graded.length > 0 && (
        <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-2xl p-6 mb-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Total Marks Obtained</p>
              <p className="text-4xl font-bold text-white">
                {totalMarksObtained}<span className="text-2xl text-slate-500">/{totalMaxMarks}</span>
              </p>
              <p className="text-sm text-slate-400 mt-1">across {graded.length} graded tasks</p>
            </div>
            <div className="text-center">
              <div className={'w-20 h-20 rounded-full border-4 flex items-center justify-center ' + (overallPct >= 80 ? 'border-green-500 text-green-400' : overallPct >= 60 ? 'border-blue-500 text-blue-400' : overallPct >= 40 ? 'border-yellow-500 text-yellow-400' : 'border-red-500 text-red-400')}>
                <span className="text-2xl font-bold">{overallPct}%</span>
              </div>
              <p className="text-xs text-slate-500 mt-2">Overall</p>
            </div>
            <div className="flex gap-3">
              {[
                { l: 'Graded', v: graded.length, c: 'text-green-400' },
                { l: 'Pending', v: pending.length, c: 'text-yellow-400' },
              ].map(s => (
                <div key={s.l} className="bg-slate-900/50 rounded-xl px-4 py-3 text-center min-w-[80px]">
                  <p className={'text-xl font-bold ' + s.c}>{s.v}</p>
                  <p className="text-[10px] text-slate-500 mt-1">{s.l}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-2 mb-6">
        {[
          { k: 'all', l: 'All', count: submissions.length },
          { k: 'graded', l: 'Graded', count: graded.length },
          { k: 'pending', l: 'Pending', count: pending.length },
        ].map(tab => (
          <button key={tab.k} onClick={() => setFilter(tab.k)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filter === tab.k ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>
            {tab.l} <span className="ml-1 opacity-60">{tab.count}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-16"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">📊</p>
          <p className="text-white font-medium mb-1">No results yet</p>
          <p className="text-slate-500 text-sm">Submit assignments to see your results here</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map(sub => {
            const isGraded = sub.status === 'graded' && sub.marksAwarded !== null
            const g = isGraded ? getGrade(sub.marksAwarded!, sub.task.maxMarks) : null
            return (
              <div key={sub.id} className={'bg-slate-900 rounded-2xl border transition-all p-5 ' + (isGraded ? 'border-white/10 hover:border-white/15' : 'border-white/5')}>
                <div className="flex items-start gap-4">
                  {isGraded && g ? (
                    <div className={'w-14 h-14 rounded-2xl border flex items-center justify-center flex-shrink-0 ' + g.bg}>
                      <span className={'text-2xl font-bold ' + g.color}>{g.grade}</span>
                    </div>
                  ) : (
                    <div className="w-14 h-14 rounded-2xl border border-white/5 bg-slate-800 flex items-center justify-center flex-shrink-0 text-2xl">{typeIcon[sub.task.taskType] || '📝'}</div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-white mb-0.5">{sub.task.title}</p>
                    <p className="text-xs text-slate-500">{sub.task.subjectName || 'General'} · Submitted {new Date(sub.submittedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                    {isGraded && (
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                          <span>Score</span><span>{sub.marksAwarded}/{sub.task.maxMarks} · {Math.round((sub.marksAwarded!/sub.task.maxMarks)*100)}%</span>
                        </div>
                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div className={'h-full rounded-full transition-all ' + (g?.color.replace('text-', 'bg-'))} style={{ width: Math.round((sub.marksAwarded!/sub.task.maxMarks)*100) + '%' }} />
                        </div>
                      </div>
                    )}
                    {sub.feedback && <div className="mt-3 flex gap-2 p-3 bg-slate-800 rounded-xl border border-white/5"><span className="text-purple-400 flex-shrink-0">💬</span><p className="text-xs text-slate-400 leading-relaxed">{sub.feedback}</p></div>}
                  </div>
                  <div className="flex-shrink-0 text-right">
                    {isGraded ? <p className={'text-2xl font-bold ' + g?.color}>{sub.marksAwarded}<span className="text-sm text-slate-500">/{sub.task.maxMarks}</span></p>
                      : <span className="text-xs text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 px-2.5 py-1 rounded-lg">Awaiting</span>}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
""")
print("Student Results done!")

print("\n=== Materials view fix is server-side, no frontend change needed beyond iframe (already used) ===")
print("Done!")