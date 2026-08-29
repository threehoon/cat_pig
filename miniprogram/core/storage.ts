export function get<T>(key: string): T | null {
  const value = wx.getStorageSync(key) as T | '' | undefined
  if (value === '' || value === undefined || value === null) {
    return null
  }
  return value
}

export function set(key: string, value: unknown): void {
  wx.setStorageSync(key, value)
}

export function remove(key: string): void {
  wx.removeStorageSync(key)
}
