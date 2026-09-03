import { bodyOf, copy, type MockRoute } from '../../../core/mock-runtime'
import { store } from '../../../mocks/store'

export const meMockRoutes: MockRoute[] = [
  { method: 'GET', pattern: '/api/v1/me', handle: () => copy(store.me) },
  {
    method: 'PATCH', pattern: '/api/v1/me', handle: (_params, options) => {
      const data = bodyOf(options)
      if ('nickname' in data) store.me.nickname = data.nickname === null ? null : String(data.nickname)
      if ('avatar_url' in data) store.me.avatar_url = data.avatar_url === null ? null : String(data.avatar_url)
      return copy(store.me)
    },
  },
]
