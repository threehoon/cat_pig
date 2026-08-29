import { ListResult, request } from '../../../core/request'
import { Video, VideoStatus, VideoWrite } from '../types/video'

export function listVideos(status?: VideoStatus, page = 1, pageSize = 20) {
  return request<ListResult<Video>>({
    method: 'GET',
    path: '/api/v1/video',
    query: { status, page, page_size: pageSize },
  })
}

export function createVideo(body: VideoWrite) {
  return request<Video>({
    method: 'POST',
    path: '/api/v1/video',
    data: body,
  })
}

export function getVideo(id: string) {
  return request<Video>({
    method: 'GET',
    path: `/api/v1/video/${id}`,
  })
}

export function deleteVideo(id: string) {
  return request<{ ok: true }>({
    method: 'DELETE',
    path: `/api/v1/video/${id}`,
  })
}
