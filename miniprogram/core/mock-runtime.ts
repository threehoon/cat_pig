export type MockQuery = Record<string, string | number | boolean | undefined>

export type MockOptions = {
  method: string
  path: string
  data?: object
  query?: MockQuery
}

export type MockError = { code: string; message: string }
export type Params = Record<string, string>
export type MockHandler = (params: Params, options: MockOptions) => unknown
export type MockRoute = { method: string; pattern: string; handle: MockHandler }

export function fail(code: string, message: string): never {
  const error: MockError = { code, message }
  throw error
}

export function isMockError(value: unknown): value is MockError {
  return (
    typeof value === 'object' &&
    value !== null &&
    'code' in value &&
    'message' in value &&
    typeof value.code === 'string' &&
    typeof value.message === 'string'
  )
}

export function copy<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export function nowIso(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
}

export function todayDate(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function newId(): string {
  const hex = () => Math.floor((1 + Math.random()) * 0x10000).toString(16).slice(1)
  return `${hex()}${hex()}-${hex()}-${hex()}-${hex()}-${hex()}${hex()}${hex()}`
}

export function queryValue(query: MockQuery | undefined, key: string): string | undefined {
  const value = query && query[key]
  return value === undefined || value === '' ? undefined : String(value)
}

export function queryPage(query: MockQuery | undefined): { page: number; page_size: number } {
  const page = Number(queryValue(query, 'page') || 1)
  const page_size = Number(queryValue(query, 'page_size') || 20)
  return {
    page: Number.isFinite(page) && page > 0 ? page : 1,
    page_size: Number.isFinite(page_size) && page_size > 0 ? page_size : 20,
  }
}

export function paginate<T>(items: T[], query: MockQuery | undefined) {
  const { page, page_size } = queryPage(query)
  const start = (page - 1) * page_size
  return { items: items.slice(start, start + page_size), total: items.length, page, page_size }
}

export function sortByCreated<T extends { created_at: string }>(items: T[]): T[] {
  return items.slice().sort((a, b) => (a.created_at < b.created_at ? 1 : a.created_at > b.created_at ? -1 : 0))
}

export function bodyOf(options: MockOptions): Record<string, unknown> {
  return (options.data || {}) as Record<string, unknown>
}

export function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)) : []
}

export function matchPath(pattern: string, path: string): Params | null {
  const patternParts = pattern.split('/').filter(Boolean)
  const pathParts = path.split('/').filter(Boolean)
  if (patternParts.length !== pathParts.length) return null
  const params: Params = {}
  for (let i = 0; i < patternParts.length; i += 1) {
    const token = patternParts[i]
    if (token.startsWith('{') && token.endsWith('}')) {
      params[token.slice(1, -1)] = decodeURIComponent(pathParts[i])
    } else if (token !== pathParts[i]) {
      return null
    }
  }
  return params
}
