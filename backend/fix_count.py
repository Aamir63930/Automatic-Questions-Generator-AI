with open("../frontend/app/(student)/student/page.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Fix undefined _count.students
content = content.replace(
    "myClass._count.students",
    "(myClass as any)._count?.students || 0"
)
content = content.replace(
    "cls._count.students",
    "(cls as any)._count?.students || 0"
)

with open("../frontend/app/(student)/student/page.tsx", "w", encoding="utf-8") as f:
    f.write(content)
print("Dashboard TypeError fixed!")