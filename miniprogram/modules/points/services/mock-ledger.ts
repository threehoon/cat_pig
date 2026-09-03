import { fail, newId, nowIso } from '../../../core/mock-runtime'
import { store } from '../../../mocks/store'
import type { PointsKind } from '../types/points'

export function addLedger(kind: PointsKind, amount: number, title: string) {
  if (kind === 'spend' && store.me.points_balance < amount) fail('POINTS_NOT_ENOUGH', '积分不足')
  store.me.points_balance += kind === 'earn' ? amount : -amount
  store.ledger.unshift({
    id: newId(), kind, amount, title,
    balance_after: store.me.points_balance, created_at: nowIso(),
  })
}

export function pointsSummary() {
  let earned = 0
  let spent = 0
  store.ledger.forEach((entry) => {
    if (entry.kind === 'earn') earned += entry.amount
    else spent += entry.amount
  })
  return { earned, spent, balance: store.me.points_balance }
}

export function inLedgerRange(iso: string, range: string): boolean {
  if (!range || range === 'all') return true
  const created = new Date(iso)
  const now = new Date()
  if (range === 'month') return created.getFullYear() === now.getFullYear() && created.getMonth() === now.getMonth()
  if (range === 'quarter') return created >= new Date(now.getFullYear(), now.getMonth() - 2, 1)
  return true
}
