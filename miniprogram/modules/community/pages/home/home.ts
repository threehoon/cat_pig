import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { replaceCard, toPostCard, PostCardView } from '../../post-view'
import { favoritePost, likePost, listPosts } from '../../services/community'

type HomeEntryId = 'video' | 'album' | 'plaza' | 'checkin'

type HomeEntry = {
  id: HomeEntryId
  label: string
  icon: string
}

Page({
  data: {
    banner: brandAssets.homeBanner,
    entries: [
      { id: 'video', label: '图生视频', icon: brandAssets.entryVideo },
      { id: 'album', label: '相册', icon: brandAssets.entryAlbum },
      { id: 'plaza', label: '广场', icon: brandAssets.entryPlaza },
      { id: 'checkin', label: '签到', icon: brandAssets.entryCheckin },
    ] as HomeEntry[],
    posts: [] as PostCardView[],
  },
  onShow() {
    listPosts('recommend', undefined, 1, 3)
      .then((result) => {
        this.setData({ posts: result.items.map((post) => toPostCard(post)) })
      })
      .catch(toastRequestError)
  },
  onEntry(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as HomeEntryId
    if (id === 'video') {
      this.onVideo()
      return
    }
    if (id === 'album') {
      this.onAlbum()
      return
    }
    if (id === 'plaza') {
      this.onPlaza()
      return
    }
    if (id === 'checkin') {
      this.onCheckin()
    }
  },
  onVideo() {
    wx.switchTab({ url: '/modules/video/pages/create/create' })
  },
  onAlbum() {
    wx.switchTab({ url: '/modules/album/pages/list/list' })
  },
  onPlaza() {
    wx.switchTab({ url: '/modules/community/pages/plaza/plaza' })
  },
  onCheckin() {
    wx.navigateTo({ url: '/modules/points/pages/checkin/checkin' })
  },
  onMore() {
    wx.switchTab({ url: '/modules/community/pages/plaza/plaza' })
  },
  onPost(e: WechatMiniprogram.CustomEvent<{ id: string }>) {
    const id = e.detail.id
    if (!id) {
      return
    }
    wx.navigateTo({ url: `/modules/community/pages/detail/detail?id=${id}` })
  },
  onLike(e: WechatMiniprogram.CustomEvent<{ id: string }>) {
    const id = e.detail.id
    if (!id) {
      return
    }
    likePost(id)
      .then((post) => {
        this.setData({ posts: replaceCard(this.data.posts, post) })
      })
      .catch(toastRequestError)
  },
  onFavorite(e: WechatMiniprogram.CustomEvent<{ id: string }>) {
    const id = e.detail.id
    if (!id) {
      return
    }
    favoritePost(id)
      .then((post) => {
        this.setData({ posts: replaceCard(this.data.posts, post) })
      })
      .catch(toastRequestError)
  },
  onReply(e: WechatMiniprogram.CustomEvent<{ id: string }>) {
    const id = e.detail.id
    if (!id) {
      return
    }
    wx.navigateTo({ url: `/modules/community/pages/detail/detail?id=${id}&reply=1` })
  },
  onShareAppMessage(e: { target?: { dataset?: { id?: string } } }) {
    const id = (e.target && e.target.dataset && e.target.dataset.id) || ''
    const path = id
      ? `/modules/community/pages/detail/detail?id=${id}`
      : '/modules/community/pages/home/home'
    return {
      title: '宠物记录',
      path,
    }
  },
})
