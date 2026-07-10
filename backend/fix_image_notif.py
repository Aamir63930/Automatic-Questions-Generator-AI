# Run from BACKEND folder
with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

old = """export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history, image } = req.body
    const userMessage = image
      ? (message || 'Please solve this problem from the image I shared') + '\\n[Student has attached an image of their problem - provide detailed step by step solution]'
      : message"""

new = """export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history, image } = req.body

    // Build message - with or without image
    const userMessage = image
      ? (message || 'Please analyze and solve the problem shown in this image') + '\\n\\n[Note: Student has attached an image. Describe what you think the image contains and provide a detailed solution/explanation based on the subject context: ' + (subject || 'General') + ']'
      : message

    if (!userMessage) return error(res, 'Message required', 400)"""

if old in content:
    content = content.replace(old, new)
else:
    # Try finding just the function start
    content = content.replace(
        "const { message, subject, history, image } = req.body",
        """const { message, subject, history, image } = req.body

    const userMessage = image
      ? (message || 'Please analyze and solve the problem shown in this image') + '\\n\\n[Student attached an image related to ' + (subject || 'General') + '. Provide detailed step-by-step solution and explanation.]'
      : message

    if (!userMessage && !image) return error(res, 'Message required', 400)"""
    )

# Fix the actual API call to use userMessage
content = content.replace(
    "{ role: 'user', content: message }",
    "{ role: 'user', content: userMessage || message }"
)

# Fix max_tokens for image responses (need more)
content = content.replace(
    "max_tokens: 1024, temperature: 0.7,",
    "max_tokens: 2048, temperature: 0.7,"
)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("AI controller fixed!")

# Fix notification controller - only unread count
with open("src/controllers/notification.controller.ts", "r", encoding="utf-8") as f:
    notif = f.read()

# Add unread count endpoint
if "getUnreadCount" not in notif:
    notif += """
export const getUnreadCount = async (req: Request, res: Response) => {
  try {
    const { userId } = (req as any).user
    const count = await prisma.notification.count({
      where: { userId, isRead: false }
    })
    return success(res, { count })
  } catch (err) { return error(res, 'Failed', 500) }
}
"""
    with open("src/controllers/notification.controller.ts", "w", encoding="utf-8") as f:
        f.write(notif)
    print("Notification controller updated!")

# Add route for unread count
with open("src/routes/notification.routes.ts", "r", encoding="utf-8") as f:
    routes = f.read()

if "getUnreadCount" not in routes:
    routes = routes.replace(
        "import { getNotifications, markRead, markAllRead, deleteNotification, sendBulkNotification, studentAlertTeacher } from '../controllers/notification.controller'",
        "import { getNotifications, markRead, markAllRead, deleteNotification, sendBulkNotification, studentAlertTeacher, getUnreadCount } from '../controllers/notification.controller'"
    )
    routes = routes.replace(
        "router.get('/', authenticate, getNotifications)",
        "router.get('/', authenticate, getNotifications)\nrouter.get('/unread-count', authenticate, getUnreadCount)"
    )
    with open("src/routes/notification.routes.ts", "w", encoding="utf-8") as f:
        f.write(routes)
    print("Notification routes updated!")

print("Backend done!")