import { bodyOf, fail, newId, paginate, type MockRoute } from '../../../core/mock-runtime'
import { store } from '../../../mocks/store'
import { AssistantAsk, AssistantRelatedPost, AssistantSource } from '../types/assistant'
import {
  GENERATED_ANSWER,
  KNOWLEDGE,
  KnowledgeEntry,
  REFUSE_ANSWER,
  REFUSE_WORDS,
  SEARCH_ANSWER,
  SEARCH_WORDS,
  SKY_ANSWER,
  SKY_WORDS,
  SUGGESTIONS,
  citationOf,
} from './mock-knowledge'

function hasAny(text: string, words: string[]): boolean {
  let i = 0
  while (i < words.length) {
    if (text.indexOf(words[i]) !== -1) {
      return true
    }
    i += 1
  }
  return false
}

function matchKnowledge(text: string): KnowledgeEntry | null {
  let i = 0
  while (i < KNOWLEDGE.length) {
    const entry = KNOWLEDGE[i]
    if (hasAny(text, entry.keywords)) {
      return entry
    }
    i += 1
  }
  return null
}

const RELATED_WORDS = ['降温', '夏天', '医院', '疫苗', '公园', '午睡', '沙发', '图生视频', '散步']

function isRelatedPost(question: string, title: string, body: string): boolean {
  const hay = `${title}${body}`
  if (!question || !hay) {
    return false
  }
  if (question.indexOf('狗') !== -1 && hay.indexOf('狗') !== -1) {
    return true
  }
  if (question.indexOf('猫') !== -1 && hay.indexOf('猫') !== -1) {
    return true
  }
  let i = 0
  while (i < RELATED_WORDS.length) {
    const word = RELATED_WORDS[i]
    if (question.indexOf(word) !== -1 && hay.indexOf(word) !== -1) {
      return true
    }
    i += 1
  }
  return false
}

function relatedPosts(question: string): AssistantRelatedPost[] {
  const items: AssistantRelatedPost[] = []
  let i = 0
  while (i < store.posts.length && items.length < 2) {
    const post = store.posts[i]
    if (post.status === 'published' && isRelatedPost(question, post.title, post.body)) {
      const cover = post.image_urls.length > 0 ? post.image_urls[0] : null
      items.push({
        id: post.id,
        title: post.title,
        body: post.body,
        cover_url: cover,
      })
    }
    i += 1
  }
  return items
}

function conversationIdOf(value: unknown): string {
  if (typeof value === 'string' && value.trim()) {
    return value.trim()
  }
  return newId()
}

function buildAsk(question: string, conversationId: string): AssistantAsk {
  if (hasAny(question, REFUSE_WORDS)) {
    return {
      conversation_id: conversationId,
      answer: REFUSE_ANSWER,
      source: 'generated',
      citations: [],
      related_posts: relatedPosts(question),
    }
  }
  const hit = matchKnowledge(question)
  if (hit) {
    return {
      conversation_id: conversationId,
      answer: hit.answer,
      source: 'knowledge',
      citations: [citationOf(hit)],
      related_posts: relatedPosts(question),
    }
  }
  let source: AssistantSource = 'generated'
  let answer = GENERATED_ANSWER
  if (hasAny(question, SEARCH_WORDS)) {
    source = 'search'
    answer = SEARCH_ANSWER
  } else if (hasAny(question, SKY_WORDS)) {
    answer = SKY_ANSWER
  }
  return {
    conversation_id: conversationId,
    answer,
    source,
    citations: [],
    related_posts: relatedPosts(question),
  }
}

export const assistantMockRoutes: MockRoute[] = [
  {
    method: 'GET',
    pattern: '/api/v1/assistant/suggestion',
    handle: (_params, options) => paginate(SUGGESTIONS, options.query),
  },
  {
    method: 'POST',
    pattern: '/api/v1/assistant/ask',
    handle: (_params, options) => {
      const body = bodyOf(options)
      const raw = body.question
      if (typeof raw !== 'string' || !raw.trim()) {
        fail('VALIDATION', '请输入问题')
      }
      return buildAsk(raw.trim(), conversationIdOf(body.conversation_id))
    },
  },
]
