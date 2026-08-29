import { brandAssets } from '../../../../assets/paths'

Component({
  properties: {
    item: { type: Object, value: {} },
    nested: { type: Boolean, value: false },
  },
  data: {
    likeIcon: brandAssets.reactLike,
    likeIconOn: brandAssets.reactLikeOn,
  },
  methods: {
    onLike() {
      this.triggerEvent('like', { id: this.properties.item.id })
    },
    onReply() {
      const item = this.properties.item
      this.triggerEvent('reply', { id: item.id, name: item.nickname })
    },
    onMore() {
      const item = this.properties.item
      this.triggerEvent('more', {
        id: item.id,
        canDelete: item.canDelete,
        isOwn: item.isOwn,
        body: item.body,
      })
    },
    onPreview() {
      const item = this.properties.item
      const urls = item.images || []
      if (!urls.length) {
        return
      }
      this.triggerEvent('preview', { urls, current: urls[0] })
    },
    onPlay() {
      const item = this.properties.item
      if (!item.audioUrl) {
        return
      }
      this.triggerEvent('play', { id: item.id, url: item.audioUrl })
    },
  },
})
