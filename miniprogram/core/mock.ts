import { albumMockRoutes } from '../modules/album/services/mock'
import { authMockRoutes } from '../modules/auth/services/mock'
import { communityMockRoutes } from '../modules/community/services/mock'
import { mediaMockRoutes } from '../modules/media/services/mock'
import { meMockRoutes } from '../modules/me/services/mock'
import { pointsMockRoutes } from '../modules/points/services/mock'
import { videoMockRoutes } from '../modules/video/services/mock'
import { isMockError, matchPath, type MockOptions, type MockRoute } from './mock-runtime'

export type { MockOptions }
export type MockResult =
  | { data: unknown; error?: undefined }
  | { data?: undefined; error: { code: string; message: string } }

const routes: MockRoute[] = [
  ...authMockRoutes,
  ...meMockRoutes,
  ...mediaMockRoutes,
  ...albumMockRoutes,
  ...communityMockRoutes,
  ...videoMockRoutes,
  ...pointsMockRoutes,
]

export function handleMock(options: MockOptions): MockResult {
  for (const route of routes) {
    if (route.method !== options.method) continue
    const params = matchPath(route.pattern, options.path)
    if (!params) continue
    try {
      return { data: route.handle(params, options) }
    } catch (error) {
      if (isMockError(error)) return { error }
      return { error: { code: 'INTERNAL', message: 'mock failed' } }
    }
  }
  return { error: { code: 'MOCK_NOT_IMPLEMENTED', message: `${options.method} ${options.path}` } }
}
