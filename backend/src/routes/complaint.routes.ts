import { Router } from 'express'
import { createComplaint, getComplaints, replyComplaint, updateComplaintStatus } from '../controllers/complaint.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'

const router = Router()

router.post('/', authenticate, createComplaint)
router.get('/', authenticate, getComplaints)
router.post('/:id/reply', authenticate, replyComplaint)
router.patch('/:id/status', authenticate, authorize('teacher', 'admin'), updateComplaintStatus)

export default router
