import { request } from '../../../core/request'
import { Me, MePatch } from '../types/me'

export function getMe() {
  return request<Me>({
    method: 'GET',
    path: '/api/v1/me',
  })
}

export function patchMe(body: MePatch) {
  return request<Me>({
    method: 'PATCH',
    path: '/api/v1/me',
    data: body,
  })
}
