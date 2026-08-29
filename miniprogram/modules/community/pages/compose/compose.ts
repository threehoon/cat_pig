import { toastRequestError } from '../../../../core/request'
import { chooseLocalImages } from '../../../media/choose'
import { uploadImages } from '../../../media/services/media'
import { createPost, getPost, patchPost } from '../../services/community'
import { Board, BOARDS, TOPIC_PRESETS } from '../../types/post'

Page({
  data: {
    id: '',
    board: 'qa' as Board,
    boards: BOARDS,
    title: '',
    body: '',
    image_urls: [] as string[],
    topic_names: [] as string[],
    topic_items: TOPIC_PRESETS.map((name) => ({ name, on: false as boolean })),
    busy: false,
  },
  onLoad(query: { id?: string }) {
    const id = query.id || ''
    if (!id) {
      return
    }
    this.setData({ id })
    getPost(id)
      .then((post) => {
        this.setData({
          board: post.board,
          title: post.title,
          body: post.body,
          image_urls: post.image_urls,
          topic_names: post.topic_names,
          topic_items: TOPIC_PRESETS.map((name) => ({
            name,
            on: post.topic_names.indexOf(name) !== -1,
          })),
        })
      })
      .catch(toastRequestError)
  },
  onBoard(e: WechatMiniprogram.TouchEvent) {
    this.setData({ board: e.currentTarget.dataset.id as Board })
  },
  onTitle(e: WechatMiniprogram.Input) {
    this.setData({ title: e.detail.value })
  },
  onBody(e: WechatMiniprogram.Input) {
    this.setData({ body: e.detail.value })
  },
  onTopic(e: WechatMiniprogram.TouchEvent) {
    const name = e.currentTarget.dataset.name as string
    const topic_names = this.data.topic_names.slice()
    const index = topic_names.indexOf(name)
    if (index === -1) {
      topic_names.push(name)
    } else {
      topic_names.splice(index, 1)
    }
    this.setData({
      topic_names,
      topic_items: TOPIC_PRESETS.map((item) => ({
        name: item,
        on: topic_names.indexOf(item) !== -1,
      })),
    })
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
  onDraft() {
    this.submit('draft')
  },
  onPublish() {
    this.submit('pending')
  },
  submit(status: 'draft' | 'pending') {
    if (this.data.busy) {
      return
    }
    this.setData({ busy: true })
    wx.showLoading({ title: status === 'draft' ? '保存中' : '发布中', mask: true })
    const payload = {
      board: this.data.board,
      title: this.data.title,
      body: this.data.body,
      image_urls: this.data.image_urls,
      topic_names: this.data.topic_names,
      status,
    }
    const job = this.data.id ? patchPost(this.data.id, payload) : createPost(payload)
    job
      .then(() => {
        wx.hideLoading()
        wx.showToast({ title: status === 'draft' ? '已存草稿' : '已发布', icon: 'none' })
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
})
