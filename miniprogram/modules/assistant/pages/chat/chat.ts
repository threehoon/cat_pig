import { toastRequestError } from '../../../../core/request'
import { askAssistant, listMessages, listSuggestions } from '../../services/assistant'
import { takeOpenConversation } from '../../services/open-conversation'
import {
  AssistantCitation,
  AssistantMessage,
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

const MESSAGE_PAGE = 50

function sourceLabel(source: AssistantSource): string {
  if (source === 'knowledge') {
    return '说明书'
  }
  if (source === 'search') {
    return '检索'
  }
  return ''
}

function bubbleSource(message: AssistantMessage): '' | AssistantSource {
  if (message.role !== 'assistant' || !message.source) {
    return ''
  }
  return message.source
}

function toBubble(message: AssistantMessage): ChatBubble {
  const source = bubbleSource(message)
  return {
    id: message.id,
    anchor: `m-${message.id}`,
    role: message.role,
    text: message.text,
    source,
    sourceLabel: source ? sourceLabel(source) : '',
    citations: message.citations,
    related_posts: [],
  }
}

function loadThread(id: string, page: number, collected: AssistantMessage[]): Promise<AssistantMessage[]> {
  return listMessages(id, page, MESSAGE_PAGE).then((result) => {
    const items = collected.concat(result.items)
    if (result.items.length === 0 || items.length >= result.total) {
      return items
    }
    return loadThread(id, page + 1, items)
  })
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
    epoch: 0,
    scrollInto: '',
  },
  onLoad() {
    listSuggestions()
      .then((result) => {
        this.setData({ suggestions: result.items })
      })
      .catch(toastRequestError)
  },
  onShow() {
    const pending = takeOpenConversation()
    if (!pending) {
      return
    }
    this.openConversation(pending)
  },
  openConversation(id: string) {
    const epoch = this.data.epoch + 1
    this.setData({
      epoch,
      sending: false,
      conversationId: id,
      messages: [],
      scrollInto: '',
    })
    loadThread(id, 1, [])
      .then((items) => {
        if (this.data.epoch !== epoch) {
          return
        }
        const messages = items.map((item) => toBubble(item))
        const last = messages[messages.length - 1]
        this.setData({
          messages,
          scrollInto: last ? last.anchor : '',
        })
      })
      .catch((err: unknown) => {
        if (this.data.epoch !== epoch) {
          return
        }
        this.setData({ conversationId: null })
        toastRequestError(err)
      })
  },
  onHistory() {
    wx.navigateTo({ url: '/modules/assistant/pages/history/history' })
  },
  onNew() {
    this.setData({
      epoch: this.data.epoch + 1,
      messages: [],
      conversationId: null,
      draft: '',
      sending: false,
      scrollInto: '',
      inputFocus: false,
    })
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
    const epoch = this.data.epoch
    const sentId = this.data.conversationId
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
      scrollInto: 'm-pending',
    })
    askAssistant(question, sentId)
      .then((ask) => {
        if (this.data.epoch !== epoch) {
          return
        }
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
        if (this.data.epoch !== epoch) {
          return
        }
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
