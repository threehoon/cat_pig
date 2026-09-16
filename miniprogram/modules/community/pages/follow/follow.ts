import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { listFollows, unfollowUser } from '../../services/community'

type PersonView = {
  id: string
  nickname: string
  avatar: string
}

Page({
  data: {
    people: [] as PersonView[],
    emptyPlaza: brandAssets.emptyPlaza,
  },
  onShow() {
    this.reload()
  },
  reload() {
    listFollows()
      .then((result) => {
        this.setData({
          people: result.items.map((item) => ({
            id: item.id,
            nickname: item.nickname || '用户',
            avatar: item.avatar_url || brandAssets.avatarDefault,
          })),
        })
      })
      .catch(toastRequestError)
  },
  onUnfollow(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as string
    if (!id) {
      return
    }
    unfollowUser(id)
      .then(() => {
        this.reload()
      })
      .catch(toastRequestError)
  },
})
