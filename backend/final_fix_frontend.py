import os

# Student Notifications Page - properly fetch
os.makedirs("../frontend/app/(student)/student/notifications", exist_ok=True)
with open("../frontend/app/(student)/student/notifications/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Notif = { id: string; title: string; body: string; type: string; isRead: boolean; createdAt: string; refId?: string }

export default function StudentNotificationsPage() {
  const { data: session } = useSession()
  const [notifs, setNotifs] = useState<Notif[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const token = session?.user?.backendToken

  const fetch_ = async () => {
    if (!token) return
    const res = await fetch(API + '/notifications', { headers: { Authorization: 'Bearer ' + token } })
    const d = await res.json()
    if (d.success) setNotifs(d.data)
    setLoading(false)
  }

  useEffect(() => { if (token) fetch_() }, [token])

  const markRead = async (id: string) => {
    await fetch(API + '/notifications/' + id + '/read', { method: 'PATCH', headers: { Authorization: 'Bearer ' + token } })
    setNotifs(p => p.map(n => n.id === id ? { ...n, isRead: true } : n))
  }

  const markAll = async () => {
    await fetch(API + '/notifications/read-all', { method: 'PATCH', headers: { Authorization: 'Bearer ' + token } })
    setNotifs(p => p.map(n => ({ ...n, isRead: true })))
  }

  const del = async (id: string) => {
    await fetch(API + '/notifications/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } })
    setNotifs(p => p.filter(n => n.id !== id))
  }

  const typeConf: Record<string, { icon: string; color: string; label: string }> = {
    task:         { icon: '📋', color: 'text-blue-400 bg-blue-500/10 border-blue-500/20', label: 'Task' },
    result:       { icon: '📊', color: 'text-green-400 bg-green-500/10 border-green-500/20', label: 'Result' },
    announcement: { icon: '📢', color: 'text-purple-400 bg-purple-500/10 border-purple-500/20', label: 'Update' },
    complaint:    { icon: '💬', color: 'text-orange-400 bg-orange-500/10 border-orange-500/20', label: 'Complaint' },
    system:       { icon: '⚙️', color: 'text-slate-400 bg-slate-700 border-white/10', label: 'System' },
  }

  const unread = notifs.filter(n => !n.isRead).length
  const filtered = filter === 'all' ? notifs : filter === 'unread' ? notifs.filter(n => !n.isRead) : notifs.filter(n => n.type === filter)

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Notifications</h1>
          <p className="text-slate-400 text-sm">{unread} unread</p>
        </div>
        {unread > 0 && <button onClick={markAll} className="text-xs text-blue-400 hover:text-blue-300 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg">Mark all read</button>}
      </div>

      <div className="flex gap-2 mb-5 flex-wrap">
        {['all','unread','task','result','announcement'].map(f => (
          <button key={f} onClick={() => setFilter(f)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filter === f ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
            {f === 'unread' && unread > 0 && <span className="ml-1.5 bg-blue-500 text-white text-[10px] px-1.5 rounded-full">{unread}</span>}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">🔕</p>
          <p className="text-white font-medium mb-1">No notifications</p>
          <p className="text-slate-500 text-sm">You're all caught up!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(n => {
            const tc = typeConf[n.type] || typeConf.system
            return (
              <div key={n.id} className={'flex items-start gap-4 p-4 rounded-2xl border transition-all cursor-pointer ' + (!n.isRead ? 'bg-slate-900 border-blue-500/20 hover:border-blue-500/30' : 'bg-slate-900 border-white/5 hover:border-white/10')}
                onClick={() => !n.isRead && markRead(n.id)}>
                <div className={'w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0 border ' + tc.color}>{tc.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-medium text-white">{n.title}</p>
                    {!n.isRead && <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />}
                    <span className={'text-[10px] px-1.5 py-0.5 rounded border font-medium ml-auto flex-shrink-0 ' + tc.color}>{tc.label}</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{n.body}</p>
                  <p className="text-[10px] text-slate-600 mt-1">{new Date(n.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true })}</p>
                </div>
                <button onClick={e => { e.stopPropagation(); del(n.id) }} className="text-slate-600 hover:text-red-400 w-7 h-7 flex items-center justify-center rounded-lg hover:bg-red-500/10 flex-shrink-0 text-sm transition-all">✕</button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
""")
print("Student Notifications done!")

# Student Materials - fetch ALL materials (no class filter by default)
os.makedirs("../frontend/app/(student)/student/materials", exist_ok=True)
with open("../frontend/app/(student)/student/materials/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

type Material = {
  id: string; title: string; fileName: string; fileUrl: string
  subject?: string | null; unit?: string | null; year?: number | null; examType?: string | null
  isPyq: boolean; fileSizeKb?: number | null; uploader: { name: string }
  classSection?: { name: string; section: string } | null
}

export default function StudentMaterialsPage() {
  const { data: session } = useSession()
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'notes'|'pyq'>('notes')
  const [fSubject, setFSubject] = useState('all')
  const [fUnit, setFUnit] = useState('all')
  const [fYear, setFYear] = useState('all')
  const [fExam, setFExam] = useState('all')
  const [search, setSearch] = useState('')
  const [preview, setPreview] = useState<Material | null>(null)
  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    // Fetch ALL materials - no class filter (everyone sees everything)
    const classId = localStorage.getItem('myClassId') || ''
    const url = classId ? API + '/materials?classId=' + classId : API + '/materials'
    fetch(url, { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json()).then(d => { if (d.success) setMaterials(d.data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [token])

  const notes = materials.filter(m => !m.isPyq)
  const pyqs = materials.filter(m => m.isPyq)
  const current = tab === 'notes' ? notes : pyqs

  const subjects = Array.from(new Set(current.map(m => m.subject).filter(Boolean))) as string[]
  const units = Array.from(new Set(notes.filter(m => fSubject === 'all' || m.subject === fSubject).map(m => m.unit).filter(Boolean))) as string[]
  const years = Array.from(new Set(pyqs.filter(m => fSubject === 'all' || m.subject === fSubject).map(m => m.year?.toString()).filter(Boolean))).sort((a,b) => (b||'').localeCompare(a||'')) as string[]

  const filtered = current.filter(m => {
    if (fSubject !== 'all' && m.subject !== fSubject) return false
    if (tab === 'notes' && fUnit !== 'all' && m.unit !== fUnit) return false
    if (tab === 'pyq' && fYear !== 'all' && m.year?.toString() !== fYear) return false
    if (tab === 'pyq' && fExam !== 'all' && m.examType !== fExam) return false
    if (search && !m.title.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const examLabel = (t?: string | null) => t === 'end_term' ? 'End Term' : t === 'mid_term' ? 'Mid Term' : t === 'unit_test' ? 'Unit Test' : t || ''

  const download = async (m: Material) => {
    if (!token) return
    const res = await fetch(API + '/materials/' + m.id + '/download', { headers: { Authorization: 'Bearer ' + token } })
    if (res.headers.get('content-type')?.includes('json')) {
      const d = await res.json()
      if (d.data?.fileUrl) window.open('http://localhost:5000' + d.data.fileUrl, '_blank')
    } else {
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = m.fileName; a.click()
    }
  }

  const reset = () => { setFSubject('all'); setFUnit('all'); setFYear('all'); setFExam('all') }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-white mb-1">Study Materials</h1>
        <p className="text-slate-400 text-sm">Notes and PYQs uploaded by your teachers</p>
      </div>

      <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-2xl p-1.5 mb-5 w-fit">
        <button onClick={() => { setTab('notes'); reset() }} className={'px-5 py-2.5 rounded-xl text-sm font-medium transition-all ' + (tab === 'notes' ? 'bg-green-500 text-white' : 'text-slate-400 hover:text-white')}>
          📚 Notes ({notes.length})
        </button>
        <button onClick={() => { setTab('pyq'); reset() }} className={'px-5 py-2.5 rounded-xl text-sm font-medium transition-all ' + (tab === 'pyq' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
          📋 PYQs ({pyqs.length})
        </button>
      </div>

      <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder={'Search ' + (tab === 'notes' ? 'notes' : 'papers') + '...'} className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 mb-4" />

      <div className="bg-slate-900 rounded-2xl border border-white/5 p-4 mb-5 space-y-4">
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">Subject</p>
          <div className="flex gap-2 flex-wrap">
            <button onClick={() => { setFSubject('all'); setFUnit('all'); setFYear('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fSubject === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>
              All ({current.length})
            </button>
            {subjects.map(s => (
              <button key={s} onClick={() => { setFSubject(s); setFUnit('all'); setFYear('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fSubject === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>
                {s.length > 22 ? s.slice(0,22)+'...' : s} ({current.filter(m => m.subject === s).length})
              </button>
            ))}
          </div>
        </div>

        {tab === 'notes' && fSubject !== 'all' && units.length > 0 && (
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">Unit</p>
            <div className="flex gap-2 flex-wrap">
              <button onClick={() => setFUnit('all')} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fUnit === 'all' ? 'bg-purple-500 text-white border-purple-500' : 'bg-slate-800 text-slate-400 border-white/5')}>All Units</button>
              {units.map(u => (
                <button key={u} onClick={() => setFUnit(u)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fUnit === u ? 'bg-purple-500 text-white border-purple-500' : 'bg-slate-800 text-slate-400 border-white/5')}>
                  {u} ({notes.filter(m => m.subject === fSubject && m.unit === u).length})
                </button>
              ))}
            </div>
          </div>
        )}

        {tab === 'pyq' && years.length > 0 && (
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">Year</p>
            <div className="flex gap-2 flex-wrap">
              <button onClick={() => { setFYear('all'); setFExam('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fYear === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>All</button>
              {years.map(y => (
                <button key={y} onClick={() => { setFYear(y); setFExam('all') }} className={'px-4 py-1.5 rounded-lg text-sm font-medium border ' + (fYear === y ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>{y}</button>
              ))}
            </div>
          </div>
        )}

        {tab === 'pyq' && fYear !== 'all' && (
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">Exam Type</p>
            <div className="flex gap-2">
              <button onClick={() => setFExam('all')} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fExam === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>All</button>
              {['end_term','mid_term','unit_test'].map(t => (
                <button key={t} onClick={() => setFExam(t)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border ' + (fExam === t ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>{examLabel(t)}</button>
              ))}
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-slate-500 mb-3">Showing {filtered.length} of {current.length}</p>

      {loading ? (
        <div className="text-center py-12"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">{tab === 'notes' ? '📚' : '📋'}</p>
          <p className="text-white font-medium mb-1">No {tab === 'notes' ? 'notes' : 'papers'} yet</p>
          <p className="text-slate-500 text-sm">Ask your teacher to upload materials</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map(m => (
            <div key={m.id} className="bg-slate-900 rounded-2xl border border-white/5 hover:border-white/10 transition-all p-5">
              <div className="flex items-start gap-4 mb-4">
                <div className={'w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0 ' + (m.isPyq ? 'bg-blue-500/10 border border-blue-500/20' : 'bg-green-500/10 border border-green-500/20')}>
                  {m.isPyq ? '📋' : '📚'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate mb-1.5">{m.title}</p>
                  <div className="flex gap-1.5 flex-wrap">
                    {m.subject && <span className="text-[10px] px-2 py-0.5 rounded-full border text-green-400 bg-green-500/10 border-green-500/20">{m.subject.length > 18 ? m.subject.slice(0,18)+'...' : m.subject}</span>}
                    {m.unit && <span className="text-[10px] px-2 py-0.5 rounded-full border text-purple-400 bg-purple-500/10 border-purple-500/20">{m.unit}</span>}
                    {m.year && <span className="text-[10px] px-2 py-0.5 rounded-full border text-blue-400 bg-blue-500/10 border-blue-500/20">{m.year}</span>}
                    {m.examType && <span className="text-[10px] px-2 py-0.5 rounded-full border text-orange-400 bg-orange-500/10 border-orange-500/20">{examLabel(m.examType)}</span>}
                  </div>
                  <p className="text-[10px] text-slate-600 mt-1">By {m.uploader.name}{m.fileSizeKb ? ' · ' + (m.fileSizeKb >= 1024 ? (m.fileSizeKb/1024).toFixed(1)+'MB' : m.fileSizeKb+'KB') : ''}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setPreview(m)} className="flex-1 py-2 bg-slate-800 text-slate-300 border border-white/10 rounded-xl text-xs font-medium hover:border-white/20">👁 View</button>
                <button onClick={() => download(m)} className="flex-1 py-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-xl text-xs font-medium hover:bg-blue-500/20">⬇ Download</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {preview && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-5xl h-[90vh] flex flex-col shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b border-white/5 flex-shrink-0">
              <div>
                <p className="text-sm font-medium text-white">{preview.title}</p>
                <p className="text-xs text-slate-500">{preview.subject} {preview.unit ? '· ' + preview.unit : ''} {preview.year ? '· ' + preview.year : ''}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => download(preview)} className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20">⬇ Download</button>
                <button onClick={() => setPreview(null)} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5">✕</button>
              </div>
            </div>
            <div className="flex-1 overflow-hidden rounded-b-2xl bg-white">
              <iframe
                src={'http://localhost:5000/api/v1/materials/' + preview.id + '/view'}
                className="w-full h-full border-0"
                title={preview.title}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Student Materials done!")

print("\n=== ALL FRONTEND DONE ===")