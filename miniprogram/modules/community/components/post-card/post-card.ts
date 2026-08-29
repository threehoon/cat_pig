import { brandAssets } from '../../../../assets/paths'

Component({
  properties: {
    postId: { type: String, value: '' },
    author: { type: String, value: '用户' },
    time: { type: String, value: '' },
    board: { type: String, value: '' },
    body: { type: String, value: '' },
    avatar: { type: String, value: brandAssets.avatarDefault },
    covers: { type: Array, value: [] },
    showMedia: { type: Boolean, value: false },
    likeCount: { type: Number, value: 0 },
    commentCount: { type: Number, value: 0 },
    favoriteCount: { type: Number, value: 0 },
    liked: { type: Boolean, value: false },
    favorited: { type: Boolean, value: false },
  },
  methods: {
    onTap() {
      this.triggerEvent('opentap', { id: this.properties.postId })
    },
    onLike(e: WechatMiniprogram.CustomEvent<{ id: string }>) {
      this.triggerEvent('like', { id: e.detail.id || this.properties.postId })
    },
    onFavorite(e: WechatMiniprogram.CustomEvent<{ id: string }>) {
      this.triggerEvent('favorite', { id: e.detail.id || this.properties.postId })
    },
    onReply(e: WechatMiniprogram.CustomEvent<{ id: string }>) {
      this.triggerEvent('reply', { id: e.detail.id || this.properties.postId })
    },
  },
})
