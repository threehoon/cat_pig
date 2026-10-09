import { config } from './config'
import { get, remove, set } from './storage'

const LIVE_TOKEN_KEY = 'assistant_live_token'
const LOGIN_CODE = 'xiaox-devtools'

const ASSISTANT_LIVE = [
  { method: 'GET', path: '/api/v1/assistant/suggestion' },
  { method: 'POST', path: '/api/v1/assistant/ask' },
]

const CONVERSATION_LIST = '/api/v1/assistant/conversation'
const MESSAGE_PREFIX = '/api/v1/assistant/conversation/'
const MESSAGE_SUFFIX = '/message'

type LoginBody = {
  data?: { token?: string }
  error?: { code: string; message: string }
}

function isConversationMessagePath(path: string): boolean {
  if (path.indexOf(MESSAGE_PREFIX) !== 0) {
    return false
  }
  if (path.slice(-MESSAGE_SUFFIX.length) !== MESSAGE_SUFFIX) {
    return false
  }
  const middle = path.slice(MESSAGE_PREFIX.length, path.length - MESSAGE_SUFFIX.length)
  if (!middle || middle.indexOf('/') !== -1) {
    return false
  }
  return true
}

export function isAssistantLivePath(method: string, path: string): boolean {
  if (method === 'GET' && path === CONVERSATION_LIST) {
    return true
  }
  if (method === 'GET' && isConversationMessagePath(path)) {
    return true
  }
  let i = 0
  while (i < ASSISTANT_LIVE.length) {
    const item = ASSISTANT_LIVE[i]
    if (item.method === method && item.path === path) {
      return true
    }
    i += 1
  }
  return false
}

export function clearLiveToken(): void {
  remove(LIVE_TOKEN_KEY)
}

export function ensureLiveToken(): Promise<string> {
  const existing = get<string>(LIVE_TOKEN_KEY)
  if (existing) {
    return Promise.resolve(existing)
  }
  return loginLive()
}

function loginLive(): Promise<string> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${config.apiBaseUrl}/api/v1/auth/login`,
      method: 'POST',
      data: { code: LOGIN_CODE },
      header: { 'Content-Type': 'application/json' },
      success(res) {
        const body = res.data as LoginBody
        if (body && body.error) {
          reject({ code: body.error.code, message: body.error.message })
          return
        }
        const token = body && body.data && body.data.token
        if (res.statusCode >= 200 && res.statusCode < 300 && token) {
          set(LIVE_TOKEN_KEY, token)
          resolve(token)
          return
        }
        reject({ code: 'INTERNAL', message: `HTTP ${res.statusCode}` })
      },
      fail() {
        reject({ code: 'INTERNAL', message: 'NETWORK' })
      },
    })
  })
}
