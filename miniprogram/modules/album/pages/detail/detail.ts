import { toastRequestError, type RequestError } from '../../../../core/request'
import { deleteAlbum, getAlbum } from '../../services/album'
import { ALBUM_VISIBILITY_LABEL } from '../../visibility'

type Thumb = {
  id: string
  url: string
  isCover: boolean
}

function formatAlbumDate(iso: string): string {
  const date = new Date(iso)
  if (isNaN(date.getTime())) {
    return ''
  }
  const now = new Date()
  const month = date.getMonth() + 1
  const day = date.getDate()
  if (date.getFullYear() === now.getFullYear()) {
    return month + '月' + day + '日'
  }
  return date.getFullYear() + '年' + month + '月' + day + '日'
}

function toThumbs(image_urls: string[], cover_url: string): Thumb[] {
  return image_urls.map((url, i) => ({
    id: String(i),
    url,
    isCover: url === cover_url,
  }))
}

Page({
  data: {
    id: '',
    pageTitle: '相册',
    ready: false,
    cover_url: '',
    image_urls: [] as string[],
    thumbs: [] as Thumb[],
    title: '',
    body: '',
    tag_names: [] as string[],
    visibility_label: '',
    time: '',
  },
  onLoad(query: { id?: string }) {
    this.setData({ id: query.id || '' })
  },
  onShow() {
    this.reload()
  },
  reload() {
    const id = this.data.id
    if (!id) {
      wx.showToast({ title: '相册不存在', icon: 'none' })
      return
    }
    getAlbum(id)
      .then((album) => {
        this.setData({
          pageTitle: album.title,
          ready: true,
          cover_url: album.cover_url,
          image_urls: album.image_urls,
          thumbs: toThumbs(album.image_urls, album.cover_url),
          title: album.title,
          body: album.body,
          tag_names: album.tag_names,
          visibility_label: ALBUM_VISIBILITY_LABEL[album.visibility],
          time: formatAlbumDate(album.created_at),
        })
      })
      .catch((err) => {
        const error = err as RequestError
        if (error.code === 'NOT_FOUND') {
          wx.navigateBack()
          return
        }
        toastRequestError(err)
      })
  },
  onPreview(e: WechatMiniprogram.TouchEvent) {
    const urls = this.data.image_urls
    if (urls.length === 0) {
      return
    }
    const current = e.currentTarget.dataset.url as string
    wx.previewImage({
      urls,
      current: current ? current : urls[0],
    })
  },
  onEdit() {
    const id = this.data.id
    if (!id) {
      return
    }
    wx.navigateTo({ url: `/modules/album/pages/upload/upload?id=${id}` })
  },
  onDelete() {
    const id = this.data.id
    if (!id) {
      return
    }
    wx.showModal({
      title: '删除相册',
      content: '删除后无法恢复',
      success: (res) => {
        if (!res.confirm) {
          return
        }
        deleteAlbum(id)
          .then(() => {
            wx.navigateBack()
          })
          .catch(toastRequestError)
      },
    })
  },
})
