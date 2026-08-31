import { brandAssets } from '../../../../assets/paths'
import { formatCreatedAt } from '../../../../utils/util'
import { mentionParts, MentionPart } from '../../mentions'
import { stickersOf, StickerView } from '../../stickers'
import { Comment, Post } from '../../types/post'

export type CommentView = {
  id: string
  nickname: string
  avatar: string
  body: string
  time: string
  replyToName: string
  canDelete: boolean
  isAuthor: boolean
  isOwn: boolean
  liked: boolean
  likeCount: number
  stickers: StickerView[]
  images: string[]
  previewImages: string[]
  showStack: boolean
  imageOverflow: number
  audioUrl: string
  audioDuration: number
  playing: boolean
  bodyParts: MentionPart[]
  replies: CommentView[]
}

export type MentionUser = { id: string; nickname: string; avatar: string }

export function collectNicknames(post: Post, comments: Comment[]): string[] {
  const names: string[] = []
  const add = (name: string | null) => { const nickname = (name || '用户').trim(); if (nickname && names.indexOf(nickname) === -1) names.push(nickname) }
  add(post.author.nickname); comments.forEach((item) => add(item.author.nickname)); return names
}

function toCommentView(item: Comment, currentUserId: string | null, postAuthorId: string, names: string[]): CommentView {
  const images = item.image_urls || []; const showStack = images.length > 3
  return {
    id: item.id, nickname: item.author.nickname || '用户', avatar: item.author.avatar_url || brandAssets.avatarDefault,
    body: item.body, time: formatCreatedAt(item.created_at), replyToName: (item.reply_to && item.reply_to.nickname) || '',
    canDelete: !!currentUserId && (item.author.id === currentUserId || postAuthorId === currentUserId), isAuthor: item.author.id === postAuthorId,
    isOwn: !!currentUserId && item.author.id === currentUserId, liked: item.liked, likeCount: item.like_count,
    stickers: stickersOf(item.sticker_ids || []).map((sticker, index) => ({ ...sticker, key: `${sticker.id}-${index}` })),
    images, previewImages: showStack ? images.slice(0, 1) : images.slice(0, 3), showStack, imageOverflow: showStack ? images.length - 1 : 0,
    audioUrl: item.audio_url || '', audioDuration: item.audio_duration || 0, playing: false, bodyParts: mentionParts(item.body, names), replies: [],
  }
}

export function collectMentions(post: Post, comments: Comment[], currentUserId: string | null): MentionUser[] {
  const seen: Record<string, boolean> = {}; const list: MentionUser[] = []
  const add = (id: string, nickname: string | null, avatar: string | null) => { if (!id || seen[id] || id === currentUserId) return; seen[id] = true; list.push({ id, nickname: nickname || '用户', avatar: avatar || brandAssets.avatarDefault }) }
  add(post.author.id, post.author.nickname, post.author.avatar_url); comments.forEach((item) => add(item.author.id, item.author.nickname, item.author.avatar_url)); return list
}

export function groupComments(items: Comment[], currentUserId: string | null, postAuthorId: string, names: string[]): CommentView[] {
  const views = items.map((item) => toCommentView(item, currentUserId, postAuthorId, names)); const byId: Record<string, CommentView> = {}; views.forEach((view) => { byId[view.id] = view })
  const roots: CommentView[] = []; items.forEach((item, index) => { const view = views[index]; if (item.parent_id && byId[item.parent_id]) byId[item.parent_id].replies.push(view); else roots.push(view) }); return roots
}

export function patchPlaying(list: CommentView[], id: string): CommentView[] { return list.map((item) => ({ ...item, playing: item.id === id, replies: patchPlaying(item.replies, id) })) }

export function patchCommentLike(list: CommentView[], id: string, liked: boolean, likeCount: number): CommentView[] {
  return list.map((item) => item.id === id ? { ...item, liked, likeCount } : item.replies.length ? { ...item, replies: patchCommentLike(item.replies, id, liked, likeCount) } : item)
}

export function mentionNames(users: MentionUser[]): string[] { return users.map((item) => item.nickname) }
