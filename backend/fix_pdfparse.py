with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Fix pdf-parse import
content = content.replace(
    "const pdfParse = require('pdf-parse')",
    "const pdfParse = require('pdf-parse').default || require('pdf-parse')"
)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("PDF parse fixed!")