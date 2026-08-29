export type Author = {
  id: string
  nickname: string | null
  avatar_url: string | null
}

export type Board = 'qa' | 'show' | 'share' | 'help' | 'daily' | 'experience'

export type PostTab = 'recommend' | 'following' | Board

export type PostStatus = 'draft' | 'pending' | 'published' | 'rejected'

export type Post = {
  id: string
  author: Author
  board: Board
  title: string
  body: string
  image_urls: string[]
  topic_names: string[]
  status: PostStatus
  followed: boolean
  like_count: number
  comment_count: number
  favorite_count: number
  liked: boolean
  favorited: boolean
  created_at: string
}

export type Comment = {
  id: string
  author: Author
  body: string
  created_at: string
}

export type PostWrite = {
  board: Board
  title: string
  body: string
  image_urls: string[]
  topic_names: string[]
  status: 'draft' | 'pending'
}

export const BOARDS: { id: Board; label: string }[] = [
  { id: 'qa', label: '问答' },
  { id: 'show', label: '晒宠' },
  { id: 'share', label: '分享' },
  { id: 'help', label: '求助' },
  { id: 'daily', label: '日常' },
  { id: 'experience', label: '经验' },
]

export const PLAZA_TABS: { id: PostTab; label: string }[] = [
  { id: 'recommend', label: '推荐' },
  { id: 'following', label: '关注' },
  ...BOARDS,
]

export const BOARD_LABEL: Record<Board, string> = {
  qa: '问答',
  show: '晒宠',
  share: '分享',
  help: '求助',
  daily: '日常',
  experience: '经验',
}

export const POST_STATUS_LABEL: Record<PostStatus, string> = {
  draft: '草稿',
  pending: '审核中',
  published: '已发布',
  rejected: '未通过',
}

export const TOPIC_PRESETS = ['可爱瞬间', '日常', '生日', '旅行', '活动']
