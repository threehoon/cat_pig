import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { formatCreatedAt } from '../../../../utils/util'
import { checkin, getPointsSummary, listLedger } from '../../services/points'
import { PointsEntry, PointsKind } from '../../types/points'

type Filter = 'all' | PointsKind

type LedgerRow = {
  id: string
  title: string
  time: string
  delta: string
  earn: boolean
}

const FILTERS: { id: Filter; label: string }[] = [
  { id: 'all', label: '全部' },
  { id: 'spend', label: '消耗' },
  { id: 'earn', label: '获取' },
]

function toRow(entry: PointsEntry): LedgerRow {
  return {
    id: entry.id,
    title: entry.title,
    time: formatCreatedAt(entry.created_at),
    delta: entry.kind === 'earn' ? `+${entry.amount}` : `-${entry.amount}`,
    earn: entry.kind === 'earn',
  }
}

Page({
  data: {
    checkinHint: '',
    gift: brandAssets.gift,
    earned: 0,
    spent: 0,
    balance: 0,
    filter: 'all' as Filter,
    filters: FILTERS,
    rows: [] as LedgerRow[],
  },
  onLoad(query: { checkin?: string }) {
    const shouldCheckin = query.checkin === '1'
    const load = () => this.reload()
    if (!shouldCheckin) {
      load()
      return
    }
    checkin()
      .then((result) => {
        const checkinHint = result.already_done
          ? '今天已经签过到了'
          : `签到成功，积分 +${result.awarded}`
        this.setData({ checkinHint })
        load()
      })
      .catch(toastRequestError)
  },
  reload() {
    const kind = this.data.filter === 'all' ? undefined : this.data.filter
    Promise.all([getPointsSummary(), listLedger(kind)])
      .then(([summary, ledger]) => {
        this.setData({
          earned: summary.earned,
          spent: summary.spent,
          balance: summary.balance,
          rows: ledger.items.map(toRow),
        })
      })
      .catch(toastRequestError)
  },
  onFilter(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as Filter
    this.setData({ filter: id }, () => {
      this.reload()
    })
  },
})
