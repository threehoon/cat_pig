import { mockPhotos } from '../../../assets/paths'
import { bodyOf, type MockRoute } from '../../../core/mock-runtime'

export const mediaMockRoutes: MockRoute[] = [
  {
    method: 'POST', pattern: '/api/v1/media', handle: (_params, options) => {
      const file = bodyOf(options).file
      return { url: typeof file === 'string' && file ? file : mockPhotos.pet1, width: 800, height: 600, mime: 'image/jpeg' }
    },
  },
]
