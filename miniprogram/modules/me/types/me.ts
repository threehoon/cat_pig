export type Me = {
  id: string
  nickname: string | null
  avatar_url: string | null
  points_balance: number
  post_count: number
  like_received_count: number
  following_count: number
  follower_count: number
}

export type MePatch = {
  nickname?: string | null
  avatar_url?: string | null
}
