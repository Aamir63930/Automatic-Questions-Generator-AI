import os

# ═══════════════════════════════════
# TEACHER NOTIFICATIONS - Multi target
# ═══════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/notifications", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/notifications/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type Notif = { id: string; title: string; body: string; type: string; isRead: boolean; createdAt: string }
type ClassSection = { id: string; name: string; section: string; branch: string; _count: { students: number } }

export default function TeacherNotificationsPage() {
  const { data: session } = useSession()
  const [tab, setTab] = useState<'inbox'|'send'|'sent'>('inbox')
  const [notifs, setNotifs] = useState<Notif[]>([])
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [sent, setSent] = useState<any[]>([])
  const [filter, setFilter] = useState('all')
  const [form, setForm] = useState({ title: '', message: '', target: 'all_students', classIds: [] as string[], priority: 'normal' })
  const [sending, setSending] = useState(false)
  const [sendSuccess, setSendSuccess] = useState(false)

  const token = session?.user?.backendToken

  const fetchNotifs = async () => {
    if (!token) return
    const res = await fetch(API + '/notifications', { headers: { Authorization: 'Bearer ' + token } })
    const data = await res.json()
    if (data.success) setNotifs(data.data)
  }

  const fetchClasses = async () => {
    if (!token) return
    const res = await fetch(API + '/auth/classes', { headers: { Authorization: 'Bearer ' + token } })
    const data = await res.json()
    if (data.success) setClasses(data.data)
  }

  useEffect(() => { if (token) { fetchNotifs(); fetchClasses() } }, [token])

  const unread = notifs.filter(n => !n.isRead).length

  const typeConf: Record<string, { icon: string; color: string; label: string }> = {
    task: { icon: '📋', color: 'text-blue-400 bg-blue-500/10 border-blue-500/20', label: 'Task' },
    result: { icon: '📊', color: 'text-green-400 bg-green-500/10 border-green-500/20', label: 'Result' },
    announcement: { icon: '📢', color: 'text-purple-400 bg-purple-500/10 border-purple-500/20', label: 'Update' },
    complaint: { icon: '💬', color: 'text-orange-400 bg-orange-500/10 border-orange-500/20', label: 'Complaint' },
    system: { icon: '⚙️', color: 'text-slate-400 bg-slate-700 border-white/10', label: 'System' },
  }

  const filtered = filter === 'all' ? notifs : filter === 'unread' ? notifs.filter(n => !n.isRead) : notifs.filter(n => n.type === filter)

  const markRead = async (id: string) => {
    await fetch(API + '/notifications/' + id + '/read', { method: 'PATCH', headers: { Authorization: 'Bearer ' + token } })
    fetchNotifs()
  }

  const markAll = async () => {
    await fetch(API + '/notifications/read-all', { method: 'PATCH', headers: { Authorization: 'Bearer ' + token } })
    fetchNotifs()
  }

  const deleteN = async (id: string) => {
    await fetch(API + '/notifications/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } })
    fetchNotifs()
  }

  const toggleClass = (id: string) => {
    setForm(p => ({
      ...p,
      classIds: p.classIds.includes(id) ? p.classIds.filter(c => c !== id) : [...p.classIds, id]
    }))
  }

  const handleSend = async () => {
    if (!form.title || !form.message || !token) return
    setSending(true)
    const res = await fetch(API + '/notifications/send', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: form.title, body: form.message, type: 'announcement', target: form.target, classIds: form.classIds })
    })
    const data = await res.json()
    if (data.success) {
      setSent(prev => [{ id: Date.now(), ...form, sentAt: new Date().toLocaleString('en-IN'), recipients: data.data.sent }, ...prev])
      setSendSuccess(true)
      setForm({ title: '', message: '', target: 'all_students', classIds: [], priority: 'normal' })
      setTimeout(() => { setSendSuccess(false); setTab('sent') }, 1500)
    }
    setSending(false)
  }

  const targetLabel = (t: string) => t === 'all_students' ? 'All Students' : t === 'specific_classes' ? 'Specific Classes' : t === 'teachers' ? 'All Teachers' : 'Everyone'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Notifications</h1>
          <p className="text-slate-400 text-sm">{unread} unread</p>
        </div>
      </div>

      <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-xl p-1 mb-6 w-fit">
        {[
          { k: 'inbox', l: '📥 Inbox', b: unread },
          { k: 'send', l: '📢 Send Update' },
          { k: 'sent', l: '✅ Sent', b: sent.length },
        ].map(t => (
          <button key={t.k} onClick={() => { setTab(t.k as any); if (t.k === 'inbox') fetchNotifs() }} className={'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ' + (tab === t.k ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
            {t.l}
            {t.b ? <span className={'text-[10px] px-1.5 py-0.5 rounded-full font-medium ' + (tab === t.k ? 'bg-white/20' : 'bg-blue-500 text-white')}>{t.b}</span> : null}
          </button>
        ))}
      </div>

      {tab === 'inbox' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex gap-2 flex-wrap">
              {['all', 'unread', 'task', 'complaint', 'announcement'].map(f => (
                <button key={f} onClick={() => setFilter(f)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filter === f ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
            {unread > 0 && <button onClick={markAll} className="text-xs text-blue-400 hover:text-blue-300">Mark all read</button>}
          </div>
          {filtered.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">🔕</p><p className="text-white font-medium">No notifications</p>
            </div>
          ) : (
            <div className="space-y-2">
              {filtered.map(n => {
                const tc = typeConf[n.type] || typeConf.system
                return (
                  <div key={n.id} className={'flex items-start gap-4 p-4 rounded-2xl border transition-all ' + (!n.isRead ? 'bg-slate-900 border-blue-500/20' : 'bg-slate-900 border-white/5')}>
                    <div className={'w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0 border ' + tc.color}>{tc.icon}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-medium text-white">{n.title}</p>
                        {!n.isRead && <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />}
                        <span className={'text-[10px] px-1.5 py-0.5 rounded border font-medium ml-auto ' + tc.color}>{tc.label}</span>
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed">{n.body}</p>
                      <p className="text-[10px] text-slate-600 mt-1">{new Date(n.createdAt).toLocaleString('en-IN')}</p>
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      {!n.isRead && <button onClick={() => markRead(n.id)} className="text-[10px] px-2 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg">Read</button>}
                      <button onClick={() => deleteN(n.id)} className="text-[10px] px-2 py-1 bg-slate-800 text-slate-500 border border-white/5 rounded-lg hover:text-red-400">✕</button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {tab === 'send' && (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-6">
          <h2 className="text-base font-medium text-white mb-5">Send Update to Students</h2>
          <div className="space-y-5">
            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Send To</label>
              <div className="grid grid-cols-2 gap-2 mb-3">
                {[
                  { v: 'all_students', l: '👥 All Students', d: 'Everyone in college' },
                  { v: 'specific_classes', l: '🏫 Specific Classes', d: 'Select classes below' },
                  { v: 'teachers', l: '👨‍🏫 All Teachers', d: 'Faculty members only' },
                  { v: 'all', l: '🌐 Everyone', d: 'Students + Teachers' },
                ].map(opt => (
                  <button key={opt.v} onClick={() => setForm(p => ({ ...p, target: opt.v, classIds: [] }))} className={'p-3 rounded-xl border text-left transition-all ' + (form.target === opt.v ? 'border-blue-500/50 bg-blue-500/10' : 'border-white/5 bg-slate-800 hover:border-white/15')}>
                    <p className="text-sm font-medium text-white">{opt.l}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{opt.d}</p>
                  </button>
                ))}
              </div>

              {form.target === 'specific_classes' && (
                <div>
                  <p className="text-xs text-slate-500 mb-2">Select Classes:</p>
                  <div className="flex gap-2 flex-wrap">
                    {classes.map(c => (
                      <button key={c.id} onClick={() => toggleClass(c.id)} className={'px-3 py-2 rounded-xl text-xs font-medium border transition-all ' + (form.classIds.includes(c.id) ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                        {c.name} {c.section} — {c.branch}
                        <span className="ml-1 opacity-60">({c._count.students})</span>
                        {form.classIds.includes(c.id) && ' ✓'}
                      </button>
                    ))}
                    {classes.length === 0 && <p className="text-xs text-slate-500">No classes created yet</p>}
                  </div>
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Priority</label>
              <div className="flex gap-2">
                {[['low', '🟢 Low'], ['normal', '🟡 Normal'], ['high', '🔴 High']].map(([v, l]) => (
                  <button key={v} onClick={() => setForm(p => ({ ...p, priority: v }))} className={'px-4 py-2 rounded-xl text-xs font-medium border transition-all ' + (form.priority === v ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>{l}</button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Title</label>
              <input type="text" value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} placeholder="Notification title..." className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
            </div>

            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Message</label>
              <textarea value={form.message} onChange={e => setForm(p => ({ ...p, message: e.target.value }))} placeholder="Write your message..." rows={4} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 resize-none" />
            </div>

            {form.title && form.message && (
              <div className="bg-slate-800 rounded-xl p-4 border border-white/5">
                <p className="text-[10px] text-slate-500 uppercase mb-2">Preview</p>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-sm">📢</div>
                  <div>
                    <p className="text-sm font-medium text-white">{form.title}</p>
                    <p className="text-xs text-slate-400 mt-1">{form.message}</p>
                    <p className="text-[10px] text-slate-500 mt-1">To: {targetLabel(form.target)}{form.target === 'specific_classes' && form.classIds.length > 0 ? ' (' + form.classIds.length + ' classes)' : ''}</p>
                  </div>
                </div>
              </div>
            )}

            <button onClick={handleSend} disabled={!form.title || !form.message || sending || sendSuccess || (form.target === 'specific_classes' && form.classIds.length === 0)} className={'w-full py-3 text-sm font-medium rounded-xl transition-all flex items-center justify-center gap-2 ' + (sendSuccess ? 'bg-green-500 text-white' : 'bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed')}>
              {sendSuccess ? '✓ Sent Successfully!' : sending ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Sending...</> : '📢 Send Notification'}
            </button>
          </div>
        </div>
      )}

      {tab === 'sent' && (
        <div className="space-y-3">
          {sent.length === 0 ? (
            <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
              <p className="text-4xl mb-3">📭</p>
              <p className="text-white font-medium mb-1">No updates sent</p>
              <button onClick={() => setTab('send')} className="mt-3 px-4 py-2 bg-blue-500 text-white text-sm rounded-xl">Send First Update</button>
            </div>
          ) : sent.map(u => (
            <div key={u.id} className="bg-slate-900 rounded-2xl border border-white/5 p-5">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-xl flex-shrink-0">📢</div>
                <div>
                  <p className="text-sm font-medium text-white mb-1">{u.title}</p>
                  <p className="text-xs text-slate-400 mb-2">{u.message}</p>
                  <div className="flex gap-2 flex-wrap">
                    <span className="text-[10px] text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded">To: {targetLabel(u.target)}</span>
                    <span className="text-[10px] text-green-400 bg-green-500/10 border border-green-500/20 px-2 py-0.5 rounded">✓ {u.recipients} recipients</span>
                    <span className="text-[10px] text-slate-500">{u.sentAt}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
""")
print("Teacher Notifications done!")

# ═══════════════════════════════════
# STUDENT MATERIALS - Subject+Unit+PYQ filter
# ═══════════════════════════════════
os.makedirs("../frontend/app/(student)/student/materials", exist_ok=True)
with open("../frontend/app/(student)/student/materials/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type Material = {
  id: string
  title: string
  fileName: string
  fileUrl: string
  fileType: string
  subject?: string | null
  unit?: string | null
  year?: number | null
  examType?: string | null
  isPyq: boolean
  fileSizeKb?: number | null
  createdAt: string
  uploader: { name: string }
}

export default function StudentMaterialsPage() {
  const { data: session } = useSession()
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'notes'|'pyq'>('notes')
  const [filterSubject, setFilterSubject] = useState('all')
  const [filterUnit, setFilterUnit] = useState('all')
  const [filterYear, setFilterYear] = useState('all')
  const [filterExam, setFilterExam] = useState('all')
  const [search, setSearch] = useState('')
  const [previewMaterial, setPreviewMaterial] = useState<Material | null>(null)

  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    fetch(API + '/materials', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(data => { if (data.success) setMaterials(data.data); setLoading(false) })
  }, [token])

  const notes = materials.filter(m => !m.isPyq)
  const pyqs = materials.filter(m => m.isPyq)

  const current = tab === 'notes' ? notes : pyqs

  const allSubjects = Array.from(new Set(current.map(m => m.subject).filter(Boolean))) as string[]
  const allUnits = Array.from(new Set(notes.filter(m => m.subject === filterSubject || filterSubject === 'all').map(m => m.unit).filter(Boolean))) as string[]
  const allYears = Array.from(new Set(pyqs.map(m => m.year?.toString()).filter(Boolean))).sort((a,b) => (b||'').localeCompare(a||'')) as string[]

  const filtered = current.filter(m => {
    if (filterSubject !== 'all' && m.subject !== filterSubject) return false
    if (tab === 'notes' && filterUnit !== 'all' && m.unit !== filterUnit) return false
    if (tab === 'pyq' && filterYear !== 'all' && m.year?.toString() !== filterYear) return false
    if (tab === 'pyq' && filterExam !== 'all' && m.examType !== filterExam) return false
    if (search && !m.title.toLowerCase().includes(search.toLowerCase()) && !m.subject?.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const handleDownload = async (m: Material) => {
    if (!token) return
    const res = await fetch(API + '/materials/' + m.id + '/download', { headers: { Authorization: 'Bearer ' + token } })
    if (res.headers.get('content-type')?.includes('application/json')) {
      const data = await res.json()
      if (data.data?.fileUrl) window.open('http://localhost:5000' + data.data.fileUrl, '_blank')
    } else {
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = m.fileName; a.click()
      URL.revokeObjectURL(url)
    }
  }

  const examLabel = (t?: string | null) => t === 'end_term' ? 'End Term' : t === 'mid_term' ? 'Mid Term' : t === 'unit_test' ? 'Unit Test' : t || ''

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-white mb-1">Study Materials</h1>
        <p className="text-slate-400 text-sm">Access notes, previous year papers uploaded by your teachers</p>
      </div>

      {/* Main tabs */}
      <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-xl p-1 mb-6 w-fit">
        <button onClick={() => { setTab('notes'); setFilterSubject('all'); setFilterUnit('all') }} className={'px-6 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ' + (tab === 'notes' ? 'bg-green-500 text-white' : 'text-slate-400 hover:text-white')}>
          📚 Notes & Materials <span className="opacity-70">({notes.length})</span>
        </button>
        <button onClick={() => { setTab('pyq'); setFilterSubject('all'); setFilterYear('all') }} className={'px-6 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ' + (tab === 'pyq' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
          📋 Previous Year QPs <span className="opacity-70">({pyqs.length})</span>
        </button>
      </div>

      {/* Search */}
      <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder={'Search ' + (tab === 'notes' ? 'notes' : 'PYQs') + '...'} className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600 mb-4" />

      {/* Filters */}
      <div className="bg-slate-900 rounded-2xl border border-white/5 p-4 mb-5 space-y-3">
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Subject</p>
          <div className="flex gap-2 flex-wrap">
            <button onClick={() => { setFilterSubject('all'); setFilterUnit('all'); setFilterYear('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterSubject === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
              All <span className="opacity-60 ml-1">{current.length}</span>
            </button>
            {allSubjects.map(s => (
              <button key={s} onClick={() => { setFilterSubject(s); setFilterUnit('all'); setFilterYear('all') }} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterSubject === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                {s.length > 22 ? s.slice(0,22)+'...' : s} <span className="opacity-60 ml-1">{current.filter(m => m.subject === s).length}</span>
              </button>
            ))}
          </div>
        </div>

        {tab === 'notes' && filterSubject !== 'all' && allUnits.length > 0 && (
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Unit</p>
            <div className="flex gap-2 flex-wrap">
              <button onClick={() => setFilterUnit('all')} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterUnit === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>All Units</button>
              {allUnits.map(u => (
                <button key={u} onClick={() => setFilterUnit(u)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterUnit === u ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                  {u} <span className="opacity-60 ml-1">{notes.filter(m => m.subject === filterSubject && m.unit === u).length}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {tab === 'pyq' && filterSubject !== 'all' && allYears.length > 0 && (
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Year</p>
            <div className="flex gap-2 flex-wrap">
              <button onClick={() => setFilterYear('all')} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterYear === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>All Years</button>
              {allYears.map(y => (
                <button key={y} onClick={() => setFilterYear(y)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterYear === y ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                  {y} <span className="opacity-60 ml-1">{pyqs.filter(m => m.subject === filterSubject && m.year?.toString() === y).length}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {tab === 'pyq' && filterYear !== 'all' && (
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Exam Type</p>
            <div className="flex gap-2">
              <button onClick={() => setFilterExam('all')} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterExam === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>All</button>
              {['end_term', 'mid_term', 'unit_test'].map(t => (
                <button key={t} onClick={() => setFilterExam(t)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterExam === t ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5')}>{examLabel(t)}</button>
              ))}
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-slate-500 mb-3">Showing {filtered.length} of {current.length} {tab === 'notes' ? 'notes' : 'papers'}</p>

      {loading ? (
        <div className="text-center py-12"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : filtered.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">📭</p>
          <p className="text-white font-medium mb-1">No {tab === 'notes' ? 'notes' : 'papers'} found</p>
          <p className="text-slate-500 text-sm">Try changing filters or ask your teacher to upload materials</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map(m => (
            <div key={m.id} className="bg-slate-900 rounded-2xl border border-white/5 hover:border-white/10 transition-all p-5 group">
              <div className="flex items-start gap-4 mb-4">
                <div className={'w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0 ' + (m.isPyq ? 'bg-blue-500/10 border border-blue-500/20' : 'bg-green-500/10 border border-green-500/20')}>
                  {m.isPyq ? '📋' : '📚'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate mb-1">{m.title}</p>
                  <div className="flex gap-2 flex-wrap">
                    {m.subject && <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-green-400 bg-green-500/10 border-green-500/20">{m.subject.length > 20 ? m.subject.slice(0,20)+'...' : m.subject}</span>}
                    {m.unit && <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-purple-400 bg-purple-500/10 border-purple-500/20">{m.unit}</span>}
                    {m.year && <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-blue-400 bg-blue-500/10 border-blue-500/20">{m.year}</span>}
                    {m.examType && <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-orange-400 bg-orange-500/10 border-orange-500/20">{examLabel(m.examType)}</span>}
                  </div>
                  <p className="text-[10px] text-slate-600 mt-1">By {m.uploader.name} · {m.fileSizeKb ? (m.fileSizeKb/1024).toFixed(1)+'MB' : ''}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setPreviewMaterial(m)} className="flex-1 py-2 bg-slate-800 text-slate-300 border border-white/10 rounded-xl text-xs font-medium hover:border-white/20 transition-all">
                  👁 View
                </button>
                <button onClick={() => handleDownload(m)} className="flex-1 py-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-xl text-xs font-medium hover:bg-blue-500/20 transition-all">
                  ⬇ Download
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewMaterial && (
        <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-5xl h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-white/5">
              <div>
                <p className="text-sm font-medium text-white">{previewMaterial.title}</p>
                <p className="text-xs text-slate-500">{previewMaterial.subject} {previewMaterial.unit ? '· ' + previewMaterial.unit : ''} {previewMaterial.year ? '· ' + previewMaterial.year : ''}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleDownload(previewMaterial)} className="text-xs px-3 py-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg hover:bg-blue-500/20">⬇ Download</button>
                <button onClick={() => setPreviewMaterial(null)} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center text-lg">✕</button>
              </div>
            </div>
            <div className="flex-1 overflow-hidden rounded-b-2xl">
              <iframe src={'http://localhost:5000' + previewMaterial.fileUrl} className="w-full h-full" title={previewMaterial.title} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Student Materials done!")

# ═══════════════════════════════════
# TEACHER MATERIALS - Unit + Subject
# ═══════════════════════════════════
os.makedirs("../frontend/app/(dashboard)/teacher/materials", exist_ok=True)
with open("../frontend/app/(dashboard)/teacher/materials/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type Material = {
  id: string
  title: string
  fileName: string
  fileUrl: string
  fileType: string
  subject?: string | null
  unit?: string | null
  year?: number | null
  examType?: string | null
  isPyq: boolean
  fileSizeKb?: number | null
  createdAt: string
  uploader: { name: string }
}

const SUBJECTS = ['Data Structures and Algorithms','Operating Systems','Computer Networks','Database Management Systems','Software Engineering','Artificial Intelligence','Machine Learning','Web Technologies','Object Oriented Programming','Discrete Mathematics']
const UNITS = ['Unit 1','Unit 2','Unit 3','Unit 4','Unit 5','All Units']

export default function TeacherMaterialsPage() {
  const { data: session } = useSession()
  const [materials, setMaterials] = useState<Material[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'all'|'notes'|'pyq'>('all')
  const [filterSubject, setFilterSubject] = useState('all')
  const [showUpload, setShowUpload] = useState(false)
  const [form, setForm] = useState({ title: '', subject: '', unit: '', fileType: 'notes', isPyq: false, year: '', examType: '' })
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)

  const token = session?.user?.backendToken

  const fetchMaterials = async () => {
    if (!token) return
    const res = await fetch(API + '/materials', { headers: { Authorization: 'Bearer ' + token } })
    const data = await res.json()
    if (data.success) setMaterials(data.data)
    setLoading(false)
  }

  useEffect(() => { if (token) fetchMaterials() }, [token])

  const current = materials.filter(m => {
    if (tab === 'notes' && m.isPyq) return false
    if (tab === 'pyq' && !m.isPyq) return false
    if (filterSubject !== 'all' && m.subject !== filterSubject) return false
    return true
  })

  const allSubjects = Array.from(new Set(materials.map(m => m.subject).filter(Boolean))) as string[]

  const handleUpload = async () => {
    if (!file || !token) return
    setUploading(true)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('title', form.title || file.name)
    fd.append('fileType', form.isPyq ? 'pyq' : form.fileType)
    fd.append('isPyq', form.isPyq ? 'true' : 'false')
    if (form.subject) fd.append('subject', form.subject)
    if (form.unit && !form.isPyq) fd.append('unit', form.unit)
    if (form.year) fd.append('year', form.year)
    if (form.examType) fd.append('examType', form.examType)

    const res = await fetch(API + '/materials/upload', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token },
      body: fd
    })
    const data = await res.json()
    if (data.success) {
      await fetchMaterials()
      setShowUpload(false)
      setFile(null)
      setForm({ title: '', subject: '', unit: '', fileType: 'notes', isPyq: false, year: '', examType: '' })
    }
    setUploading(false)
  }

  const handleDelete = async (id: string) => {
    if (!token || !confirm('Delete this material?')) return
    await fetch(API + '/materials/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } })
    fetchMaterials()
  }

  const examLabel = (t?: string | null) => t === 'end_term' ? 'End Term' : t === 'mid_term' ? 'Mid Term' : t === 'unit_test' ? 'Unit Test' : t || ''

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white mb-1">Materials</h1>
          <p className="text-slate-400 text-sm">Upload notes (unit-wise) and PYQs (year-wise) for students</p>
        </div>
        <button onClick={() => setShowUpload(true)} className="px-4 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600">+ Upload Material</button>
      </div>

      <div className="flex gap-2 mb-5 flex-wrap">
        <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-xl p-1">
          {[['all','📁 All',materials.length],['notes','📚 Notes',materials.filter(m=>!m.isPyq).length],['pyq','📋 PYQs',materials.filter(m=>m.isPyq).length]].map(([k,l,c]) => (
            <button key={k as string} onClick={() => setTab(k as any)} className={'px-4 py-2 rounded-lg text-xs font-medium transition-all ' + (tab === k ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white')}>
              {l as string} <span className="opacity-70 ml-1">({c as number})</span>
            </button>
          ))}
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => setFilterSubject('all')} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterSubject === 'all' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>All Subjects</button>
          {allSubjects.map(s => (
            <button key={s} onClick={() => setFilterSubject(s)} className={'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ' + (filterSubject === s ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-slate-900 text-slate-400 border-white/5 hover:border-white/15')}>
              {s.length > 20 ? s.slice(0,20)+'...' : s}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
      ) : current.length === 0 ? (
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-12 text-center">
          <p className="text-4xl mb-3">📭</p>
          <p className="text-white font-medium mb-1">No materials yet</p>
          <button onClick={() => setShowUpload(true)} className="mt-3 px-4 py-2 bg-blue-500 text-white text-sm rounded-xl hover:bg-blue-600">Upload First Material</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {current.map(m => (
            <div key={m.id} className="bg-slate-900 rounded-2xl border border-white/5 hover:border-white/10 transition-all p-5">
              <div className="flex items-start gap-4 mb-4">
                <div className={'w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0 ' + (m.isPyq ? 'bg-blue-500/10 border border-blue-500/20' : 'bg-green-500/10 border border-green-500/20')}>{m.isPyq ? '📋' : '📚'}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate mb-1">{m.title}</p>
                  <div className="flex gap-2 flex-wrap">
                    {m.subject && <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-green-400 bg-green-500/10 border-green-500/20">{m.subject.length > 18 ? m.subject.slice(0,18)+'...' : m.subject}</span>}
                    {m.unit && <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-purple-400 bg-purple-500/10 border-purple-500/20">{m.unit}</span>}
                    {m.year && <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-blue-400 bg-blue-500/10 border-blue-500/20">{m.year}</span>}
                    {m.examType && <span className="text-[10px] px-2 py-0.5 rounded border font-medium text-orange-400 bg-orange-500/10 border-orange-500/20">{examLabel(m.examType)}</span>}
                  </div>
                  <p className="text-[10px] text-slate-600 mt-1">{m.fileSizeKb ? (m.fileSizeKb/1024).toFixed(1)+'MB' : ''} · {new Date(m.createdAt).toLocaleDateString('en-IN')}</p>
                </div>
              </div>
              <div className="flex gap-2 pt-3 border-t border-white/5">
                <button onClick={() => window.open('http://localhost:5000' + m.fileUrl, '_blank')} className="flex-1 py-2 bg-slate-800 text-slate-300 border border-white/10 rounded-xl text-xs hover:border-white/20">👁 View</button>
                <button onClick={() => handleDelete(m.id)} className="px-4 py-2 bg-red-500/10 text-red-400 border border-red-500/20 rounded-xl text-xs hover:bg-red-500/20">Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <p className="text-sm font-medium text-white">Upload Material</p>
              <button onClick={() => { setShowUpload(false); setFile(null) }} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center">✕</button>
            </div>
            <div className="p-5 space-y-4">
              {/* Type toggle */}
              <div className="flex gap-2">
                <button onClick={() => setForm(p => ({ ...p, isPyq: false }))} className={'flex-1 py-2.5 rounded-xl text-sm font-medium border transition-all ' + (!form.isPyq ? 'bg-green-500 text-white border-green-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                  📚 Study Notes
                </button>
                <button onClick={() => setForm(p => ({ ...p, isPyq: true }))} className={'flex-1 py-2.5 rounded-xl text-sm font-medium border transition-all ' + (form.isPyq ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                  📋 Previous Year QP
                </button>
              </div>

              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Title (Optional)</label>
                <input type="text" value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} placeholder="Material title (auto from filename)" className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 placeholder:text-slate-600" />
              </div>

              <div>
                <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Subject *</label>
                <select value={form.subject} onChange={e => setForm(p => ({ ...p, subject: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50">
                  <option value="">-- Select Subject --</option>
                  {SUBJECTS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>

              {!form.isPyq && (
                <div>
                  <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Unit</label>
                  <div className="grid grid-cols-3 gap-2">
                    {UNITS.map(u => (
                      <button key={u} onClick={() => setForm(p => ({ ...p, unit: p.unit === u ? '' : u }))} className={'py-2 rounded-xl text-xs font-medium border transition-all ' + (form.unit === u ? 'bg-purple-500 text-white border-purple-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/15')}>
                        {u}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {form.isPyq && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Year</label>
                    <select value={form.year} onChange={e => setForm(p => ({ ...p, year: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50">
                      <option value="">Select Year</option>
                      {['2025','2024','2023','2022','2021','2020'].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500 uppercase tracking-wider mb-2">Exam Type</label>
                    <select value={form.examType} onChange={e => setForm(p => ({ ...p, examType: e.target.value }))} className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50">
                      <option value="">Select Type</option>
                      <option value="end_term">End Term</option>
                      <option value="mid_term">Mid Term</option>
                      <option value="unit_test">Unit Test</option>
                    </select>
                  </div>
                </div>
              )}

              <div onDrop={e => { e.preventDefault(); setDragOver(false); setFile(e.dataTransfer.files[0]) }} onDragOver={e => { e.preventDefault(); setDragOver(true) }} onDragLeave={() => setDragOver(false)} onClick={() => document.getElementById('mat-file')?.click()} className={'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ' + (dragOver ? 'border-blue-500 bg-blue-500/5' : file ? 'border-green-500/50 bg-green-500/5' : 'border-white/10 hover:border-white/20')}>
                <input id="mat-file" type="file" accept=".pdf,.doc,.docx,.ppt,.pptx" className="hidden" onChange={e => setFile(e.target.files?.[0] || null)} />
                {file ? (
                  <div><p className="text-green-400 text-2xl mb-1">✓</p><p className="text-sm font-medium text-white">{file.name}</p><p className="text-xs text-slate-500 mt-1">{(file.size/1024/1024).toFixed(1)} MB</p></div>
                ) : (
                  <div><p className="text-3xl mb-1">📁</p><p className="text-sm text-slate-400">Drop file or click to browse</p><p className="text-xs text-slate-600 mt-1">PDF, DOC, PPT supported</p></div>
                )}
              </div>

              <button onClick={handleUpload} disabled={!file || !form.subject || uploading} className="w-full py-3 bg-blue-500 text-white text-sm font-medium rounded-xl hover:bg-blue-600 disabled:opacity-40 flex items-center justify-center gap-2">
                {uploading ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Uploading...</> : '⬆ Upload Material'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
""")
print("Teacher Materials done!")

# ═══════════════════════════════════
# STUDENT DASHBOARD - Show materials
# ═══════════════════════════════════
with open("../frontend/app/(student)/student/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import Link from 'next/link'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type Task = { id: string; title: string; subjectName?: string | null; taskType: string; deadline?: string | null; maxMarks: number }
type Material = { id: string; title: string; subject?: string | null; unit?: string | null; year?: number | null; isPyq: boolean; createdAt: string }
type Submission = { id: string; taskId: string; marksAwarded?: number | null; task: { title: string; maxMarks: number } }

export default function StudentDashboard() {
  const { data: session } = useSession()
  const [tasks, setTasks] = useState<Task[]>([])
  const [materials, setMaterials] = useState<Material[]>([])
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(true)
  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    Promise.all([
      fetch(API + '/tasks', { headers: { Authorization: 'Bearer ' + token } }).then(r => r.json()),
      fetch(API + '/materials', { headers: { Authorization: 'Bearer ' + token } }).then(r => r.json()),
      fetch(API + '/submissions', { headers: { Authorization: 'Bearer ' + token } }).then(r => r.json()),
    ]).then(([t, m, s]) => {
      if (t.success) setTasks(t.data)
      if (m.success) setMaterials(m.data)
      if (s.success) setSubmissions(s.data)
      setLoading(false)
    })
  }, [token])

  const submittedIds = submissions.map(s => s.taskId)
  const pending = tasks.filter(t => !submittedIds.includes(t.id))
  const recentNotes = materials.filter(m => !m.isPyq).slice(0, 4)
  const recentPyqs = materials.filter(m => m.isPyq).slice(0, 4)
  const graded = submissions.filter(s => s.marksAwarded !== null && s.marksAwarded !== undefined)

  const typeIcon: Record<string, string> = { assignment: '📝', class_test: '✍️', quiz: '❓', project: '🔬' }

  const getDaysLeft = (d?: string | null) => {
    if (!d) return { label: 'No deadline', color: 'text-slate-400' }
    const diff = new Date(d).getTime() - Date.now()
    const days = Math.ceil(diff / 86400000)
    if (diff < 0) return { label: 'Overdue!', color: 'text-red-400' }
    if (days === 0) return { label: 'Due Today!', color: 'text-red-400' }
    if (days <= 2) return { label: days + 'd left', color: 'text-yellow-400' }
    return { label: days + 'd left', color: 'text-green-400' }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white mb-1">Welcome, {session?.user?.name?.split(' ')[0] || 'Student'} 👋</h1>
        <p className="text-slate-400 text-sm">Your academic overview</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { l: 'Pending Tasks', v: pending.length, i: '📋', c: 'text-blue-400 bg-blue-500/10 border-blue-500/20', h: '/student/assignments' },
          { l: 'Submitted', v: submissions.length, i: '✅', c: 'text-green-400 bg-green-500/10 border-green-500/20', h: '/student/assignments' },
          { l: 'Notes Available', v: materials.filter(m => !m.isPyq).length, i: '📚', c: 'text-purple-400 bg-purple-500/10 border-purple-500/20', h: '/student/materials' },
          { l: 'PYQs Available', v: materials.filter(m => m.isPyq).length, i: '📄', c: 'text-orange-400 bg-orange-500/10 border-orange-500/20', h: '/student/materials' },
        ].map(s => (
          <Link key={s.l} href={s.h}>
            <div className="bg-slate-900 rounded-2xl border border-white/5 hover:border-white/10 transition-all p-5 cursor-pointer group">
              <div className={'w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-3 border ' + s.c}>{s.i}</div>
              <p className="text-2xl font-semibold text-white mb-1">{s.v}</p>
              <p className="text-xs text-slate-500">{s.l}</p>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Tasks */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-white">Pending Tasks ({pending.length})</h2>
            <Link href="/student/assignments" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
          </div>
          {pending.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-2xl mb-2">🎉</p>
              <p className="text-slate-400 text-sm">All caught up!</p>
            </div>
          ) : (
            <div className="space-y-2">
              {pending.slice(0, 4).map(task => {
                const dl = getDaysLeft(task.deadline)
                return (
                  <div key={task.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                    <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center text-base flex-shrink-0">{typeIcon[task.taskType] || '📋'}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{task.title}</p>
                      <p className="text-[10px] text-slate-500">{task.subjectName} · {task.maxMarks}M</p>
                    </div>
                    <span className={'text-[10px] font-medium flex-shrink-0 ' + dl.color}>{dl.label}</span>
                  </div>
                )
              })}
            </div>
          )}
          {pending.length > 0 && (
            <Link href="/student/assignments">
              <button className="w-full mt-3 py-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-xl text-xs font-medium hover:bg-blue-500/20">Submit Assignments →</button>
            </Link>
          )}
        </div>

        {/* Recent Notes */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-white">Recent Notes ({materials.filter(m=>!m.isPyq).length})</h2>
            <Link href="/student/materials" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
          </div>
          {recentNotes.length === 0 ? (
            <div className="text-center py-6"><p className="text-2xl mb-2">📭</p><p className="text-slate-400 text-sm">No notes uploaded yet</p></div>
          ) : (
            <div className="space-y-2">
              {recentNotes.map(m => (
                <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                  <div className="w-8 h-8 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center text-base flex-shrink-0">📚</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white truncate">{m.title}</p>
                    <div className="flex gap-1 mt-0.5">
                      {m.subject && <span className="text-[10px] text-green-400">{m.subject.length > 18 ? m.subject.slice(0,18)+'...' : m.subject}</span>}
                      {m.unit && <span className="text-[10px] text-slate-500">· {m.unit}</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent PYQs */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-white">Previous Year Papers ({materials.filter(m=>m.isPyq).length})</h2>
            <Link href="/student/materials" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
          </div>
          {recentPyqs.length === 0 ? (
            <div className="text-center py-6"><p className="text-2xl mb-2">📭</p><p className="text-slate-400 text-sm">No PYQs uploaded yet</p></div>
          ) : (
            <div className="space-y-2">
              {recentPyqs.map(m => (
                <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800 rounded-xl border border-white/5">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-base flex-shrink-0">📋</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white truncate">{m.title}</p>
                    <div className="flex gap-1 mt-0.5">
                      {m.subject && <span className="text-[10px] text-blue-400">{m.subject.length > 18 ? m.subject.slice(0,18)+'...' : m.subject}</span>}
                      {m.year && <span className="text-[10px] text-slate-500">· {m.year}</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-slate-900 rounded-2xl border border-white/5 p-5">
          <h2 className="text-sm font-medium text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-2">
            {[
              { l: 'Submit Assignment', i: '📤', h: '/student/assignments', c: 'hover:border-blue-500/30 hover:bg-blue-500/5' },
              { l: 'Study Notes', i: '📚', h: '/student/materials', c: 'hover:border-green-500/30 hover:bg-green-500/5' },
              { l: 'Previous Papers', i: '📋', h: '/student/materials', c: 'hover:border-purple-500/30 hover:bg-purple-500/5' },
              { l: 'AI Chatbot', i: '🤖', h: '/student/chatbot', c: 'hover:border-orange-500/30 hover:bg-orange-500/5' },
            ].map(a => (
              <Link key={a.l} href={a.h}>
                <div className={'p-3 bg-slate-800 rounded-xl border border-white/5 transition-all cursor-pointer ' + a.c}>
                  <span className="text-xl">{a.i}</span>
                  <p className="text-xs font-medium text-white mt-2">{a.l}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
""")
print("Student Dashboard done!")

print("\n=== ALL FRONTEND DONE ===")