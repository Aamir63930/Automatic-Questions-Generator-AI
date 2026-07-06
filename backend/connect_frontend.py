import os

# 1. API helper - frontend ke liye
os.makedirs("frontend/lib", exist_ok=True)
with open("../frontend/lib/api.ts", "w", encoding="utf-8") as f:
    f.write("""// API helper - connects frontend to backend
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1'

export async function apiCall(
  endpoint: string,
  options: RequestInit = {},
  token?: string
) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: 'Bearer ' + token }),
    ...(options.headers as Record<string, string>),
  }

  const res = await fetch(API_URL + endpoint, {
    ...options,
    headers,
  })

  const data = await res.json()

  if (!res.ok) {
    throw new Error(data.message || 'API Error')
  }

  return data
}

// Auth
export const authAPI = {
  azureLogin: (body: { email: string; name: string; azureOid: string; avatarUrl?: string }) =>
    apiCall('/auth/azure', { method: 'POST', body: JSON.stringify(body) }),

  getMe: (token: string) =>
    apiCall('/auth/me', {}, token),
}

// Tasks
export const taskAPI = {
  getAll: (token: string, params?: string) =>
    apiCall('/tasks' + (params ? '?' + params : ''), {}, token),

  create: (token: string, formData: FormData) =>
    fetch(API_URL + '/tasks', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token },
      body: formData,
    }).then(r => r.json()),

  updateStatus: (token: string, id: string, status: string) =>
    apiCall('/tasks/' + id + '/status', { method: 'PATCH', body: JSON.stringify({ status }) }, token),

  delete: (token: string, id: string) =>
    apiCall('/tasks/' + id, { method: 'DELETE' }, token),
}

// Submissions
export const submissionAPI = {
  getAll: (token: string, taskId?: string) =>
    apiCall('/submissions' + (taskId ? '?taskId=' + taskId : ''), {}, token),

  submit: (token: string, formData: FormData) =>
    fetch(API_URL + '/submissions', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token },
      body: formData,
    }).then(r => r.json()),

  grade: (token: string, id: string, marks: number, feedback: string) =>
    apiCall('/submissions/' + id + '/grade', {
      method: 'PATCH',
      body: JSON.stringify({ marks, feedback }),
    }, token),
}

// Materials
export const materialAPI = {
  getAll: (token: string, params?: string) =>
    apiCall('/materials' + (params ? '?' + params : ''), {}, token),

  upload: (token: string, formData: FormData) =>
    fetch(API_URL + '/materials/upload', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token },
      body: formData,
    }).then(r => r.json()),

  download: (token: string, id: string, fileName: string) => {
    fetch(API_URL + '/materials/' + id + '/download', {
      headers: { Authorization: 'Bearer ' + token },
    }).then(async res => {
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      a.click()
      URL.revokeObjectURL(url)
    })
  },

  delete: (token: string, id: string) =>
    apiCall('/materials/' + id, { method: 'DELETE' }, token),
}

// Notifications
export const notificationAPI = {
  getAll: (token: string) =>
    apiCall('/notifications', {}, token),

  markRead: (token: string, id: string) =>
    apiCall('/notifications/' + id + '/read', { method: 'PATCH' }, token),

  markAllRead: (token: string) =>
    apiCall('/notifications/read-all', { method: 'PATCH' }, token),

  send: (token: string, title: string, body: string, type?: string) =>
    apiCall('/notifications/send', {
      method: 'POST',
      body: JSON.stringify({ title, body, type }),
    }, token),
}

// Complaints
export const complaintAPI = {
  getAll: (token: string) =>
    apiCall('/complaints', {}, token),

  create: (token: string, data: { subject: string; category: string; description: string }) =>
    apiCall('/complaints', { method: 'POST', body: JSON.stringify(data) }, token),

  reply: (token: string, id: string, message: string) =>
    apiCall('/complaints/' + id + '/reply', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }, token),

  updateStatus: (token: string, id: string, status: string) =>
    apiCall('/complaints/' + id + '/status', {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }, token),
}
""")
print("API helper done!")

