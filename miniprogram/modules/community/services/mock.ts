import {
  asStringArray,
  assertCanDeleteComment,
  assertOwnPost,
  bodyOf,
  BOARDS,
  CURRENT_USER_ID,
  fail,
  findComment,
  findPost,
  newId,
  nowIso,
  paginate,
  presentComment,
  presentPost,
  publishPost,
  currentAuthor,
  queryValue,
  REPORT_REASONS,
  resolveCommentParent,
  sortByCreated,
  STICKER_IDS,
  syncCommentCount,
  type MockRoute,
  store,
} from '../../../core/mock-runtime'
import type { MockComment, MockPost } from '../../../core/mock-store'

function reparentChildren(deletedId: string, newParentId: string | null) {
  store.comments.forEach((item) => {
    if (item.parent_id === deletedId) item.parent_id = newParentId
  })
}

const postRoutes: MockRoute[] = [
  {
    method: 'GET',
    pattern: '/api/v1/community/post/mine',
    handle: (_params, options) => {
      const status = queryValue(options.query, 'status')
      const mine = sortByCreated(
        store.posts.filter((post) => post.author.id === CURRENT_USER_ID && (!status || post.status === status)),
      ).map(presentPost)
      return paginate(mine, options.query)
    },
  },
  {
    method: 'GET',
    pattern: '/api/v1/community/post',
    handle: (_params, options) => {
      const tab = queryValue(options.query, 'tab') || 'recommend'
      const q = (queryValue(options.query, 'q') || '').trim()
      const items = sortByCreated(
        store.posts.filter((post) => {
          if (post.status !== 'published') return false
          if (tab === 'following' && store.follows.indexOf(post.author.id) === -1) return false
          if ((BOARDS as readonly string[]).indexOf(tab) !== -1 && post.board !== tab) return false
          return !q || post.title.indexOf(q) !== -1 || post.body.indexOf(q) !== -1
        }),
      ).map(presentPost)
      return paginate(items, options.query)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/community/post',
    handle: (_params, options) => {
      const data = bodyOf(options)
      const board = String(data.board || '')
      const status = String(data.status || '')
      const title = typeof data.title === 'string' ? data.title : ''
      const body = typeof data.body === 'string' ? data.body : ''
      const image_urls = asStringArray(data.image_urls)
      if ((BOARDS as readonly string[]).indexOf(board) === -1) fail('VALIDATION', '板块不正确')
      if (status !== 'draft' && status !== 'pending') fail('VALIDATION', '状态只允许 draft 或 pending')
      if (!body.trim() && image_urls.length === 0) fail('VALIDATION', '正文和图片不能同时为空')
      if (body.length > 500) fail('VALIDATION', '正文最多 500 字')
      if (image_urls.length > 9) fail('VALIDATION', '最多 9 张照片')
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
      if (status === 'pending') publishPost(post)
      store.posts.unshift(post)
      return presentPost(post)
    },
  },
  { method: 'GET', pattern: '/api/v1/community/post/{id}', handle: (params) => presentPost(findPost(params.id)) },
  {
    method: 'PATCH',
    pattern: '/api/v1/community/post/{id}',
    handle: (params, options) => {
      const post = findPost(params.id)
      assertOwnPost(post)
      const data = bodyOf(options)
      if (typeof data.board === 'string') {
        if ((BOARDS as readonly string[]).indexOf(data.board) === -1) fail('VALIDATION', '板块不正确')
        post.board = data.board as MockPost['board']
      }
      if (typeof data.title === 'string') post.title = data.title
      if (typeof data.body === 'string') {
        if (data.body.length > 500) fail('VALIDATION', '正文最多 500 字')
        post.body = data.body
      }
      if (Array.isArray(data.image_urls)) {
        const image_urls = asStringArray(data.image_urls)
        if (image_urls.length > 9) fail('VALIDATION', '最多 9 张照片')
        post.image_urls = image_urls
      }
      if (Array.isArray(data.topic_names)) post.topic_names = asStringArray(data.topic_names)
      if (!post.body.trim() && post.image_urls.length === 0) fail('VALIDATION', '正文和图片不能同时为空')
      if (typeof data.status === 'string') {
        if (data.status === 'pending' && post.status === 'draft') publishPost(post)
        else if (data.status !== post.status) fail('VALIDATION', '不能这样改状态')
      }
      return presentPost(post)
    },
  },
  {
    method: 'DELETE',
    pattern: '/api/v1/community/post/{id}',
    handle: (params) => {
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
    handle: (params) => {
      const post = findPost(params.id)
      post.liked = !post.liked
      post.like_count = Math.max(0, post.like_count + (post.liked ? 1 : -1))
      return presentPost(post)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/community/post/{id}/favorite',
    handle: (params) => {
      const post = findPost(params.id)
      post.favorited = !post.favorited
      post.favorite_count = Math.max(0, post.favorite_count + (post.favorited ? 1 : -1))
      return presentPost(post)
    },
  },
]

const commentRoutes: MockRoute[] = [
  {
    method: 'GET',
    pattern: '/api/v1/community/post/{id}/comment',
    handle: (params, options) => {
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
    handle: (params, options) => {
      const post = findPost(params.id)
      const data = bodyOf(options)
      const body = String(data.body || '').trim()
      const sticker_ids = asStringArray(data.sticker_ids)
      const image_urls = asStringArray(data.image_urls)
      if (body.length > 200) fail('VALIDATION', '评论最多 200 字')
      if (sticker_ids.length > 8) fail('VALIDATION', '贴纸最多 8 个')
      if (sticker_ids.some((id) => (STICKER_IDS as readonly string[]).indexOf(id) === -1))
        fail('VALIDATION', '贴纸不存在')
      if (image_urls.length > 9) fail('VALIDATION', '图片最多 9 张')
      const audio_url_raw = data.audio_url
      const audio_url = typeof audio_url_raw === 'string' && audio_url_raw ? audio_url_raw : null
      const audio_duration = Math.max(0, Math.floor(Number(data.audio_duration || 0)))
      if (audio_url && (audio_duration < 1 || audio_duration > 60)) {
        fail('VALIDATION', '语音时长要在 1 到 60 秒')
      }
      if (!audio_url && audio_duration !== 0) fail('VALIDATION', '没有语音文件')
      if (!body && !sticker_ids.length && !image_urls.length && !audio_url) fail('VALIDATION', '评论不能为空')
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
    handle: (params) => {
      findPost(params.id)
      const comment = findComment(params.id, params.comment_id)
      comment.liked = !comment.liked
      comment.like_count = Math.max(0, comment.like_count + (comment.liked ? 1 : -1))
      return presentComment(comment)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/community/post/{id}/comment/{comment_id}/report',
    handle: (params, options) => {
      findPost(params.id)
      const comment = findComment(params.id, params.comment_id)
      if (comment.author.id === CURRENT_USER_ID) fail('FORBIDDEN', '不能举报自己的评论')
      const reason = String(bodyOf(options).reason || '')
      if ((REPORT_REASONS as readonly string[]).indexOf(reason) === -1) fail('VALIDATION', '请选择举报原因')
      return { ok: true }
    },
  },
  {
    method: 'DELETE',
    pattern: '/api/v1/community/post/{id}/comment/{comment_id}',
    handle: (params) => {
      const post = findPost(params.id)
      const comment = findComment(params.id, params.comment_id)
      assertCanDeleteComment(post, comment)
      reparentChildren(comment.id, comment.parent_id)
      store.comments = store.comments.filter((item) => item.id !== comment.id)
      syncCommentCount(post)
      return { ok: true, comment_count: post.comment_count }
    },
  },
]

export const communityMockRoutes: MockRoute[] = [
  ...postRoutes,
  ...commentRoutes,
  {
    method: 'POST',
    pattern: '/api/v1/community/follow',
    handle: (_params, options) => {
      const userId = String(bodyOf(options).user_id || '')
      if (!userId) fail('VALIDATION', '缺少 user_id')
      if (userId === CURRENT_USER_ID) fail('VALIDATION', '不能关注自己')
      if (store.follows.indexOf(userId) !== -1) fail('CONFLICT', '已经关注')
      store.follows.push(userId)
      return { ok: true }
    },
  },
  {
    method: 'DELETE',
    pattern: '/api/v1/community/follow/{user_id}',
    handle: (params) => {
      store.follows = store.follows.filter((id) => id !== params.user_id)
      return { ok: true }
    },
  },
]
