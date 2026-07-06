import jwt from 'jsonwebtoken'

const SECRET = process.env.JWT_SECRET || 'aiqpg-secret-key-krmu-2024'
const EXPIRES = process.env.JWT_EXPIRES_IN || '30d'

const SPECIAL_TEACHERS = ['akumarjaan123@gmail.com']

export function getRoleFromEmail(email: string): string {
  if (!email) return 'unknown'
  if (SPECIAL_TEACHERS.includes(email.toLowerCase())) return 'teacher'
  const prefix = email.split('@')[0]
  const domain = email.split('@')[1]
  // Accept any domain for now (college-wide access)
  if (!domain) return 'unknown'
  // Numbers = student, letters = teacher
  if (/^[0-9]/.test(prefix)) return 'student'
  if (/^[a-zA-Z]/.test(prefix)) return 'teacher'
  return 'unknown'
}

export function signToken(payload: object): string {
  return (jwt as any).sign(payload, SECRET, { expiresIn: EXPIRES })
}

export function verifyToken(token: string): any {
  return (jwt as any).verify(token, SECRET)
}
