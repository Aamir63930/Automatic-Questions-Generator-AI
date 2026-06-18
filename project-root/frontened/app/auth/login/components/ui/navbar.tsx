'use client'

export default function Navbar() {
  return (
    <header className="h-14 bg-slate-900 border-b border-white/5 flex items-center justify-between px-6">

      {/* Left: Page title */}
      <h1 className="text-sm font-medium text-white">Dashboard</h1>

      {/* Right: Notification + Avatar */}
      <div className="flex items-center gap-3">

        {/* Notification bell */}
        <button className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 transition-all relative">
          🔔
          <span className="absolute top-1 right-1 w-2 h-2 bg-blue-500 rounded-full"></span>
        </button>

        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-sm font-medium cursor-pointer">
          U
        </div>

      </div>
    </header>
  )
}