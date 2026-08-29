import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { chooseLocalImages } from '../../../media/choose'
import { uploadImages } from '../../../media/services/media'
import { createVideo } from '../../services/video'
import { VIDEO_RESOLUTIONS, VideoResolution } from '../../types/video'

Page({
  data: {
    prompt: '',
    resolution: '1080p' as VideoResolution,
    prompts: ['出门散步', '吃饭瞬间', '生日记录', '睡午觉'],
    resolutions: VIDEO_RESOLUTIONS,
    emptyTasks: brandAssets.emptyTasks,
    image_urls: [] as string[],
    busy: false,
  },
  onPrompt(e: WechatMiniprogram.Input) {
    this.setData({ prompt: e.detail.value })
  },
  onPromptChip(e: WechatMiniprogram.TouchEvent) {
    const text = e.currentTarget.dataset.text as string
    this.setData({ prompt: text })
  },
  onResolution(e: WechatMiniprogram.TouchEvent) {
    const text = e.currentTarget.dataset.text as VideoResolution
    this.setData({ resolution: text })
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
  onGenerate() {
    if (this.data.busy) {
      return
    }
    this.setData({ busy: true })
    wx.showLoading({ title: '提交中', mask: true })
    createVideo({
      title: '',
      image_urls: this.data.image_urls,
      prompt: this.data.prompt,
      resolution: this.data.resolution,
    })
      .then(() => {
        wx.hideLoading()
        this.setData({ image_urls: [], prompt: '' })
        wx.navigateTo({ url: '/modules/video/pages/tasks/tasks' })
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
