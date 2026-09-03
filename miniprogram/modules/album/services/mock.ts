import {
  asStringArray,
  bodyOf,
  copy,
  fail,
  newId,
  nowIso,
  paginate,
  sortByCreated,
  type MockRoute,
} from '../../../core/mock-runtime'
import { store, type MockAlbum } from '../../../mocks/store'
import { syncAlbumToForum } from '../../community/services/mock-helpers'

function findAlbum(id: string): MockAlbum {
  const album = store.albums.find((item) => item.id === id)
  if (!album) fail('NOT_FOUND', '相册不存在')
  return album
}

export const albumMockRoutes: MockRoute[] = [
  {
    method: 'GET',
    pattern: '/api/v1/album',
    handle: (_params, options) => paginate(sortByCreated(store.albums).map(copy), options.query),
  },
  {
    method: 'POST',
    pattern: '/api/v1/album',
    handle: (_params, options) => {
      const data = bodyOf(options)
      const title = String(data.title || '').trim()
      const body = String(data.body || '').trim()
      const image_urls = asStringArray(data.image_urls)
      if (!title || !body) fail('VALIDATION', '标题和说明不能为空')
      if (image_urls.length < 1 || image_urls.length > 9)
        fail('VALIDATION', image_urls.length < 1 ? '至少上传一张照片' : '最多 9 张照片')
      const album: MockAlbum = {
        id: newId(),
        title,
        body,
        image_urls,
        cover_url: typeof data.cover_url === 'string' && data.cover_url ? data.cover_url : image_urls[0],
        tag_names: asStringArray(data.tag_names),
        sync_to_forum: Boolean(data.sync_to_forum),
        created_at: nowIso(),
      }
      store.albums.unshift(album)
      if (album.sync_to_forum) syncAlbumToForum(album)
      return copy(album)
    },
  },
  { method: 'GET', pattern: '/api/v1/album/{id}', handle: (params) => copy(findAlbum(params.id)) },
  {
    method: 'PATCH',
    pattern: '/api/v1/album/{id}',
    handle: (params, options) => {
      const album = findAlbum(params.id)
      const data = bodyOf(options)
      if (typeof data.title === 'string') {
        if (!data.title.trim()) fail('VALIDATION', '标题不能为空')
        album.title = data.title.trim()
      }
      if (typeof data.body === 'string') {
        if (!data.body.trim()) fail('VALIDATION', '说明不能为空')
        album.body = data.body.trim()
      }
      if (Array.isArray(data.image_urls)) {
        const image_urls = asStringArray(data.image_urls)
        if (image_urls.length < 1 || image_urls.length > 9) fail('VALIDATION', '照片数量须为 1–9 张')
        album.image_urls = image_urls
        album.cover_url = image_urls[0]
      }
      if (typeof data.cover_url === 'string' && data.cover_url) album.cover_url = data.cover_url
      if (Array.isArray(data.tag_names)) album.tag_names = asStringArray(data.tag_names)
      if (typeof data.sync_to_forum === 'boolean') album.sync_to_forum = data.sync_to_forum
      return copy(album)
    },
  },
  {
    method: 'DELETE',
    pattern: '/api/v1/album/{id}',
    handle: (params) => {
      findAlbum(params.id)
      store.albums = store.albums.filter((item) => item.id !== params.id)
      return { ok: true }
    },
  },
]
