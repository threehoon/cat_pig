import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { getMe } from '../../services/me'

Page({
  data: {
    avatar: brandAssets.avatarDefault as string,
    nickname: '用户',
    points_balance: 0,
  },
  onShow() {
    getMe()
      .then((me) => {
        this.setData({
          avatar: me.avatar_url || brandAssets.avatarDefault,
          nickname: me.nickname || '用户',
          points_balance: me.points_balance,
        })
      })
      .catch(toastRequestError)
  },
  onMine() {
    wx.navigateTo({ url: '/modules/community/pages/mine/mine' })
  },
  onPoints() {
    wx.navigateTo({ url: '/modules/points/pages/list/list' })
  },
  onTasks() {
    wx.navigateTo({ url: '/modules/video/pages/tasks/tasks' })
  },
})
