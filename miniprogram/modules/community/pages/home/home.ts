import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { replaceCard, toPostCard, PostCardView } from '../../post-view'
import { favoritePost, likePost, listPosts } from '../../services/community'

Page({
  data: {
    banner: brandAssets.homeBanner,
    entryVideo: brandAssets.entryVideo,
    entryAlbum: brandAssets.entryAlbum,
    entryPlaza: brandAssets.entryPlaza,
    entryCheckin: brandAssets.entryCheckin,
    posts: [] as PostCardView[],
  },
  onShow() {
    listPosts('recommend', undefined, 1, 3)
      .then((result) => {
        this.setData({ posts: result.items.map((post) => toPostCard(post)) })
      })
      .catch(toastRequestError)
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
    wx.navigateTo({ url: '/modules/points/pages/list/list?checkin=1' })
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
  onShareAppMessage(e: WechatMiniprogram.Page.IShareAppMessageOption) {
    const id = (e.target && e.target.dataset && (e.target.dataset.id as string)) || ''
    const path = id
      ? `/modules/community/pages/detail/detail?id=${id}`
      : '/modules/community/pages/home/home'
    return {
      title: '宠物记录',
      path,
    }
  },
})
