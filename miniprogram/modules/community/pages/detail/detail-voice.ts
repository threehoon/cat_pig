import { toastRequestError } from '../../../../core/request'
import { createComment } from '../../services/community'
import { CommentView, patchPlaying } from './detail-view'
import { uploadCommentVoice } from './detail-media'

type VoicePage = {
  data: { id: string; comments: CommentView[]; voiceMode: boolean; recording: boolean; sending: boolean; replyParentId: string }
  setData: (data: Record<string, unknown>) => void
  resetComposer: () => void
  reload: () => void
}

let recorder: WechatMiniprogram.RecorderManager | null = null
let audioPlayer: WechatMiniprogram.InnerAudioContext | null = null
let holdingVoice = false

export function ensureRecorder(page: VoicePage) {
  if (recorder) return
  recorder = wx.getRecorderManager()
  recorder.onStop((res) => { const pages = getCurrentPages(); const current = pages[pages.length - 1] as { handleRecordStop?: (result: { tempFilePath?: string; duration?: number }) => void }; if (current && current.handleRecordStop) current.handleRecordStop(res) })
  recorder.onError(() => { holdingVoice = false; page.setData({ recording: false }); wx.showToast({ title: '录音失败，电脑端可能不支持', icon: 'none' }) })
}

export function stopRecording(page: VoicePage) { holdingVoice = false; if (recorder && page.data.recording) { try { recorder.stop() } catch (err) { /* platform may already be stopped */ } } if (page.data.recording) page.setData({ recording: false }) }

export function startRecording(page: VoicePage) {
  if (!page.data.voiceMode || page.data.sending) return
  holdingVoice = true; ensureRecorder(page)
  if (!recorder) { holdingVoice = false; wx.showToast({ title: '无法开始录音', icon: 'none' }); return }
  page.setData({ recording: true })
  try { recorder.start({ duration: 60000, format: 'mp3', sampleRate: 16000, numberOfChannels: 1, encodeBitRate: 48000 }) } catch (err) { holdingVoice = false; page.setData({ recording: false }); wx.showToast({ title: '无法开始录音', icon: 'none' }) }
}

export function endRecording(page: VoicePage) { if (!page.data.voiceMode || !recorder || !holdingVoice) return; try { recorder.stop() } catch (err) { page.setData({ recording: false }) } }

export function handleRecordStop(page: VoicePage, result: { tempFilePath?: string; duration?: number }) {
  const wasHolding = holdingVoice; holdingVoice = false; page.setData({ recording: false }); if (!wasHolding) return
  const duration = Math.max(0, Math.round((result.duration || 0) / 1000)); if (duration < 1 || !result.tempFilePath) { wx.showToast({ title: '说话时间太短', icon: 'none' }); return }
  const id = page.data.id; if (!id || page.data.sending) return; page.setData({ sending: true })
  uploadCommentVoice(result.tempFilePath).then((audio_url) => createComment(id, { body: '', parent_id: page.data.replyParentId || null, sticker_ids: [], image_urls: [], audio_url, audio_duration: Math.min(60, duration) })).then(() => { page.resetComposer(); page.reload() }).catch((err) => { page.setData({ sending: false }); toastRequestError(err) })
}

export function playComment(page: VoicePage, event: WechatMiniprogram.CustomEvent<{ id: string; url: string }>) {
  const id = event.detail.id; const url = event.detail.url; if (!url) return
  let already = false; const scan = (list: CommentView[]) => list.forEach((item) => { if (item.id === id && item.playing) already = true; scan(item.replies) }); scan(page.data.comments)
  if (!audioPlayer) { audioPlayer = wx.createInnerAudioContext(); audioPlayer.onEnded(() => page.setData({ comments: patchPlaying(page.data.comments, '') })); audioPlayer.onError(() => { wx.showToast({ title: '语音无法播放', icon: 'none' }); page.setData({ comments: patchPlaying(page.data.comments, '') }) }) }
  if (already) { audioPlayer.stop(); page.setData({ comments: patchPlaying(page.data.comments, '') }); return }
  audioPlayer.stop(); audioPlayer.src = url; audioPlayer.play(); page.setData({ comments: patchPlaying(page.data.comments, id) })
}

export function disposeVoice() { holdingVoice = false; if (recorder) { try { recorder.stop() } catch (err) { /* noop */ } } if (audioPlayer) { audioPlayer.stop(); audioPlayer.destroy(); audioPlayer = null } recorder = null }
