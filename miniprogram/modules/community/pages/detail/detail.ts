import { brandAssets } from '../../../../assets/paths'
import { getUserId } from '../../../../core/auth'
import { toastRequestError } from '../../../../core/request'
import { formatCreatedAt } from '../../../../utils/util'
import { chooseLocalImages } from '../../../media/choose'
import { uploadImages, uploadMedia } from '../../../media/services/media'
import { applyMentionDelete, insertMention, mentionParts, MentionPart } from '../../mentions'
import { UNICODE_EMOJIS, stickersOf, StickerView } from '../../stickers'
import {
  createComment,
  deleteComment,
  deletePost,
  favoritePost,
  followUser,
  getPost,
  likeComment,
  likePost,
  listComments,
  reportComment,
  unfollowUser,
} from '../../services/community'
import { BOARD_LABEL, Comment, CommentReportReason, Post } from '../../types/post'

type CommentView = {
  id: string
  nickname: string
  avatar: string
  body: string
  time: string
  replyToName: string
  canDelete: boolean
  isAuthor: boolean
  isOwn: boolean
  liked: boolean
  likeCount: number
  stickers: StickerView[]
  images: string[]
  previewImages: string[]
  showStack: boolean
  imageOverflow: number
  audioUrl: string
  audioDuration: number
  playing: boolean
  bodyParts: MentionPart[]
  replies: CommentView[]
}

type MentionUser = {
  id: string
  nickname: string
  avatar: string
}

let blurTimer: ReturnType<typeof setTimeout> | 0 = 0
let recordTick: ReturnType<typeof setInterval> | 0 = 0
let recorder: WechatMiniprogram.RecorderManager | null = null
let audioPlayer: WechatMiniprogram.InnerAudioContext | null = null
let holdingVoice = false

const REPORT_OPTIONS: { label: string; reason: CommentReportReason }[] = [
  { label: '垃圾广告', reason: 'spam' },
  { label: '不友善', reason: 'abuse' },
  { label: '色情低俗', reason: 'porn' },
  { label: '其他', reason: 'other' },
]

function collectNicknames(post: Post, comments: Comment[]): string[] {
  const names: string[] = []
  const add = (name: string | null) => {
    const nickname = (name || '用户').trim()
    if (nickname && names.indexOf(nickname) === -1) {
      names.push(nickname)
    }
  }
  add(post.author.nickname)
  comments.forEach((item) => add(item.author.nickname))
  return names
}

function toCommentView(
  item: Comment,
  currentUserId: string | null,
  postAuthorId: string,
  names: string[],
): CommentView {
  const images = item.image_urls || []
  const showStack = images.length > 3
  return {
    id: item.id,
    nickname: item.author.nickname || '用户',
    avatar: item.author.avatar_url || brandAssets.avatarDefault,
    body: item.body,
    time: formatCreatedAt(item.created_at),
    replyToName: (item.reply_to && item.reply_to.nickname) || '',
    canDelete: !!currentUserId && (item.author.id === currentUserId || postAuthorId === currentUserId),
    isAuthor: item.author.id === postAuthorId,
    isOwn: !!currentUserId && item.author.id === currentUserId,
    liked: item.liked,
    likeCount: item.like_count,
    stickers: stickersOf(item.sticker_ids || []).map((sticker, index) => ({
      ...sticker,
      key: `${sticker.id}-${index}`,
    })),
    images,
    previewImages: showStack ? images.slice(0, 1) : images.slice(0, 3),
    showStack,
    imageOverflow: showStack ? images.length - 1 : 0,
    audioUrl: item.audio_url || '',
    audioDuration: item.audio_duration || 0,
    playing: false,
    bodyParts: mentionParts(item.body, names),
    replies: [],
  }
}

function collectMentions(post: Post, comments: Comment[], currentUserId: string | null): MentionUser[] {
  const seen: Record<string, boolean> = {}
  const list: MentionUser[] = []
  const add = (id: string, nickname: string | null, avatar: string | null) => {
    if (!id || seen[id] || id === currentUserId) {
      return
    }
    seen[id] = true
    list.push({
      id,
      nickname: nickname || '用户',
      avatar: avatar || brandAssets.avatarDefault,
    })
  }
  add(post.author.id, post.author.nickname, post.author.avatar_url)
  comments.forEach((item) => add(item.author.id, item.author.nickname, item.author.avatar_url))
  return list
}

