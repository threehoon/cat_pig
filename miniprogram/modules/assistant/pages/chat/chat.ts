import { toastRequestError } from '../../../../core/request'
import { askAssistant, listSuggestions } from '../../services/assistant'
import {
  AssistantCitation,
  AssistantRelatedPost,
  AssistantSource,
  AssistantSuggestion,
} from '../../types/assistant'

type ChatBubble = {
  id: string
  anchor: string
  role: 'user' | 'assistant'
  text: string
  source: '' | AssistantSource
  sourceLabel: string
  citations: AssistantCitation[]
  related_posts: AssistantRelatedPost[]
}

function takeTwo<T>(items: T[]): T[] {
  const out: T[] = []
  let i = 0
  while (i < items.length && out.length < 2) {
    out.push(items[i])
    i += 1
  }
  return out
}

function sourceLabel(source: AssistantSource): string {
  if (source === 'knowledge') {
    return '说明书'
  }
  if (source === 'search') {
    return '检索'
  }
  return '仅供参考'
}

Page({
  data: {
    suggestions: [] as AssistantSuggestion[],
    messages: [] as ChatBubble[],
    draft: '',
    inputFocus: false,
    conversationId: null as string | null,
    sending: false,
    seq: 0,
    scrollInto: '',
  },
  onLoad() {
    listSuggestions()
      .then((result) => {
        this.setData({ suggestions: result.items })
      })
      .catch(toastRequestError)
  },
  onInput(e: WechatMiniprogram.Input) {
    this.setData({ draft: e.detail.value })
  },
  onSuggest(e: WechatMiniprogram.TouchEvent) {
    const question = e.currentTarget.dataset.question as string
    if (!question) {
      return
    }
    this.setData({ draft: question, inputFocus: false }, () => {
      this.setData({ inputFocus: true })
    })
  },
  onInputBlur() {
    this.setData({ inputFocus: false })
  },
  onSend() {
    this.sendQuestion(this.data.draft)
  },
  sendQuestion(raw: string) {
    const question = raw.trim()
    if (!question) {
      wx.showToast({ title: '请输入问题', icon: 'none' })
      return
    }
    if (this.data.sending) {
      return
    }
    const seq = this.data.seq + 1
    const userId = `u${seq}`
    const user: ChatBubble = {
      id: userId,
      anchor: `m-${userId}`,
      role: 'user',
      text: question,
      source: '',
      sourceLabel: '',
      citations: [],
      related_posts: [],
    }
    this.setData({
      sending: true,
      draft: '',
      inputFocus: false,
      seq,
      messages: this.data.messages.concat([user]),
      scrollInto: `m-${userId}`,
    })
    askAssistant(question, this.data.conversationId)
      .then((ask) => {
        const next = this.data.seq + 1
        const aid = `a${next}`
        const assistant: ChatBubble = {
          id: aid,
          anchor: `m-${aid}`,
          role: 'assistant',
          text: ask.answer,
          source: ask.source,
          sourceLabel: sourceLabel(ask.source),
          citations: ask.citations,
          related_posts: takeTwo(ask.related_posts),
        }
        this.setData({
          sending: false,
          seq: next,
          conversationId: ask.conversation_id,
          messages: this.data.messages.concat([assistant]),
          scrollInto: `m-${aid}`,
        })
      })
      .catch((err: unknown) => {
        this.setData({ sending: false })
        toastRequestError(err)
      })
  },
  onRelated(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as string
    if (!id) {
      return
    }
    wx.navigateTo({ url: `/modules/community/pages/detail/detail?id=${encodeURIComponent(id)}` })
  },
})
