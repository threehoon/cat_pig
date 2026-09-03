import {
  asStringArray,
  bodyOf,
  copy,
  fail,
  newId,
  nowIso,
  paginate,
  queryValue,
  sortByCreated,
  todayDate,
  type MockRoute,
} from '../../../core/mock-runtime'
import { store, type MockVideo } from '../../../mocks/store'
import { addLedger } from '../../points/services/mock-ledger'
import { VIDEO_RESOLUTIONS } from '../types/video'

function findVideo(id: string): MockVideo {
  const video = store.videos.find((item) => item.id === id)
  if (!video) fail('NOT_FOUND', '任务不存在')
  return video
}

export const videoMockRoutes: MockRoute[] = [
  {
    method: 'GET',
    pattern: '/api/v1/video',
    handle: (_params, options) => {
      const status = queryValue(options.query, 'status')
      return paginate(
        sortByCreated(store.videos.filter((video) => !status || video.status === status)).map(copy),
        options.query,
      )
    },
  },
  {
    method: 'POST',
    pattern: '/api/v1/video',
    handle: (_params, options) => {
      const data = bodyOf(options)
      const image_urls = asStringArray(data.image_urls)
      const prompt = typeof data.prompt === 'string' ? data.prompt : ''
      const resolution = String(data.resolution || '')
      if (image_urls.length < 2 || image_urls.length > 9) fail('VALIDATION', '请选择 2–9 张照片')
      if (prompt.length > 100) fail('VALIDATION', '提示词最多 100 字')
      if ((VIDEO_RESOLUTIONS as readonly string[]).indexOf(resolution) === -1) fail('VALIDATION', '分辨率不正确')
      addLedger('spend', 50, '图生视频')
      const video: MockVideo = {
        id: newId(),
        title: String(data.title || '').trim() || todayDate(),
        image_urls,
        prompt,
        resolution: resolution as MockVideo['resolution'],
        status: 'pending',
        result_url: null,
        points_cost: 50,
        error_message: null,
        created_at: nowIso(),
      }
      store.videos.unshift(video)
      return copy(video)
    },
  },
  { method: 'GET', pattern: '/api/v1/video/{id}', handle: (params) => copy(findVideo(params.id)) },
  {
    method: 'DELETE',
    pattern: '/api/v1/video/{id}',
    handle: (params) => {
      const video = findVideo(params.id)
      if (video.status === 'running') fail('CONFLICT', '生成中不能删除')
      store.videos = store.videos.filter((item) => item.id !== params.id)
      return { ok: true }
    },
  },
]
