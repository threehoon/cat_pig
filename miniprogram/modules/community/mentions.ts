export type MentionPart = {
  key: string
  text: string
  mention: boolean
}

export type MentionSpan = {
  start: number
  end: number
  name: string
}

function uniqueNames(names: string[]): string[] {
  const seen: Record<string, boolean> = {}
  const list: string[] = []
  names.forEach((name) => {
    const trimmed = name.trim()
    if (!trimmed || seen[trimmed]) {
      return
    }
    seen[trimmed] = true
    list.push(trimmed)
  })
  return list.sort((a, b) => b.length - a.length)
}

export function mentionSpans(text: string, names: string[]): MentionSpan[] {
  const sorted = uniqueNames(names)
  const spans: MentionSpan[] = []
  let index = 0
  while (index < text.length) {
    if (text.charAt(index) === '@') {
      let matched: MentionSpan | null = null
      for (let i = 0; i < sorted.length; i += 1) {
        const name = sorted[i]
        const token = `@${name}`
        if (text.indexOf(token, index) !== index) {
          continue
        }
        const after = index + token.length
        const nextChar = after < text.length ? text.charAt(after) : ''
        if (nextChar && nextChar !== ' ' && nextChar !== '，' && nextChar !== ',' && nextChar !== '。') {
          continue
        }
        const end = nextChar === ' ' ? after + 1 : after
        matched = { start: index, end, name }
        break
      }
      if (matched) {
        spans.push(matched)
        index = matched.end
        continue
      }
    }
    index += 1
  }
  return spans
}

export function mentionParts(text: string, names: string[]): MentionPart[] {
  if (!text) {
    return []
  }
  const spans = mentionSpans(text, names)
  if (!spans.length) {
    return [{ key: '0', text, mention: false }]
  }
  const parts: MentionPart[] = []
  let cursor = 0
  spans.forEach((span, order) => {
    if (span.start > cursor) {
      parts.push({
        key: `t-${order}-${cursor}`,
        text: text.slice(cursor, span.start),
        mention: false,
      })
    }
    parts.push({
      key: `m-${order}-${span.start}`,
      text: text.slice(span.start, span.end),
      mention: true,
    })
    cursor = span.end
  })
  if (cursor < text.length) {
    parts.push({
      key: `t-end-${cursor}`,
      text: text.slice(cursor),
      mention: false,
    })
  }
  return parts
}

export function applyMentionDelete(
  prev: string,
  next: string,
  cursor: number,
  names: string[],
): { value: string; cursor: number } {
  if (next.length >= prev.length) {
    return { value: next, cursor }
  }
  const delLen = prev.length - next.length
  const delStart = cursor
  const delEnd = cursor + delLen
  const hit = mentionSpans(prev, names).find((span) => delStart < span.end && delEnd > span.start)
  if (!hit) {
    return { value: next, cursor }
  }
  return {
    value: prev.slice(0, hit.start) + prev.slice(hit.end),
    cursor: hit.start,
  }
}

export function insertMention(body: string, name: string, maxLen = 200): { value: string; cursor: number } {
  const prefix = body && !/\s$/.test(body) ? ' ' : ''
  const token = `${prefix}@${name} `
  const value = `${body}${token}`.slice(0, maxLen)
  return { value, cursor: value.length }
}
