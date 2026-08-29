import { getToken } from './session'
import { config } from './config'
import { handleMock } from './mock'

export type ListResult<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

export type RequestMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE'

export type RequestOptions = {
  method: RequestMethod
  path: string
  data?: object
  query?: Record<string, string | number | boolean | undefined>
}

export type RequestError = {
  code: string
  message: string
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const base = `${config.apiBaseUrl}${path}`
  if (!query) {
    return base
  }
  const parts: string[] = []
  Object.keys(query).forEach((key) => {
    const value = query[key]
    if (value === undefined) {
      return
    }
    parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
  })
  if (parts.length === 0) {
    return base
  }
  return `${base}?${parts.join('&')}`
}

function rejectError(code: string, message: string): Promise<never> {
  const error: RequestError = { code, message }
  return Promise.reject(error)
}

export function toastRequestError(err: unknown): void {
  const error = err as RequestError
  wx.showToast({ title: error.message || error.code || '失败', icon: 'none' })
}

export function request<T>(options: RequestOptions): Promise<T> {
  if (config.useMock) {
    const result = handleMock(options)
    if (result.error) {
      return rejectError(result.error.code, result.error.message)
    }
    return Promise.resolve(result.data as T)
  }

  const token = getToken()
  const header: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    header.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: buildUrl(options.path, options.query),
      method: options.method as WechatMiniprogram.RequestOption['method'],
      data: options.data,
      header,
      success(res) {
        const body = res.data as { data?: T; error?: RequestError }
        if (body && body.error) {
          reject({ code: body.error.code, message: body.error.message })
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve((body && body.data) as T)
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
