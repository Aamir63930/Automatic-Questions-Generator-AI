import { Router } from 'express'
import { generateQuestions, getMaterialUnits, aiChat, checkAnswer } from '../controllers/ai.controller'
import { authenticate } from '../middleware/auth.middleware'

const router = Router()
router.get('/material-units', authenticate, getMaterialUnits)
router.post('/generate-questions', authenticate, generateQuestions)
router.post('/chat', authenticate, aiChat)
router.post('/check-answer', authenticate, checkAnswer)
export default router
