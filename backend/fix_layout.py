with open("../frontend/app/(student)/layout.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Force class selection check via API
old = """    // Always allow student in - class selection handled in dashboard
    setReady(true)"""
new = """    // Check if student has a class
    const t = session.user.backendToken
    if (t) {
      fetch((process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1') + '/auth/me', {
        headers: { Authorization: 'Bearer ' + t }
      }).then(r => r.json()).then(d => {
        const hasClass = !!d.data?.classSection
        const skipped = localStorage.getItem('classSkipped')
        if (!hasClass && !skipped && pathname !== '/student/select-class') {
          router.push('/student/select-class')
        } else {
          setReady(true)
        }
      }).catch(() => setReady(true))
    } else {
      setReady(true)
    }"""

if old in content:
    content = content.replace(old, new)
    with open("../frontend/app/(student)/layout.tsx", "w", encoding="utf-8") as f:
        f.write(content)
    print("Student layout fixed!")
else:
    print("Already has check")