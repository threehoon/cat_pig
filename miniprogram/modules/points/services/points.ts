import { ListResult, request } from '../../../core/request'
import { CheckinResult, PointsEntry, PointsKind, PointsRange, PointsSummary } from '../types/points'

export function getPointsSummary() {
  return request<PointsSummary>({
    method: 'GET',
    path: '/api/v1/points/summary',
  })
}

export function listLedger(kind?: PointsKind, range: PointsRange = 'all', page = 1, pageSize = 20) {
  return request<ListResult<PointsEntry>>({
    method: 'GET',
    path: '/api/v1/points/ledger',
    query: { kind, range, page, page_size: pageSize },
  })
}

export function checkin() {
  return request<CheckinResult>({
    method: 'POST',
    path: '/api/v1/points/checkin',
    data: {},
  })
}
