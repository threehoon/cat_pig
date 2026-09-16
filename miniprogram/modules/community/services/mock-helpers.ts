import { copy, fail, newId } from '../../../core/mock-runtime'
import {
  CURRENT_USER_ID,
  currentAuthor,
  store,
  type MockAlbum,
  type MockAuthor,
  type MockComment,
  type MockPost,
} from '../../../mocks/store'
import { addLedger } from '../../points/services/mock-ledger'

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

export function presentUser(id: string): MockAuthor | null {
  if (id === CURRENT_USER_ID) return currentAuthor()
  let found: MockAuthor | null = null
  for (let i = 0; i < store.authors.length; i += 1) {
    if (store.authors[i].id === id) {
      found = store.authors[i]
      break
    }
  }
  if (!found) return null
  return copy(found)
}

export function presentUsers(ids: string[]): MockAuthor[] {
  const items: MockAuthor[] = []
  for (let i = ids.length - 1; i >= 0; i -= 1) {
    const author = presentUser(ids[i])
    if (author) items.push(author)
  }
  return items
}

function presentAuthor(author: MockComment['author']) {
  if (author.id !== CURRENT_USER_ID) {
    return { id: author.id, nickname: author.nickname, avatar_url: author.avatar_url }
  }
  return { id: author.id, nickname: store.me.nickname, avatar_url: store.me.avatar_url }
}

export function presentComment(item: MockComment) {
  return copy({
    id: item.id,
    author: presentAuthor(item.author),
    body: item.body,
    parent_id: item.parent_id,
    reply_to: item.reply_to ? presentAuthor(item.reply_to) : null,
    sticker_ids: item.sticker_ids.slice(),
    image_urls: item.image_urls.slice(),
    audio_url: item.audio_url || null,
    audio_duration: item.audio_duration || 0,
    like_count: item.like_count,
    liked: item.liked,
    created_at: item.created_at,
  })
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

export function reparentChildren(deletedId: string, newParentId: string | null) {
  store.comments.forEach((item) => {
    if (item.parent_id === deletedId) item.parent_id = newParentId
  })
}

export function syncAlbumToForum(album: MockAlbum) {
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
