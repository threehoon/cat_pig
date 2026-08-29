import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { formatCreatedAt } from '../../../../utils/util'
import { getUserId } from '../../../../core/auth'
import { deletePost, followUser, getPost, reactPost, unfollowUser } from '../../services/community'
import { BOARD_LABEL, Post, ReactKind } from '../../types/post'

Page({
  data: {
    id: '',
    post: null as Post | null,
    avatar: brandAssets.avatarDefault as string,
    nickname: '用户',
    time: '',
    boardLabel: '',
    isOwn: false,
    followLabel: '关注',
  },
  onLoad(query: { id?: string }) {
    const id = query.id || ''
    this.setData({ id })
    if (!id) {
      wx.showToast({ title: '帖子不存在', icon: 'none' })
    }
  },
  onShow() {
    this.reload()
  },
  reload() {
    const id = this.data.id
    if (!id) {
      return
    }
    getPost(id)
      .then((post) => {
        this.setData({
          post,
          avatar: post.author.avatar_url || brandAssets.avatarDefault,
          nickname: post.author.nickname || '用户',
          time: formatCreatedAt(post.created_at),
          boardLabel: BOARD_LABEL[post.board],
          isOwn: post.author.id === getUserId(),
          followLabel: post.followed ? '已关注' : '关注',
        })
      })
      .catch(toastRequestError)
  },
  onFollow() {
    const post = this.data.post
    if (!post || this.data.isOwn) {
      return
    }
    const job = post.followed ? unfollowUser(post.author.id) : followUser(post.author.id)
    job
      .then(() => this.reload())
      .catch(toastRequestError)
  },
  onReact(e: WechatMiniprogram.CustomEvent<{ kind: ReactKind }>) {
    const id = this.data.id
    const kind = e.detail.kind
    if (!id || !kind) {
      return
    }
    reactPost(id, kind)
      .then((post) => {
        this.setData({
          post,
          followLabel: post.followed ? '已关注' : '关注',
        })
      })
      .catch(toastRequestError)
  },
  onEdit() {
    const id = this.data.id
    if (!id) {
      return
    }
    wx.navigateTo({ url: `/modules/community/pages/compose/compose?id=${id}` })
  },
  onDelete() {
    const id = this.data.id
    if (!id) {
      return
    }
    wx.showModal({
      title: '删除帖子',
      content: '删除后无法恢复',
      success: (res) => {
        if (!res.confirm) {
          return
        }
        deletePost(id)
          .then(() => {
            wx.navigateBack()
          })
          .catch(toastRequestError)
      },
    })
  },
})
