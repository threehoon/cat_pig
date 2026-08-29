export type Me = {
  id: string
  nickname: string | null
  avatar_url: string | null
  points_balance: number
}

export type MePatch = {
  nickname?: string | null
  avatar_url?: string | null
}
