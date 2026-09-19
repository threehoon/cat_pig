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
