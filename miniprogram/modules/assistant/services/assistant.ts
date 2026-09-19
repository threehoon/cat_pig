import { ListResult, request } from '../../../core/request'
import { AssistantAsk, AssistantSuggestion } from '../types/assistant'

export function listSuggestions(page = 1, pageSize = 20) {
  return request<ListResult<AssistantSuggestion>>({
    method: 'GET',
    path: '/api/v1/assistant/suggestion',
    query: { page, page_size: pageSize },
  })
}

export function askAssistant(question: string, conversationId: string | null) {
  return request<AssistantAsk>({
    method: 'POST',
    path: '/api/v1/assistant/ask',
    data: { question, conversation_id: conversationId },
  })
}
