with open("src/utils/jwt.ts", "w", encoding="utf-8") as f:
    f.write("""import jwt from 'jsonwebtoken'

const SECRET = process.env.JWT_SECRET || 'fallback-secret'

export function signToken(payload: object): string {
  return (jwt as any).sign(payload, SECRET, { expiresIn: '7d' })
}

export function verifyToken(token: string): any {
  return (jwt as any).verify(token, SECRET)
}

export function getRoleFromEmail(email: string): string {
  if (!email) return 'unknown'

  const SPECIAL: Record<string, string> = {
    'akumarjaan123@gmail.com': 'teacher',
  }
  if (SPECIAL[email]) return SPECIAL[email]

  const prefix = email.split('@')[0]
  const domain = email.split('@')[1]

  if (domain !== 'krmu.edu.in') return 'unknown'
  if (/^[0-9]/.test(prefix)) return 'student'
  if (/^[a-zA-Z]/.test(prefix)) return 'teacher'
  return 'unknown'
}
""")
print("Done!")