function patchPlaying(list: CommentView[], id: string): CommentView[] {
  return list.map((item) => ({
    ...item,
    playing: item.id === id,
    replies: patchPlaying(item.replies, id),
  }))
}

function groupComments(
  items: Comment[],
  currentUserId: string | null,
  postAuthorId: string,
  names: string[],
): CommentView[] {
  const views = items.map((item) => toCommentView(item, currentUserId, postAuthorId, names))
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

function patchCommentLike(list: CommentView[], id: string, liked: boolean, likeCount: number): CommentView[] {
  return list.map((item) => {
    if (item.id === id) {
      return { ...item, liked, likeCount }
    }
    if (item.replies.length) {
      return { ...item, replies: patchCommentLike(item.replies, id, liked, likeCount) }
    }
    return item
  })
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
    this.clearRecordTick()
    holdingVoice = false
    if (recorder) {
      try {
        recorder.stop()
      } catch (err) {
        // ignore
      }
    }
    if (audioPlayer) {
      audioPlayer.stop()
      audioPlayer.destroy()
      audioPlayer = null
    }
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
  clearRecordTick() {
    if (recordTick) {
      clearInterval(recordTick)
      recordTick = 0
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
  focusComposer() {
    this.clearBlurTimer()
    this.setData({ commentFocus: false, emojiOpen: false, mentionOpen: false, voiceMode: false }, () => {
      this.setData({ commentFocus: true, scrollInto: 'comments' }, () => this.syncComposer())
    })
  },
  onComposerFocus() {
    this.clearBlurTimer()
    this.setData({ commentFocus: true, emojiOpen: false, mentionOpen: false, voiceMode: false }, () => this.syncComposer())
  },
  onComposerBlur() {
    this.clearBlurTimer()
    blurTimer = setTimeout(() => {
      this.setData({ commentFocus: false }, () => this.syncComposer())
    }, 120)
  },
  onReply() {
    this.setData({
      replyParentId: '',
      replyToName: '',
      commentPlaceholder: '写一条评论',
    })
    this.focusComposer()
  },
  onReplyTo(e: WechatMiniprogram.CustomEvent<{ id: string; name: string }>) {
    const id = e.detail.id
    const name = e.detail.name || '用户'
    this.setData({
      replyParentId: id,
      replyToName: name,
      commentPlaceholder: `评论 ${name}`,
    })
    this.focusComposer()
  },
  onCancelReply() {
    this.clearBlurTimer()
    this.setData(
      {
        replyParentId: '',
        replyToName: '',
        commentPlaceholder: '写一条评论',
        commentFocus: false,
        emojiOpen: false,
        mentionOpen: false,
        voiceMode: false,
        recording: false,
      },
      () => this.syncComposer(),
    )
  },
  mentionNames(): string[] {
    return this.data.mentionUsers.map((item) => item.nickname)
  },
  setCommentBody(value: string, cursor?: number) {
    const data: Record<string, unknown> = {
      commentBody: value,
    }
    if (cursor !== undefined) {
      data.composerCursor = cursor
    }
    this.setData(data, () => {
      if (cursor !== undefined) {
        this.setData({ composerCursor: -1 })
      }
      this.syncComposer()
    })
  },
  onCommentInput(e: WechatMiniprogram.TextareaInput) {
    const next = e.detail.value
    const cursor = typeof e.detail.cursor === 'number' ? e.detail.cursor : next.length
    const patched = applyMentionDelete(this.data.commentBody, next, cursor, this.mentionNames())
    if (patched.value !== next) {
      this.setCommentBody(patched.value, patched.cursor)
      return
    }
    this.setCommentBody(next)
  },
  onToggleEmoji() {
    this.clearBlurTimer()
    const open = !this.data.emojiOpen
    this.setData(
      {
        emojiOpen: open,
        mentionOpen: false,
        voiceMode: false,
        commentFocus: false,
      },
      () => this.syncComposer(),
    )
  },
  onToggleMention() {
    this.clearBlurTimer()
    const open = !this.data.mentionOpen
    this.setData({
      mentionOpen: open,
      emojiOpen: false,
      voiceMode: false,
      commentFocus: false,
    })
  },
  onPickMention(e: WechatMiniprogram.TouchEvent) {
    const name = (e.currentTarget.dataset.name as string) || '用户'
    const inserted = insertMention(this.data.commentBody, name)
    this.setData(
      {
        commentBody: inserted.value,
        composerCursor: inserted.cursor,
        mentionOpen: false,
        voiceMode: false,
        commentFocus: true,
      },
      () => this.syncComposer(),
    )
  },
  onToggleVoice() {
    this.clearBlurTimer()
    const open = !this.data.voiceMode
    if (!open) {
      this.stopRecording()
    }
    this.setData({
      voiceMode: open,
      emojiOpen: false,
      mentionOpen: false,
      commentFocus: false,
    })
  },
  ensureRecorder() {
    if (recorder) {
      return
    }
    recorder = wx.getRecorderManager()
    recorder.onStop((res) => {
      const pages = getCurrentPages()
      const page = pages[pages.length - 1] as { handleRecordStop?: (result: { tempFilePath?: string; duration?: number }) => void }
      if (page && page.handleRecordStop) {
        page.handleRecordStop(res)
      }
    })
    recorder.onError(() => {
      holdingVoice = false
      const pages = getCurrentPages()
      const page = pages[pages.length - 1] as { setData?: (data: { recording: boolean }) => void }
      if (page && page.setData) {
        page.setData({ recording: false })
      }
      wx.showToast({ title: '录音失败，电脑端可能不支持', icon: 'none' })
    })
  },
  stopRecording() {
    this.clearRecordTick()
    holdingVoice = false
    if (recorder && this.data.recording) {
      try {
        recorder.stop()
      } catch (err) {
        // ignore
      }
    }
    if (this.data.recording) {
      this.setData({ recording: false })
    }
  },
  onVoiceHoldStart() {
    if (!this.data.voiceMode || this.data.sending) {
      return
    }
    holdingVoice = true
    this.ensureRecorder()
    if (!recorder) {
      holdingVoice = false
      wx.showToast({ title: '无法开始录音', icon: 'none' })
      return
    }
    this.setData({ recording: true })
    try {
      recorder.start({
        duration: 60000,
        format: 'mp3',
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 48000,
      })
    } catch (err) {
      holdingVoice = false
      this.setData({ recording: false })
      wx.showToast({ title: '无法开始录音', icon: 'none' })
    }
  },
  onVoiceHoldEnd() {
    if (!this.data.voiceMode) {
      return
    }
    if (recorder && holdingVoice) {
      try {
        recorder.stop()
      } catch (err) {
        this.setData({ recording: false })
      }
    }
  },
  handleRecordStop(res: { tempFilePath?: string; duration?: number }) {
    this.clearRecordTick()
    const wasHolding = holdingVoice
    holdingVoice = false
    this.setData({ recording: false })
    if (!wasHolding) {
      return
    }
    const duration = Math.max(0, Math.round((res.duration || 0) / 1000))
    if (duration < 1 || !res.tempFilePath) {
      wx.showToast({ title: '说话时间太短', icon: 'none' })
      return
    }
    const id = this.data.id
    if (!id || this.data.sending) {
      return
    }
    this.setData({ sending: true })
    uploadMedia(res.tempFilePath)
      .then((media) =>
        createComment(id, {
          body: '',
          parent_id: this.data.replyParentId || null,
          sticker_ids: [],
          image_urls: [],
          audio_url: media.url,
          audio_duration: Math.min(60, duration),
        }),
      )
      .then(() => {
        this.resetComposer()
        this.reload()
      })
      .catch((err) => {
        this.setData({ sending: false })
        toastRequestError(err)
      })
  },
  onPlayComment(e: WechatMiniprogram.CustomEvent<{ id: string; url: string }>) {
    const id = e.detail.id
    const url = e.detail.url
    if (!url) {
      return
    }
    let already = false
    const scan = (list: CommentView[]) => {
      list.forEach((item) => {
        if (item.id === id && item.playing) {
          already = true
        }
        scan(item.replies)
      })
    }
    scan(this.data.comments)
    if (!audioPlayer) {
      audioPlayer = wx.createInnerAudioContext()
      audioPlayer.onEnded(() => {
        this.setData({ comments: patchPlaying(this.data.comments, '') })
      })
      audioPlayer.onError(() => {
        wx.showToast({ title: '语音无法播放', icon: 'none' })
        this.setData({ comments: patchPlaying(this.data.comments, '') })
      })
    }
    if (already) {
      audioPlayer.stop()
      this.setData({ comments: patchPlaying(this.data.comments, '') })
      return
    }
    audioPlayer.stop()
    audioPlayer.src = url
    audioPlayer.play()
    this.setData({ comments: patchPlaying(this.data.comments, id) })
  },
  onPickEmoji(e: WechatMiniprogram.TouchEvent) {
    const emoji = e.currentTarget.dataset.emoji as string
    if (!emoji) {
      return
    }
    const next = `${this.data.commentBody}${emoji}`.slice(0, 200)
    this.setCommentBody(next, next.length)
  },
  onPickImage() {
    this.clearBlurTimer()
    const remain = 9 - this.data.draftImages.length
    if (remain <= 0) {
      wx.showToast({ title: '图片最多 9 张', icon: 'none' })
      return
    }
    this.setData({ emojiOpen: false, mentionOpen: false, voiceMode: false })
    chooseLocalImages(remain)
      .then((paths) => uploadImages(paths))
      .then((urls) => {
        if (!urls.length) {
          return
        }
        this.setData({ draftImages: this.data.draftImages.concat(urls) }, () => this.syncComposer())
      })
      .catch(toastRequestError)
  },
  onRemoveImage(e: WechatMiniprogram.TouchEvent) {
    const index = Number(e.currentTarget.dataset.index)
    const draftImages = this.data.draftImages.slice()
    draftImages.splice(index, 1)
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
    if (this.data.voiceMode) {
      return
    }
    const id = this.data.id
    const body = this.data.commentBody.trim()
    const image_urls = this.data.draftImages.slice()
    if (!id || this.data.sending || (!body && !image_urls.length)) {
      return
    }
    this.setData({ sending: true })
    createComment(id, {
      body,
      parent_id: this.data.replyParentId || null,
      sticker_ids: [],
      image_urls,
      audio_url: null,
      audio_duration: 0,
    })
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
    const commentId = e.detail.id
    const postId = this.data.id
    if (!commentId || !postId) {
      return
    }
    likeComment(postId, commentId)
      .then((comment) => {
        this.setData({
          comments: patchCommentLike(this.data.comments, comment.id, comment.liked, comment.like_count),
        })
      })
      .catch(toastRequestError)
  },
  onPreviewComment(e: WechatMiniprogram.CustomEvent<{ urls: string[]; current: string }>) {
    const urls = e.detail.urls || []
    if (!urls.length) {
      return
    }
    wx.previewImage({
      urls,
      current: e.detail.current || urls[0],
    })
  },
  onMoreComment(e: WechatMiniprogram.CustomEvent<{ id: string; canDelete: boolean; isOwn: boolean; body: string }>) {
    const detail = e.detail
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
          this.copyComment(detail.body)
          return
        }
        if (label === '举报') {
          this.reportComment(detail.id)
          return
        }
        if (label === '删除') {
          this.deleteCommentById(detail.id)
        }
      },
    })
  },
  copyComment(body: string) {
    wx.setClipboardData({
      data: body || '评论',
    })
  },
  reportComment(commentId: string) {
    const postId = this.data.id
    wx.showActionSheet({
      itemList: REPORT_OPTIONS.map((item) => item.label),
      success: (res) => {
        const picked = REPORT_OPTIONS[res.tapIndex]
        if (!picked || !postId) {
          return
        }
        reportComment(postId, commentId, picked.reason)
          .then(() => {
            wx.showToast({ title: '已收到举报', icon: 'none' })
          })
          .catch(toastRequestError)
      },
    })
  },
  deleteCommentById(commentId: string) {
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