# 2. .env.local update
with open("../frontend/.env.local", "r", encoding="utf-8") as f:
    content = f.read()

if "NEXT_PUBLIC_API_URL" not in content:
    with open("../frontend/.env.local", "a", encoding="utf-8") as f:
        f.write("\nNEXT_PUBLIC_API_URL=http://localhost:5000/api/v1\n")
    print(".env.local updated!")
else:
    print(".env.local already has API URL!")

# 3. NextAuth callback - saves user to backend DB
with open("../frontend/app/api/auth/[...nextauth]/route.ts", "w", encoding="utf-8") as f:
    f.write("""import { handlers } from '@/lib/auth'
export const { GET, POST } = handlers
""")
print("NextAuth route done!")

# 4. Update lib/auth.ts to call backend after login
with open("../frontend/lib/auth.ts", "w", encoding="utf-8") as f:
    f.write("""import NextAuth from 'next-auth'
import AzureAD from 'next-auth/providers/microsoft-entra-id'

const SPECIAL_ACCOUNTS: Record<string, string> = {
  'akumarjaan123@gmail.com': 'teacher',
}

function getRoleFromEmail(email: string): string {
  if (!email) return 'unknown'
  if (SPECIAL_ACCOUNTS[email]) return SPECIAL_ACCOUNTS[email]
  const prefix = email.split('@')[0]
  const domain = email.split('@')[1]
  if (domain !== 'krmu.edu.in') return 'unknown'
  if (/^[0-9]/.test(prefix)) return 'student'
  if (/^[a-zA-Z]/.test(prefix)) return 'teacher'
  return 'unknown'
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true,
  providers: [
    AzureAD({
      clientId: process.env.AZURE_CLIENT_ID!,
      clientSecret: process.env.AZURE_CLIENT_SECRET!,
      tenantId: process.env.AZURE_TENANT_ID!,
      checks: ['none'],
    }),
  ],
  pages: { signIn: '/login', error: '/login' },
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account && profile) {
        const email = (profile.email || token.email || '') as string
        const role = getRoleFromEmail(email)
        token.email = email
        token.name = profile.name
        token.role = role
        token.picture = profile.picture as string || token.picture

        // Register/login user in our backend DB
        try {
          const res = await fetch(
            (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1') + '/auth/azure',
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                email,
                name: profile.name,
                azureOid: profile.sub || account.providerAccountId,
                avatarUrl: profile.picture || null,
              }),
            }
          )
          if (res.ok) {
            const data = await res.json()
            token.backendToken = data.data?.token
            token.userId = data.data?.user?.id
            token.collegeId = data.data?.user?.collegeId
          }
        } catch (err) {
          console.error('Backend sync error:', err)
        }
      }
      return token
    },
    async session({ session, token }) {
      session.user.role = token.role as string
      session.user.email = token.email as string
      session.user.backendToken = token.backendToken as string
      session.user.userId = token.userId as string
      return session
    },
  },
})
""")
print("auth.ts updated!")

# 5. TypeScript types for session
with open("../frontend/types/next-auth.d.ts", "w", encoding="utf-8") as f:
    f.write("""import 'next-auth'

declare module 'next-auth' {
  interface Session {
    user: {
      name?: string | null
      email?: string | null
      image?: string | null
      role?: string
      backendToken?: string
      userId?: string
    }
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    role?: string
    backendToken?: string
    userId?: string
    collegeId?: string
  }
}
""")
print("Types done!")

print("\n" + "="*50)
print("FRONTEND-BACKEND CONNECTION DONE!")
print("="*50)
print("Flow:")
print("1. User logs in with Microsoft")
print("2. NextAuth calls our backend /auth/azure")
print("3. Backend creates/finds user in PostgreSQL")
print("4. Backend JWT token stored in session")
print("5. All API calls use backend token")