export type Album = {
  id: string
  title: string
  body: string
  image_urls: string[]
  cover_url: string
  tag_names: string[]
  sync_to_forum: boolean
  created_at: string
}

export type AlbumWrite = {
  title: string
  body: string
  image_urls: string[]
  cover_url?: string
  tag_names: string[]
  sync_to_forum: boolean
}

export const ALBUM_TAG_PRESETS = ['写真', '美食', '生活', '温馨', '风景']
