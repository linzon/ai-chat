import { useState, useRef, useEffect } from 'react';
import Button from '../../../components/base/Button';
import { useFileUpload } from '../../../hooks/useFileUpload';

interface MessageInputProps {
  onSendMessage: (content: string, type: 'text' | 'image' | 'document' | 'audio', file?: File) => void;
  theme: 'light' | 'dark';
  disabled: boolean;
}

export default function MessageInput({ onSendMessage, theme, disabled }: MessageInputProps) {
  const [input, setInput] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [showToolMenu, setShowToolMenu] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const toolMenuRef = useRef<HTMLDivElement>(null);
  const toolButtonRef = useRef<HTMLButtonElement>(null);
  const { uploadedFiles, uploadFile, removeFile, clearFiles, uploading, error } = useFileUpload();

  // 初始化时设置文本框高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '24px';
      textareaRef.current.style.overflowY = 'hidden';
      
      // 强制重绘以确保样式正确应用
      textareaRef.current.offsetHeight;
    }
  }, []);

  // 点击外部区域关闭工具菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        showToolMenu &&
        toolMenuRef.current &&
        !toolMenuRef.current.contains(event.target as Node) &&
        toolButtonRef.current &&
        !toolButtonRef.current.contains(event.target as Node)
      ) {
        setShowToolMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showToolMenu]);

  // 自动调整文本框高度
  useEffect(() => {
    if (textareaRef.current) {
      // 重置高度以获取正确的scrollHeight
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.overflowY = 'hidden';
      const scrollHeight = textareaRef.current.scrollHeight;
      
      // 设置新的高度，但不超过最大高度
      if (input) {
        const newHeight = Math.min(scrollHeight, 150); // 最大高度增加到150px
        textareaRef.current.style.height = `${newHeight}px`;
        textareaRef.current.style.overflowY = scrollHeight > 150 ? 'auto' : 'hidden';
      } else {
        textareaRef.current.style.height = '45px';
      }
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((input.trim() || uploadedFiles.length > 0) && !disabled && !uploading) {
      // Determine message type based on uploaded files
      let messageType: 'text' | 'image' | 'document' | 'audio' = 'text';
      let file: File | undefined;
      
      if (uploadedFiles.length > 0) {
        const firstFile = uploadedFiles[0].file;
        if (firstFile.type.startsWith('image/')) {
          messageType = 'image';
        } else if (firstFile.type.startsWith('audio/')) {
          messageType = 'audio';
        } else {
          messageType = 'document';
        }
        file = firstFile;
      }
      
      onSendMessage(input.trim() || '请分析附件内容', messageType, file);
      setInput('');
      clearFiles();
      
      // 关闭工具菜单
      setShowToolMenu(false);
    }
  };

  const handleFileSelect = async (file: File) => {
    try {
      await uploadFile(file);
      // 关闭工具菜单
      setShowToolMenu(false);
    } catch (error) {
      console.error('文件上传失败:', error);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    // 限制输入字符数不超过5000
    if (e.target.value.length <= 5000) {
      setInput(e.target.value);
    }
  };

  const handleToolSelect = (tool: 'image' | 'file' | 'voice') => {
    if (tool === 'image' || tool === 'file') {
      fileInputRef.current?.click();
    } else if (tool === 'voice') {
      // 语音输入功能开发中
      console.log('语音输入功能开发中');
    }
  };

  const inputAreaClasses = theme === 'dark' 
    ? 'bg-gray-900 border-gray-700' 
    : 'bg-white border-gray-200';

  const inputClasses = theme === 'dark'
    ? 'bg-gray-800 border-gray-600 text-gray-100'
    : 'bg-white border-gray-300 text-gray-900';

  const tools = [
    {
      key: 'image' as const,
      icon: 'ri-image-add-line',
      label: '图片上传',
      available: true
    },
    {
      key: 'file' as const,
      icon: 'ri-file-add-line',
      label: '文件上传',
      available: true
    },
    {
      key: 'voice' as const,
      icon: 'ri-mic-line',
      label: '语音输入',
      available: false
    }
  ];

  return (
    <div className={`border-t ${inputAreaClasses}`}>
      {/* 错误提示 */}
      {error && (
        <div className="p-3 bg-red-100 text-red-700 text-sm">
          {error}
        </div>
      )}
      
      {/* 文件预览区域 */}
      {uploadedFiles.length > 0 && (
        <div className="p-3 border-b border-gray-200 dark:border-gray-700">
          <div className="flex flex-wrap gap-2">
            {uploadedFiles.map((file) => (
              <div 
                key={file.id} 
                className="relative group flex flex-col items-center"
              >
                {file.previewUrl ? (
                  <div className="relative">
                    <img 
                      src={file.previewUrl} 
                      alt={file.name}
                      className="w-16 h-16 object-cover rounded-lg border"
                    />
                    <button
                      onClick={() => removeFile(file.id)}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <i className="ri-close-line"></i>
                    </button>
                  </div>
                ) : (
                  <div className="w-16 h-16 flex flex-col items-center justify-center rounded-lg border bg-gray-100 dark:bg-gray-700 relative">
                    <i className="ri-file-line text-2xl text-gray-500"></i>
                    <button
                      onClick={() => removeFile(file.id)}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600"
                    >
                      <i className="ri-close-line"></i>
                    </button>
                  </div>
                )}
                <span className="text-xs mt-1 truncate max-w-16 text-gray-500 dark:text-gray-400">
                  {file.name.length > 8 ? file.name.substring(0, 8) + '...' : file.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 字符计数器 */}
      {input.length > 0 && (
        <div className="text-right text-xs px-4 py-1 text-gray-500">
          {input.length}/5000
        </div>
      )}

      {/* 工具栏 */}
      <div className="flex items-end p-3 gap-2">
        <div className="relative">
          <button
            ref={toolButtonRef}
            onClick={() => setShowToolMenu(!showToolMenu)}
            className={`p-2 rounded-full ${theme === 'dark' ? 'hover:bg-gray-700 bg-gray-800' : 'hover:bg-gray-100 bg-gray-50'} transition-colors duration-200`}
            disabled={disabled || uploading}
          >
            <i className="ri-add-circle-fill text-2xl text-blue-500"></i>
          </button>
          
          {showToolMenu && (
            <div 
              ref={toolMenuRef}
              className={`absolute bottom-full left-0 mb-2 rounded-xl shadow-lg p-1 ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} border ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} transition-all duration-200`}
            >
              <div className="flex">
                {tools.map((tool) => (
                  <button
                    key={tool.key}
                    onClick={() => tool.available && handleToolSelect(tool.key)}
                    disabled={!tool.available || disabled || uploading}
                    className={`p-2 rounded-lg ${tool.available ? (theme === 'dark' ? 'hover:bg-gray-700' : 'hover:bg-gray-100') : 'opacity-50 cursor-not-allowed'}`}
                    title={tool.label}
                  >
                    <i className={`${tool.icon} text-xl`}></i>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              handleFileSelect(file);
            }
            e.target.value = ''; // Reset input to allow selecting the same file again
          }}
          disabled={disabled || uploading}
        />
        
        <form onSubmit={handleSubmit} className="flex-1 flex">
          <div className={`flex-1 flex items-center border rounded-2xl mx-2 ${inputClasses} transition-all duration-200 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 min-h-12`}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              placeholder="输入消息..."
              className="flex-1 bg-transparent border-0 py-3 px-4 resize-none focus:outline-none focus:ring-0 min-h-0 max-h-36 text-base placeholder:italic placeholder:text-gray-400"
              style={{
                lineHeight: '1.5'
              }}
              disabled={disabled || uploading}
              rows={1}
            />
          </div>
          
          <Button
            type="submit"
            className="self-end mb-1"
            disabled={disabled || uploading || (input.trim() === '' && uploadedFiles.length === 0)}
            loading={uploading}
          >
            <i className="ri-send-plane-fill text-xl"></i>
          </Button>
        </form>
      </div>
    </div>
  );
}