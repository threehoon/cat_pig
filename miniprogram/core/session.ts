import { get, remove, set } from './storage'

const TOKEN_KEY = 'auth_token'
const USER_ID_KEY = 'auth_user_id'

export function getToken(): string | null {
  const token = get<string>(TOKEN_KEY)
  return token ? token : null
}

export function setToken(token: string): void {
  set(TOKEN_KEY, token)
}

export function getUserId(): string | null {
  const id = get<string>(USER_ID_KEY)
  return id ? id : null
}

export function setUserId(id: string): void {
  set(USER_ID_KEY, id)
}

export function clearSession(): void {
  remove(TOKEN_KEY)
  remove(USER_ID_KEY)
}
