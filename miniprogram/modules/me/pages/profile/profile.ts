import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { uploadMedia } from '../../../media/services/media'
import { getMe, patchMe } from '../../services/me'

function trimText(value: string): string {
  return value.trim()
}

function displayAvatar(avatarUrl: string | null): string {
  if (avatarUrl) {
    return avatarUrl
  }
  return brandAssets.avatarDefault
}

Page({
  data: {
    draftAvatar: brandAssets.avatarDefault as string,
    draftNickname: '',
    savedAvatarUrl: null as string | null,
    savedNickname: null as string | null,
    busy: false,
  },
  onShow() {
    if (this.data.busy) {
      return
    }
    if (this.hasDraftChanges()) {
      return
    }
    this.loadMe()
  },
  loadMe() {
    getMe()
      .then((me) => {
        this.setData({
          savedAvatarUrl: me.avatar_url,
          savedNickname: me.nickname,
          draftAvatar: displayAvatar(me.avatar_url),
          draftNickname: me.nickname ? me.nickname : '',
        })
      })
      .catch(toastRequestError)
  },
  hasDraftChanges(): boolean {
    const nickname = trimText(this.data.draftNickname)
    const savedNickname = this.data.savedNickname ? this.data.savedNickname : ''
    if (nickname !== savedNickname) {
      return true
    }
    return this.data.draftAvatar !== displayAvatar(this.data.savedAvatarUrl)
  },
  onChooseAvatar(e: WechatMiniprogram.CustomEvent<{ avatarUrl: string }>) {
    const avatarUrl = e.detail.avatarUrl
    if (!avatarUrl) {
      wx.showToast({ title: '选择头像失败', icon: 'none' })
      return
    }
    this.setData({ draftAvatar: avatarUrl })
  },
  onNickname(e: WechatMiniprogram.Input) {
    this.setData({ draftNickname: e.detail.value })
  },
  onSave(e: WechatMiniprogram.FormSubmit) {
    if (this.data.busy) {
      return
    }
    const value = e.detail.value
    const fromForm = typeof value.nickname === 'string' ? value.nickname : this.data.draftNickname
    const nickname = trimText(fromForm)
    if (!nickname || nickname.length > 16) {
      wx.showToast({ title: '昵称须为 1–16 字', icon: 'none' })
      return
    }
    const savedAvatarUrl = this.data.savedAvatarUrl
    const draftAvatar = this.data.draftAvatar
    const avatarChanged = draftAvatar !== displayAvatar(savedAvatarUrl)
    this.setData({ busy: true })
    wx.showLoading({ title: '保存中', mask: true })
    const upload = avatarChanged
      ? uploadMedia(draftAvatar).then((media) => media.url)
      : Promise.resolve(savedAvatarUrl)
    upload
      .then((avatar_url) => patchMe({ nickname, avatar_url }).then(() => avatar_url))
      .then((avatar_url) => {
        wx.hideLoading()
        this.setData({
          savedNickname: nickname,
          savedAvatarUrl: avatar_url,
          draftNickname: nickname,
          draftAvatar: displayAvatar(avatar_url),
        })
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
  onBack() {
    if (!this.hasDraftChanges()) {
      wx.navigateBack()
      return
    }
    wx.showModal({
      title: '放弃本次修改？',
      content: '返回后本次修改不会保存',
      success: (res) => {
        if (!res.confirm) {
          return
        }
        wx.navigateBack()
      },
    })
  },
})
