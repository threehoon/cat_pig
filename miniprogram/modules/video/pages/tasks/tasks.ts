import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { listVideos } from '../../services/video'
import { VIDEO_STATUS_LABEL, Video } from '../../types/video'

type TaskRow = {
  id: string
  title: string
  status: string
  cover: string
}

Page({
  data: {
    tasks: [] as TaskRow[],
    total: 0,
    pending: 0,
    running: 0,
    done: 0,
    emptyTasks: brandAssets.emptyTasks,
  },
  onShow() {
    listVideos()
      .then((result) => {
        let pending = 0
        let running = 0
        let done = 0
        result.items.forEach((video: Video) => {
          if (video.status === 'pending') {
            pending += 1
          } else if (video.status === 'running') {
            running += 1
          } else if (video.status === 'success') {
            done += 1
          }
        })
        this.setData({
          total: result.total,
          pending,
          running,
          done,
          tasks: result.items.map((video) => ({
            id: video.id,
            title: video.title,
            status: VIDEO_STATUS_LABEL[video.status],
            cover: video.image_urls[0] || '',
          })),
        })
      })
      .catch(toastRequestError)
  },
  onCreate() {
    wx.switchTab({ url: '/modules/video/pages/create/create' })
  },
  onDetail(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as string
    wx.navigateTo({ url: `/modules/video/pages/detail/detail?id=${id}` })
  },
})
