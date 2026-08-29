import { ListResult, request } from '../../../core/request'
import { Comment, CommentReportReason, CommentWrite, Post, PostStatus, PostTab, PostWrite } from '../types/post'

export function listPosts(tab: PostTab = 'recommend', q?: string, page = 1, pageSize = 20) {
  return request<ListResult<Post>>({
    method: 'GET',
    path: '/api/v1/community/post',
    query: { tab, q, page, page_size: pageSize },
  })
}

export function listMyPosts(status?: PostStatus, page = 1, pageSize = 20) {
  return request<ListResult<Post>>({
    method: 'GET',
    path: '/api/v1/community/post/mine',
    query: { status, page, page_size: pageSize },
  })
}

export function createPost(body: PostWrite) {
  return request<Post>({
    method: 'POST',
    path: '/api/v1/community/post',
    data: body,
  })
}

export function getPost(id: string) {
  return request<Post>({
    method: 'GET',
    path: `/api/v1/community/post/${id}`,
  })
}

export function patchPost(id: string, body: Partial<PostWrite>) {
  return request<Post>({
    method: 'PATCH',
    path: `/api/v1/community/post/${id}`,
    data: body,
  })
}

export function deletePost(id: string) {
  return request<{ ok: true }>({
    method: 'DELETE',
    path: `/api/v1/community/post/${id}`,
  })
}

export function likePost(id: string) {
  return request<Post>({
    method: 'POST',
    path: `/api/v1/community/post/${id}/like`,
    data: {},
  })
}

export function favoritePost(id: string) {
  return request<Post>({
    method: 'POST',
    path: `/api/v1/community/post/${id}/favorite`,
    data: {},
  })
}

export function listComments(id: string, page = 1, pageSize = 20) {
  return request<ListResult<Comment>>({
    method: 'GET',
    path: `/api/v1/community/post/${id}/comment`,
    query: { page, page_size: pageSize },
  })
}

export function createComment(id: string, body: CommentWrite) {
  return request<Comment>({
    method: 'POST',
    path: `/api/v1/community/post/${id}/comment`,
    data: {
      body: body.body,
      parent_id: body.parent_id || null,
      sticker_ids: body.sticker_ids || [],
      image_urls: body.image_urls || [],
      audio_url: body.audio_url || null,
      audio_duration: body.audio_duration || 0,
    },
  })
}

export function deleteComment(postId: string, commentId: string) {
  return request<{ ok: true; comment_count: number }>({
    method: 'DELETE',
    path: `/api/v1/community/post/${postId}/comment/${commentId}`,
  })
}

export function likeComment(postId: string, commentId: string) {
  return request<Comment>({
    method: 'POST',
    path: `/api/v1/community/post/${postId}/comment/${commentId}/like`,
    data: {},
  })
}

export function reportComment(postId: string, commentId: string, reason: CommentReportReason) {
  return request<{ ok: true }>({
    method: 'POST',
    path: `/api/v1/community/post/${postId}/comment/${commentId}/report`,
    data: { reason },
  })
}

export function followUser(userId: string) {
  return request<{ ok: true }>({
    method: 'POST',
    path: '/api/v1/community/follow',
    data: { user_id: userId },
  })
}

export function unfollowUser(userId: string) {
  return request<{ ok: true }>({
    method: 'DELETE',
    path: `/api/v1/community/follow/${userId}`,
  })
}
