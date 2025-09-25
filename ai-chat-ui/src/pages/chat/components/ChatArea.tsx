import { useState, useRef, useEffect } from 'react';
import { Message } from '../../../api/client';
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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const chatAreaClasses = theme === 'dark' 
    ? 'bg-gray-800' 
    : 'bg-gray-50';

  return (
    <div className={`flex-1 flex flex-col ${chatAreaClasses}`}>
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
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
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                theme={theme}
              />
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  theme === 'dark' ? 'bg-gray-700' : 'bg-white'
                }`}>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
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