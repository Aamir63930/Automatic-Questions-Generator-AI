with open("src/app.ts", "w", encoding="utf-8") as f:
    f.write("""import express from 'express'
import cors from 'cors'
import path from 'path'

const app = express()
const PORT = process.env.PORT || 5000

// CORS - allow everything
app.use(cors({
  origin: true,
  credentials: true,
  methods: ['GET','POST','PUT','PATCH','DELETE','OPTIONS'],
  allowedHeaders: ['Content-Type','Authorization'],
}))

app.use(express.json({ limit: '50mb' }))
app.use(express.urlencoded({ extended: true, limit: '50mb' }))
app.use('/uploads', express.static(path.join(process.cwd(), 'uploads')))

// Health check
app.get('/health', (_req, res) => res.json({ status: 'OK', time: new Date() }))
app.get('/', (_req, res) => res.json({ message: 'AIQPG Backend Live!' }))

import authRoutes         from './routes/auth.routes'
import materialRoutes     from './routes/material.routes'
import taskRoutes         from './routes/task.routes'
import submissionRoutes   from './routes/submission.routes'
import notificationRoutes from './routes/notification.routes'
import complaintRoutes    from './routes/complaint.routes'
import aiRoutes           from './routes/ai.routes'
import paperRoutes        from './routes/paper.routes'

app.use('/api/v1/auth',          authRoutes)
app.use('/api/v1/materials',     materialRoutes)
app.use('/api/v1/tasks',         taskRoutes)
app.use('/api/v1/submissions',   submissionRoutes)
app.use('/api/v1/notifications', notificationRoutes)
app.use('/api/v1/complaints',    complaintRoutes)
app.use('/api/v1/ai',            aiRoutes)
app.use('/api/v1/papers',        paperRoutes)

app.listen(PORT, () => {
  console.log('Backend running on port ' + PORT)
})

export default app
""")
print("app.ts fixed!")