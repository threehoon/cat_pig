import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { replaceCard, toPostCard, PostCardView } from '../../post-view'
import { favoritePost, likePost, listFavoritePosts } from '../../services/community'

Page({
  data: {
    posts: [] as PostCardView[],
    emptyPlaza: brandAssets.emptyPlaza,
  },
  onShow() {
    this.reload()
  },
  reload() {
    listFavoritePosts()
      .then((result) => {
        this.setData({ posts: result.items.map((post) => toPostCard(post)) })
      })
      .catch(toastRequestError)
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
        if (!post.favorited) {
          this.setData({
            posts: this.data.posts.filter((card) => card.id !== post.id),
          })
          return
        }
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
        : '/modules/community/pages/favorites/favorites',
    }
  },
})
