import { Router } from 'express'
import { createTask, createBulkTasks, getTasks, getTask, updateTaskStatus, extendDeadline, deleteTask } from '../controllers/task.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'

const router = Router()
router.post('/', authenticate, authorize('teacher', 'admin'), upload.single('attachment'), createTask)
router.post('/bulk', authenticate, authorize('teacher', 'admin'), createBulkTasks)
router.get('/', authenticate, getTasks)
router.get('/:id', authenticate, getTask)
router.patch('/:id/status', authenticate, authorize('teacher', 'admin'), updateTaskStatus)
router.patch('/:id/extend-deadline', authenticate, authorize('teacher', 'admin'), extendDeadline)
router.delete('/:id', authenticate, authorize('teacher', 'admin'), deleteTask)

export default router
