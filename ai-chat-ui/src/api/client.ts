// API Client for connecting frontend to backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface User {
  id: number;
  username: string;
  email: string;
  phone: string;
  created_at: string;
  updated_at: string;
}

interface LoginRequest {
  email_or_phone: string;
  password: string;
}

interface RegisterRequest {
  username: string;
  email: string;
  phone: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

interface Conversation {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

interface Message {
  id: number;
  conversation_id: number;
  content: string;
  role: 'user' | 'assistant';
  message_type: 'text' | 'image' | 'document' | 'audio';
  file_url?: string;
  created_at: string;
}

interface ChatRequest {
  conversation_id: number;
  model: string;
  message: string;
  message_type: 'text' | 'image' | 'document' | 'audio';
}

interface ChatResponse {
  user_message: {
    id: number;
    content: string;
    role: string;
    message_type: string;
  };
  ai_message: {
    id: number;
    content: string;
    role: string;
    message_type: string;
  };
}

interface UploadResponse {
  filename: string;
  saved_filename: string;
  url: string;
  content_type: string;
  size: number;
}

class ApiClient {
  public baseUrl: string;
  private token: string | null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.token = localStorage.getItem('token');
  }

  private getHeaders(includeAuth: boolean = true): Record<string, string> {
    const headers: Record<string, string> = {};

    if (includeAuth && this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  private async handleResponse(response: Response): Promise<any> {
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }
    return await response.json();
  }

  // User authentication
  async login(emailOrPhone: string, password: string): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/users/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email_or_phone: emailOrPhone,
        password: password,
      }),
    });

    const data = await this.handleResponse(response);
    this.token = data.access_token;
    localStorage.setItem('token', this.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }

  async register(username: string, email: string, phone: string, password: string): Promise<User> {
    const response = await fetch(`${this.baseUrl}/users/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        email,
        phone,
        password,
      }),
    });

    const data = await this.handleResponse(response);
    return data;
  }

  logout(): void {
    this.token = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  // Conversations
  async getConversations(): Promise<Conversation[]> {
    const response = await fetch(`${this.baseUrl}/conversations/`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return await this.handleResponse(response);
  }

  async createConversation(title: string): Promise<Conversation> {
    const response = await fetch(`${this.baseUrl}/conversations/`, {
      method: 'POST',
      headers: {
        ...this.getHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title }),
    });

    return await this.handleResponse(response);
  }

  async updateConversationTitle(conversationId: number, title: string): Promise<Conversation> {
    const response = await fetch(`${this.baseUrl}/conversations/${conversationId}`, {
      method: 'PUT',
      headers: {
        ...this.getHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title }),
    });

    return await this.handleResponse(response);
  }

  async deleteConversation(conversationId: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/conversations/${conversationId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    await this.handleResponse(response);
  }

  // Messages
  async getMessages(conversationId: number): Promise<Message[]> {
    const response = await fetch(`${this.baseUrl}/conversations/${conversationId}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return await this.handleResponse(response);
  }

  // Chat
  async chat(fileUrl: string, conversationId: number, model: string, message: string, messageType: string = 'text'): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/conversations/chat`, {
      method: 'POST',
      headers: {
        ...this.getHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        file_url: fileUrl,
        conversation_id: conversationId,
        model,
        message,
        message_type: messageType,
      }),
    });

    return await this.handleResponse(response);
  }

  // File upload
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/upload/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: formData,
    });

    return await this.handleResponse(response);
  }

  // Models
  async getAvailableModels(): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/conversations/models`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    const data = await this.handleResponse(response);
    return data.models;
  }
}

export const apiClient = new ApiClient();
export type { User, Conversation, Message, UploadResponse };