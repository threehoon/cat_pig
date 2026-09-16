import { fail, newId, nowIso, todayDate } from '../../../core/mock-runtime'
import { store } from '../../../mocks/store'
import type { CheckinResult, MakeupResult, PointsKind } from '../types/points'

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/
const POST_DAILY_CAP = 3
const COMMENT_DAILY_CAP = 1
const LIKE_DAILY_CAP = 3

function pad2(n: number): string {
  return String(n).padStart(2, '0')
}

function formatLocalDate(value: Date): string {
  return `${value.getFullYear()}-${pad2(value.getMonth() + 1)}-${pad2(value.getDate())}`
}

function localDateFromIso(iso: string): string {
  return formatLocalDate(new Date(iso))
}

function shiftDate(date: string, days: number): string {
  const parts = date.split('-')
  const year = Number(parts[0])
  const month = Number(parts[1])
  const day = Number(parts[2])
  return formatLocalDate(new Date(year, month - 1, day + days))
}

function hasCheckin(date: string): boolean {
  return store.checkin_dates.indexOf(date) !== -1
}

export function checkinStreak(): number {
  const today = todayDate()
  let cursor = hasCheckin(today) ? today : shiftDate(today, -1)
  if (!hasCheckin(cursor)) return 0
  let n = 0
  while (hasCheckin(cursor)) {
    n += 1
    cursor = shiftDate(cursor, -1)
  }
  return n
}

export function makeupDates(): string[] {
  const today = todayDate()
  const dates: string[] = []
  let i = 1
  while (i <= 6) {
    const date = shiftDate(today, -i)
    if (!hasCheckin(date)) dates.push(date)
    i += 1
  }
  return dates
}

export function addLedger(kind: PointsKind, amount: number, title: string) {
  if (kind === 'spend' && store.me.points_balance < amount) fail('POINTS_NOT_ENOUGH', '积分不足')
  store.me.points_balance += kind === 'earn' ? amount : -amount
  store.ledger.unshift({
    id: newId(),
    kind,
    amount,
    title,
    balance_after: store.me.points_balance,
    created_at: nowIso(),
  })
}

function countEarnToday(title: string): number {
  const today = todayDate()
  let count = 0
  store.ledger.forEach((entry) => {
    if (entry.kind !== 'earn' || entry.title !== title) return
    if (localDateFromIso(entry.created_at) === today) count += 1
  })
  return count
}

function monthPrefix(date: string): string {
  return date.slice(0, 7)
}

function previousMonthPrefix(today: string): string {
  const year = Number(today.slice(0, 4))
  const month = Number(today.slice(5, 7))
  const prev = new Date(year, month - 2, 1)
  return `${prev.getFullYear()}-${pad2(prev.getMonth() + 1)}`
}

function visibleCheckinDates(): string[] {
  const today = todayDate()
  const current = monthPrefix(today)
  const previous = previousMonthPrefix(today)
  const dates: string[] = []
  store.checkin_dates.forEach((date) => {
    const prefix = monthPrefix(date)
    if (prefix === current || prefix === previous) dates.push(date)
  })
  return dates
}

export function awardPublishedPost() {
  if (countEarnToday('发布帖子') >= POST_DAILY_CAP) return
  addLedger('earn', 20, '发布帖子')
}

export function awardComment() {
  if (countEarnToday('评论') >= COMMENT_DAILY_CAP) return
  addLedger('earn', 5, '评论')
}

export function awardLike() {
  if (countEarnToday('点赞') >= LIKE_DAILY_CAP) return
  addLedger('earn', 2, '点赞')
}

export function pointsSummary() {
  let earned = 0
  let spent = 0
  store.ledger.forEach((entry) => {
    if (entry.kind === 'earn') earned += entry.amount
    else spent += entry.amount
  })
  return {
    earned,
    spent,
    balance: store.me.points_balance,
    streak: checkinStreak(),
    makeup_card_count: store.makeup_card_count,
    today_checked: hasCheckin(todayDate()),
    makeup_dates: makeupDates(),
    checkin_dates: visibleCheckinDates(),
    today_post_count: countEarnToday('发布帖子'),
    today_comment_count: countEarnToday('评论'),
    today_like_count: countEarnToday('点赞'),
  }
}

export function performCheckin(): CheckinResult {
  const date = todayDate()
  if (hasCheckin(date)) {
    return {
      awarded: 0,
      balance: store.me.points_balance,
      already_done: true,
      date,
      streak: checkinStreak(),
      extra: 0,
      makeup_cards_awarded: 0,
      makeup_card_count: store.makeup_card_count,
    }
  }
  addLedger('earn', 10, '签到')
  store.checkin_dates.push(date)
  const streak = checkinStreak()
  let extra = 0
  let makeup_cards_awarded = 0
  if (streak === 3) {
    extra = 20
    makeup_cards_awarded = 1
  } else if (streak === 7) {
    extra = 50
    makeup_cards_awarded = 1
  }
  if (extra > 0) addLedger('earn', extra, '连续签到奖励')
  if (makeup_cards_awarded > 0) store.makeup_card_count += makeup_cards_awarded
  return {
    awarded: 10 + extra,
    balance: store.me.points_balance,
    already_done: false,
    date,
    streak,
    extra,
    makeup_cards_awarded,
    makeup_card_count: store.makeup_card_count,
  }
}

export function performMakeup(date: unknown): MakeupResult {
  if (typeof date !== 'string' || !DATE_RE.test(date)) fail('VALIDATION', '日期无效')
  if (date === todayDate()) fail('VALIDATION', '不能补今天')
  if (hasCheckin(date)) fail('VALIDATION', '这一天已经签过到了')
  if (store.makeup_card_count < 1) fail('VALIDATION', '无法补签')
  if (makeupDates().indexOf(date) === -1) fail('VALIDATION', '不在可补签范围内')
  store.makeup_card_count -= 1
  store.checkin_dates.push(date)
  addLedger('earn', 10, '补签')
  return {
    awarded: 10,
    balance: store.me.points_balance,
    date,
    streak: checkinStreak(),
    makeup_card_count: store.makeup_card_count,
  }
}

export function inLedgerRange(iso: string, range: string): boolean {
  if (!range || range === 'all') return true
  const created = new Date(iso)
  const now = new Date()
  if (range === 'month') {
    return created.getFullYear() === now.getFullYear() && created.getMonth() === now.getMonth()
  }
  if (range === 'quarter') return created >= new Date(now.getFullYear(), now.getMonth() - 2, 1)
  return true
}
