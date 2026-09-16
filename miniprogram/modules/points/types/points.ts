export type PointsKind = 'earn' | 'spend'

export type PointsRange = 'all' | 'month' | 'quarter'

export type PointsSummary = {
  earned: number
  spent: number
  balance: number
  streak: number
  makeup_card_count: number
  today_checked: boolean
  makeup_dates: string[]
  checkin_dates: string[]
  today_post_count: number
  today_comment_count: number
  today_like_count: number
}

export type PointsEntry = {
  id: string
  kind: PointsKind
  amount: number
  title: string
  balance_after: number
  created_at: string
}

export type CheckinResult = {
  awarded: number
  balance: number
  already_done: boolean
  date: string
  streak: number
  extra: number
  makeup_cards_awarded: number
  makeup_card_count: number
}

export type MakeupResult = {
  awarded: number
  balance: number
  date: string
  streak: number
  makeup_card_count: number
}
