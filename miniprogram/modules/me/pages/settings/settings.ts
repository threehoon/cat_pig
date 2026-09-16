Page({
  onLogout() {
    wx.showModal({
      title: '注销账号',
      content: '注销后无法恢复',
      success(res) {
        if (!res.confirm) {
          return
        }
        setTimeout(() => {
          wx.showToast({ title: '开发期不能注销', icon: 'none' })
        }, 300)
      },
    })
  },
})
