import { bodyOf, copy, fail, type MockRoute } from '../../../core/mock-runtime'
import { store } from '../../../mocks/store'

function patchNickname(value: unknown): string | null {
  if (value === null) return null
  const nickname = String(value).trim()
  if (!nickname || nickname.length > 16) fail('VALIDATION', '昵称须为 1–16 字')
  return nickname
}

function presentMe() {
  const published = store.posts.filter(
    (post) => post.author.id === store.me.id && post.status === 'published',
  )
  let like_received_count = 0
  published.forEach((post) => {
    like_received_count += post.like_count
  })
  return {
    ...copy(store.me),
    post_count: published.length,
    like_received_count,
    following_count: store.follows.length,
    follower_count: store.followers.length,
  }
}

export const meMockRoutes: MockRoute[] = [
  { method: 'GET', pattern: '/api/v1/me', handle: () => presentMe() },
  {
    method: 'PATCH', pattern: '/api/v1/me', handle: (_params, options) => {
      const data = bodyOf(options)
      if ('nickname' in data) store.me.nickname = patchNickname(data.nickname)
      if ('avatar_url' in data) store.me.avatar_url = data.avatar_url === null ? null : String(data.avatar_url)
      return presentMe()
    },
  },
]
