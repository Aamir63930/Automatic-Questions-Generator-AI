# Auth controller - when new student logs in, fetch classes and show them
with open("src/controllers/auth.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# In getMe, include all available classes for students without class
old = """    return success(res, user)"""
new = """    // For students without class, also send available classes
    let availableClasses: any[] = []
    if (user.role === 'student' && !user.classSectionId) {
      availableClasses = await prisma.classSection.findMany({
        where: { isActive: true },
        include: { _count: { select: { students: true } } },
        orderBy: [{ semester: 'asc' }, { branch: 'asc' }]
      })
    }
    return success(res, { ...user, availableClasses })"""

if old in content:
    content = content.replace(old, new)
    with open("src/controllers/auth.controller.ts", "w", encoding="utf-8") as f:
        f.write(content)
    print("Auth controller updated!")
else:
    print("Already updated")