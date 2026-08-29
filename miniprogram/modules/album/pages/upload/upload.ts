import { toastRequestError } from '../../../../core/request'
import { chooseLocalImages } from '../../../media/choose'
import { uploadImages } from '../../../media/services/media'
import { createAlbum, deleteAlbum, getAlbum, patchAlbum } from '../../services/album'
import { ALBUM_TAG_PRESETS } from '../../types/album'

Page({
  data: {
    id: '',
    title: '',
    body: '',
    image_urls: [] as string[],
    tag_names: [] as string[],
    tag_items: ALBUM_TAG_PRESETS.map((name) => ({ name, on: false })),
    sync_to_forum: false,
    busy: false,
  },
  onLoad(query: { id?: string }) {
    const id = query.id || ''
    if (!id) {
      return
    }
    this.setData({ id })
    getAlbum(id)
      .then((album) => {
        this.setData({
          title: album.title,
          body: album.body,
          image_urls: album.image_urls,
          tag_names: album.tag_names,
          tag_items: ALBUM_TAG_PRESETS.map((name) => ({
            name,
            on: album.tag_names.indexOf(name) !== -1,
          })),
          sync_to_forum: album.sync_to_forum,
        })
      })
      .catch(toastRequestError)
  },
  onTitle(e: WechatMiniprogram.Input) {
    this.setData({ title: e.detail.value })
  },
  onBody(e: WechatMiniprogram.Input) {
    this.setData({ body: e.detail.value })
  },
  onTag(e: WechatMiniprogram.TouchEvent) {
    const name = e.currentTarget.dataset.name as string
    const tag_names = this.data.tag_names.slice()
    const index = tag_names.indexOf(name)
    if (index === -1) {
      tag_names.push(name)
    } else {
      tag_names.splice(index, 1)
    }
    this.setData({
      tag_names,
      tag_items: ALBUM_TAG_PRESETS.map((item) => ({
        name: item,
        on: tag_names.indexOf(item) !== -1,
      })),
    })
  },
  onSync(e: WechatMiniprogram.SwitchChange) {
    this.setData({ sync_to_forum: e.detail.value })
  },
  onAddImage() {
    const remain = 9 - this.data.image_urls.length
    chooseLocalImages(remain)
      .then((paths) => uploadImages(paths))
      .then((urls) => {
        if (urls.length === 0) {
          return
        }
        this.setData({ image_urls: this.data.image_urls.concat(urls) })
      })
      .catch(toastRequestError)
  },
  onRemoveImage(e: WechatMiniprogram.TouchEvent) {
    const index = Number(e.currentTarget.dataset.index)
    const image_urls = this.data.image_urls.slice()
    image_urls.splice(index, 1)
    this.setData({ image_urls })
  },
  onSubmit() {
    if (this.data.busy) {
      return
    }
    this.setData({ busy: true })
    wx.showLoading({ title: '保存中', mask: true })
    const payload = {
      title: this.data.title,
      body: this.data.body,
      image_urls: this.data.image_urls,
      tag_names: this.data.tag_names,
      sync_to_forum: this.data.sync_to_forum,
    }
    const job = this.data.id ? patchAlbum(this.data.id, payload) : createAlbum(payload)
    job
      .then(() => {
        wx.hideLoading()
        wx.showToast({ title: '已保存', icon: 'none' })
        setTimeout(() => {
          wx.navigateBack()
        }, 400)
      })
      .catch((err) => {
        wx.hideLoading()
        toastRequestError(err)
      })
      .then(() => {
        this.setData({ busy: false })
      })
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
