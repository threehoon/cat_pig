import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { replaceCard, toPostCard, PostCardView } from '../../post-view'
import { favoritePost, likePost, listPosts } from '../../services/community'
import { PLAZA_TABS, Post, PostTab } from '../../types/post'

type WatchCard = {
  id: string
  cover: string
  body: string
}

function toWatchCards(items: Post[]): WatchCard[] {
  const cards: WatchCard[] = []
  let i = 0
  while (i < items.length && cards.length < 6) {
    const post = items[i]
    if (post.image_urls.length > 0) {
      cards.push({
        id: post.id,
        cover: post.image_urls[0],
        body: post.title || post.body,
      })
    }
    i += 1
  }
  return cards
}

Page({
  data: {
    tab: 'recommend' as PostTab,
    tabs: PLAZA_TABS,
    q: '',
    watching: [] as WatchCard[],
    posts: [] as PostCardView[],
    emptyPlaza: brandAssets.emptyPlaza,
    emptyTitle: '还没有动态',
    emptyHint: '发一条动态看看',
    emptyAction: '去发布',
  },
  onShow() {
    this.reload()
  },
  reload() {
    const tab = this.data.tab
    const q = this.data.q.trim()
    Promise.all([listPosts(tab, q || undefined, 1, 20), listPosts('recommend', undefined, 1, 10)])
      .then(([feed, rec]) => {
        const following = tab === 'following'
        this.setData({
          watching: q ? [] : toWatchCards(rec.items),
          posts: feed.items.map((post) => toPostCard(post)),
          emptyTitle: following ? '还没有关注的内容' : '还没有动态',
          emptyHint: following ? '去帖子详情关注作者，再回到这里' : '发一条动态看看',
          emptyAction: following ? '' : '去发布',
        })
      })
      .catch(toastRequestError)
  },
  onTab(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as PostTab
    this.setData({ tab: id }, () => {
      this.reload()
    })
  },
  onQuery(e: WechatMiniprogram.Input) {
    this.setData({ q: e.detail.value })
  },
  onSearch() {
    this.reload()
  },
  onCompose() {
    wx.navigateTo({ url: '/modules/community/pages/compose/compose' })
  },
  onWatch(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as string
    if (!id) {
      return
    }
    wx.navigateTo({ url: `/modules/community/pages/detail/detail?id=${id}` })
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
    return {
      title: '宠物记录',
      path: id
        ? `/modules/community/pages/detail/detail?id=${id}`
        : '/modules/community/pages/plaza/plaza',
    }
  },
})
