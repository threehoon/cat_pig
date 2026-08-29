import { mockPhotos } from '../assets/paths'
import {
  CURRENT_USER_ID,
  currentAuthor,
  store,
  type MockAlbum,
  type MockComment,
  type MockPost,
  type MockVideo,
} from './mock-store'

type MockQuery = Record<string, string | number | boolean | undefined>

type MockOptions = {
  method: string
  path: string
  data?: object
  query?: MockQuery
}

type MockError = { code: string; message: string }

type MockResult = { data: unknown; error?: undefined } | { data?: undefined; error: MockError }

type Params = Record<string, string>

function fail(code: string, message: string): never {
  const error: MockError = { code, message }
  throw error
}

function isMockError(value: unknown): value is MockError {
  return !!value && typeof value === 'object' && 'code' in value && 'message' in value
}

function copy<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function nowIso(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
}

function todayDate(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function newId(): string {
  const hex = () =>
    Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .slice(1)
  return `${hex()}${hex()}-${hex()}-${hex()}-${hex()}-${hex()}${hex()}${hex()}`
}

function queryValue(query: MockQuery | undefined, key: string): string | undefined {
  if (!query) {
    return undefined
  }
  const value = query[key]
  if (value === undefined || value === '') {
    return undefined
  }
  return String(value)
}

function queryPage(query: MockQuery | undefined): { page: number; page_size: number } {
  const page = Number(queryValue(query, 'page') || 1)
  const page_size = Number(queryValue(query, 'page_size') || 20)
  return {
    page: Number.isFinite(page) && page > 0 ? page : 1,
    page_size: Number.isFinite(page_size) && page_size > 0 ? page_size : 20,
  }
}

function paginate<T>(items: T[], query: MockQuery | undefined) {
  const { page, page_size } = queryPage(query)
  const start = (page - 1) * page_size
  return {
    items: items.slice(start, start + page_size),
    total: items.length,
    page,
    page_size,
  }
}

function sortByCreated<T extends { created_at: string }>(items: T[]): T[] {
  return items.slice().sort((a, b) => (a.created_at < b.created_at ? 1 : a.created_at > b.created_at ? -1 : 0))
}

function bodyOf(options: MockOptions): Record<string, unknown> {
  return (options.data || {}) as Record<string, unknown>
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.map((item) => String(item))
}

function matchPath(pattern: string, path: string): Params | null {
  const patternParts = pattern.split('/').filter((part) => part.length > 0)
  const pathParts = path.split('/').filter((part) => part.length > 0)
  if (patternParts.length !== pathParts.length) {
    return null
  }
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

function presentPost(post: MockPost) {
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

function addLedger(kind: 'earn' | 'spend', amount: number, title: string) {
  if (kind === 'spend' && store.me.points_balance < amount) {
    fail('POINTS_NOT_ENOUGH', '积分不足')
  }
  if (kind === 'earn') {
    store.me.points_balance += amount
  } else {
    store.me.points_balance -= amount
  }
  store.ledger.unshift({
    id: newId(),
    kind,
    amount,
    title,
    balance_after: store.me.points_balance,
    created_at: nowIso(),
  })
}

function findAlbum(id: string): MockAlbum {
  const album = store.albums.find((item) => item.id === id)
  if (!album) {
    fail('NOT_FOUND', '相册不存在')
  }
  return album
}

const STICKER_IDS = ['blush', 'happy', 'cry', 'paw', 'heart', 'sleep', 'wow', 'kiss']
const REPORT_REASONS = ['spam', 'abuse', 'porn', 'other']

function presentComment(item: MockComment) {
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

function reparentChildren(deletedId: string, newParentId: string | null) {
  store.comments.forEach((item) => {
    if (item.parent_id === deletedId) {
      item.parent_id = newParentId
    }
  })
}

function assertCanDeleteComment(post: MockPost, comment: MockComment) {
  const isCommentAuthor = comment.author.id === CURRENT_USER_ID
  const isPostOwner = post.author.id === CURRENT_USER_ID
  if (!isCommentAuthor && !isPostOwner) {
    fail('FORBIDDEN', '只能删除自己的评论')
  }
}

function syncCommentCount(post: MockPost) {
  post.comment_count = store.comments.filter((item) => item.post_id === post.id).length
}

function findComment(postId: string, commentId: string): MockComment {
  const comment = store.comments.find((item) => item.id === commentId && item.post_id === postId)
  if (!comment) {
    fail('NOT_FOUND', '评论不存在')
  }
  return comment
}

function resolveCommentParent(postId: string, parentId: string | undefined) {
  if (!parentId) {
    return { parent_id: null as string | null, reply_to: null as MockComment['reply_to'] }
  }
  const parent = store.comments.find((item) => item.id === parentId && item.post_id === postId)
  if (!parent) {
    fail('VALIDATION', '要评论的内容不存在')
  }
  return {
    parent_id: parent.parent_id || parent.id,
    reply_to: {
      id: parent.author.id,
      nickname: parent.author.nickname,
      avatar_url: parent.author.avatar_url,
    },
  }
}

function findPost(id: string): MockPost {
  const post = store.posts.find((item) => item.id === id)
  if (!post) {
    fail('NOT_FOUND', '帖子不存在')
  }
  return post
}

function findVideo(id: string): MockVideo {
  const video = store.videos.find((item) => item.id === id)
  if (!video) {
    fail('NOT_FOUND', '任务不存在')
  }
  return video
}

function assertOwnPost(post: MockPost) {
  if (post.author.id !== CURRENT_USER_ID) {
    fail('FORBIDDEN', '只能操作自己的帖子')
  }
}

function publishPost(post: MockPost) {
  if (post.status === 'published') {
    return
  }
  post.status = 'published'
  addLedger('earn', 20, '发布帖子')
}

function createShowPostFromAlbum(album: MockAlbum) {
  const post: MockPost = {
    id: newId(),
    author: currentAuthor(),
    board: 'show',
    title: album.title,
    body: album.body,
    image_urls: album.image_urls.slice(),
    topic_names: album.tag_names.slice(),
    status: 'draft',
    like_count: 0,
    comment_count: 0,
    favorite_count: 0,
    liked: false,
    favorited: false,
    created_at: album.created_at,
  }
  publishPost(post)
  store.posts.unshift(post)
}

function pointsSummary() {
  let earned = 0
  let spent = 0
  store.ledger.forEach((entry) => {
    if (entry.kind === 'earn') {
      earned += entry.amount
    } else {
      spent += entry.amount
    }
  })
  return { earned, spent, balance: store.me.points_balance }
}

function inLedgerRange(iso: string, range: string): boolean {
  if (!range || range === 'all') {
    return true
  }
  const created = new Date(iso)
  const now = new Date()
  if (range === 'month') {
    return created.getFullYear() === now.getFullYear() && created.getMonth() === now.getMonth()
  }
  if (range === 'quarter') {
    const from = new Date(now.getFullYear(), now.getMonth() - 2, 1)
    return created >= from
  }
  return true
}

const BOARDS = ['qa', 'show', 'share', 'help', 'daily', 'experience']
const RESOLUTIONS = ['540p', '720p', '1080p', '2k', '4k']

type Handler = (params: Params, options: MockOptions) => unknown

const routes: { method: string; pattern: string; handle: Handler }[] = [
  {
    method: 'POST',
    pattern: '/api/v1/auth/login',
    handle() {
      return { token: 'jwt-or-mock', expires_in: 604800 }
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/me',
    handle() {
      return copy(store.me)
    },
  },
  {
    method: 'PATCH',
    pattern: '/api/v1/me',
    handle(_params, options) {
      const data = bodyOf(options)
      if ('nickname' in data) {
        store.me.nickname = data.nickname === null ? null : String(data.nickname)
      }
      if ('avatar_url' in data) {
        store.me.avatar_url = data.avatar_url === null ? null : String(data.avatar_url)
      }
      return copy(store.me)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/media',
    handle(_params, options) {
      const file = bodyOf(options).file
      return {
        url: typeof file === 'string' && file ? file : mockPhotos.pet1,
        width: 800,
        height: 600,
        mime: 'image/jpeg',
      }
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/album',
    handle(_params, options) {
      return paginate(sortByCreated(store.albums).map(copy), options.query)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/album',
    handle(_params, options) {
      const data = bodyOf(options)
      const title = String(data.title || '').trim()
      const body = String(data.body || '').trim()
      const image_urls = asStringArray(data.image_urls)
      if (!title || !body) {
        fail('VALIDATION', '标题和说明不能为空')
      }
      if (image_urls.length < 1) {
        fail('VALIDATION', '至少上传一张照片')
      }
      if (image_urls.length > 9) {
        fail('VALIDATION', '最多 9 张照片')
      }
      const created_at = nowIso()
      const album: MockAlbum = {
        id: newId(),
        title,
        body,
        image_urls,
        cover_url: typeof data.cover_url === 'string' && data.cover_url ? data.cover_url : image_urls[0],
        tag_names: asStringArray(data.tag_names),
        sync_to_forum: Boolean(data.sync_to_forum),
        created_at,
      }
      store.albums.unshift(album)
      if (album.sync_to_forum) {
        createShowPostFromAlbum(album)
      }
      return copy(album)
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/album/{id}',
    handle(params) {
      return copy(findAlbum(params.id))
    },
  },
  {
    method: 'PATCH',
    pattern: '/api/v1/album/{id}',
    handle(params, options) {
      const album = findAlbum(params.id)
      const data = bodyOf(options)
      if (typeof data.title === 'string') {
        if (!data.title.trim()) {
          fail('VALIDATION', '标题不能为空')
        }
        album.title = data.title.trim()
      }
      if (typeof data.body === 'string') {
        if (!data.body.trim()) {
          fail('VALIDATION', '说明不能为空')
        }
        album.body = data.body.trim()
      }
      if (Array.isArray(data.image_urls)) {
        const image_urls = asStringArray(data.image_urls)
        if (image_urls.length < 1 || image_urls.length > 9) {
          fail('VALIDATION', '照片数量须为 1–9 张')
        }
        album.image_urls = image_urls
        album.cover_url = image_urls[0]
      }
      if (typeof data.cover_url === 'string' && data.cover_url) {
        album.cover_url = data.cover_url
      }
      if (Array.isArray(data.tag_names)) {
        album.tag_names = asStringArray(data.tag_names)
      }
      if (typeof data.sync_to_forum === 'boolean') {
        album.sync_to_forum = data.sync_to_forum
      }
      return copy(album)
    },
  },
  {
    method: 'DELETE',
    pattern: '/api/v1/album/{id}',
    handle(params) {
      findAlbum(params.id)
      store.albums = store.albums.filter((item) => item.id !== params.id)
      return { ok: true }
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/community/post/mine',
    handle(_params, options) {
      const status = queryValue(options.query, 'status')
      const mine = sortByCreated(
        store.posts.filter((post) => {
          if (post.author.id !== CURRENT_USER_ID) {
            return false
          }
          if (status && post.status !== status) {
            return false
          }
          return true
        }),
      ).map(presentPost)
      return paginate(mine, options.query)
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/community/post',
    handle(_params, options) {
      const tab = queryValue(options.query, 'tab') || 'recommend'
      const q = (queryValue(options.query, 'q') || '').trim()
      const items = sortByCreated(
        store.posts.filter((post) => {
          if (post.status !== 'published') {
            return false
          }
          if (tab === 'following' && store.follows.indexOf(post.author.id) === -1) {
            return false
          }
          if (BOARDS.indexOf(tab) !== -1 && post.board !== tab) {
            return false
          }
          if (q && post.title.indexOf(q) === -1 && post.body.indexOf(q) === -1) {
            return false
          }
          return true
        }),
      ).map(presentPost)
      return paginate(items, options.query)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/community/post',
    handle(_params, options) {
      const data = bodyOf(options)
      const board = String(data.board || '')
      const status = String(data.status || '')
      const title = typeof data.title === 'string' ? data.title : ''
      const body = typeof data.body === 'string' ? data.body : ''
      const image_urls = asStringArray(data.image_urls)
      if (BOARDS.indexOf(board) === -1) {
        fail('VALIDATION', '板块不正确')
      }
      if (status !== 'draft' && status !== 'pending') {
        fail('VALIDATION', '状态只允许 draft 或 pending')
      }
      if (!body.trim() && image_urls.length === 0) {
        fail('VALIDATION', '正文和图片不能同时为空')
      }
      if (body.length > 500) {
        fail('VALIDATION', '正文最多 500 字')
      }
      if (image_urls.length > 9) {
        fail('VALIDATION', '最多 9 张照片')
      }
      const post: MockPost = {
        id: newId(),
        author: currentAuthor(),
        board: board as MockPost['board'],
        title,
        body,
        image_urls,
        topic_names: asStringArray(data.topic_names),
        status: 'draft',
        like_count: 0,
        comment_count: 0,
        favorite_count: 0,
        liked: false,
        favorited: false,
        created_at: nowIso(),
      }
      if (status === 'pending') {
        publishPost(post)
      }
      store.posts.unshift(post)
      return presentPost(post)
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/community/post/{id}',
    handle(params) {
      return presentPost(findPost(params.id))
    },
  },
  {
    method: 'PATCH',
    pattern: '/api/v1/community/post/{id}',
    handle(params, options) {
      const post = findPost(params.id)
      assertOwnPost(post)
      const data = bodyOf(options)
      if (typeof data.board === 'string') {
        if (BOARDS.indexOf(data.board) === -1) {
          fail('VALIDATION', '板块不正确')
        }
        post.board = data.board as MockPost['board']
      }
      if (typeof data.title === 'string') {
        post.title = data.title
      }
      if (typeof data.body === 'string') {
        if (data.body.length > 500) {
          fail('VALIDATION', '正文最多 500 字')
        }
        post.body = data.body
      }
      if (Array.isArray(data.image_urls)) {
        const image_urls = asStringArray(data.image_urls)
        if (image_urls.length > 9) {
          fail('VALIDATION', '最多 9 张照片')
        }
        post.image_urls = image_urls
      }
      if (Array.isArray(data.topic_names)) {
        post.topic_names = asStringArray(data.topic_names)
      }
      if (!post.body.trim() && post.image_urls.length === 0) {
        fail('VALIDATION', '正文和图片不能同时为空')
      }
      if (typeof data.status === 'string') {
        if (data.status === 'pending' && post.status === 'draft') {
          publishPost(post)
        } else if (data.status === 'draft' && post.status === 'draft') {
          post.status = 'draft'
        } else if (data.status !== post.status) {
          fail('VALIDATION', '不能这样改状态')
        }
      }
      return presentPost(post)
    },
  },
  {
    method: 'DELETE',
    pattern: '/api/v1/community/post/{id}',
    handle(params) {
      const post = findPost(params.id)
      assertOwnPost(post)
      store.comments = store.comments.filter((item) => item.post_id !== params.id)
      store.posts = store.posts.filter((item) => item.id !== params.id)
      return { ok: true }
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/community/post/{id}/like',
    handle(params) {
      const post = findPost(params.id)
      if (post.liked) {
        post.liked = false
        post.like_count = Math.max(0, post.like_count - 1)
      } else {
        post.liked = true
        post.like_count += 1
      }
      return presentPost(post)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/community/post/{id}/favorite',
    handle(params) {
      const post = findPost(params.id)
      if (post.favorited) {
        post.favorited = false
        post.favorite_count = Math.max(0, post.favorite_count - 1)
      } else {
        post.favorited = true
        post.favorite_count += 1
      }
      return presentPost(post)
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/community/post/{id}/comment',
    handle(params, options) {
      findPost(params.id)
      const items = store.comments
        .filter((item) => item.post_id === params.id)
        .slice()
        .sort((a, b) => (a.created_at < b.created_at ? -1 : a.created_at > b.created_at ? 1 : 0))
        .map(presentComment)
      return paginate(items, options.query)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/community/post/{id}/comment',
    handle(params, options) {
      const post = findPost(params.id)
      const data = bodyOf(options)
      const body = String(data.body || '').trim()
      if (body.length > 200) {
        fail('VALIDATION', '评论最多 200 字')
      }
      const sticker_ids = asStringArray(data.sticker_ids)
      if (sticker_ids.length > 8) {
        fail('VALIDATION', '贴纸最多 8 个')
      }
      if (sticker_ids.some((id) => STICKER_IDS.indexOf(id) === -1)) {
        fail('VALIDATION', '贴纸不存在')
      }
      const image_urls = asStringArray(data.image_urls)
      if (image_urls.length > 9) {
        fail('VALIDATION', '图片最多 9 张')
      }
      const audio_url_raw = data.audio_url
      const audio_url = typeof audio_url_raw === 'string' && audio_url_raw ? audio_url_raw : null
      const audio_duration = Math.max(0, Math.floor(Number(data.audio_duration || 0)))
      if (audio_url && (audio_duration < 1 || audio_duration > 60)) {
        fail('VALIDATION', '语音时长要在 1 到 60 秒')
      }
      if (!audio_url && audio_duration !== 0) {
        fail('VALIDATION', '没有语音文件')
      }
      if (!body && sticker_ids.length === 0 && image_urls.length === 0 && !audio_url) {
        fail('VALIDATION', '评论不能为空')
      }
      const parentRaw = data.parent_id
      const parentId = typeof parentRaw === 'string' && parentRaw ? parentRaw : undefined
      const thread = resolveCommentParent(post.id, parentId)
      const comment: MockComment = {
        id: newId(),
        post_id: post.id,
        author: currentAuthor(),
        body,
        parent_id: thread.parent_id,
        reply_to: thread.reply_to,
        sticker_ids,
        image_urls,
        audio_url,
        audio_duration: audio_url ? audio_duration : 0,
        like_count: 0,
        liked: false,
        created_at: nowIso(),
      }
      store.comments.push(comment)
      syncCommentCount(post)
      return presentComment(comment)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/community/post/{id}/comment/{comment_id}/like',
    handle(params) {
      findPost(params.id)
      const comment = findComment(params.id, params.comment_id)
      if (comment.liked) {
        comment.liked = false
        comment.like_count = Math.max(0, comment.like_count - 1)
      } else {
        comment.liked = true
        comment.like_count += 1
      }
      return presentComment(comment)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/community/post/{id}/comment/{comment_id}/report',
    handle(params, options) {
      findPost(params.id)
      const comment = findComment(params.id, params.comment_id)
      if (comment.author.id === CURRENT_USER_ID) {
        fail('FORBIDDEN', '不能举报自己的评论')
      }
      const reason = String(bodyOf(options).reason || '')
      if (REPORT_REASONS.indexOf(reason) === -1) {
        fail('VALIDATION', '请选择举报原因')
      }
      return { ok: true }
    },
  },
  {
    method: 'DELETE',
    pattern: '/api/v1/community/post/{id}/comment/{comment_id}',
    handle(params) {
      const post = findPost(params.id)
      const comment = findComment(params.id, params.comment_id)
      assertCanDeleteComment(post, comment)
      reparentChildren(comment.id, comment.parent_id)
      store.comments = store.comments.filter((item) => item.id !== comment.id)
      syncCommentCount(post)
      return { ok: true, comment_count: post.comment_count }
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/community/follow',
    handle(_params, options) {
      const userId = String(bodyOf(options).user_id || '')
      if (!userId) {
        fail('VALIDATION', '缺少 user_id')
      }
      if (userId === CURRENT_USER_ID) {
        fail('VALIDATION', '不能关注自己')
      }
      if (store.follows.indexOf(userId) !== -1) {
        fail('CONFLICT', '已经关注')
      }
      store.follows.push(userId)
      return { ok: true }
    },
  },
  {
    method: 'DELETE',
    pattern: '/api/v1/community/follow/{user_id}',
    handle(params) {
      store.follows = store.follows.filter((id) => id !== params.user_id)
      return { ok: true }
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/video',
    handle(_params, options) {
      const status = queryValue(options.query, 'status')
      const items = sortByCreated(
        store.videos.filter((video) => !status || video.status === status),
      ).map(copy)
      return paginate(items, options.query)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/video',
    handle(_params, options) {
      const data = bodyOf(options)
      const image_urls = asStringArray(data.image_urls)
      const prompt = typeof data.prompt === 'string' ? data.prompt : ''
      const resolution = String(data.resolution || '')
      if (image_urls.length < 2 || image_urls.length > 9) {
        fail('VALIDATION', '请选择 2–9 张照片')
      }
      if (prompt.length > 100) {
        fail('VALIDATION', '提示词最多 100 字')
      }
      if (RESOLUTIONS.indexOf(resolution) === -1) {
        fail('VALIDATION', '分辨率不正确')
      }
      addLedger('spend', 50, '图生视频')
      const title = String(data.title || '').trim() || todayDate()
      const video: MockVideo = {
        id: newId(),
        title,
        image_urls,
        prompt,
        resolution: resolution as MockVideo['resolution'],
        status: 'pending',
        result_url: null,
        points_cost: 50,
        error_message: null,
        created_at: nowIso(),
      }
      store.videos.unshift(video)
      return copy(video)
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/video/{id}',
    handle(params) {
      return copy(findVideo(params.id))
    },
  },
  {
    method: 'DELETE',
    pattern: '/api/v1/video/{id}',
    handle(params) {
      const video = findVideo(params.id)
      if (video.status === 'running') {
        fail('CONFLICT', '生成中不能删除')
      }
      store.videos = store.videos.filter((item) => item.id !== params.id)
      return { ok: true }
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/points/summary',
    handle() {
      return pointsSummary()
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/points/ledger',
    handle(_params, options) {
      const kind = queryValue(options.query, 'kind')
      const range = queryValue(options.query, 'range') || 'all'
      const items = sortByCreated(
        store.ledger.filter((entry) => {
          if (kind && entry.kind !== kind) {
            return false
          }
          return inLedgerRange(entry.created_at, range)
        }),
      ).map(copy)
      return paginate(items, options.query)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/points/checkin',
    handle() {
      const date = todayDate()
      if (store.last_checkin_date === date) {
        return { awarded: 0, balance: store.me.points_balance, already_done: true, date }
      }
      addLedger('earn', 10, '签到')
      store.last_checkin_date = date
      return { awarded: 10, balance: store.me.points_balance, already_done: false, date }
    },
  },
]

export function handleMock(options: MockOptions): MockResult {
  for (let i = 0; i < routes.length; i += 1) {
    const route = routes[i]
    if (route.method !== options.method) {
      continue
    }
    const params = matchPath(route.pattern, options.path)
    if (!params) {
      continue
    }
    try {
      return { data: route.handle(params, options) }
    } catch (error) {
      if (isMockError(error)) {
        return { error }
      }
      return { error: { code: 'INTERNAL', message: 'mock failed' } }
    }
  }
  return {
    error: {
      code: 'MOCK_NOT_IMPLEMENTED',
      message: `${options.method} ${options.path}`,
    },
  }
}
