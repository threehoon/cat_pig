import { brandAssets, mockPhotos } from '../assets/paths'

export const CURRENT_USER_ID = '10101010-1010-1010-1010-101010101010'
export const OTHER_USER_ID = '20202020-2020-2020-2020-202020202020'

export type MockAuthor = {
  id: string
  nickname: string | null
  avatar_url: string | null
}

export type MockMe = MockAuthor & { points_balance: number }

export type MockAlbum = {
  id: string
  title: string
  body: string
  image_urls: string[]
  cover_url: string
  tag_names: string[]
  sync_to_forum: boolean
  created_at: string
}

export type MockPost = {
  id: string
  author: MockAuthor
  board: 'qa' | 'show' | 'share' | 'help' | 'daily' | 'experience'
  title: string
  body: string
  image_urls: string[]
  topic_names: string[]
  status: 'draft' | 'pending' | 'published' | 'rejected'
  like_count: number
  comment_count: number
  favorite_count: number
  liked: boolean
  favorited: boolean
  created_at: string
}

export type MockComment = {
  id: string
  post_id: string
  author: MockAuthor
  body: string
  parent_id: string | null
  reply_to: MockAuthor | null
  created_at: string
}

export type MockVideo = {
  id: string
  title: string
  image_urls: string[]
  prompt: string
  resolution: '540p' | '720p' | '1080p' | '2k' | '4k'
  status: 'pending' | 'running' | 'success' | 'failed'
  result_url: string | null
  points_cost: number
  error_message: string | null
  created_at: string
}

export type MockLedger = {
  id: string
  kind: 'earn' | 'spend'
  amount: number
  title: string
  balance_after: number
  created_at: string
}

const me: MockMe = {
  id: CURRENT_USER_ID,
  nickname: '用户',
  avatar_url: brandAssets.avatarDefault,
  points_balance: 180,
}

const other: MockAuthor = {
  id: OTHER_USER_ID,
  nickname: '邻家铲屎官',
  avatar_url: brandAssets.avatarDefault,
}

export const store = {
  me,
  follows: [] as string[],
  last_checkin_date: null as string | null,
  albums: [
    {
      id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      title: '周末出门',
      body: '去公园晒太阳',
      image_urls: [mockPhotos.pet1, mockPhotos.pet2],
      cover_url: mockPhotos.pet1,
      tag_names: ['生活'],
      sync_to_forum: false,
      created_at: '2026-08-24T10:00:00Z',
    },
    {
      id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaab',
      title: '午睡',
      body: '晒到沙发上睡着了',
      image_urls: [mockPhotos.pet3],
      cover_url: mockPhotos.pet3,
      tag_names: ['温馨'],
      sync_to_forum: false,
      created_at: '2026-08-22T08:00:00Z',
    },
  ] as MockAlbum[],
  posts: [
    {
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      author: { ...me },
      board: 'qa',
      title: '给两只小狗起个标题',
      body: '想把两只小狗放到草地上跑一跑，有人试过图生视频吗？',
      image_urls: [mockPhotos.pet1, mockPhotos.pet2],
      topic_names: ['日常'],
      status: 'published',
      like_count: 2,
      comment_count: 2,
      favorite_count: 0,
      liked: false,
      favorited: false,
      created_at: '2026-08-24T10:00:00Z',
    },
    {
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbe',
      author: { ...other },
      board: 'show',
      title: '今天的窗边光',
      body: '午睡醒了不肯下沙发。',
      image_urls: [mockPhotos.pet3],
      topic_names: ['可爱瞬间'],
      status: 'published',
      like_count: 4,
      comment_count: 0,
      favorite_count: 1,
      liked: false,
      favorited: false,
      created_at: '2026-08-23T14:00:00Z',
    },
    {
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbf',
      author: { ...other },
      board: 'daily',
      title: '',
      body: '晚上散步绕了小区两圈。',
      image_urls: [mockPhotos.pet2],
      topic_names: ['日常'],
      status: 'published',
      like_count: 1,
      comment_count: 0,
      favorite_count: 0,
      liked: false,
      favorited: false,
      created_at: '2026-08-22T11:30:00Z',
    },
    {
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbb10',
      author: { ...me },
      board: 'daily',
      title: '',
      body: '下周带去打疫苗的清单',
      image_urls: [],
      topic_names: [],
      status: 'draft',
      like_count: 0,
      comment_count: 0,
      favorite_count: 0,
      liked: false,
      favorited: false,
      created_at: '2026-08-21T09:00:00Z',
    },
  ] as MockPost[],
  comments: [
    {
      id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
      post_id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      author: { ...other },
      body: '也想试试，阳光好的时候拍一组。',
      parent_id: null,
      reply_to: null,
      created_at: '2026-08-24T11:00:00Z',
    },
    {
      id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeef',
      post_id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      author: { ...me },
      body: '你也去公园拍过吗？',
      parent_id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
      reply_to: { ...other },
      created_at: '2026-08-24T11:20:00Z',
    },
  ] as MockComment[],
  videos: [
    {
      id: 'cccccccc-cccc-cccc-cccc-cccccccccccc',
      title: '周末成长视频',
      image_urls: [mockPhotos.pet1, mockPhotos.pet2],
      prompt: '草地上跑',
      resolution: '720p',
      status: 'pending',
      result_url: null,
      points_cost: 50,
      error_message: null,
      created_at: '2026-08-24T10:00:00Z',
    },
  ] as MockVideo[],
  ledger: [
    {
      id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
      kind: 'earn',
      amount: 20,
      title: '发布帖子',
      balance_after: 180,
      created_at: '2026-08-24T10:00:00Z',
    },
    {
      id: 'dddddddd-dddd-dddd-dddd-ddddddddddde',
      kind: 'earn',
      amount: 10,
      title: '签到',
      balance_after: 160,
      created_at: '2026-08-23T09:00:00Z',
    },
    {
      id: 'dddddddd-dddd-dddd-dddd-dddddddddddf',
      kind: 'earn',
      amount: 20,
      title: '发布帖子',
      balance_after: 150,
      created_at: '2026-08-22T12:00:00Z',
    },
    {
      id: 'dddddddd-dddd-dddd-dddd-ddddddddddd0',
      kind: 'earn',
      amount: 20,
      title: '发布帖子',
      balance_after: 130,
      created_at: '2026-08-21T12:00:00Z',
    },
    {
      id: 'dddddddd-dddd-dddd-dddd-ddddddddddd1',
      kind: 'earn',
      amount: 10,
      title: '签到',
      balance_after: 110,
      created_at: '2026-08-21T09:00:00Z',
    },
    {
      id: 'dddddddd-dddd-dddd-dddd-ddddddddddd2',
      kind: 'earn',
      amount: 100,
      title: '注册',
      balance_after: 100,
      created_at: '2026-08-20T12:00:00Z',
    },
  ] as MockLedger[],
}

export function currentAuthor(): MockAuthor {
  return {
    id: store.me.id,
    nickname: store.me.nickname,
    avatar_url: store.me.avatar_url,
  }
}
