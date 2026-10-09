import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { listConversations } from '../../services/assistant'
import { stageOpenConversation } from '../../services/open-conversation'
import { AssistantConversation } from '../../types/assistant'

type HistoryRow = {
  id: string
  title: string
  time: string
}

function pad(value: number): string {
  if (value < 10) {
    return '0' + value
  }
  return String(value)
}

function rawTimeLabel(value: string): string {
  const text = value.replace('T', ' ')
  const end = text.indexOf('Z')
  if (end === -1) {
    return text
  }
  return text.slice(0, end)
}

function timeLabel(value: string): string {
  const parsed = new Date(value)
  if (isNaN(parsed.getTime())) {
    return rawTimeLabel(value)
  }
  return (
    parsed.getFullYear() +
    '-' +
    pad(parsed.getMonth() + 1) +
    '-' +
    pad(parsed.getDate()) +
    ' ' +
    pad(parsed.getHours()) +
    ':' +
    pad(parsed.getMinutes()) +
    ':' +
    pad(parsed.getSeconds())
  )
}

function toRow(item: AssistantConversation): HistoryRow {
  return {
    id: item.id,
    title: item.title,
    time: timeLabel(item.updated_at),
  }
}

Page({
  data: {
    items: [] as HistoryRow[],
    page: 1,
    total: 0,
    loading: false,
    emptyPlaza: brandAssets.emptyPlaza,
  },
  onShow() {
    this.fetch(1)
  },
  fetch(page: number) {
    if (this.data.loading) {
      return
    }
    this.setData({ loading: true })
    listConversations(page, 20)
      .then((result) => {
        const rows = result.items.map((item) => toRow(item))
        const items = page === 1 ? rows : this.data.items.concat(rows)
        this.setData({
          items,
          page,
          total: result.total,
          loading: false,
        })
      })
      .catch((err: unknown) => {
        this.setData({ loading: false })
        toastRequestError(err)
      })
  },
  onMore() {
    if (this.data.loading || this.data.items.length >= this.data.total) {
      return
    }
    this.fetch(this.data.page + 1)
  },
  onOpen(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as string
    if (!id) {
      return
    }
    stageOpenConversation(id)
    wx.switchTab({ url: '/modules/assistant/pages/chat/chat' })
  },
})
