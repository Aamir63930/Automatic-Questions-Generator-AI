import { Router } from 'express'
import { createSubmission, getSubmissions, gradeSubmission, getPendingSummary, getTaskSubmissionStatus, getResultsSummary } from '../controllers/submission.controller'
import { authenticate, authorize } from '../middleware/auth.middleware'
import { upload } from '../middleware/upload.middleware'

const router = Router()
router.post('/', authenticate, authorize('student'), upload.single('file'), createSubmission)
router.get('/', authenticate, getSubmissions)
router.get('/pending-summary', authenticate, authorize('teacher', 'admin'), getPendingSummary)
router.get('/results-summary', authenticate, authorize('teacher', 'admin'), getResultsSummary)
router.get('/task/:taskId/status', authenticate, authorize('teacher', 'admin'), getTaskSubmissionStatus)
router.patch('/:id/grade', authenticate, authorize('teacher', 'admin'), gradeSubmission)
export default router
