import { bodyOf, copy, fail, type MockRoute } from '../../../core/mock-runtime'
import { store } from '../../../mocks/store'

function patchNickname(value: unknown): string | null {
  if (value === null) return null
  const nickname = String(value).trim()
  if (!nickname || nickname.length > 16) fail('VALIDATION', '昵称须为 1–16 字')
  return nickname
}

export const meMockRoutes: MockRoute[] = [
  { method: 'GET', pattern: '/api/v1/me', handle: () => copy(store.me) },
  {
    method: 'PATCH', pattern: '/api/v1/me', handle: (_params, options) => {
      const data = bodyOf(options)
      if ('nickname' in data) store.me.nickname = patchNickname(data.nickname)
      if ('avatar_url' in data) store.me.avatar_url = data.avatar_url === null ? null : String(data.avatar_url)
      return copy(store.me)
    },
  },
]
