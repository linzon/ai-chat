import { useState } from 'react';
import { Conversation } from '../../../api/client';
import Button from '../../../components/base/Button';

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: number | null;
  onSelectConversation: (id: number) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: number) => void;
  onUpdateConversationTitle: (id: number, title: string) => void;
  theme: 'light' | 'dark';
}

export default function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onUpdateConversationTitle,
  theme
}: SidebarProps) {
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) {
      return '今天';
    }
    if (days === 1) {
      return '昨天';
    }
    if (days < 7) {
      return `${days}天前`;
    }
    // 精确到年月日
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  const handleEditStart = (conversation: Conversation) => {
    setEditingId(conversation.id);
    setEditTitle(conversation.title);
  };

  const handleEditSave = async (id: number) => {
    if (editTitle.trim()) {
      onUpdateConversationTitle(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const handleKeyPress = (e: React.KeyboardEvent, id: number) => {
    if (e.key === 'Enter') {
      handleEditSave(id);
    } else if (e.key === 'Escape') {
      handleEditCancel();
    }
  };

  const sidebarClasses = theme === 'dark' 
    ? 'bg-gray-900 border-gray-700' 
    : 'bg-white border-gray-200';
    
  const textClasses = theme === 'dark' 
    ? 'text-gray-100' 
    : 'text-gray-900';
    
  const hoverClasses = theme === 'dark' 
    ? 'hover:bg-gray-800' 
    : 'hover:bg-gray-50';

  return (
    <div className={`w-80 border-r flex flex-col ${sidebarClasses}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <Button
          onClick={onNewConversation}
          className="w-full flex items-center justify-center"
        >
          <i className="ri-add-line mr-2"></i>
          新建对话
        </Button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.map((conversation) => (
          <div
            key={conversation.id}
            className={`p-3 border-b border-gray-200 dark:border-gray-700 cursor-pointer relative ${hoverClasses} ${
              activeConversationId === conversation.id ? (theme === 'dark' ? 'bg-gray-800' : 'bg-gray-100') : ''
            }`}
            onClick={() => onSelectConversation(conversation.id)}
            onMouseEnter={() => setHoveredId(conversation.id)}
            onMouseLeave={() => setHoveredId(null)}
          >
            {editingId === conversation.id ? (
              // 编辑状态
              <div className="flex flex-col">
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onKeyDown={(e) => handleKeyPress(e, conversation.id)}
                  className="w-full p-1 mb-1 bg-transparent border-b border-gray-400 focus:outline-none focus:border-blue-500"
                  autoFocus
                />
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleEditSave(conversation.id)}
                    className="text-xs px-2 py-1 bg-blue-500 text-white rounded"
                  >
                    保存
                  </button>
                  <button
                    onClick={handleEditCancel}
                    className="text-xs px-2 py-1 bg-gray-500 text-white rounded"
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              // 显示状态
              <>
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{conversation.title}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {formatTime(conversation.updated_at)}
                    </div>
                  </div>
                  {hoveredId === conversation.id && (
                    <div className="flex space-x-1 ml-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditStart(conversation);
                        }}
                        className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
                        title="编辑标题"
                      >
                        <i className="ri-edit-line text-sm"></i>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteConversation(conversation.id);
                        }}
                        className="p-1 rounded hover:bg-red-500 hover:text-white"
                        title="删除对话"
                      >
                        <i className="ri-delete-bin-line text-sm"></i>
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 text-center text-xs text-gray-500 dark:text-gray-400">
        AI Chat © {new Date().getFullYear()}
      </div>
    </div>
  );
}