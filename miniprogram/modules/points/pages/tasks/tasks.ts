import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { getPointsSummary } from '../../services/points'

type TaskView = {
  key: string
  title: string
  reward: string
  progress: number
  limit: number
  done: boolean
  icon: string
}

Page({
  data: {
    mascots: brandAssets.mascots,
    tasks: [] as TaskView[],
  },
  onShow() {
    this.reload()
  },
  reload() {
    return getPointsSummary()
      .then((summary) => {
        const tasks: TaskView[] = [
          {
            key: 'post',
            title: '发布动态',
            reward: '+20',
            progress: summary.today_post_count,
            limit: 3,
            done: summary.today_post_count >= 3,
            icon: brandAssets.entryPlaza,
          },
          {
            key: 'comment',
            title: '发表评论',
            reward: '+5',
            progress: summary.today_comment_count,
            limit: 1,
            done: summary.today_comment_count >= 1,
            icon: brandAssets.composeEmoji,
          },
          {
            key: 'like',
            title: '点赞帖子',
            reward: '+2',
            progress: summary.today_like_count,
            limit: 3,
            done: summary.today_like_count >= 3,
            icon: brandAssets.reactLike,
          },
        ]
        this.setData({ tasks })
      })
      .catch(toastRequestError)
  },
  onTask(e: WechatMiniprogram.TouchEvent) {
    const key = e.currentTarget.dataset.key as string
    if (!key) return
    const tasks = this.data.tasks
    let done = false
    let i = 0
    while (i < tasks.length) {
      if (tasks[i].key === key) {
        done = tasks[i].done
        break
      }
      i += 1
    }
    if (done) return
    if (key === 'post') {
      wx.navigateTo({ url: '/modules/community/pages/compose/compose' })
      return
    }
    wx.switchTab({ url: '/modules/community/pages/plaza/plaza' })
  },
})
