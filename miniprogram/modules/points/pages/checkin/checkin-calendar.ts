export type CalCell = {
  key: string
  label: string
  date: string
  signed: boolean
  today: boolean
  makeup: boolean
  future: boolean
  empty: boolean
}

function pad2(n: number): string {
  return String(n).padStart(2, '0')
}

export function todayDate(): string {
  const now = new Date()
  return `${now.getFullYear()}-${pad2(now.getMonth() + 1)}-${pad2(now.getDate())}`
}

export function nowYearMonth(): { year: number; month: number } {
  const now = new Date()
  return { year: now.getFullYear(), month: now.getMonth() + 1 }
}

export function monthTitle(year: number, month: number): string {
  return `${year}年${month}月`
}

export function shiftMonth(year: number, month: number, delta: number): { year: number; month: number } {
  const next = new Date(year, month - 1 + delta, 1)
  return { year: next.getFullYear(), month: next.getMonth() + 1 }
}

export function isCurrentMonth(year: number, month: number): boolean {
  const now = nowYearMonth()
  return year === now.year && month === now.month
}

export function buildCells(
  year: number,
  month: number,
  today: string,
  signedDates: string[],
  makeupDates: string[],
): CalCell[] {
  const startWeekday = new Date(year, month - 1, 1).getDay()
  const daysInMonth = new Date(year, month, 0).getDate()
  const cells: CalCell[] = []
  let i = 0
  while (i < startWeekday) {
    cells.push({
      key: `pad-${i}`,
      label: '',
      date: '',
      signed: false,
      today: false,
      makeup: false,
      future: false,
      empty: true,
    })
    i += 1
  }
  let day = 1
  while (day <= daysInMonth) {
    const date = `${year}-${pad2(month)}-${pad2(day)}`
    cells.push({
      key: date,
      label: String(day),
      date,
      signed: signedDates.indexOf(date) !== -1,
      today: date === today,
      makeup: makeupDates.indexOf(date) !== -1,
      future: date > today,
      empty: false,
    })
    day += 1
  }
  return cells
}
