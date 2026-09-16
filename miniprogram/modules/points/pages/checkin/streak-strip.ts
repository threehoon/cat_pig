export type StreakCell = {
  key: string
  day: number
  label: string
  points: string
  card: boolean
  filled: boolean
  next: boolean
}

export function buildStreakStrip(streak: number, todayChecked: boolean): StreakCell[] {
  const filledCount = streak < 7 ? streak : 7
  const nextDay = todayChecked || filledCount >= 7 ? 0 : filledCount + 1
  const cells: StreakCell[] = []
  let day = 1
  while (day <= 7) {
    let points = '+10'
    let card = false
    if (day === 3) {
      points = '+30'
      card = true
    } else if (day === 7) {
      points = '+60'
      card = true
    }
    cells.push({
      key: String(day),
      day,
      label: `第${day}天`,
      points,
      card,
      filled: day <= filledCount,
      next: day === nextDay,
    })
    day += 1
  }
  return cells
}

export function checkinToastTitle(
  alreadyDone: boolean,
  awarded: number,
  makeupCardsAwarded: number,
): string {
  if (alreadyDone) return '今天已经签过了'
  if (makeupCardsAwarded > 0) return `积分 +${awarded}，补签卡 +${makeupCardsAwarded}`
  return `签到成功，积分 +${awarded}`
}
