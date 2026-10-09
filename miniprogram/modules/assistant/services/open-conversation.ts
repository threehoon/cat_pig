import { get, remove, set } from '../../../core/storage'

const OPEN_KEY = 'assistant_open_conversation'

export function stageOpenConversation(id: string): void {
  set(OPEN_KEY, id)
}

export function takeOpenConversation(): string | null {
  const id = get<string>(OPEN_KEY)
  if (!id) {
    return null
  }
  remove(OPEN_KEY)
  return id
}