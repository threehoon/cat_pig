export type PointsKind = 'earn' | 'spend'

export type PointsRange = 'all' | 'month' | 'quarter'

export type PointsSummary = {
  earned: number
  spent: number
  balance: number
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
}
