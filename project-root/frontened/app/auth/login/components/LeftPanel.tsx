const features = [
  {
    id: 1,
    icon: '🤖',
    title: 'AI Question Generation',
    desc: '2, 5, 10 marks — difficulty-controlled, PYQ pattern-based',
    bg: 'bg-blue-500/10',
  },
  {
    id: 2,
    icon: '📄',
    title: 'Branded PDF Export',
    desc: 'College branding ke saath professional exam papers',
    bg: 'bg-green-500/10',
  },
  {
    id: 3,
    icon: '💬',
    title: 'RAG Chatbot',
    desc: 'Subject-wise AI chatbot from uploaded materials',
    bg: 'bg-purple-500/10',
  },
  {
    id: 4,
    icon: '🏫',
    title: 'Multi-Tenant',
    desc: 'Har college ka alag isolated data',
    bg: 'bg-orange-500/10',
  },
]

export default function LeftPanel() {
  return (
    <div className="w-[340px] flex-shrink-0 bg-[#0e1628]
                    border-r border-white/5 p-10
                    flex flex-col justify-between">

      <div>
        {/* Brand */}
        <div className="flex items-center gap-2.5 mb-12">
          <div className="w-9 h-9 rounded-[10px] bg-blue-500
                          flex items-center justify-center
                          text-white text-lg">
            ✦
          </div>
          <div>
            <p className="text-sm font-semibold text-white leading-tight">
              AI Question Paper Generator
            </p>
            <p className="text-[11px] text-gray-500">
              Academic Management System
            </p>
          </div>
        </div>

        {/* Heading */}
        <h2 className="text-xl font-semibold text-white leading-snug mb-7">
          Smarter exams,<br />
          <span className="text-blue-400">powered by AI</span>
        </h2>

        {/* Features */}
        <ul className="space-y-4">
          {features.map((f) => (
            <li key={f.id} className="flex items-start gap-3">
              <div className={`w-7 h-7 rounded-lg ${f.bg}
                              flex items-center justify-center
                              text-sm flex-shrink-0 mt-0.5`}>
                {f.icon}
              </div>
              <div>
                <p className="text-[13px] font-medium text-white">
                  {f.title}
                </p>
                <p className="text-[12px] text-gray-500 leading-snug">
                  {f.desc}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Footer */}
      <div className="border-t border-white/5 pt-4 mt-6">
        <p className="text-[11px] text-gray-600">
          Secured with Azure AD · JWT Auth · Role-Based Access
        </p>
      </div>

    </div>
  )
}