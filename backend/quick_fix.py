with open("src/controllers/submission.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Fix: cast req.params to string
content = content.replace(
    "where: { id: req.params.taskId, collegeId }",
    "where: { id: req.params.taskId as string, collegeId }"
)
content = content.replace(
    "where: { taskId: req.params.taskId },",
    "where: { taskId: req.params.taskId as string },"
)

with open("src/controllers/submission.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed!")