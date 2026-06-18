'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const teacherLinks = [
  { href: '/teacher', icon: '🏠', label: 'Dashboard' },
  { href: '/teacher/generate', icon: '🤖', label: 'Generate Questions' },
  { href: '/teacher/papers', icon: '📄', label: 'My Papers' },
  { href: '/teacher/tasks', icon: '📋', label: 'Tasks' },
  { href: '/teacher/materials', icon: '📚', label: 'Materials' },
  { href: '/teacher/complaints', icon: '💬', label: 'Complaints' },
]

const studentLinks = [
  { href: '/student', icon: '🏠', label: 'Dashboard' },
  { href: '/student/assignments', icon: '📋', label: 'Assignments' },
  { href: '/student/submissions', icon: '📤', label: 'My Submissions' },
  { href: '/student/results', icon: '📊', label: 'Results' },
  { href: '/student/chatbot', icon: '💬', label: 'AI Chatbot' },
]

type Props = {
  role: 'teacher' | 'student' | 'admin' | 'hod'
}

export default function Sidebar({ role }: Props) {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  const links = role === 'teacher' ? teacherLinks : studentLinks

  return (
    <aside className={`${collapsed ? 'w-[70px]' : 'w-[240px]'} transition-all duration-300 bg-slate-900 border-r border-white/5 flex flex-col min-h-screen`}>

      {/* Logo */}
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center text-white font-bold">
              ✦
            </div>
            <span className="text-sm font-semibold text-white">AIQPG</span>
          </div>
        )}
        {collapsed && (
          <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center text-white font-bold mx-auto">
            ✦
          </div>
        )}
        {!collapsed && (
          <button
            onClick={() => setCollapsed(true)}
            className="text-slate-500 hover:text-white transition-colors"
          >
            ◀
          </button>
        )}
      </div>

      {collapsed && (
        <button
          onClick={() => setCollapsed(false)}
          className="text-slate-500 hover:text-white transition-colors p-3 text-center"
        >
          ▶
        </button>
      )}

      {/* Role Badge */}
      {!collapsed && (
        <div className="px-4 py-3">
          <span className="text-xs font-medium text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-1 rounded-md uppercase tracking-wider">
            {role}
          </span>
        </div>
      )}

      {/* Nav Links */}
      <nav className="flex-1 px-2 py-2 space-y-1">
        {links.map((link) => {
          const isActive = pathname === link.href
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all
                ${isActive
                  ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
            >
              <span className="text-base flex-shrink-0">{link.icon}</span>
              {!collapsed && <span>{link.label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* User info */}
      {!collapsed && (
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-sm font-medium">
              U
            </div>
            <div>
              <p className="text-xs font-medium text-white">User Name</p>
              <p className="text-[10px] text-slate-500">user@college.ac.in</p>
            </div>
          </div>
        </div>
      )}

    </aside>
  )
}