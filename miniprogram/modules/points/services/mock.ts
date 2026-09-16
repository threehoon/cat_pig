import {
  bodyOf,
  copy,
  paginate,
  queryValue,
  sortByCreated,
  type MockRoute,
} from '../../../core/mock-runtime'
import { store } from '../../../mocks/store'
import { inLedgerRange, performCheckin, performMakeup, pointsSummary } from './mock-ledger'

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
    handle: () => performCheckin(),
  },
  {
    method: 'POST',
    pattern: '/api/v1/points/makeup',
    handle: (_params, options) => performMakeup(bodyOf(options).date),
  },
]
