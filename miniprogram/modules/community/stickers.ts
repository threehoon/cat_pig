import { brandAssets } from '../../assets/paths'
import { CommentStickerId } from './types/post'

export type StickerView = {
  id: CommentStickerId
  src: string
  key?: string
}

export const COMMENT_STICKERS: StickerView[] = [
  { id: 'blush', src: brandAssets.stickerBlush },
  { id: 'happy', src: brandAssets.stickerHappy },
  { id: 'cry', src: brandAssets.stickerCry },
  { id: 'paw', src: brandAssets.stickerPaw },
  { id: 'heart', src: brandAssets.stickerHeart },
  { id: 'sleep', src: brandAssets.stickerSleep },
  { id: 'wow', src: brandAssets.stickerWow },
  { id: 'kiss', src: brandAssets.stickerKiss },
]

export const QUICK_STICKERS = COMMENT_STICKERS.filter(
  (item) => item.id === 'blush' || item.id === 'happy' || item.id === 'cry',
)

export const UNICODE_EMOJIS = [
  '😂',
  '😭',
  '🥰',
  '😍',
  '😊',
  '😘',
  '😜',
  '😎',
  '👍',
  '🙏',
  '👏',
  '💪',
  '🔥',
  '✨',
  '❤️',
  '🧡',
  '🐶',
  '🐱',
  '🐰',
  '🐻',
  '🐼',
  '🦊',
  '🐷',
  '🐥',
  '🐾',
  '🦴',
  '☀️',
  '🌙',
  '⭐',
  '💤',
  '🎾',
  '🏠',
]

const STICKER_SRC: Record<CommentStickerId, string> = {
  blush: brandAssets.stickerBlush,
  happy: brandAssets.stickerHappy,
  cry: brandAssets.stickerCry,
  paw: brandAssets.stickerPaw,
  heart: brandAssets.stickerHeart,
  sleep: brandAssets.stickerSleep,
  wow: brandAssets.stickerWow,
  kiss: brandAssets.stickerKiss,
}

export function stickersOf(ids: string[]): StickerView[] {
  return ids
    .filter((id): id is CommentStickerId => id in STICKER_SRC)
    .map((id) => ({ id, src: STICKER_SRC[id] }))
}
