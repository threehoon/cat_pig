import { toastRequestError } from '../../../../core/request'
import { checkin, getPointsSummary, makeup } from '../../services/points'
import {
  buildCells,
  isCurrentMonth,
  monthTitle,
  nowYearMonth,
  shiftMonth,
  todayDate,
  type CalCell,
} from './checkin-calendar'
import {
  buildStreakStrip,
  checkinToastTitle,
  type StreakCell,
} from './streak-strip'

const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六']

Page({
  data: {
    weekdays: WEEKDAYS,
    year: 0,
    month: 0,
    title: '',
    canPrev: false,
    canNext: false,
    cells: [] as CalCell[],
    streakCells: [] as StreakCell[],
    streak: 0,
    makeup_card_count: 0,
    today_checked: false,
    makeup_dates: [] as string[],
    checkin_dates: [] as string[],
    busy: false,
  },
  onShow() {
    const now = nowYearMonth()
    this.setData({ year: now.year, month: now.month })
    this.reload()
  },
  reload() {
    return getPointsSummary()
      .then((summary) => {
        this.setData({
          streak: summary.streak,
          streakCells: buildStreakStrip(summary.streak, summary.today_checked),
          makeup_card_count: summary.makeup_card_count,
          today_checked: summary.today_checked,
          makeup_dates: summary.makeup_dates,
          checkin_dates: summary.checkin_dates,
        })
        this.paintCalendar()
      })
      .catch(toastRequestError)
  },
  paintCalendar() {
    const year = this.data.year
    const month = this.data.month
    const current = isCurrentMonth(year, month)
    this.setData({
      title: monthTitle(year, month),
      canPrev: current,
      canNext: !current,
      cells: buildCells(
        year,
        month,
        todayDate(),
        this.data.checkin_dates,
        this.data.makeup_dates,
      ),
    })
  },
  onPrev() {
    if (!this.data.canPrev) return
    const next = shiftMonth(this.data.year, this.data.month, -1)
    this.setData({ year: next.year, month: next.month })
    this.paintCalendar()
  },
  onNext() {
    if (!this.data.canNext) return
    const next = shiftMonth(this.data.year, this.data.month, 1)
    this.setData({ year: next.year, month: next.month })
    this.paintCalendar()
  },
  onCheckin() {
    if (this.data.busy || this.data.today_checked) return
    this.setData({ busy: true })
    checkin()
      .then((result) => {
        const title = checkinToastTitle(
          result.already_done,
          result.awarded,
          result.makeup_cards_awarded,
        )
        wx.showToast({ title, icon: 'none' })
        return this.reload()
      })
      .catch(toastRequestError)
      .then(() => {
        this.setData({ busy: false })
      })
  },
  onDay(e: WechatMiniprogram.TouchEvent) {
    if (this.data.busy) return
    const date = e.currentTarget.dataset.date as string
    if (!date) return
    if (this.data.makeup_dates.indexOf(date) === -1) return
    wx.showModal({
      title: '补签',
      content: '是否补签这一天？',
      success: (res) => {
        if (!res.confirm) return
        this.doMakeup(date)
      },
    })
  },
  doMakeup(date: string) {
    if (this.data.busy) return
    if (this.data.makeup_card_count < 1) {
      wx.showToast({ title: '无法补签', icon: 'none' })
      return
    }
    this.setData({ busy: true })
    makeup(date)
      .then((result) => {
        wx.showToast({ title: `补签成功，积分 +${result.awarded}`, icon: 'none' })
        return this.reload()
      })
      .catch(() => {
        wx.showToast({ title: '无法补签', icon: 'none' })
      })
      .then(() => {
        this.setData({ busy: false })
      })
  },
})
