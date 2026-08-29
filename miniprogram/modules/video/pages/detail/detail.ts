import { toastRequestError } from '../../../../core/request'
import { deleteVideo, getVideo } from '../../services/video'
import { VIDEO_STATUS_LABEL, Video } from '../../types/video'

Page({
  data: {
    id: '',
    video: null as Video | null,
    statusLabel: '',
    cover: '',
    canDelete: false,
  },
  onLoad(query: { id?: string }) {
    const id = query.id || ''
    this.setData({ id })
    if (!id) {
      wx.showToast({ title: '任务不存在', icon: 'none' })
      return
    }
    getVideo(id)
      .then((video) => {
        this.setData({
          video,
          statusLabel: VIDEO_STATUS_LABEL[video.status],
          cover: video.image_urls[0] || '',
          canDelete: video.status !== 'running',
        })
      })
      .catch(toastRequestError)
  },
  onDelete() {
    const id = this.data.id
    if (!id) {
      return
    }
    wx.showModal({
      title: '删除任务',
      content: '删除后无法恢复',
      success: (res) => {
        if (!res.confirm) {
          return
        }
        deleteVideo(id)
          .then(() => {
            wx.navigateBack()
          })
          .catch(toastRequestError)
      },
    })
  },
})
