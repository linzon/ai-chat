import { useState } from 'react';
import { Message } from '../../../api/client';

interface MessageBubbleProps {
  message: Message;
  theme: 'light' | 'dark';
}

export default function MessageBubble({ message, theme }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);

  const handleCopy = async () => {
    try {
      if (!navigator.clipboard) {
        // 降级处理：使用document.execCommand
        const textArea = document.createElement('textarea');
        textArea.value = message.content;
        document.body.appendChild(textArea);
        textArea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (success) {
          setCopied(true);
          setCopyError(false);
          setTimeout(() => setCopied(false), 2000);
        } else {
          setCopyError(true);
          setTimeout(() => setCopyError(false), 2000);
        }
        return;
      }
      
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setCopyError(false);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('复制失败:', error);
      setCopyError(true);
      setTimeout(() => setCopyError(false), 2000);
    }
  };

  const formatContent = (content: string) => {
    // 简单的markdown渲染
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>')
      .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-100 p-3 rounded mt-2 overflow-x-auto"><code>$1</code></pre>')
      .replace(/^## (.*$)/gim, '<h2 class="text-lg font-semibold mt-4 mb-2">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-xl font-bold mt-4 mb-2">$1</h1>')
      .replace(/\n/g, '<br />');
  };

  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
            <i className="ri-user-line text-white text-sm"></i>
          </div>
        ) : (
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            theme === 'dark' ? 'bg-green-600' : 'bg-green-500'
          }`}>
            <i className="ri-robot-line text-white text-sm"></i>
          </div>
        )}
      </div>

      {/* Message Bubble */}
      <div className={`flex-1 ${isUser ? 'flex justify-end' : ''}`}>
        <div className={`px-4 py-3 rounded-2xl shadow-sm relative group max-w-[75%] min-w-[300px] ${
          isUser
            ? 'bg-blue-400 text-white rounded-br-md'
            : theme === 'dark'
            ? 'bg-gray-700 text-gray-100 rounded-bl-md'
            : 'bg-white text-gray-900 border border-gray-200 rounded-bl-md'
        }`}>
          {/* 文件预览 */}
          {message.message_type === 'image' && message.file_url && (
            <div className="mb-3">
              <img
                src={message.file_url}
                alt="User uploaded"
                className="max-w-full h-auto rounded-lg"
              />
            </div>
          )}
          
          {message.message_type !== 'image' && message.file_url && (
            <div className="mb-2 flex items-center p-2 bg-gray-100 dark:bg-gray-600 rounded">
              <i className="ri-file-line text-2xl mr-2"></i>
              <div>
                <div className="text-sm font-medium">附件文件</div>
                <div className="text-xs text-gray-500 dark:text-gray-300">
                  {message.file_url.split('/').pop()}
                </div>
              </div>
            </div>
          )}
          
          {/* 文本内容 */}
          {message.content && (
            <div 
              className="text-sm leading-relaxed break-words"
              style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}
              dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
            />
          )}
          
          <div className="flex items-center justify-between mt-3">
            <span className={`text-xs ${
              isUser 
                ? 'text-blue-100' 
                : theme === 'dark' 
                ? 'text-gray-400' 
                : 'text-gray-500'
            }`}>
              {new Date(message.created_at).toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              })}
            </span>
            
            {/* 为用户和AI消息都添加复制按钮 */}
            <button
              onClick={handleCopy}
              className={`opacity-0 group-hover:opacity-100 transition-opacity ml-2 p-1.5 rounded-lg hover:bg-opacity-20 cursor-pointer flex items-center ${
                theme === 'dark' ? 'hover:bg-gray-600' : 'hover:bg-gray-200'
              }`}
              title={copyError ? "复制失败" : copied ? "已复制" : "复制消息"}
            >
              {copied ? (
                <i className="ri-check-line text-green-500 text-sm"></i>
              ) : copyError ? (
                <i className="ri-close-line text-red-500 text-sm"></i>
              ) : (
                <i className={`ri-file-copy-line ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'} text-sm`}></i>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}