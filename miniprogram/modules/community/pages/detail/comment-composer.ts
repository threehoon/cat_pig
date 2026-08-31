import { applyMentionDelete, insertMention } from '../../mentions'
import { CommentWrite } from '../../types/post'
import { uploadCommentImages } from './detail-media'

export type ComposerState = {
  id: string
  commentBody: string
  commentFocus: boolean
  emojiOpen: boolean
  mentionOpen: boolean
  voiceMode: boolean
  recording: boolean
  replyParentId: string
  replyToName: string
  commentPlaceholder: string
  draftImages: string[]
  composerCursor: number
  canSend: boolean
  sending: boolean
}

export type ComposerPatch = Partial<ComposerState> & { scrollInto?: string }

export function focusComposerPatches(): { blur: ComposerPatch; focus: ComposerPatch } {
  return {
    blur: {
      commentFocus: false,
      emojiOpen: false,
      mentionOpen: false,
      voiceMode: false,
    },
    focus: {
      commentFocus: true,
      scrollInto: 'comments',
    },
  }
}

export function composerFocusPatch(): ComposerPatch {
  return {
    commentFocus: true,
    emojiOpen: false,
    mentionOpen: false,
    voiceMode: false,
  }
}

export function composerBlurPatch(): ComposerPatch {
  return { commentFocus: false }
}

export function replyToPatch(id: string, name: string): ComposerPatch {
  const replyToName = name || '用户'
  return {
    replyParentId: id,
    replyToName,
    commentPlaceholder: `评论 ${replyToName}`,
  }
}

export function clearReplyPatch(): ComposerPatch {
  return {
    replyParentId: '',
    replyToName: '',
    commentPlaceholder: '写一条评论',
    commentFocus: false,
    emojiOpen: false,
    mentionOpen: false,
    voiceMode: false,
    recording: false,
  }
}

export function setBodyPatch(value: string, cursor?: number): ComposerPatch {
  const patch: ComposerPatch = { commentBody: value }
  if (cursor !== undefined) {
    patch.composerCursor = cursor
  }
  return patch
}

export function inputBodyValue(
  current: string,
  value: string,
  cursor: number,
  names: string[],
): { value: string; cursor?: number } {
  const patched = applyMentionDelete(current, value, cursor, names)
  return {
    value: patched.value,
    cursor: patched.value === value ? undefined : patched.cursor,
  }
}

export function toggleEmojiPatch(state: ComposerState): ComposerPatch {
  return {
    emojiOpen: !state.emojiOpen,
    mentionOpen: false,
    voiceMode: false,
    commentFocus: false,
  }
}

export function toggleMentionPatch(state: ComposerState): ComposerPatch {
  return {
    mentionOpen: !state.mentionOpen,
    emojiOpen: false,
    voiceMode: false,
    commentFocus: false,
  }
}

export function pickMentionPatch(state: ComposerState, name: string): ComposerPatch {
  const inserted = insertMention(state.commentBody, name || '用户')
  return {
    commentBody: inserted.value,
    composerCursor: inserted.cursor,
    mentionOpen: false,
    voiceMode: false,
    commentFocus: true,
  }
}

export function toggleVoicePatch(state: ComposerState): {
  patch: ComposerPatch
  shouldStopRecording: boolean
} {
  const voiceMode = !state.voiceMode
  return {
    patch: {
      voiceMode,
      emojiOpen: false,
      mentionOpen: false,
      commentFocus: false,
    },
    shouldStopRecording: !voiceMode,
  }
}

export function appendEmoji(body: string, emoji: string): { value: string; cursor: number } | null {
  if (!emoji) {
    return null
  }
  const value = `${body}${emoji}`.slice(0, 200)
  return { value, cursor: value.length }
}

export function removeImage(images: string[], index: number): string[] {
  const next = images.slice()
  next.splice(index, 1)
  return next
}

export function canSendComment(state: Pick<ComposerState, 'commentBody' | 'draftImages'>): boolean {
  return !!(state.commentBody.trim() || state.draftImages.length)
}

export function commentPayload(state: ComposerState): CommentWrite | null {
  if (state.voiceMode || !state.id || state.sending) {
    return null
  }
  const body = state.commentBody.trim()
  const image_urls = state.draftImages.slice()
  if (!body && !image_urls.length) {
    return null
  }
  return {
    body,
    parent_id: state.replyParentId || null,
    sticker_ids: [],
    image_urls,
    audio_url: null,
    audio_duration: 0,
  }
}

export function uploadImages(limit: number): Promise<string[]> {
  return uploadCommentImages(limit)
}
