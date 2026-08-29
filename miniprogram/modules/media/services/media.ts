import { request } from '../../../core/request'
import { Media } from '../types/media'

export function uploadMedia(filePath: string) {
  return request<Media>({
    method: 'POST',
    path: '/api/v1/media',
    data: { file: filePath },
  })
}

export async function uploadImages(filePaths: string[]): Promise<string[]> {
  const urls: string[] = []
  for (let i = 0; i < filePaths.length; i += 1) {
    const media = await uploadMedia(filePaths[i])
    urls.push(media.url)
  }
  return urls
}
