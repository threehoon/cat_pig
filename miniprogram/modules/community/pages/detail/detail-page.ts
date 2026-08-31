import { brandAssets } from '../../../../assets/paths'
import { getUserId } from '../../../../core/auth'
import { toastRequestError } from '../../../../core/request'
import { formatCreatedAt } from '../../../../utils/util'
import { UNICODE_EMOJIS } from '../../stickers'
import {
  deletePost,
  favoritePost,
  followUser,
  getPost,
  likePost,
  listComments,
  unfollowUser,
} from '../../services/community'
import { BOARD_LABEL, Post } from '../../types/post'
import { CommentView, MentionUser, collectMentions, collectNicknames, groupComments } from './detail-view'
import { likeCommentAction, moreCommentAction, previewCommentAction } from './comment-actions'
import { playComment, startRecording, endRecording, handleRecordStop, stopRecording, disposeVoice } from './detail-voice'
import { clearReply, composerBlur, composerFocus, focusComposer, inputBody, pickEmoji, pickImages, pickMention, removeImage, replyTo, sendComment, setBody, toggleEmoji, toggleMention, toggleVoice } from './comment-composer'

let blurTimer: ReturnType<typeof setTimeout> | 0 = 0

export const detailPage = {
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
    emojiOpen: false,
    mentionOpen: false,
    voiceMode: false,
    recording: false,
    emojis: UNICODE_EMOJIS,
    draftImages: [] as string[],
    mentionUsers: [] as MentionUser[],
    composerCursor: -1,
    canSend: false,
    sending: false,
    iconAlbum: brandAssets.composeAlbum,
    iconEmoji: brandAssets.composeEmoji,
    iconEmojiOn: brandAssets.composeEmojiOn,
    iconAt: brandAssets.composeAt,
    iconAtOn: brandAssets.composeAtOn,
    iconMic: brandAssets.composeMic,
    iconMicOn: brandAssets.composeMicOn,
  },
  onLoad(query: { id?: string; reply?: string }) {
    const id = query.id || ''
    this.setData(
      {
        id,
        commentFocus: query.reply === '1',
        scrollInto: query.reply === '1' ? 'comments' : '',
      },
      () => this.syncComposer(),
    )
    if (!id) {
      wx.showToast({ title: '帖子不存在', icon: 'none' })
    }
  },
  onShow() {
    this.reload()
  },
  onUnload() {
    this.clearBlurTimer()
    disposeVoice()
  },
  syncComposer() {
    const canSend = !!(this.data.commentBody.trim() || this.data.draftImages.length)
    this.setData({ canSend })
  },
  clearBlurTimer() {
    if (blurTimer) {
      clearTimeout(blurTimer)
      blurTimer = 0
    }
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
          comments: groupComments(
            comments.items,
            currentUserId,
            post.author.id,
            collectNicknames(post, comments.items),
          ),
          mentionUsers: collectMentions(post, comments.items, currentUserId),
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
  focusComposer() { focusComposer(this) },
  onComposerFocus() { composerFocus(this) },
  onComposerBlur() { composerBlur(this, (callback, ms) => { blurTimer = setTimeout(callback, ms) }) },
  onReply() { this.setData({ replyParentId: '', replyToName: '', commentPlaceholder: '写一条评论' }); focusComposer(this) },
  onReplyTo(e: WechatMiniprogram.CustomEvent<{ id: string; name: string }>) {
    const id = e.detail.id
    const name = e.detail.name || '用户'
    replyTo(this, id, name)
  },
  onCancelReply() { clearReply(this) },
  mentionNames(): string[] {
    return this.data.mentionUsers.map((item) => item.nickname)
  },
  setCommentBody(value: string, cursor?: number) {
    setBody(this, value, cursor)
  },
  onCommentInput(e: WechatMiniprogram.TextareaInput) {
    const next = e.detail.value
    const cursor = typeof e.detail.cursor === 'number' ? e.detail.cursor : next.length
    inputBody(this, next, cursor)
  },
  onToggleEmoji() {
    toggleEmoji(this)
  },
  onToggleMention() {
    toggleMention(this)
  },
  onPickMention(e: WechatMiniprogram.TouchEvent) {
    const name = (e.currentTarget.dataset.name as string) || '用户'
    pickMention(this, name)
  },
  onToggleVoice() {
    toggleVoice(this)
  },
  stopRecording() { stopRecording(this) },
  onVoiceHoldStart() { startRecording(this) },
  onVoiceHoldEnd() { endRecording(this) },
  handleRecordStop(res: { tempFilePath?: string; duration?: number }) { handleRecordStop(this, res) },
  onPlayComment(e: WechatMiniprogram.CustomEvent<{ id: string; url: string }>) { playComment(this, e) },
  onPickEmoji(e: WechatMiniprogram.TouchEvent) { pickEmoji(this, e.currentTarget.dataset.emoji as string) },
  onPickImage() { pickImages(this) },
  onRemoveImage(e: WechatMiniprogram.TouchEvent) { removeImage(this, Number(e.currentTarget.dataset.index)) },
  resetComposer() {
    this.stopRecording()
    this.setData({
      commentBody: '',
      replyParentId: '',
      replyToName: '',
      commentPlaceholder: '写一条评论',
      commentFocus: false,
      emojiOpen: false,
      mentionOpen: false,
      voiceMode: false,
      recording: false,
      draftImages: [],
      composerCursor: -1,
      canSend: false,
      sending: false,
    })
  },
  onSendComment() { sendComment(this) },
  onLikeComment(e: WechatMiniprogram.CustomEvent<{ id: string }>) { likeCommentAction(this, e) },
  onPreviewComment(e: WechatMiniprogram.CustomEvent<{ urls: string[]; current: string }>) { previewCommentAction(e) },
  onMoreComment(e: WechatMiniprogram.CustomEvent<{ id: string; canDelete: boolean; isOwn: boolean; body: string }>) { moreCommentAction(this, e) },
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
}
