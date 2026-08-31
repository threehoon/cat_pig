import { toastRequestError } from '../../../../core/request'
import { deleteComment, likeComment, reportComment } from '../../services/community'
import { CommentReportReason, Post } from '../../types/post'
import { CommentView, patchCommentLike } from './detail-view'

type ActionCallbacks = {
  getPost: () => Post | null
  setPost: (post: Post | null) => void
  reload: () => void
}

const REPORT_OPTIONS: { label: string; reason: CommentReportReason }[] = [
  { label: '垃圾广告', reason: 'spam' },
  { label: '不友善', reason: 'abuse' },
  { label: '色情低俗', reason: 'porn' },
  { label: '其他', reason: 'other' },
]

export function likeCommentAction(
  postId: string,
  getComments: () => CommentView[],
  event: WechatMiniprogram.CustomEvent<{ id: string }>,
  setComments: (comments: CommentView[]) => void,
) {
  const commentId = event.detail.id
  if (!commentId || !postId) {
    return
  }

  likeComment(postId, commentId)
    .then((comment) => {
      setComments(patchCommentLike(getComments(), comment.id, comment.liked, comment.like_count))
    })
    .catch(toastRequestError)
}

export function previewCommentAction(event: WechatMiniprogram.CustomEvent<{ urls: string[]; current: string }>) {
  const urls = event.detail.urls || []
  if (!urls.length) {
    return
  }
  wx.previewImage({ urls, current: event.detail.current || urls[0] })
}

export function moreCommentAction(
  postId: string,
  event: WechatMiniprogram.CustomEvent<{
    id: string
    canDelete: boolean
    isOwn: boolean
    body: string
  }>,
  callbacks: ActionCallbacks,
) {
  const detail = event.detail
  const itemList = ['复制']
  if (!detail.isOwn) {
    itemList.push('举报')
  }
  if (detail.canDelete) {
    itemList.push('删除')
  }

  wx.showActionSheet({
    itemList,
    success: (res) => {
      const label = itemList[res.tapIndex]
      if (label === '复制') {
        copyComment(detail.body)
      } else if (label === '举报') {
        reportCommentAction(postId, detail.id)
      } else if (label === '删除') {
        deleteCommentAction(postId, detail.id, callbacks)
      }
    },
  })
}

function copyComment(body: string) {
  wx.setClipboardData({ data: body || '评论' })
}

function reportCommentAction(postId: string, commentId: string) {
  wx.showActionSheet({
    itemList: REPORT_OPTIONS.map((item) => item.label),
    success: (res) => {
      const picked = REPORT_OPTIONS[res.tapIndex]
      if (!picked || !postId) {
        return
      }
      reportComment(postId, commentId, picked.reason)
        .then(() => wx.showToast({ title: '已收到举报', icon: 'none' }))
        .catch(toastRequestError)
    },
  })
}

function deleteCommentAction(postId: string, commentId: string, callbacks: ActionCallbacks) {
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
          const post = callbacks.getPost()
          callbacks.setPost(post ? { ...post, comment_count: result.comment_count } : post)
          callbacks.reload()
        })
        .catch(toastRequestError)
    },
  })
}
