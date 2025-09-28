import { useState, useEffect, useRef } from 'react';
import type { Message } from '../../../api/client';

interface MessageBubbleProps {
  message: Message;
  theme: 'light' | 'dark';
  onContentUpdate?: () => void;
  isNewMessage?: boolean;
}

export default function MessageBubble({ message, theme, onContentUpdate, isNewMessage = false }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
  // 思考过程和模型回复的状态
  const [thinkingExpanded, setThinkingExpanded] = useState(true);
  const [displayedThinking, setDisplayedThinking] = useState('');
  const [displayedModel, setDisplayedModel] = useState('');
  const [isThinkingStreaming, setIsThinkingStreaming] = useState(false);
  const [isModelStreaming, setIsModelStreaming] = useState(false);
  const thinkingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const modelIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const thinkingStepsRef = useRef<string[]>([]);
  const thinkingStepIndexRef = useRef(0);

  // 解析内容为思考过程和模型回复
  const parseContent = (content: string) => {
    // 检查是否包含思考过程和模型回复的标记
    const hasThinkingProcess = content.includes('[思考过程]');
    const hasModelResponse = content.includes('[模型回复]');
    
    if (hasThinkingProcess && hasModelResponse) {
      // 使用更简单的字符串处理方式
      const thinkingStart = content.indexOf('[思考过程]') + 6; // 6是"[思考过程]"的长度
      const modelStart = content.indexOf('[模型回复]');
      
      if (thinkingStart >= 6 && modelStart > thinkingStart) {
        const thinking = content.substring(thinkingStart, modelStart).trim();
        const model = content.substring(modelStart + 6).trim(); // 6是"[模型回复]"的长度
        return { thinking, model };
      }
    }
    
    // 如果没有找到标记，将所有内容作为模型回复
    return {
      thinking: '',
      model: content
    };
  };

  // 清理定时器
  const clearIntervals = () => {
    if (thinkingIntervalRef.current) {
      clearInterval(thinkingIntervalRef.current);
      thinkingIntervalRef.current = null;
    }
    if (modelIntervalRef.current) {
      clearInterval(modelIntervalRef.current);
      modelIntervalRef.current = null;
    }
  };

  // 思考过程流式显示
  const typeThinking = (thinking: string, model: string) => {
    clearIntervals();
    thinkingStepsRef.current = thinking.split('\n').filter(step => step.trim() !== '');
    thinkingStepIndexRef.current = 0;
    setDisplayedThinking('');
    setIsThinkingStreaming(true);
    
    thinkingIntervalRef.current = setInterval(() => {
      if (thinkingStepIndexRef.current < thinkingStepsRef.current.length) {
        const newThinking = thinkingStepsRef.current.slice(0, thinkingStepIndexRef.current + 1).join('\n');
        setDisplayedThinking(newThinking);
        thinkingStepIndexRef.current++;
        if (onContentUpdate) {
          onContentUpdate();
        }
      } else {
        if (thinkingIntervalRef.current) {
          clearInterval(thinkingIntervalRef.current);
          thinkingIntervalRef.current = null;
          setIsThinkingStreaming(false);
          // 开始模型流式
          typeModel(model);
        }
      }
    }, 300);
  };

  // 模型回复流式显示
  const typeModel = (content: string) => {
    clearIntervals();
    let index = 0;
    setDisplayedModel('');
    setIsModelStreaming(true);
    
    modelIntervalRef.current = setInterval(() => {
      if (index <= content.length) {
        const newContent = content.substring(0, index);
        setDisplayedModel(newContent);
        index++;
        if (onContentUpdate) {
          onContentUpdate();
        }
      } else {
        if (modelIntervalRef.current) {
          clearInterval(modelIntervalRef.current);
          modelIntervalRef.current = null;
          setIsModelStreaming(false);
        }
      }
    }, 20);
  };

  useEffect(() => {
    const { thinking, model } = parseContent(message.content);
    
    // 对于新消息且是AI回复，启动流式
    if (isNewMessage && message.role === 'assistant') {
      if (thinking) {
        typeThinking(thinking, model);
      } else {
        typeModel(model);
      }
    } else {
      // 历史消息直接显示完整内容
      setDisplayedThinking(thinking);
      setDisplayedModel(model);
      setIsThinkingStreaming(false);
      setIsModelStreaming(false);
    }
    
    // 清理定时器
    return () => {
      clearIntervals();
    };
  }, [message.content, message.role, isNewMessage]);

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

  const formatModelResponse = (content: string) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>')
      .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-100 p-3 rounded mt-2 overflow-x-auto"><code>$1</code></pre>')
      .replace(/^## (.*$)/gim, '<h2 class="text-lg font-semibold mt-4 mb-2">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-xl font-bold mt-4 mb-2">$1</h1>')
      .replace(/\n/g, '');
  };

  const isUser = message.role === 'user';

  // 新增：仅对AI消息解析内容
  const { thinking, model } = message.role === 'assistant' 
    ? parseContent(message.content)
    : { thinking: '', model: message.content };

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
            >
              {message.role === 'assistant' ? (
                <>
                  {/* 思考过程区域 */}
                  {thinking && (
                    <div className="mb-3">
                      <div 
                        className="flex items-center cursor-pointer p-2 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded transition-colors"
                        onClick={() => setThinkingExpanded(!thinkingExpanded)}
                      >
                        <i className={`ri-arrow-${thinkingExpanded ? 'down' : 'right'}-s-line mr-2 text-blue-500 dark:text-blue-400`}></i>
                        <h3 className="text-sm font-semibold text-blue-500 dark:text-blue-400">
                          思考过程
                        </h3>
                        {isThinkingStreaming && (
                          <div className="ml-2 flex space-x-1">
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                          </div>
                        )}
                      </div>
                      {thinkingExpanded && (
                        <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded border-l-4 border-blue-500 dark:border-blue-400">
                          <div 
                            className="text-gray-800 dark:text-gray-200"
                            dangerouslySetInnerHTML={{ 
                              __html: formatModelResponse(displayedThinking || thinking) 
                            }}
                          />
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* 模型回复区域 */}
                  <div className="mt-2 p-3 bg-green-50 dark:bg-green-900/20 rounded border-l-4 border-green-500 dark:border-green-400">
                    <div className="flex items-center mb-2">
                      <h3 className="text-sm font-semibold text-green-600 dark:text-green-400">
                        模型回复
                      </h3>
                      {isModelStreaming && (
                        <div className="ml-2 flex space-x-1">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                        </div>
                      )}
                    </div>
                    <div 
                      className="text-gray-800 dark:text-gray-200"
                      dangerouslySetInnerHTML={{ 
                        __html: formatModelResponse(displayedModel || model) 
                      }}
                    />
                  </div>
                </>
              ) : (
                // 保持用户消息的原始显示样式
                <div 
                  className="text-gray-800 dark:text-gray-200"
                  dangerouslySetInnerHTML={{ 
                    __html: formatModelResponse(message.content)
                  }}
                />
              )}
            </div>
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