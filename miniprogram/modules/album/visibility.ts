import { AlbumVisibility } from './types/album'

export const ALBUM_VISIBILITY_LABEL: Record<AlbumVisibility, string> = {
  public: '公开',
  friends: '好友可见',
  private: '私密',
}

export const ALBUM_VISIBILITY_FILTERS: { id: 'all' | AlbumVisibility; label: string }[] = [
  { id: 'all', label: '全部' },
  { id: 'public', label: '公开' },
  { id: 'friends', label: '好友可见' },
  { id: 'private', label: '私密' },
]

export const ALBUM_VISIBILITY_OPTIONS: AlbumVisibility[] = ['public', 'friends', 'private']

export function parseVisibility(value: unknown): AlbumVisibility | null {
  if (value === 'public' || value === 'private' || value === 'friends') {
    return value
  }
  return null
}

export function resolveVisibility(value: unknown): AlbumVisibility {
  const parsed = parseVisibility(value)
  if (parsed) {
    return parsed
  }
  return 'private'
}

export function canView(input: {
  viewerId: string
  ownerId: string
  visibility: AlbumVisibility
  mutualFollow: boolean
  blocked: boolean
}): boolean {
  if (input.blocked) {
    return false
  }
  if (input.viewerId === input.ownerId) {
    return true
  }
  if (input.visibility === 'public') {
    return true
  }
  if (input.visibility === 'friends' && input.mutualFollow) {
    return true
  }
  return false
}
