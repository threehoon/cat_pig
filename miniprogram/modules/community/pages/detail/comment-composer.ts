import { toastRequestError } from '../../../../core/request'
import { applyMentionDelete, insertMention } from '../../mentions'
import { createComment } from '../../services/community'
import { uploadCommentImages } from './detail-media'

type ComposerData = {
  id: string; commentBody: string; commentFocus: boolean; emojiOpen: boolean; mentionOpen: boolean; voiceMode: boolean
  replyParentId: string; replyToName: string; commentPlaceholder: string; draftImages: string[]; composerCursor: number; canSend: boolean; sending: boolean
}
type ComposerPage = { data: ComposerData; setData: (data: Record<string, unknown>, callback?: () => void) => void; clearBlurTimer: () => void; stopRecording: () => void; syncComposer: () => void; resetComposer: () => void; reload: () => void; mentionNames: () => string[] }

export function focusComposer(page: ComposerPage) { page.clearBlurTimer(); page.setData({ commentFocus: false, emojiOpen: false, mentionOpen: false, voiceMode: false }, () => page.setData({ commentFocus: true, scrollInto: 'comments' }, () => page.syncComposer())) }
export function composerFocus(page: ComposerPage) { page.clearBlurTimer(); page.setData({ commentFocus: true, emojiOpen: false, mentionOpen: false, voiceMode: false }, () => page.syncComposer()) }
export function composerBlur(page: ComposerPage, schedule: (callback: () => void, ms: number) => void) { page.clearBlurTimer(); schedule(() => page.setData({ commentFocus: false }, () => page.syncComposer()), 120) }
export function replyTo(page: ComposerPage, id: string, name: string) { page.setData({ replyParentId: id, replyToName: name || '用户', commentPlaceholder: `评论 ${name || '用户'}` }); focusComposer(page) }
export function clearReply(page: ComposerPage) { page.clearBlurTimer(); page.setData({ replyParentId: '', replyToName: '', commentPlaceholder: '写一条评论', commentFocus: false, emojiOpen: false, mentionOpen: false, voiceMode: false, recording: false }, () => page.syncComposer()) }
export function setBody(page: ComposerPage, value: string, cursor?: number) { const data: Record<string, unknown> = { commentBody: value }; if (cursor !== undefined) data.composerCursor = cursor; page.setData(data, () => { if (cursor !== undefined) page.setData({ composerCursor: -1 }); page.syncComposer() }) }
export function inputBody(page: ComposerPage, value: string, cursor: number) { const patched = applyMentionDelete(page.data.commentBody, value, cursor, page.mentionNames()); setBody(page, patched.value, patched.value === value ? undefined : patched.cursor) }
export function toggleEmoji(page: ComposerPage) { page.clearBlurTimer(); page.setData({ emojiOpen: !page.data.emojiOpen, mentionOpen: false, voiceMode: false, commentFocus: false }, () => page.syncComposer()) }
export function toggleMention(page: ComposerPage) { page.clearBlurTimer(); page.setData({ mentionOpen: !page.data.mentionOpen, emojiOpen: false, voiceMode: false, commentFocus: false }) }
export function pickMention(page: ComposerPage, name: string) { const inserted = insertMention(page.data.commentBody, name || '用户'); page.setData({ commentBody: inserted.value, composerCursor: inserted.cursor, mentionOpen: false, voiceMode: false, commentFocus: true }, () => page.syncComposer()) }
export function toggleVoice(page: ComposerPage) { page.clearBlurTimer(); const open = !page.data.voiceMode; if (!open) page.stopRecording(); page.setData({ voiceMode: open, emojiOpen: false, mentionOpen: false, commentFocus: false }) }
export function pickEmoji(page: ComposerPage, emoji: string) { if (!emoji) return; const next = `${page.data.commentBody}${emoji}`.slice(0, 200); setBody(page, next, next.length) }
export function pickImages(page: ComposerPage) { page.clearBlurTimer(); const remain = 9 - page.data.draftImages.length; if (remain <= 0) { wx.showToast({ title: '图片最多 9 张', icon: 'none' }); return } page.setData({ emojiOpen: false, mentionOpen: false, voiceMode: false }); uploadCommentImages(remain).then((urls) => { if (urls.length) page.setData({ draftImages: page.data.draftImages.concat(urls) }, () => page.syncComposer()) }).catch(toastRequestError) }
export function removeImage(page: ComposerPage, index: number) { const draftImages = page.data.draftImages.slice(); draftImages.splice(index, 1); page.setData({ draftImages }, () => page.syncComposer()) }
export function sendComment(page: ComposerPage) { if (page.data.voiceMode) return; const id = page.data.id; const body = page.data.commentBody.trim(); const image_urls = page.data.draftImages.slice(); if (!id || page.data.sending || (!body && !image_urls.length)) return; page.setData({ sending: true }); createComment(id, { body, parent_id: page.data.replyParentId || null, sticker_ids: [], image_urls, audio_url: null, audio_duration: 0 }).then(() => { page.resetComposer(); page.reload() }).catch((err) => { page.setData({ sending: false }); toastRequestError(err) }) }
