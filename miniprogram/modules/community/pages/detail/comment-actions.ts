import { toastRequestError } from '../../../../core/request'
import { deleteComment, likeComment, reportComment } from '../../services/community'
import { CommentReportReason } from '../../types/post'
import { CommentView, patchCommentLike } from './detail-view'

type ActionPage = {
  data: { id: string; comments: CommentView[]; post: { comment_count: number } | null }
  setData: (data: Record<string, unknown>, callback?: () => void) => void
  reload: () => void
}

const REPORT_OPTIONS: { label: string; reason: CommentReportReason }[] = [
  { label: '垃圾广告', reason: 'spam' }, { label: '不友善', reason: 'abuse' }, { label: '色情低俗', reason: 'porn' }, { label: '其他', reason: 'other' },
]

export function likeCommentAction(page: ActionPage, event: WechatMiniprogram.CustomEvent<{ id: string }>) {
  const commentId = event.detail.id; const postId = page.data.id
  if (!commentId || !postId) return
  likeComment(postId, commentId).then((comment) => page.setData({ comments: patchCommentLike(page.data.comments, comment.id, comment.liked, comment.like_count) })).catch(toastRequestError)
}

export function previewCommentAction(event: WechatMiniprogram.CustomEvent<{ urls: string[]; current: string }>) {
  const urls = event.detail.urls || []; if (!urls.length) return
  wx.previewImage({ urls, current: event.detail.current || urls[0] })
}

export function moreCommentAction(page: ActionPage, event: WechatMiniprogram.CustomEvent<{ id: string; canDelete: boolean; isOwn: boolean; body: string }>) {
  const detail = event.detail; const itemList = ['复制']
  if (!detail.isOwn) itemList.push('举报')
  if (detail.canDelete) itemList.push('删除')
  wx.showActionSheet({ itemList, success: (res) => { const label = itemList[res.tapIndex]; if (label === '复制') copyComment(detail.body); else if (label === '举报') reportCommentAction(page, detail.id); else if (label === '删除') deleteCommentAction(page, detail.id) } })
}

function copyComment(body: string) { wx.setClipboardData({ data: body || '评论' }) }

function reportCommentAction(page: ActionPage, commentId: string) {
  const postId = page.data.id
  wx.showActionSheet({ itemList: REPORT_OPTIONS.map((item) => item.label), success: (res) => { const picked = REPORT_OPTIONS[res.tapIndex]; if (!picked || !postId) return; reportComment(postId, commentId, picked.reason).then(() => wx.showToast({ title: '已收到举报', icon: 'none' })).catch(toastRequestError) } })
}

function deleteCommentAction(page: ActionPage, commentId: string) {
  const postId = page.data.id; if (!commentId || !postId) return
  wx.showModal({ title: '删除评论', content: '删除后无法恢复', success: (res) => { if (!res.confirm) return; deleteComment(postId, commentId).then((result) => { const post = page.data.post; page.setData({ post: post ? { ...post, comment_count: result.comment_count } : post }); page.reload() }).catch(toastRequestError) } })
}
