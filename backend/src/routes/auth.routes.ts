import { Router } from 'express'
import { azureLogin, getMe, getUsers, updateSubjects, getClasses, createClass, deleteClass, joinClassByCode, selectClass, assignClass } from '../controllers/auth.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'

const router = Router()

router.post('/azure', azureLogin)
router.get('/me', authenticate, getMe)
router.get('/users', authenticate, getUsers)
router.patch('/subjects', authenticate, updateSubjects)
router.get('/classes', authenticate, getClasses)
router.post('/classes', authenticate, authorize('teacher', 'admin'), createClass)
router.delete('/classes/:id', authenticate, authorize('teacher', 'admin'), deleteClass)
router.post('/join-class', authenticate, authorize('student'), joinClassByCode)
router.patch('/select-class', authenticate, selectClass)
router.patch('/assign-class', authenticate, authorize('teacher', 'admin'), assignClass)

export default router
