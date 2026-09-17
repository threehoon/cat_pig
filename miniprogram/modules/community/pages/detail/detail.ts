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
  createComment,
} from '../../services/community'
import { Post } from '../../types/post'
import { CommentView, MentionUser, collectMentions, collectNicknames, groupComments } from './detail-view'
import { likeCommentAction, moreCommentAction, previewCommentAction } from './comment-actions'
import {
  attachVoicePage,
  disposeVoice,
  endRecording,
  handleRecordStop,
  playComment,
  startRecording,
  stopRecording,
} from './detail-voice'
import {
  appendEmoji,
  canSendComment,
  clearReplyPatch,
  commentPayload,
  composerBlurPatch,
  composerFocusPatch,
  focusComposerPatches,
  inputBodyValue,
  pickMentionPatch,
  removeImage as removeDraftImage,
  replyToPatch,
  setBodyPatch,
  toggleEmojiPatch,
  toggleMentionPatch,
  toggleVoicePatch,
} from './comment-composer'
import { uploadCommentImages } from './detail-media'

let blurTimer: ReturnType<typeof setTimeout> | 0 = 0

Page({
  data: {
    id: '',
    post: null as Post | null,
    avatar: brandAssets.avatarDefault as string,
    nickname: '用户',
    time: '',
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
    attachVoicePage({
      handleRecordStop: (res) => this.handleRecordStop(res),
      setRecording: (recording) => this.setData({ recording }),
    })
    this.reload()
  },
  onUnload() {
    this.clearBlurTimer()
    disposeVoice()
  },
  syncComposer() {
    this.setData({ canSend: canSendComment(this.data) })
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
        const time = formatCreatedAt(post.created_at)
        const topic = post.topic_names[0] || ''
        this.setData({
          post,
          avatar: post.author.avatar_url || brandAssets.avatarDefault,
          nickname: post.author.nickname || '用户',
          time: topic ? `${time} · ${topic}` : time,
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
  focusComposer() {
    this.clearBlurTimer()
    const patches = focusComposerPatches()
    this.setData(patches.blur, () => {
      this.setData(patches.focus, () => this.syncComposer())
    })
  },
  onComposerFocus() {
    this.clearBlurTimer()
    this.setData(composerFocusPatch(), () => this.syncComposer())
  },
  onComposerBlur() {
    this.clearBlurTimer()
    blurTimer = setTimeout(() => {
      this.setData(composerBlurPatch(), () => this.syncComposer())
    }, 120)
  },
  onReply() {
    this.setData({ replyParentId: '', replyToName: '', commentPlaceholder: '写一条评论' })
    this.focusComposer()
  },
  onReplyTo(e: WechatMiniprogram.CustomEvent<{ id: string; name: string }>) {
    const id = e.detail.id
    const name = e.detail.name || '用户'
    this.setData(replyToPatch(id, name))
    this.focusComposer()
  },
  onCancelReply() {
    this.clearBlurTimer()
    this.setData(clearReplyPatch(), () => this.syncComposer())
  },
  mentionNames(): string[] {
    return this.data.mentionUsers.map((item) => item.nickname)
  },
  setCommentBody(value: string, cursor?: number) {
    this.setData(setBodyPatch(value, cursor), () => {
      if (cursor !== undefined) {
        this.setData({ composerCursor: -1 })
      }
      this.syncComposer()
    })
  },
  onCommentInput(e: WechatMiniprogram.TextareaInput) {
    const next = e.detail.value
    const cursor = typeof e.detail.cursor === 'number' ? e.detail.cursor : next.length
    const patched = inputBodyValue(this.data.commentBody, next, cursor, this.mentionNames())
    this.setCommentBody(patched.value, patched.cursor)
  },
  onToggleEmoji() {
    this.clearBlurTimer()
    this.setData(toggleEmojiPatch(this.data), () => this.syncComposer())
  },
  onToggleMention() {
    this.clearBlurTimer()
    this.setData(toggleMentionPatch(this.data))
  },
  onPickMention(e: WechatMiniprogram.TouchEvent) {
    const name = (e.currentTarget.dataset.name as string) || '用户'
    this.setData(pickMentionPatch(this.data, name), () => this.syncComposer())
  },
  onToggleVoice() {
    this.clearBlurTimer()
    const result = toggleVoicePatch(this.data)
    if (result.shouldStopRecording) {
      this.stopRecording()
    }
    this.setData(result.patch)
  },
  stopRecording() {
    stopRecording(this.data, (data) => this.setData(data))
  },
  onVoiceHoldStart() {
    startRecording(this.data, (data) => this.setData(data))
  },
  onVoiceHoldEnd() {
    endRecording(this.data, (data) => this.setData(data))
  },
  handleRecordStop(res: { tempFilePath?: string; duration?: number }) {
    handleRecordStop(this.data, res, {
      setData: (data) => this.setData(data),
      resetComposer: () => this.resetComposer(),
      reload: () => this.reload(),
    })
  },
  onPlayComment(e: WechatMiniprogram.CustomEvent<{ id: string; url: string }>) {
    playComment(() => this.data.comments, e, (comments) => this.setData({ comments }))
  },
  onPickEmoji(e: WechatMiniprogram.TouchEvent) {
    const result = appendEmoji(this.data.commentBody, e.currentTarget.dataset.emoji as string)
    if (result) {
      this.setCommentBody(result.value, result.cursor)
    }
  },
  onPickImage() {
    this.clearBlurTimer()
    const remain = 9 - this.data.draftImages.length
    if (remain <= 0) {
      wx.showToast({ title: '图片最多 9 张', icon: 'none' })
      return
    }
    this.setData({ emojiOpen: false, mentionOpen: false, voiceMode: false })
    uploadCommentImages(remain)
      .then((urls) => {
        if (urls.length) {
          this.setData({ draftImages: this.data.draftImages.concat(urls) }, () => this.syncComposer())
        }
      })
      .catch(toastRequestError)
  },
  onRemoveImage(e: WechatMiniprogram.TouchEvent) {
    const draftImages = removeDraftImage(this.data.draftImages, Number(e.currentTarget.dataset.index))
    this.setData({ draftImages }, () => this.syncComposer())
  },
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
  onSendComment() {
    const payload = commentPayload(this.data)
    if (!payload) {
      return
    }
    this.setData({ sending: true })
    createComment(this.data.id, payload)
      .then(() => {
        this.resetComposer()
        this.reload()
      })
      .catch((err) => {
        this.setData({ sending: false })
        toastRequestError(err)
      })
  },
  onLikeComment(e: WechatMiniprogram.CustomEvent<{ id: string }>) {
    likeCommentAction(this.data.id, () => this.data.comments, e, (comments) => {
      this.setData({ comments })
    })
  },
  onPreviewComment(e: WechatMiniprogram.CustomEvent<{ urls: string[]; current: string }>) {
    previewCommentAction(e)
  },
  onMoreComment(e: WechatMiniprogram.CustomEvent<{ id: string; canDelete: boolean; isOwn: boolean; body: string }>) {
    moreCommentAction(this.data.id, e, {
      getPost: () => this.data.post,
      setPost: (post) => this.setData({ post }),
      reload: () => this.reload(),
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
