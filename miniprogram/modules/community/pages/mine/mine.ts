import { toastRequestError } from '../../../../core/request'
import { replaceCard, toPostCard, PostCardView } from '../../post-view'
import { listMyPosts, reactPost } from '../../services/community'
import { PostStatus, ReactKind } from '../../types/post'

const FILTERS: { id: 'all' | PostStatus; label: string }[] = [
  { id: 'all', label: '全部' },
  { id: 'published', label: '已发布' },
  { id: 'pending', label: '审核中' },
  { id: 'rejected', label: '未通过' },
  { id: 'draft', label: '草稿' },
]

Page({
  data: {
    filter: 'all' as 'all' | PostStatus,
    filters: FILTERS,
    posts: [] as PostCardView[],
    published: 0,
    pending: 0,
    draft: 0,
    likes: 0,
  },
  onShow() {
    this.reload()
  },
  reload() {
    const filter = this.data.filter === 'all' ? undefined : this.data.filter
    Promise.all([listMyPosts(undefined, 1, 20), listMyPosts(filter, 1, 20)])
      .then(([all, filtered]) => {
        let published = 0
        let pending = 0
        let draft = 0
        let likes = 0
        all.items.forEach((post) => {
          if (post.status === 'published') {
            published += 1
            likes += post.react_heart + post.react_bone + post.react_star
          } else if (post.status === 'pending') {
            pending += 1
          } else if (post.status === 'draft') {
            draft += 1
          }
        })
        this.setData({
          published,
          pending,
          draft,
          likes,
          posts: filtered.items.map((post) => toPostCard(post, 'status')),
        })
      })
      .catch(toastRequestError)
  },
  onFilter(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as 'all' | PostStatus
    this.setData({ filter: id }, () => {
      this.reload()
    })
  },
  onCompose() {
    wx.navigateTo({ url: '/modules/community/pages/compose/compose' })
  },
  onPost(e: WechatMiniprogram.CustomEvent<{ id: string }>) {
    const id = e.detail.id
    if (!id) {
      return
    }
    wx.navigateTo({ url: `/modules/community/pages/detail/detail?id=${id}` })
  },
  onReact(e: WechatMiniprogram.CustomEvent<{ id: string; kind: ReactKind }>) {
    const { id, kind } = e.detail
    if (!id || !kind) {
      return
    }
    reactPost(id, kind)
      .then((post) => {
        this.setData({ posts: replaceCard(this.data.posts, post, 'status') })
      })
      .catch(toastRequestError)
  },
})
