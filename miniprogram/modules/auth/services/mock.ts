import type { MockRoute } from '../../../core/mock-runtime'

export const authMockRoutes: MockRoute[] = [
  { method: 'POST', pattern: '/api/v1/auth/login', handle: () => ({ token: 'jwt-or-mock', expires_in: 604800 }) },
]
