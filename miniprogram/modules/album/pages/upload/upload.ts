import { toastRequestError } from '../../../../core/request'
import { chooseLocalImages } from '../../../media/choose'
import { uploadImages } from '../../../media/services/media'
import { createAlbum, deleteAlbum, getAlbum, patchAlbum } from '../../services/album'
import { ALBUM_TAG_PRESETS, AlbumVisibility } from '../../types/album'
import { ALBUM_VISIBILITY_LABEL, ALBUM_VISIBILITY_OPTIONS } from '../../visibility'

type TagItem = {
  name: string
  on: boolean
}

type VisibilityItem = {
  id: AlbumVisibility
  label: string
  on: boolean
}

function buildTagItems(tag_names: string[]): TagItem[] {
  const items: TagItem[] = ALBUM_TAG_PRESETS.map((name) => ({
    name,
    on: tag_names.indexOf(name) !== -1,
  }))
  for (let i = 0; i < tag_names.length; i += 1) {
    const name = tag_names[i]
    if (ALBUM_TAG_PRESETS.indexOf(name) === -1) {
      items.push({ name, on: true })
    }
  }
  return items
}

function buildVisibilityItems(current: AlbumVisibility): VisibilityItem[] {
  return ALBUM_VISIBILITY_OPTIONS.map((id) => ({
    id,
    label: ALBUM_VISIBILITY_LABEL[id],
    on: id === current,
  }))
}

function oneTag(tag_names: string[]): string[] {
  if (tag_names.length === 0) {
    return []
  }
  return [tag_names[0]]
}

function resolveCover(image_urls: string[], cover_url: string): string {
  if (cover_url && image_urls.indexOf(cover_url) !== -1) {
    return cover_url
  }
  if (image_urls.length > 0) {
    return image_urls[0]
  }
  return ''
}

Page({
  data: {
    id: '',
    pageTitle: '上传到相册',
    title: '',
    body: '',
    image_urls: [] as string[],
    cover_url: '',
    tag_names: [] as string[],
    tag_items: buildTagItems([]),
    visibility: 'private' as AlbumVisibility,
    visibility_items: buildVisibilityItems('private'),
    sync_to_forum: false,
    syncDisabled: true,
    busy: false,
  },
  onLoad(query: { id?: string }) {
    const id = query.id || ''
    if (!id) {
      return
    }
    this.setData({ id, pageTitle: '编辑相册' })
    getAlbum(id)
      .then((album) => {
        const tag_names = oneTag(album.tag_names)
        const visibility = album.visibility
        const syncDisabled = visibility !== 'public'
        this.setData({
          title: album.title,
          body: album.body,
          image_urls: album.image_urls,
          cover_url: resolveCover(album.image_urls, album.cover_url),
          tag_names,
          tag_items: buildTagItems(tag_names),
          visibility,
          visibility_items: buildVisibilityItems(visibility),
          sync_to_forum: syncDisabled ? false : album.sync_to_forum,
          syncDisabled,
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
    const current = this.data.tag_names
    const tag_names = current.length === 1 && current[0] === name ? [] : [name]
    this.setData({ tag_names, tag_items: buildTagItems(tag_names) })
  },
  onCustomTag() {
    wx.showModal({
      title: '自定义标签',
      editable: true,
      placeholderText: '输入标签',
      success: (res) => {
        if (!res.confirm) {
          return
        }
        const raw = res.content
        const name = raw ? raw.trim() : ''
        if (!name) {
          return
        }
        const tag_names = [name]
        this.setData({ tag_names, tag_items: buildTagItems(tag_names) })
      },
    })
  },
  onVisibility(e: WechatMiniprogram.TouchEvent) {
    const visibility = e.currentTarget.dataset.id as AlbumVisibility
    const syncDisabled = visibility !== 'public'
    this.setData({
      visibility,
      visibility_items: buildVisibilityItems(visibility),
      syncDisabled,
      sync_to_forum: syncDisabled ? false : this.data.sync_to_forum,
    })
  },
  onSync(e: WechatMiniprogram.SwitchChange) {
    if (this.data.syncDisabled) {
      this.setData({ sync_to_forum: false })
      return
    }
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
        const image_urls = this.data.image_urls.concat(urls)
        this.setData({
          image_urls,
          cover_url: resolveCover(image_urls, this.data.cover_url),
        })
      })
      .catch(toastRequestError)
  },
  onPreviewImage(e: WechatMiniprogram.TouchEvent) {
    const index = Number(e.currentTarget.dataset.index)
    const urls = this.data.image_urls
    const current = urls[index]
    if (!current) {
      return
    }
    wx.previewImage({ urls, current })
  },
  onSetCover(e: WechatMiniprogram.TouchEvent) {
    const index = Number(e.currentTarget.dataset.index)
    const url = this.data.image_urls[index]
    if (!url || url === this.data.cover_url) {
      return
    }
    this.setData({ cover_url: url })
  },
  onRemoveImage(e: WechatMiniprogram.TouchEvent) {
    const index = Number(e.currentTarget.dataset.index)
    const image_urls = this.data.image_urls.slice()
    if (index < 0 || index >= image_urls.length) {
      return
    }
    image_urls.splice(index, 1)
    this.setData({
      image_urls,
      cover_url: resolveCover(image_urls, this.data.cover_url),
    })
  },
  onSubmit() {
    if (this.data.busy) {
      return
    }
    this.setData({ busy: true })
    wx.showLoading({ title: '保存中', mask: true })
    const visibility = this.data.visibility
    const payload = {
      title: this.data.title,
      body: this.data.body,
      image_urls: this.data.image_urls,
      cover_url: this.data.cover_url,
      tag_names: this.data.tag_names,
      visibility,
      sync_to_forum: visibility === 'public' ? this.data.sync_to_forum : false,
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
