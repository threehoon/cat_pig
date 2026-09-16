import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { followUser, listFollowers, listFollows, unfollowUser } from '../../services/community'

type PersonView = {
  id: string
  nickname: string
  avatar: string
  action: string
  following: boolean
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
    Promise.all([listFollowers(), listFollows()])
      .then(([fans, follows]) => {
        const followingIds = follows.items.map((item) => item.id)
        this.setData({
          people: fans.items.map((item) => {
            let following = false
            for (let i = 0; i < followingIds.length; i += 1) {
              if (followingIds[i] === item.id) {
                following = true
                break
              }
            }
            return {
              id: item.id,
              nickname: item.nickname || '用户',
              avatar: item.avatar_url || brandAssets.avatarDefault,
              action: following ? '取消关注' : '回关',
              following,
            }
          }),
        })
      })
      .catch(toastRequestError)
  },
  onAction(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as string
    const action = e.currentTarget.dataset.action as string
    if (!id) {
      return
    }
    const run = action === 'unfollow' ? unfollowUser(id) : followUser(id)
    run
      .then(() => {
        this.reload()
      })
      .catch(toastRequestError)
  },
})
