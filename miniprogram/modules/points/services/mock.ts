import {
  addLedger,
  copy,
  inLedgerRange,
  paginate,
  pointsSummary,
  queryValue,
  sortByCreated,
  todayDate,
  type MockRoute,
  store,
} from '../../../core/mock-runtime'

export const pointsMockRoutes: MockRoute[] = [
  { method: 'GET', pattern: '/api/v1/points/summary', handle: () => pointsSummary() },
  {
    method: 'GET',
    pattern: '/api/v1/points/ledger',
    handle: (_params, options) => {
      const kind = queryValue(options.query, 'kind')
      const range = queryValue(options.query, 'range') || 'all'
      const items = sortByCreated(
        store.ledger.filter((entry) => (!kind || entry.kind === kind) && inLedgerRange(entry.created_at, range)),
      ).map(copy)
      return paginate(items, options.query)
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/points/checkin',
    handle: () => {
      const date = todayDate()
      if (store.last_checkin_date === date)
        return { awarded: 0, balance: store.me.points_balance, already_done: true, date }
      addLedger('earn', 10, '签到')
      store.last_checkin_date = date
      return { awarded: 10, balance: store.me.points_balance, already_done: false, date }
    },
  },
]
