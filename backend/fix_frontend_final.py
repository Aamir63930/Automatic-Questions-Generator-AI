import os

# ══════════════════════════════════════
# Student Layout - API se check karo
# ══════════════════════════════════════
with open("../frontend/app/(student)/layout.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter, usePathname } from 'next/navigation'
import StudentSidebar from '@/components/student/StudentSidebar'
import StudentNavbar from '@/components/student/StudentNavbar'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const pathname = usePathname()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (status === 'loading') return
    if (!session) { router.push('/login'); return }
    if (session.user.role !== 'student') { router.push('/teacher'); return }
    if (pathname === '/student/select-class') { setReady(true); return }

    const token = session.user.backendToken
    if (!token) { setReady(true); return }

    // Check from API if student has a class
    fetch(API + '/auth/me', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(data => {
        const hasClass = !!(data.data?.classSection)
        const skipped = localStorage.getItem('classSkipped')
        if (!hasClass && !skipped) {
          router.push('/student/select-class')
        } else {
          setReady(true)
        }
      })
      .catch(() => setReady(true))
  }, [session, status, pathname])

  if (!ready) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Loading...</p>
      </div>
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

# ══════════════════════════════════════
# Select Class Page - token save karo
# ══════════════════════════════════════
os.makedirs("../frontend/app/(student)/student/select-class", exist_ok=True)
with open("../frontend/app/(student)/student/select-class/page.tsx", "w", encoding="utf-8") as f:
    f.write("""'use client'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

const API = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`

type ClassSection = {
  id: string; name: string; section: string; branch: string
  semester: number; year: number; uniqueCode: string
  _count: { students: number }
}

export default function SelectClassPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [classes, setClasses] = useState<ClassSection[]>([])
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState<'code'|'browse'>('code')
  const [code, setCode] = useState('')
  const [joining, setJoining] = useState(false)
  const [err, setErr] = useState('')
  const [ok, setOk] = useState('')
  const [selBranch, setSelBranch] = useState('')
  const [selSem, setSelSem] = useState('')
  const [selClass, setSelClass] = useState('')

  const token = session?.user?.backendToken

  useEffect(() => {
    if (!token) return
    fetch(API + '/auth/classes', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.json())
      .then(d => { if (d.success) setClasses(d.data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [token])

  const branches = Array.from(new Set(classes.map(c => c.branch))).sort()
  const sems = Array.from(new Set(classes.filter(c => !selBranch || c.branch === selBranch).map(c => c.semester.toString()))).sort()
  const filteredClasses = classes.filter(c => (!selBranch || c.branch === selBranch) && (!selSem || c.semester.toString() === selSem))

  const afterJoin = (newToken?: string) => {
    // Store new token in localStorage for immediate use
    if (newToken) localStorage.setItem('studentToken', newToken)
    setOk('Class joined! Redirecting to dashboard...')
    setTimeout(() => {
      // Hard redirect to reload session completely
      window.location.href = '/student'
    }, 1200)
  }

  const joinByCode = async () => {
    if (!code.trim() || !token) return
    setJoining(true); setErr('')
    try {
      const res = await fetch(API + '/auth/join-class', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code.toUpperCase().trim() })
      })
      const d = await res.json()
      if (d.success) {
        afterJoin(d.data?.token)
      } else {
        setErr(d.message || 'Invalid code. Ask your teacher for the correct code.')
      }
    } catch { setErr('Cannot connect to server. Is backend running on port 5000?') }
    setJoining(false)
  }

  const joinBySelect = async () => {
    if (!selClass || !token) return
    setJoining(true); setErr('')
    try {
      const res = await fetch(API + '/auth/select-class', {
        method: 'PATCH',
        headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ classSectionId: selClass })
      })
      const d = await res.json()
      if (d.success) afterJoin(d.data?.token)
      else setErr(d.message || 'Failed')
    } catch { setErr('Connection error') }
    setJoining(false)
  }

  if (status === 'loading') return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-green-500/20 to-blue-500/20 border border-green-500/30 flex items-center justify-center text-4xl mx-auto mb-4">🎓</div>
          <h1 className="text-2xl font-bold text-white mb-2">Join Your Class</h1>
          <p className="text-slate-400 text-sm">Enter the class code from your teacher to access tasks and materials</p>
          {session?.user?.name && <p className="text-green-400 text-sm mt-2">Welcome, {session.user.name.split(' ')[0]}! 👋</p>}
        </div>

        <div className="flex gap-1 bg-slate-900 border border-white/10 rounded-2xl p-1.5 mb-6">
          <button onClick={() => { setMode('code'); setErr('') }} className={'flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ' + (mode === 'code' ? 'bg-green-500 text-white shadow-lg' : 'text-slate-400 hover:text-white')}>
            🔑 Class Code
          </button>
          <button onClick={() => { setMode('browse'); setErr('') }} className={'flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ' + (mode === 'browse' ? 'bg-blue-500 text-white shadow-lg' : 'text-slate-400 hover:text-white')}>
            📋 Browse Classes
          </button>
        </div>

        {mode === 'code' && (
          <div className="bg-slate-900 rounded-2xl border border-white/10 p-6">
            <label className="block text-xs text-slate-400 mb-3 uppercase tracking-widest">Enter Class Code</label>
            <input
              type="text" value={code}
              onChange={e => { setCode(e.target.value.toUpperCase()); setErr('') }}
              onKeyDown={e => e.key === 'Enter' && joinByCode()}
              placeholder="e.g. CSE1A-B3F2"
              maxLength={15} autoFocus
              className="w-full bg-slate-800 border border-white/10 rounded-xl px-5 py-4 text-2xl font-mono font-bold text-white text-center tracking-widest outline-none focus:border-green-500/60 placeholder:text-slate-700 placeholder:text-sm placeholder:font-normal mb-4"
            />
            {err && <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4 text-xs text-red-400">⚠️ {err}</div>}
            {ok && <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3 mb-4 text-xs text-green-400">✓ {ok}</div>}
            <button onClick={joinByCode} disabled={code.length < 5 || joining || !!ok} className="w-full py-3.5 bg-green-500 text-white text-sm font-bold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center justify-center gap-2 mb-3">
              {joining ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Joining...</> : '🚀 Join Class'}
            </button>
            <p className="text-center text-xs text-slate-600">Get the code from your teacher's dashboard → Class Management</p>
          </div>
        )}

        {mode === 'browse' && (
          <div className="bg-slate-900 rounded-2xl border border-white/10 p-6">
            {loading ? (
              <div className="text-center py-8"><div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" /></div>
            ) : classes.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-3">⏳</p>
                <p className="text-white font-medium mb-2">No classes yet</p>
                <p className="text-slate-400 text-sm mb-4">Ask your teacher for the class code</p>
                <button onClick={() => setMode('code')} className="px-4 py-2 bg-green-500 text-white text-sm rounded-xl">Use Code Instead</button>
              </div>
            ) : (
              <>
                <div className="mb-4">
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Select Branch</p>
                  <div className="grid grid-cols-3 gap-2">
                    {branches.map(b => (
                      <button key={b} onClick={() => { setSelBranch(b); setSelSem(''); setSelClass('') }} className={'py-2.5 rounded-xl text-sm font-medium border transition-all ' + (selBranch === b ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/20')}>{b}</button>
                    ))}
                  </div>
                </div>

                {selBranch && (
                  <div className="mb-4">
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Select Semester</p>
                    <div className="grid grid-cols-4 gap-2">
                      {sems.map(s => (
                        <button key={s} onClick={() => { setSelSem(s); setSelClass('') }} className={'py-2 rounded-xl text-sm font-medium border transition-all ' + (selSem === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-slate-800 text-slate-400 border-white/5 hover:border-white/20')}>Sem {s}</button>
                      ))}
                    </div>
                  </div>
                )}

                {selSem && filteredClasses.map(c => (
                  <button key={c.id} onClick={() => setSelClass(c.id)} className={'w-full p-4 rounded-xl border text-left mb-2 transition-all ' + (selClass === c.id ? 'border-green-500/60 bg-green-500/10' : 'border-white/5 bg-slate-800 hover:border-white/20')}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-bold text-white">{c.name} — Sec {c.section}</p>
                        <p className="text-xs text-slate-500">{c.branch} · Sem {c.semester} · {c._count.students} students</p>
                      </div>
                      <span className="text-xs font-mono text-green-400 bg-green-500/10 px-2 py-1 rounded-lg border border-green-500/20">{c.uniqueCode}</span>
                    </div>
                  </button>
                ))}

                {err && <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-3 text-xs text-red-400">{err}</div>}
                {ok && <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3 mb-3 text-xs text-green-400">✓ {ok}</div>}

                {selClass && (
                  <button onClick={joinBySelect} disabled={joining || !!ok} className="w-full py-3 bg-green-500 text-white text-sm font-bold rounded-xl hover:bg-green-600 disabled:opacity-40 flex items-center justify-center gap-2">
                    {joining ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Joining...</> : '✓ Join This Class'}
                  </button>
                )}
              </>
            )}
          </div>
        )}

        <div className="text-center mt-5">
          <button onClick={() => { localStorage.setItem('classSkipped', 'true'); window.location.href = '/student' }} className="text-slate-600 hover:text-slate-400 text-xs">
            Skip — join class later
          </button>
        </div>
      </div>
    </div>
  )
}
""")
print("Select class page done!")

print("\nAll frontend fixes done!")