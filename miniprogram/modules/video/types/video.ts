export type VideoStatus = 'pending' | 'running' | 'success' | 'failed'

export type VideoResolution = '540p' | '720p' | '1080p' | '2k' | '4k'

export type Video = {
  id: string
  title: string
  image_urls: string[]
  prompt: string
  resolution: VideoResolution
  status: VideoStatus
  result_url: string | null
  points_cost: number
  error_message: string | null
  created_at: string
}

export type VideoWrite = {
  title: string
  image_urls: string[]
  prompt: string
  resolution: VideoResolution
}

export const VIDEO_STATUS_LABEL: Record<VideoStatus, string> = {
  pending: '待执行',
  running: '执行中',
  success: '执行成功',
  failed: '执行失败',
}

export const VIDEO_RESOLUTIONS: VideoResolution[] = ['540p', '720p', '1080p', '2k', '4k']
