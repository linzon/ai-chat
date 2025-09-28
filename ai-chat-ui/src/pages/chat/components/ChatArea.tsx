import { useState, useRef, useEffect } from 'react';
import type { Message } from '../../../api/client';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';

interface ChatAreaProps {
  messages: Message[];
  onSendMessage: (content: string, type: 'text' | 'image' | 'document' | 'audio', file?: File) => void;
  theme: 'light' | 'dark';
  isLoading: boolean;
}

export default function ChatArea({ messages, onSendMessage, theme, isLoading }: ChatAreaProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const prevMessageCountRef = useRef<number>(0);
  const prevIsLoadingRef = useRef<boolean>(false);
  const [streamingMessageIds, setStreamingMessageIds] = useState<Set<number>>(new Set());

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 内容更新时的回调函数
  const handleContentUpdate = () => {
    // 延迟滚动以确保DOM已更新
    setTimeout(() => {
      scrollToBottom();
    }, 50);
  };

  useEffect(() => {
    // 检查是否需要滚动到底部
    const shouldScrollToBottom = 
      // 消息数量增加时
      messages.length > prevMessageCountRef.current ||
      // 从加载状态变为非加载状态时
      (prevIsLoadingRef.current && !isLoading) ||
      // 消息内容更新时（流式输出）
      isLoading;

    if (shouldScrollToBottom) {
      // 延迟滚动以确保DOM已更新
      setTimeout(() => {
        scrollToBottom();
      }, 100);
    }

    // 更新引用值
    prevMessageCountRef.current = messages.length;
    prevIsLoadingRef.current = isLoading;
  }, [messages, isLoading]);

  const chatAreaClasses = theme === 'dark' 
    ? 'bg-gray-800' 
    : 'bg-gray-50';

  // 确定哪些消息是新消息（需要流式输出的）
  const getIsNewMessage = (message: Message, index: number) => {
    // 只有在streamingMessageIds集合中的消息才需要流式输出
    return streamingMessageIds.has(message.id);
  };

  // 当有新消息添加时，将其添加到流式显示集合中
  useEffect(() => {
    if (messages.length > prevMessageCountRef.current && messages.length > 0) {
      // 获取最新的AI消息
      const latestMessage = messages[messages.length - 1];
      if (latestMessage.role === 'assistant' && !isLoading) {
        setStreamingMessageIds(prev => new Set(prev).add(latestMessage.id));
      }
    }
    
    // 更新引用值
    prevMessageCountRef.current = messages.length;
  }, [messages, isLoading]);

  // 在每次渲染后检查是否需要滚动到底部
  useEffect(() => {
    // 延迟执行滚动以确保DOM已更新
    const timer = setTimeout(() => {
      scrollToBottom();
    }, 100);
    
    return () => clearTimeout(timer);
  });

  return (
    <div className={`flex-1 flex flex-col ${chatAreaClasses}`}>
      {/* Messages Area */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              <i className="ri-chat-3-line text-4xl mb-4"></i>
              <p className="text-lg font-medium">开始新的对话</p>
              <p className="text-sm mt-2">向AI助手提问或上传图片进行分析</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <MessageBubble
                key={message.id}
                message={message}
                theme={theme}
                onContentUpdate={handleContentUpdate}
                isNewMessage={getIsNewMessage(message, index)} // 传递新消息标识
              />
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  theme === 'dark' ? 'bg-gray-700' : 'bg-white'
                }`}>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      {/* Message Input */}
      <MessageInput 
        onSendMessage={onSendMessage}
        theme={theme}
        disabled={isLoading}
      />
    </div>
  );
}