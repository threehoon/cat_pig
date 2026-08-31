import { chooseLocalImages } from '../../../media/choose'
import { uploadImages, uploadMedia } from '../../../media/services/media'

export function uploadCommentImages(limit: number): Promise<string[]> {
  return chooseLocalImages(limit).then((paths) => uploadImages(paths))
}

export function uploadCommentVoice(path: string): Promise<string> {
  return uploadMedia(path).then((media) => media.url)
}
