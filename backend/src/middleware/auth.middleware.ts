import { Request, Response, NextFunction } from 'express'
import { verifyToken } from '../utils/jwt'
import { error } from '../utils/response'

export const authenticate = (req: Request, res: Response, next: NextFunction) => {
  try {
    const authHeader = req.headers.authorization
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return error(res, 'No token provided', 401)
    }
    const token = authHeader.split(' ')[1]
    const decoded = verifyToken(token)
    ;(req as any).user = decoded
    next()
  } catch (err) {
    return error(res, 'Invalid or expired token', 401)
  }
}

export const authorize = (...roles: string[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = (req as any).user
    if (!user || !roles.includes(user.role)) {
      return error(res, 'Access denied', 403)
    }
    next()
  }
}
