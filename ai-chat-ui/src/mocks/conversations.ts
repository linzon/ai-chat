
import { Message as ApiMessage, Conversation as ApiConversation } from '../api/client';

export interface Message extends ApiMessage {
  id: string; // 保持字符串类型以兼容现有代码
  timestamp: number; // 保持时间戳格式以兼容现有代码
}

export interface Conversation extends ApiConversation {
  id: string; // 保持字符串类型以兼容现有代码
  messages: Message[];
  createdAt: number; // 保持时间戳格式以兼容现有代码
  updatedAt: number; // 保持时间戳格式以兼容现有代码
}

export const mockConversations: Conversation[] = [
  {
    id: '1',
    user_id: 1,
    title: '你好，世界！',
    messages: [
      {
        id: '1-1',
        conversation_id: 1,
        content: '你好，AI助手！',
        role: 'user',
        message_type: 'text',
        created_at: new Date(Date.now() - 3600000).toISOString(),
        timestamp: Date.now() - 3600000
      },
      {
        id: '1-2',
        conversation_id: 1,
        content: '你好！我是AI助手，很高兴为你服务。有什么我可以帮你的吗？',
        role: 'assistant',
        message_type: 'text',
        created_at: new Date(Date.now() - 3500000).toISOString(),
        timestamp: Date.now() - 3500000
      }
    ],
    created_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date(Date.now() - 3500000).toISOString(),
    createdAt: Date.now() - 3600000,
    updatedAt: Date.now() - 3500000
  },
  {
    id: '2',
    user_id: 1,
    title: '图片识别',
    messages: [
      {
        id: '2-1',
        conversation_id: 2,
        content: '请分析这张图片',
        role: 'user',
        message_type: 'image',
        file_url: 'https://example.com/image.jpg',
        created_at: new Date(Date.now() - 86400000).toISOString(),
        timestamp: Date.now() - 86400000
      },
      {
        id: '2-2',
        conversation_id: 2,
        content: '这是一张风景图片，我看到了山和湖。',
        role: 'assistant',
        message_type: 'text',
        created_at: new Date(Date.now() - 86300000).toISOString(),
        timestamp: Date.now() - 86300000
      }
    ],
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86300000).toISOString(),
    createdAt: Date.now() - 86400000,
    updatedAt: Date.now() - 86300000
  }
];

export const aiModels = [
  { value: 'gpt-4', label: 'GPT-4 (最强推理)' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo (平衡性能)' },
  { value: 'claude-3', label: 'Claude-3 (创意写作)' },
  { value: 'gemini-pro', label: 'Gemini Pro (多模态)' }
];
