import { useState, useEffect } from 'react';
import { apiClient, type Conversation, type Message } from '../api/client';

interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export function useConversations() {
  const [conversations, setConversations] = useState<ConversationWithMessages[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load conversations
  const loadConversations = async () => {
    try {
      setLoading(true);
      const convs = await apiClient.getConversations();
      
      // Load messages for each conversation
      const convsWithMessages = await Promise.all(
        convs.map(async (conv) => {
          const messages = await apiClient.getMessages(conv.id);
          return { ...conv, messages };
        })
      );
      
      setConversations(convsWithMessages);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversations');
      setLoading(false);
    }
  };

  // Create new conversation
  const createConversation = async (title: string) => {
    try {
      const newConversation = await apiClient.createConversation(title);
      const convWithMessages: ConversationWithMessages = {
        ...newConversation,
        messages: []
      };
      setConversations(prev => [convWithMessages, ...prev]);
      setActiveConversationId(newConversation.id);
      return newConversation;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create conversation');
      throw err;
    }
  };

  // Update conversation title
  const updateConversationTitle = async (conversationId: number, title: string) => {
    try {
      const updatedConversation = await apiClient.updateConversationTitle(conversationId, title);
      setConversations(prev => 
        prev.map(conv => 
          conv.id === conversationId ? { ...conv, ...updatedConversation } : conv
        )
      );
      return updatedConversation;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update conversation title');
      throw err;
    }
  };

  // Delete conversation
  const deleteConversation = async (conversationId: number) => {
    try {
      await apiClient.deleteConversation(conversationId);
      setConversations(prev => prev.filter(c => c.id !== conversationId));
      if (activeConversationId === conversationId) {
        const remaining = conversations.filter(c => c.id !== conversationId);
        setActiveConversationId(remaining.length > 0 ? remaining[0]?.id : null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete conversation');
      throw err;
    }
  };

  // Send message with proper user message display and streaming AI response
  const sendMessage = async (
    selectedModel: string,
    conversationId: number, 
    content: string, 
    messageType: string = 'text',
    file?: File
  ) => {
    try {
      // Handle file upload if provided
      let fileUrl: string = '';
      if (file) {
        // Upload the file to the backend
        const uploadResponse = await apiClient.uploadFile(file);
        fileUrl = `${apiClient.baseUrl}${uploadResponse.url}`;
      }

      // First, add the user message immediately to the UI
      const userMessage: Message = {
        id: Date.now(), // Temporary ID
        conversation_id: conversationId,
        content: content,
        role: 'user',
        message_type: messageType as 'text' | 'image' | 'document' | 'audio',
        file_url: fileUrl,
        created_at: new Date().toISOString()
      };

      // Update conversation with user message immediately
      setConversations(prev => 
        prev.map(conv => {
          if (conv.id === conversationId) {
            return {
              ...conv,
              messages: [...conv.messages, userMessage],
              updated_at: new Date().toISOString()
            };
          }
          return conv;
        })
      );

      // Create a temporary AI message for streaming
      const tempAiMessageId = Date.now() + 1;
      const tempAiMessage: Message = {
        id: tempAiMessageId,
        conversation_id: conversationId,
        content: '',
        role: 'assistant',
        message_type: 'text',
        created_at: new Date().toISOString()
      };

      // Add temporary AI message
      setConversations(prev => 
        prev.map(conv => {
          if (conv.id === conversationId) {
            return {
              ...conv,
              messages: [...conv.messages, tempAiMessage],
              updated_at: new Date().toISOString()
            };
          }
          return conv;
        })
      );

      // Use streaming to get AI response
      let accumulatedContent = '';
      let thinkingProcess = '';
      
      await apiClient.chatStream(
        fileUrl,
        conversationId,
        selectedModel, // Default model
        content,
        messageType,
        (event: any) => {
          if (event.type === 'thinking_process') {
            // 累积思考过程
            thinkingProcess += event.data.message + '\n';
            
            // 更新消息内容，包含思考过程和模型回复的格式
            const formattedContent = `[思考过程]\n${thinkingProcess}[模型回复]\n${accumulatedContent}`;
            
            // 更新AI消息内容
            setConversations(prev => 
              prev.map(conv => {
                if (conv.id === conversationId) {
                  const updatedMessages = conv.messages.map(msg => {
                    if (msg.id === tempAiMessageId) {
                      return {
                        ...msg,
                        content: formattedContent
                      };
                    }
                    return msg;
                  });
                  
                  return {
                    ...conv,
                    messages: updatedMessages,
                    updated_at: new Date().toISOString()
                  };
                }
                return conv;
              })
            );
          } else if (event.type === 'text_message_delta') {
            accumulatedContent += event.data.content;
            
            // 更新消息内容，包含思考过程和模型回复的格式
            const formattedContent = thinkingProcess 
              ? `[思考过程]\n${thinkingProcess}[模型回复]\n${accumulatedContent}`
              : accumulatedContent;
            
            // 更新AI消息内容
            setConversations(prev => 
              prev.map(conv => {
                if (conv.id === conversationId) {
                  const updatedMessages = conv.messages.map(msg => {
                    if (msg.id === tempAiMessageId) {
                      return {
                        ...msg,
                        content: formattedContent
                      };
                    }
                    return msg;
                  });
                  
                  return {
                    ...conv,
                    messages: updatedMessages,
                    updated_at: new Date().toISOString()
                  };
                }
                return conv;
              })
            );
          } else if (event.type === 'text_message_end') {
            // 构建最终的格式化内容
            const finalContent = thinkingProcess 
              ? `[思考过程]\n${thinkingProcess}[模型回复]\n${accumulatedContent}`
              : accumulatedContent;
            
            // Replace temporary message with final message
            setConversations(prev => 
              prev.map(conv => {
                if (conv.id === conversationId) {
                  const updatedMessages = conv.messages.map(msg => {
                    if (msg.id === tempAiMessageId) {
                      return {
                        ...msg,
                        id: event.data.message_id, // Use real ID from backend
                        content: finalContent
                      };
                    }
                    return msg;
                  });
                  
                  return {
                    ...conv,
                    messages: updatedMessages,
                    updated_at: new Date().toISOString()
                  };
                }
                return conv;
              })
            );
          }
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      // Remove the temporary messages if there was an error
      setConversations(prev => 
        prev.map(conv => {
          if (conv.id === conversationId) {
            const filteredMessages = conv.messages.filter(
              msg => msg.id !== Date.now() && msg.id !== (Date.now() + 1)
            );
            return {
              ...conv,
              messages: filteredMessages,
              updated_at: new Date().toISOString()
            };
          }
          return conv;
        })
      );
      throw err;
    }
  };

  // Get active conversation
  const activeConversation = conversations.find(c => c.id === activeConversationId) || null;

  return {
    conversations,
    activeConversation,
    activeConversationId,
    setActiveConversationId,
    loading,
    error,
    loadConversations,
    createConversation,
    updateConversationTitle,
    deleteConversation,
    sendMessage
  };
}