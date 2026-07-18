with open("src/routes/auth.routes.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Remove the broken fix-cloudinary endpoint
import re
content = re.sub(
    r"// ONE TIME FIX.*?export default router",
    "export default router",
    content,
    flags=re.DOTALL
)

with open("src/routes/auth.routes.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("Reverted!")