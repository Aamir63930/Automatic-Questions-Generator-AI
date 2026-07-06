# Fix frontend - subject field name
import re

with open("../frontend/app/(dashboard)/teacher/tasks/page.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Replace subjectId with subjectName in formData
content = content.replace("formData.append('subjectId', form.subject)", "formData.append('subjectName', form.subject)")

with open("../frontend/app/(dashboard)/teacher/tasks/page.tsx", "w", encoding="utf-8") as f:
    f.write(content)
print("Tasks frontend fixed!")