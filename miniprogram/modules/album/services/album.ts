import { ListResult, request } from '../../../core/request'
import { Album, AlbumWrite } from '../types/album'

export function listAlbums(page = 1, pageSize = 20) {
  return request<ListResult<Album>>({
    method: 'GET',
    path: '/api/v1/album',
    query: { page, page_size: pageSize },
  })
}

export function createAlbum(body: AlbumWrite) {
  return request<Album>({
    method: 'POST',
    path: '/api/v1/album',
    data: body,
  })
}

export function getAlbum(id: string) {
  return request<Album>({
    method: 'GET',
    path: `/api/v1/album/${id}`,
  })
}

export function patchAlbum(id: string, body: Partial<AlbumWrite>) {
  return request<Album>({
    method: 'PATCH',
    path: `/api/v1/album/${id}`,
    data: body,
  })
}

export function deleteAlbum(id: string) {
  return request<{ ok: true }>({
    method: 'DELETE',
    path: `/api/v1/album/${id}`,
  })
}
