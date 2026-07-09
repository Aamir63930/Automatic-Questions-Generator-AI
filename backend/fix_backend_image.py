import os

# ═══════════════════════════════════════════
# SCRIPT 1: Run from BACKEND folder
# ═══════════════════════════════════════════

with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Fix aiChat to support image
old = """export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history } = req.body"""

new = """export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history, image } = req.body
    const userMessage = image
      ? (message || 'Please solve this problem from the image I shared') + '\\n[Student has attached an image of their problem - provide detailed step by step solution]'
      : message"""

content = content.replace(old, new)

# Fix the message used in API call
old2 = "{ role: 'user', content: message }"
new2 = "{ role: 'user', content: userMessage }"
content = content.replace(old2, new2)

# Fix system prompt
old3 = """'You are an expert academic tutor for ' + (subject || 'all subjects') + ' at K.R Mangalam University. Be clear and educational.'"""
new3 = """'You are HAYAT, an expert academic tutor for ' + (subject || 'all subjects') + ' at K.R Mangalam University. ' + (image ? 'The student has shared an image of their handwritten problem. Analyze it and provide detailed step-by-step solution with explanation.' : 'Be clear, concise and use examples.')"""
content = content.replace(old3, new3)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("Backend AI controller done!")