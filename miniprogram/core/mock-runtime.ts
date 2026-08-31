import {
  CURRENT_USER_ID,
  currentAuthor,
  store,
  type MockAlbum,
  type MockComment,
  type MockPost,
  type MockVideo,
} from './mock-store'

export type MockQuery = Record<string, string | number | boolean | undefined>

export type MockOptions = {
  method: string
  path: string
  data?: object
  query?: MockQuery
}

export type MockError = { code: string; message: string }
export type Params = Record<string, string>
export type MockHandler = (params: Params, options: MockOptions) => unknown
export type MockRoute = { method: string; pattern: string; handle: MockHandler }

export { CURRENT_USER_ID, currentAuthor, store }

export function fail(code: string, message: string): never {
  const error: MockError = { code, message }
  throw error
}

export function isMockError(value: unknown): value is MockError {
  return !!value && typeof value === 'object' && 'code' in value && 'message' in value
}

export function copy<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export function nowIso(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
}

export function todayDate(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function newId(): string {
  const hex = () => Math.floor((1 + Math.random()) * 0x10000).toString(16).slice(1)
  return `${hex()}${hex()}-${hex()}-${hex()}-${hex()}-${hex()}${hex()}${hex()}`
}

export function queryValue(query: MockQuery | undefined, key: string): string | undefined {
  const value = query && query[key]
  return value === undefined || value === '' ? undefined : String(value)
}

export function queryPage(query: MockQuery | undefined): { page: number; page_size: number } {
  const page = Number(queryValue(query, 'page') || 1)
  const page_size = Number(queryValue(query, 'page_size') || 20)
  return {
    page: Number.isFinite(page) && page > 0 ? page : 1,
    page_size: Number.isFinite(page_size) && page_size > 0 ? page_size : 20,
  }
}

export function paginate<T>(items: T[], query: MockQuery | undefined) {
  const { page, page_size } = queryPage(query)
  const start = (page - 1) * page_size
  return { items: items.slice(start, start + page_size), total: items.length, page, page_size }
}

export function sortByCreated<T extends { created_at: string }>(items: T[]): T[] {
  return items.slice().sort((a, b) => (a.created_at < b.created_at ? 1 : a.created_at > b.created_at ? -1 : 0))
}

export function bodyOf(options: MockOptions): Record<string, unknown> {
  return (options.data || {}) as Record<string, unknown>
}

export function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)) : []
}

export function matchPath(pattern: string, path: string): Params | null {
  const patternParts = pattern.split('/').filter(Boolean)
  const pathParts = path.split('/').filter(Boolean)
  if (patternParts.length !== pathParts.length) return null
  const params: Params = {}
  for (let i = 0; i < patternParts.length; i += 1) {
    const token = patternParts[i]
    if (token.startsWith('{') && token.endsWith('}')) {
      params[token.slice(1, -1)] = decodeURIComponent(pathParts[i])
    } else if (token !== pathParts[i]) {
      return null
    }
  }
  return params
}

export function presentPost(post: MockPost) {
  return {
    ...copy(post),
    author: {
      id: post.author.id,
      nickname: post.author.id === CURRENT_USER_ID ? store.me.nickname : post.author.nickname,
      avatar_url: post.author.id === CURRENT_USER_ID ? store.me.avatar_url : post.author.avatar_url,
    },
    followed: store.follows.indexOf(post.author.id) !== -1,
  }
}

export function presentComment(item: MockComment) {
  return copy({
    id: item.id,
    author: item.author,
    body: item.body,
    parent_id: item.parent_id,
    reply_to: item.reply_to,
    sticker_ids: item.sticker_ids.slice(),
    image_urls: item.image_urls.slice(),
    audio_url: item.audio_url || null,
    audio_duration: item.audio_duration || 0,
    like_count: item.like_count,
    liked: item.liked,
    created_at: item.created_at,
  })
}

export function addLedger(kind: 'earn' | 'spend', amount: number, title: string) {
  if (kind === 'spend' && store.me.points_balance < amount) fail('POINTS_NOT_ENOUGH', '积分不足')
  store.me.points_balance += kind === 'earn' ? amount : -amount
  store.ledger.unshift({
    id: newId(), kind, amount, title,
    balance_after: store.me.points_balance, created_at: nowIso(),
  })
}

export function findAlbum(id: string): MockAlbum {
  const album = store.albums.find((item) => item.id === id)
  if (!album) fail('NOT_FOUND', '相册不存在')
  return album
}

export function findPost(id: string): MockPost {
  const post = store.posts.find((item) => item.id === id)
  if (!post) fail('NOT_FOUND', '帖子不存在')
  return post
}

export function findComment(postId: string, commentId: string): MockComment {
  const comment = store.comments.find((item) => item.id === commentId && item.post_id === postId)
  if (!comment) fail('NOT_FOUND', '评论不存在')
  return comment
}

export function findVideo(id: string): MockVideo {
  const video = store.videos.find((item) => item.id === id)
  if (!video) fail('NOT_FOUND', '任务不存在')
  return video
}

export function assertOwnPost(post: MockPost) {
  if (post.author.id !== CURRENT_USER_ID) fail('FORBIDDEN', '只能操作自己的帖子')
}

export function publishPost(post: MockPost) {
  if (post.status === 'published') return
  post.status = 'published'
  addLedger('earn', 20, '发布帖子')
}

export function syncCommentCount(post: MockPost) {
  post.comment_count = store.comments.filter((item) => item.post_id === post.id).length
}

export function resolveCommentParent(postId: string, parentId: string | undefined) {
  if (!parentId) return { parent_id: null as string | null, reply_to: null as MockComment['reply_to'] }
  const parent = store.comments.find((item) => item.id === parentId && item.post_id === postId)
  if (!parent) fail('VALIDATION', '要评论的内容不存在')
  return {
    parent_id: parent.parent_id || parent.id,
    reply_to: { id: parent.author.id, nickname: parent.author.nickname, avatar_url: parent.author.avatar_url },
  }
}

export function assertCanDeleteComment(post: MockPost, comment: MockComment) {
  if (comment.author.id !== CURRENT_USER_ID && post.author.id !== CURRENT_USER_ID) {
    fail('FORBIDDEN', '只能删除自己的评论')
  }
}

export function pointsSummary() {
  let earned = 0
  let spent = 0
  store.ledger.forEach((entry) => {
    if (entry.kind === 'earn') earned += entry.amount
    else spent += entry.amount
  })
  return { earned, spent, balance: store.me.points_balance }
}

export function inLedgerRange(iso: string, range: string): boolean {
  if (!range || range === 'all') return true
  const created = new Date(iso)
  const now = new Date()
  if (range === 'month') return created.getFullYear() === now.getFullYear() && created.getMonth() === now.getMonth()
  if (range === 'quarter') return created >= new Date(now.getFullYear(), now.getMonth() - 2, 1)
  return true
}

export const BOARDS = ['qa', 'show', 'share', 'help', 'daily', 'experience'] as const
export const RESOLUTIONS = ['540p', '720p', '1080p', '2k', '4k'] as const
export const STICKER_IDS = ['blush', 'happy', 'cry', 'paw', 'heart', 'sleep', 'wow', 'kiss'] as const
export const REPORT_REASONS = ['spam', 'abuse', 'porn', 'other'] as const
