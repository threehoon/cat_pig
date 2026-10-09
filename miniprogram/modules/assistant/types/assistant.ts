export type AssistantSource = 'knowledge' | 'search' | 'generated'

export type AssistantSuggestion = {
  id: string
  question: string
}

export type AssistantCitation = {
  id: string
  title: string
  snippet: string
}

export type AssistantRelatedPost = {
  id: string
  title: string
  body: string
  cover_url: string | null
}

export type AssistantAsk = {
  conversation_id: string
  answer: string
  source: AssistantSource
  citations: AssistantCitation[]
  related_posts: AssistantRelatedPost[]
}

export type AssistantConversation = {
  id: string
  title: string
  updated_at: string
}

export type AssistantMessage = {
  id: string
  role: 'user' | 'assistant'
  text: string
  source: AssistantSource | null
  citations: AssistantCitation[]
}
