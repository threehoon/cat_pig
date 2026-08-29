import { config } from './config'
import { handleMock } from './mock'
import { request } from './request'
import { clearSession, getToken, getUserId, setToken, setUserId } from './session'

export { getToken, getUserId, setToken, setUserId }

export function clearToken(): void {
  clearSession()
}

function bootstrapMockSession(): void {
  if (getToken() && getUserId()) {
    return
  }
  const loginRes = handleMock({ method: 'POST', path: '/api/v1/auth/login', data: { code: 'mock' } })
  if (loginRes.data) {
    setToken((loginRes.data as { token: string }).token)
  }
  const meRes = handleMock({ method: 'GET', path: '/api/v1/me' })
  if (meRes.data) {
    setUserId((meRes.data as { id: string }).id)
  }
}

export function login(): Promise<void> {
  if (getToken() && getUserId()) {
    return Promise.resolve()
  }
  if (config.useMock) {
    bootstrapMockSession()
    return Promise.resolve()
  }
  const send = (code: string) =>
    request<{ token: string; expires_in: number }>({
      method: 'POST',
      path: '/api/v1/auth/login',
      data: { code },
    })
      .then((data) => {
        setToken(data.token)
        return request<{ id: string }>({
          method: 'GET',
          path: '/api/v1/me',
        })
      })
      .then((me) => {
        setUserId(me.id)
      })
  return new Promise((resolve, reject) => {
    wx.login({
      success(res) {
        send(res.code).then(resolve).catch(reject)
      },
      fail() {
        reject({ code: 'WECHAT_LOGIN_FAILED', message: '微信登录失败' })
      },
    })
  })
}
