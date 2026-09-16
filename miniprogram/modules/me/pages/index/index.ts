import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { getMe } from '../../services/me'

Page({
  data: {
    avatar: brandAssets.avatarDefault as string,
    nickname: '用户',
    points_balance: 0,
    post_count: 0,
    like_received_count: 0,
    following_count: 0,
    follower_count: 0,
  },
  onShow() {
    getMe()
      .then((me) => {
        this.setData({
          avatar: me.avatar_url || brandAssets.avatarDefault,
          nickname: me.nickname || '用户',
          points_balance: me.points_balance,
          post_count: me.post_count,
          like_received_count: me.like_received_count,
          following_count: me.following_count,
          follower_count: me.follower_count,
        })
      })
      .catch(toastRequestError)
  },
  onProfile() {
    wx.navigateTo({ url: '/modules/me/pages/profile/profile' })
  },
  onStat(e: WechatMiniprogram.TouchEvent) {
    const kind = e.currentTarget.dataset.kind as string
    if (kind === 'posts' || kind === 'likes') {
      wx.navigateTo({ url: '/modules/community/pages/mine/mine' })
      return
    }
    if (kind === 'following') {
      wx.navigateTo({ url: '/modules/community/pages/follow/follow' })
      return
    }
    if (kind === 'followers') {
      wx.navigateTo({ url: '/modules/community/pages/follower/follower' })
    }
  },
  onMine() {
    wx.navigateTo({ url: '/modules/community/pages/mine/mine' })
  },
  onFavorites() {
    wx.navigateTo({ url: '/modules/community/pages/favorites/favorites' })
  },
  onAlbum() {
    wx.switchTab({ url: '/modules/album/pages/list/list' })
  },
  onFollow() {
    wx.navigateTo({ url: '/modules/community/pages/follow/follow' })
  },
  onFollowers() {
    wx.navigateTo({ url: '/modules/community/pages/follower/follower' })
  },
  onPoints() {
    wx.navigateTo({ url: '/modules/points/pages/list/list' })
  },
  onPointTasks() {
    wx.navigateTo({ url: '/modules/points/pages/tasks/tasks' })
  },
  onRecords() {
    wx.navigateTo({ url: '/modules/video/pages/tasks/tasks' })
  },
  onSettings() {
    wx.navigateTo({ url: '/modules/me/pages/settings/settings' })
  },
})
