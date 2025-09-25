
import { useState } from 'react';
import Select from '../../../components/base/Select';
import Button from '../../../components/base/Button';
import Modal from '../../../components/base/Modal';

interface TopBarProps {
  aiModels: string[];
  selectedModel: string;
  onModelChange: (model: string) => void;
  theme: 'light' | 'dark';
  onThemeToggle: () => void;
  onExportChat: () => void;
  onShareChat: () => void;
  onLogout: () => void;
  conversationTitle?: string;
}

export default function TopBar({
  aiModels,
  selectedModel,
  onModelChange,
  theme,
  onThemeToggle,
  onExportChat,
  onShareChat,
  onLogout,
  conversationTitle
}: TopBarProps) {
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareUrl, setShareUrl] = useState('');

  const handleShare = () => {
    // 模拟生成分享链接
    const mockShareUrl = `https://chat.example.com/share/${Math.random().toString(36).substr(2, 9)}`;
    setShareUrl(mockShareUrl);
    setShowShareModal(true);
    onShareChat();
  };

  const copyShareUrl = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      alert('分享链接已复制到剪贴板');
    } catch (error) {
      console.error('复制失败:', error);
    }
  };

  const topBarClasses = theme === 'dark' 
    ? 'bg-gray-900 border-gray-700 text-gray-100' 
    : 'bg-white border-gray-200 text-gray-900';

  return (
    <>
      <div className={`border-b px-4 py-3 flex items-center justify-between ${topBarClasses}`}>
        <div className="flex items-center space-x-4">
          <h1 className="text-lg font-semibold">
            {conversationTitle || '智能聊天机器人'}
          </h1>
        </div>

        <div className="flex items-center space-x-3">
          {/* AI Model Selection */}
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">AI模型:</span>
            <Select
              options={aiModels ? aiModels : []}
              value={selectedModel}
              onChange={onModelChange}
              className="w-48"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={onExportChat}
              title="导出聊天记录"
            >
              <i className="ri-download-line"></i>
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleShare}
              title="分享对话"
            >
              <i className="ri-share-line"></i>
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onThemeToggle}
              title={theme === 'light' ? '切换到深色模式' : '切换到浅色模式'}
            >
              <i className={theme === 'light' ? 'ri-moon-line' : 'ri-sun-line'}></i>
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onLogout}
              title="退出登录"
            >
              <i className="ri-logout-box-line"></i>
            </Button>
          </div>
        </div>
      </div>

      {/* Share Modal */}
      <Modal
        isOpen={showShareModal}
        onClose={() => setShowShareModal(false)}
        title="分享对话"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            通过以下链接分享此对话，其他人可以查看对话内容：
          </p>
          <div className="flex space-x-2">
            <input
              type="text"
              value={shareUrl}
              readOnly
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
            />
            <Button size="sm" onClick={copyShareUrl}>
              复制
            </Button>
          </div>
          <div className="text-xs text-gray-500">
            注意：分享的对话将公开可见，请确保不包含敏感信息。
          </div>
        </div>
      </Modal>
    </>
  );
}
