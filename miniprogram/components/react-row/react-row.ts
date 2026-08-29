import { brandAssets } from '../../assets/paths'

Component({
  properties: {
    postId: { type: String, value: '' },
    likeCount: { type: Number, value: 0 },
    commentCount: { type: Number, value: 0 },
    favoriteCount: { type: Number, value: 0 },
    liked: { type: Boolean, value: false },
    favorited: { type: Boolean, value: false },
    interactive: { type: Boolean, value: false },
  },
  data: {
    likeIcon: brandAssets.reactLike,
    likeIconOn: brandAssets.reactLikeOn,
    replyIcon: brandAssets.reactReply,
    replyIconOn: brandAssets.reactReplyOn,
    favoriteIcon: brandAssets.reactFavorite,
    favoriteIconOn: brandAssets.reactFavoriteOn,
    shareIcon: brandAssets.reactShare,
    shareIconOn: brandAssets.reactShareOn,
    popAction: '',
  },
  methods: {
    onAction(e: WechatMiniprogram.TouchEvent) {
      if (!this.properties.interactive) {
        return
      }
      const action = e.currentTarget.dataset.action as string
      this.setData({ popAction: action })
      this.triggerEvent(action, { id: this.properties.postId })
      setTimeout(() => {
        if (this.data.popAction === action) {
          this.setData({ popAction: '' })
        }
      }, 280)
    },
  },
})
