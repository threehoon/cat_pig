import { AssistantCitation, AssistantSuggestion } from '../types/assistant'

export type KnowledgeEntry = {
  id: string
  title: string
  snippet: string
  keywords: string[]
  answer: string
}

export const SUGGESTIONS: AssistantSuggestion[] = [
  { id: 'e1111111-1111-1111-1111-111111111111', question: '夏天怎么给狗降温' },
  { id: 'e2222222-2222-2222-2222-222222222222', question: '附近有没有靠谱的宠物医院' },
  { id: 'e3333333-3333-3333-3333-333333333333', question: '为什么天空是蓝的' },
  { id: 'e4444444-4444-4444-4444-444444444444', question: '猫咪发烧该吃什么药' },
]

export const KNOWLEDGE: KnowledgeEntry[] = [
  {
    id: 'k1111111-1111-1111-1111-111111111111',
    title: '夏天给狗降温',
    snippet: '避开正午出门，室内通风，提供阴凉饮水和湿毛巾擦身，不要用冰水浇身。',
    keywords: ['降温', '夏天', '热'],
    answer:
      '夏天给狗降温，先避开正午出门，改在清晨或傍晚。屋里通风、留阴凉处，随时有干净凉水。可以用湿毛巾擦肚皮和脚垫散热，不要浇冰水、不要把狗关在停驶的车里。我是小x，这是说明书里的日常护理，不能代替兽医。',
  },
]

export const REFUSE_WORDS = ['发烧', '吃药', '用药', '开药', '剂量', '诊断', '拉肚子', '什么药']

export const SEARCH_WORDS = ['医院', '附近']

export const SKY_WORDS = ['天空', '蓝']

export const REFUSE_ANSWER =
  '我是小x。知识库里没有足够依据回答看病或用药的问题。请带毛孩子去医院，不要自行用药。我不会编诊断、药名或剂量。'

export const SEARCH_ANSWER =
  '小x没有你的定位，给不了具体店名。可以在地图里搜「宠物医院」，认准营业资质和评价。紧急情况先就近送诊，不要在对话里等指路。'

export const SKY_ANSWER =
  '天空显蓝，是因为阳光里的短波蓝光更容易被空气散射，从地面看上去就是一片蓝。这是常识说明，仅供参考。'

export const GENERATED_ANSWER = '我是小x。这是常识说明，仅供参考，不能代替专业意见。'

export function citationOf(entry: KnowledgeEntry): AssistantCitation {
  return {
    id: entry.id,
    title: entry.title,
    snippet: entry.snippet,
  }
}
