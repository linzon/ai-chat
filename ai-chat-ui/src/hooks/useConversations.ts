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
    conversationId: number, 
    model: string, 
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

      // Then send the message to the API and get AI response
      const response = await apiClient.chat(fileUrl, conversationId, model, content, messageType);
      
      // Update with the real AI message (replace temporary IDs if needed)
      setConversations(prev => 
        prev.map(conv => {
          if (conv.id === conversationId) {
            // Find and replace the AI message (in case we want to stream it in the future)
            const updatedMessages = [
              ...conv.messages,
              {
                id: response.ai_message.id,
                conversation_id: conversationId,
                content: response.ai_message.content,
                role: 'assistant' as const,
                message_type: response.ai_message.message_type,
                created_at: new Date().toISOString()
              }
            ];
            
            return {
              ...conv,
              messages: updatedMessages,
              updated_at: new Date().toISOString()
            };
          }
          return conv;
        })
      );
      
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
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