import { brandAssets } from '../../../../assets/paths'
import { getUserId } from '../../../../core/auth'
import { toastRequestError } from '../../../../core/request'
import { formatCreatedAt } from '../../../../utils/util'
import {
  createComment,
  deleteComment,
  deletePost,
  favoritePost,
  followUser,
  getPost,
  likePost,
  listComments,
  unfollowUser,
} from '../../services/community'
import { BOARD_LABEL, Comment, Post } from '../../types/post'

type CommentView = {
  id: string
  nickname: string
  avatar: string
  body: string
  time: string
  replyToName: string
  canDelete: boolean
  replies: CommentView[]
}

function toCommentView(item: Comment, canDelete: boolean): CommentView {
  return {
    id: item.id,
    nickname: item.author.nickname || '用户',
    avatar: item.author.avatar_url || brandAssets.avatarDefault,
    body: item.body,
    time: formatCreatedAt(item.created_at),
    replyToName: (item.reply_to && item.reply_to.nickname) || '',
    canDelete,
    replies: [],
  }
}

function canDeleteComment(item: Comment, currentUserId: string | null, postAuthorId: string): boolean {
  if (!currentUserId) {
    return false
  }
  return item.author.id === currentUserId || postAuthorId === currentUserId
}

function groupComments(items: Comment[], currentUserId: string | null, postAuthorId: string): CommentView[] {
  const views = items.map((item) => toCommentView(item, canDeleteComment(item, currentUserId, postAuthorId)))
  const byId: Record<string, CommentView> = {}
  views.forEach((view) => {
    byId[view.id] = view
  })
  const roots: CommentView[] = []
  items.forEach((item, index) => {
    const view = views[index]
    if (item.parent_id && byId[item.parent_id]) {
      byId[item.parent_id].replies.push(view)
    } else {
      roots.push(view)
    }
  })
  return roots
}

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
    comments: [] as CommentView[],
    commentBody: '',
    commentFocus: false,
    commentPlaceholder: '写一条评论',
    replyParentId: '',
    replyToName: '',
    scrollInto: '',
  },
  onLoad(query: { id?: string; reply?: string }) {
    const id = query.id || ''
    this.setData({
      id,
      commentFocus: query.reply === '1',
      scrollInto: query.reply === '1' ? 'comments' : '',
    })
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
    Promise.all([getPost(id), listComments(id, 1, 50)])
      .then(([post, comments]) => {
        const currentUserId = getUserId()
        this.setData({
          post,
          avatar: post.author.avatar_url || brandAssets.avatarDefault,
          nickname: post.author.nickname || '用户',
          time: formatCreatedAt(post.created_at),
          boardLabel: BOARD_LABEL[post.board],
          isOwn: post.author.id === currentUserId,
          followLabel: post.followed ? '已关注' : '关注',
          comments: groupComments(comments.items, currentUserId, post.author.id),
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
    job.then(() => this.reload()).catch(toastRequestError)
  },
  onLike() {
    const id = this.data.id
    if (!id) {
      return
    }
    likePost(id)
      .then((post) => {
        this.setData({ post })
      })
      .catch(toastRequestError)
  },
  onFavorite() {
    const id = this.data.id
    if (!id) {
      return
    }
    favoritePost(id)
      .then((post) => {
        this.setData({ post })
      })
      .catch(toastRequestError)
  },
  focusComposer() {
    this.setData({ commentFocus: false }, () => {
      this.setData({ commentFocus: true, scrollInto: 'comments' })
    })
  },
  onReply() {
    this.setData({
      replyParentId: '',
      replyToName: '',
      commentPlaceholder: '写一条评论',
    })
    this.focusComposer()
  },
  onReplyTo(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as string
    const name = (e.currentTarget.dataset.name as string) || '用户'
    this.setData({
      replyParentId: id,
      replyToName: name,
      commentPlaceholder: `评论 ${name}`,
    })
    this.focusComposer()
  },
  onCancelReply() {
    this.setData({
      replyParentId: '',
      replyToName: '',
      commentPlaceholder: '写一条评论',
      commentFocus: false,
    })
  },
  onCommentInput(e: WechatMiniprogram.Input) {
    this.setData({ commentBody: e.detail.value })
  },
  onSendComment() {
    const id = this.data.id
    const body = this.data.commentBody.trim()
    if (!id || !body) {
      return
    }
    const parentId = this.data.replyParentId || null
    createComment(id, body, parentId)
      .then(() => {
        this.setData({
          commentBody: '',
          replyParentId: '',
          replyToName: '',
          commentPlaceholder: '写一条评论',
          commentFocus: false,
        })
        this.reload()
      })
      .catch(toastRequestError)
  },
  onDeleteComment(e: WechatMiniprogram.TouchEvent) {
    const commentId = e.currentTarget.dataset.id as string
    const postId = this.data.id
    if (!commentId || !postId) {
      return
    }
    wx.showModal({
      title: '删除评论',
      content: '删除后无法恢复',
      success: (res) => {
        if (!res.confirm) {
          return
        }
        deleteComment(postId, commentId)
          .then((result) => {
            const post = this.data.post
            this.setData({
              post: post ? { ...post, comment_count: result.comment_count } : post,
            })
            this.reload()
          })
          .catch(toastRequestError)
      },
    })
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
  onShareAppMessage() {
    const id = this.data.id
    const post = this.data.post
    return {
      title: (post && (post.title || post.body)) || '宠物记录',
      path: `/modules/community/pages/detail/detail?id=${id}`,
    }
  },
})
