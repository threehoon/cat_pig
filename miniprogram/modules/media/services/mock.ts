import { mockPhotos } from '../../../assets/paths'
import { bodyOf, type MockRoute } from '../../../core/mock-runtime'

function isAudioPath(path: string): boolean {
  const lower = path.toLowerCase()
  const q = lower.indexOf('?')
  const clean = q === -1 ? lower : lower.slice(0, q)
  return (
    clean.indexOf('.mp3') !== -1 ||
    clean.indexOf('.m4a') !== -1 ||
    clean.indexOf('.aac') !== -1 ||
    clean.indexOf('.wav') !== -1 ||
    clean.indexOf('.silk') !== -1
  )
}

export const mediaMockRoutes: MockRoute[] = [
  {
    method: 'POST',
    pattern: '/api/v1/media',
    handle: (_params, options) => {
      const file = bodyOf(options).file
      const url = typeof file === 'string' && file ? file : mockPhotos.pet1
      if (isAudioPath(url)) {
        return { url, width: 0, height: 0, mime: 'audio/mpeg' }
      }
      return { url, width: 800, height: 600, mime: 'image/jpeg' }
    },
  },
]
