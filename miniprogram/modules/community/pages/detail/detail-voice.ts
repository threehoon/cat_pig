import { toastRequestError } from '../../../../core/request'
import { createComment } from '../../services/community'
import { CommentView, patchPlaying } from './detail-view'
import { uploadCommentVoice } from './detail-media'

export type VoiceState = {
  id: string
  comments: CommentView[]
  voiceMode: boolean
  recording: boolean
  sending: boolean
  replyParentId: string
}

type SetData = (data: Record<string, unknown>) => void

type VoiceCallbacks = {
  setData: SetData
  resetComposer: () => void
  reload: () => void
}

let recorder: WechatMiniprogram.RecorderManager | null = null
let audioPlayer: WechatMiniprogram.InnerAudioContext | null = null
let holdingVoice = false

export function ensureRecorder() {
  if (recorder) {
    return
  }

  recorder = wx.getRecorderManager()
  recorder.onStop((res) => {
    const pages = getCurrentPages()
    const current = pages[pages.length - 1] as {
      handleRecordStop?: (result: { tempFilePath?: string; duration?: number }) => void
    }
    if (current && current.handleRecordStop) {
      current.handleRecordStop(res)
    }
  })
  recorder.onError(() => {
    holdingVoice = false
    const pages = getCurrentPages()
    const current = pages[pages.length - 1] as {
      setData?: (data: { recording: boolean }) => void
    }
    if (current && current.setData) {
      current.setData({ recording: false })
    }
    wx.showToast({ title: '录音失败，电脑端可能不支持', icon: 'none' })
  })
}

export function stopRecording(state: Pick<VoiceState, 'recording'>, setData: SetData) {
  holdingVoice = false
  if (recorder && state.recording) {
    try {
      recorder.stop()
    } catch (err) {
      // The platform may already have stopped recording.
    }
  }
  if (state.recording) {
    setData({ recording: false })
  }
}

export function startRecording(state: Pick<VoiceState, 'voiceMode' | 'sending'>, setData: SetData) {
  if (!state.voiceMode || state.sending) {
    return
  }

  holdingVoice = true
  ensureRecorder()
  if (!recorder) {
    holdingVoice = false
    wx.showToast({ title: '无法开始录音', icon: 'none' })
    return
  }

  setData({ recording: true })
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
    setData({ recording: false })
    wx.showToast({ title: '无法开始录音', icon: 'none' })
  }
}

export function endRecording(state: Pick<VoiceState, 'voiceMode'>, setData: SetData) {
  if (!state.voiceMode || !recorder || !holdingVoice) {
    return
  }

  try {
    recorder.stop()
  } catch (err) {
    setData({ recording: false })
  }
}

export function handleRecordStop(
  state: Pick<VoiceState, 'id' | 'replyParentId' | 'sending'>,
  result: { tempFilePath?: string; duration?: number },
  callbacks: VoiceCallbacks,
) {
  const wasHolding = holdingVoice
  holdingVoice = false
  callbacks.setData({ recording: false })
  if (!wasHolding) {
    return
  }

  const duration = Math.max(0, Math.round((result.duration || 0) / 1000))
  if (duration < 1 || !result.tempFilePath) {
    wx.showToast({ title: '说话时间太短', icon: 'none' })
    return
  }

  const id = state.id
  if (!id || state.sending) {
    return
  }

  callbacks.setData({ sending: true })
  uploadCommentVoice(result.tempFilePath)
    .then((audio_url) =>
      createComment(id, {
        body: '',
        parent_id: state.replyParentId || null,
        sticker_ids: [],
        image_urls: [],
        audio_url,
        audio_duration: Math.min(60, duration),
      }),
    )
    .then(() => {
      callbacks.resetComposer()
      callbacks.reload()
    })
    .catch((err) => {
      callbacks.setData({ sending: false })
      toastRequestError(err)
    })
}

export function playComment(
  state: Pick<VoiceState, 'comments'>,
  event: WechatMiniprogram.CustomEvent<{ id: string; url: string }>,
  setComments: (comments: CommentView[]) => void,
) {
  const id = event.detail.id
  const url = event.detail.url
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
  scan(state.comments)

  if (!audioPlayer) {
    audioPlayer = wx.createInnerAudioContext()
    audioPlayer.onEnded(() => updateCurrentComments())
    audioPlayer.onError(() => {
      wx.showToast({ title: '语音无法播放', icon: 'none' })
      updateCurrentComments()
    })
  }

  if (already) {
    audioPlayer.stop()
    setComments(patchPlaying(state.comments, ''))
    return
  }

  audioPlayer.stop()
  audioPlayer.src = url
  audioPlayer.play()
  setComments(patchPlaying(state.comments, id))
}

function updateCurrentComments() {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1] as {
    data?: { comments?: CommentView[] }
    setData?: SetData
  }
  const comments = current && current.data && current.data.comments
  if (current && current.setData && comments) {
    current.setData({ comments: patchPlaying(comments, '') })
  }
}

export function disposeVoice() {
  holdingVoice = false
  if (recorder) {
    try {
      recorder.stop()
    } catch (err) {
      // The platform may already be stopped.
    }
  }
  if (audioPlayer) {
    audioPlayer.stop()
    audioPlayer.destroy()
    audioPlayer = null
  }
}
