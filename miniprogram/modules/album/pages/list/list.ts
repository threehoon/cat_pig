import { brandAssets } from '../../../../assets/paths'
import { toastRequestError } from '../../../../core/request'
import { listAlbums } from '../../services/album'
import { Album, AlbumVisibility } from '../../types/album'
import { ALBUM_VISIBILITY_FILTERS, ALBUM_VISIBILITY_LABEL } from '../../visibility'

type VisibilityFilter = 'all' | AlbumVisibility

type AlbumCard = {
  id: string
  title: string
  cover_url: string
  sub: string
  tag_names: string[]
  visibility: AlbumVisibility
  visibility_label: string
}

function formatAlbumDate(iso: string): string {
  const date = new Date(iso)
  if (isNaN(date.getTime())) {
    return ''
  }
  const now = new Date()
  const month = date.getMonth() + 1
  const day = date.getDate()
  if (date.getFullYear() === now.getFullYear()) {
    return month + '月' + day + '日'
  }
  return date.getFullYear() + '年' + month + '月' + day + '日'
}

function albumSub(count: number, iso: string): string {
  const date = formatAlbumDate(iso)
  if (date) {
    return count + ' 张 · ' + date
  }
  return count + ' 张'
}

function toCard(album: Album): AlbumCard {
  return {
    id: album.id,
    title: album.title,
    cover_url: album.cover_url,
    sub: albumSub(album.image_urls.length, album.created_at),
    tag_names: album.tag_names,
    visibility: album.visibility,
    visibility_label: ALBUM_VISIBILITY_LABEL[album.visibility],
  }
}

function applyFilter(albums: AlbumCard[], filter: VisibilityFilter): AlbumCard[] {
  if (filter === 'all') {
    return albums
  }
  return albums.filter((item) => item.visibility === filter)
}

Page({
  data: {
    emptyAlbum: brandAssets.emptyAlbum,
    filter: 'all' as VisibilityFilter,
    filters: ALBUM_VISIBILITY_FILTERS,
    albums: [] as AlbumCard[],
    shown: [] as AlbumCard[],
  },
  onShow() {
    listAlbums()
      .then((result) => {
        const albums = result.items.map(toCard)
        this.setData({
          albums,
          shown: applyFilter(albums, this.data.filter),
        })
      })
      .catch(toastRequestError)
  },
  onFilter(e: WechatMiniprogram.TouchEvent) {
    const filter = e.currentTarget.dataset.id as VisibilityFilter
    this.setData({
      filter,
      shown: applyFilter(this.data.albums, filter),
    })
  },
  onUpload() {
    wx.navigateTo({ url: '/modules/album/pages/upload/upload' })
  },
  onOpen(e: WechatMiniprogram.TouchEvent) {
    const id = e.currentTarget.dataset.id as string
    wx.navigateTo({ url: `/modules/album/pages/detail/detail?id=${id}` })
  },
})
