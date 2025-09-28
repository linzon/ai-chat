import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useConversations } from '../../hooks/useConversations';
import { useTheme } from '../../hooks/useTheme';
import { apiClient, type Message, type AGUIEvent } from '../../api/client';
import LoginPage from '../auth/LoginPage';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import TopBar from './components/TopBar';

export default function ChatPage() {
  const { user, logout } = useAuth();
  const {
    conversations,
    activeConversation,
    activeConversationId,
    setActiveConversationId,
    loadConversations,
    createConversation,
    updateConversationTitle,
    deleteConversation,
    sendMessage
  } = useConversations();
  const { theme, toggleTheme } = useTheme();
  const [aiModels, setAiModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    if (user) {
      loadConversations().catch(err => {
        setError(err instanceof Error ? err.message : '加载对话失败');
      });
      
      // 获取AI模型列表
      loadAiModels().catch(err => {
        setError(err instanceof Error ? err.message : '加载AI模型失败');
      });
    }
  }, [user]);

  const loadAiModels = async () => {
    try {
      const models = await apiClient.getAvailableModels();
      setAiModels(models);
      // 默认选择第一个模型，如果列表为空则不设置
      if (models.length > 0 && !selectedModel) {
        setSelectedModel(models[0]);
      }
    } catch (err) {
      console.error('获取AI模型列表失败:', err);
      setAiModels([]); // 空列表保护
      throw err;
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConversation = await createConversation('新对话');
      // 创建成功后立即切换到新对话
      if (newConversation?.id) {
        setActiveConversationId(newConversation.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建对话失败');
    }
  };

  const handleDeleteConversation = async (id: number) => {
    try {
      await deleteConversation(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除对话失败');
    }
  };

  const handleUpdateConversationTitle = async (id: number, title: string) => {
    try {
      await updateConversationTitle(id, title);
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新对话标题失败');
    }
  };

  const handleSendMessage = async (content: string, type: 'text' | 'image' | 'document' | 'audio' = 'text', file?: File) => {
    if (!activeConversationId || !user) return;

    try {
      setIsLoading(true);
      setError(null);
      
      // 发送消息
      await sendMessage(selectedModel, activeConversationId, content, type, file);
    } catch (err) {
      setError(err instanceof Error ? err.message : '发送消息失败');
      console.error('发送消息失败:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // 获取需要流式输出的消息ID列表
  const getStreamingMessageIds = () => {
    if (!activeConversation) return new Set<string>();
    
    // 只有最新的AI消息需要流式输出
    const aiMessages = activeConversation.messages.filter(msg => msg.role === 'assistant');
    if (aiMessages.length > 0) {
      const latestAiMessage = aiMessages[aiMessages.length - 1];
      return new Set([latestAiMessage.id]);
    }
    return new Set<string>();
  };

  const streamingMessageIds = getStreamingMessageIds();

  const handleExportChat = () => {
    if (!activeConversation) return;
    
    const exportData = {
      title: activeConversation.title,
      messages: activeConversation.messages,
      exportTime: new Date().toLocaleString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${activeConversation.title}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleShareChat = () => {
    // Share functionality is handled in TopBar component
    console.log('Sharing chat:', activeConversation?.title);
  };

  const handleLoginSuccess = () => {
    // 登录成功后重新加载页面或刷新状态
    window.location.reload();
  };

  if (!user) {
    return <LoginPage onSuccess={handleLoginSuccess} />;
  }

  const containerClasses = theme === 'dark' 
    ? 'bg-gray-900 text-gray-100' 
    : 'bg-gray-50 text-gray-900';

  return (
    <div className={`h-screen flex flex-col ${containerClasses}`}>
      <TopBar
        aiModels={aiModels}
        selectedModel={selectedModel}
        onModelChange={setSelectedModel}
        theme={theme}
        onThemeToggle={toggleTheme}
        onExportChat={handleExportChat}
        onShareChat={handleShareChat}
        onLogout={logout}
        conversationTitle={activeConversation?.title}
      />
      
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={setActiveConversationId}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          onUpdateConversationTitle={handleUpdateConversationTitle}
          theme={theme}
        />
        
        {activeConversation ? (
          <ChatArea
            messages={activeConversation.messages}
            onSendMessage={handleSendMessage}
            theme={theme}
            isLoading={isLoading}
          />
        ) : (
          <div className={`flex-1 flex items-center justify-center ${theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'}`}>
            <div className="text-center text-gray-500">
              <i className="ri-chat-3-line text-6xl mb-4"></i>
              <p className="text-xl font-medium">选择对话或创建新对话</p>
              <p className="text-sm mt-2">开始与AI助手的智能对话</p>
            </div>
          </div>
        )}
      </div>
      
      {error && (
        <div className="absolute bottom-4 right-4 bg-red-500 text-white p-3 rounded-lg shadow-lg">
          错误: {error}
        </div>
      )}
    </div>
  );
}