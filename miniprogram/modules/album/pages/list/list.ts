import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { listAlbums } from '../../services/album'
import { Album } from '../../types/album'

Page({
  data: {
    emptyAlbum: brandAssets.emptyAlbum,
    albums: [] as Album[],
  },
  onShow() {
    listAlbums()
      .then((result) => {
        this.setData({ albums: result.items })
      })
      .catch(toastRequestError)
  },
  onUpload() {
    wx.navigateTo({ url: '/modules/album/pages/upload/upload' })
  },
  onOpen(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as string
    wx.navigateTo({ url: `/modules/album/pages/upload/upload?id=${id}` })
  },
})
