import { brandAssets } from '../../assets/paths'
import { formatCreatedAt } from '../../utils/util'
import { BOARD_LABEL, POST_STATUS_LABEL, Post } from './types/post'

export type PostCardView = {
  id: string
  author: string
  avatar: string
  time: string
  board: string
  body: string
  covers: string[]
  showMedia: boolean
  like_count: number
  comment_count: number
  favorite_count: number
  liked: boolean
  favorited: boolean
}

export function toPostCard(post: Post, mode: 'board' | 'status' = 'board'): PostCardView {
  const board = mode === 'status' ? POST_STATUS_LABEL[post.status] : BOARD_LABEL[post.board]
  const covers = post.image_urls.slice(0, 2)
  return {
    id: post.id,
    author: post.author.nickname || '用户',
    avatar: post.author.avatar_url || brandAssets.avatarDefault,
    time: formatCreatedAt(post.created_at),
    board,
    body: post.title || post.body,
    covers,
    showMedia: covers.length > 0,
    like_count: post.like_count,
    comment_count: post.comment_count,
    favorite_count: post.favorite_count,
    liked: post.liked,
    favorited: post.favorited,
  }
}

export function replaceCard(cards: PostCardView[], post: Post, mode: 'board' | 'status' = 'board'): PostCardView[] {
  const next = toPostCard(post, mode)
  return cards.map((card) => (card.id === post.id ? next : card))
}
