import NextAuth from 'next-auth'
import AzureAD from 'next-auth/providers/microsoft-entra-id'

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    AzureAD({
      clientId:     process.env.AZURE_CLIENT_ID!,
      clientSecret: process.env.AZURE_CLIENT_SECRET!,
      tenantId:     process.env.AZURE_TENANT_ID!,
    }),
  ],
  pages: {
    signIn: '/login',
  },
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.role = 'teacher'
      }
      return token
    },
    async session({ session, token }) {
      session.user.role = token.role as string
      return session
    },
  },
})