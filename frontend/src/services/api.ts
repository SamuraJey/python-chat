// API Service for Python Chat Application

// Base API URL - Using Vite's proxy configuration
const API_URL = '';

// Interface for API responses
export interface ApiResponse<T = any> {
  success?: boolean;
  data?: T;
  error?: string;
}

// Auth Types
export interface LoginRequest {
  username: string;
  password: string;
  remember?: boolean;
}

export interface RegisterRequest {
  username: string;
  password: string;
  password2: string;
}

// Chat Types
export interface Chat {
  id: number;
  name: string;
  is_group: boolean;
}

export interface ChatMessage {
  id: number;
  content: string;
  username: string;
  timestamp: string;
}

export interface ChatMember {
  id: number;
  username: string;
  is_moderator: boolean;
}

export interface User {
  id: number;
  username: string;
}

// API client for authentication
export const authApi = {
  // Login user
  login: async (credentials: LoginRequest): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
        credentials: 'include', // Important for cookies
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }

      return {
        success: true,
        data: { username: data.username }
      };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Login failed' };
    }
  },

  // Register user
  register: async (userData: RegisterRequest): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      return { success: true, data };
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Registration failed' };
    }
  },

  // Logout user
  logout: async (): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/api/auth/logout`, {
        method: 'POST', // Changed to POST as per our API implementation
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Logout failed');
      }

      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Logout failed' };
    }
  },

  // Check authentication status
  checkStatus: async (): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/api/auth/status`, {
        method: 'GET',
        credentials: 'include',
      });

      const data = await response.json();

      return {
        success: response.ok,
        data: {
          isAuthenticated: data.isAuthenticated,
          username: data.username,
          userId: data.userId
        }
      };
    } catch (error) {
      console.error('Auth status check error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to check authentication status',
        data: { isAuthenticated: false }
      };
    }
  },
};

// API client for chats
export const chatApi = {
  // Get all chats for the current user
  getUserChats: async (): Promise<ApiResponse<Chat[]>> => {
    try {
      const response = await fetch(`${API_URL}/api/chats`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch chats');
      }

      const { chats } = await response.json();
      return { success: true, data: chats };
    } catch (error) {
      console.error('Error fetching chats:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Failed to fetch chats' };
    }
  },

  // Get messages for a specific chat
  getChatMessages: async (chatId: number): Promise<ApiResponse<ChatMessage[]>> => {
    try {
      const response = await fetch(`${API_URL}/api/messages/${chatId}`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch messages');
      }

      const { messages } = await response.json();
      return { success: true, data: messages };
    } catch (error) {
      console.error('Error fetching chat messages:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Failed to fetch chat messages' };
    }
  },

  // Get members of a specific chat
  getChatMembers: async (chatId: number): Promise<ApiResponse<ChatMember[]>> => {
    try {
      const response = await fetch(`${API_URL}/api/chat/${chatId}/members`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch chat members');
      }

      const { members } = await response.json();
      return { success: true, data: members };
    } catch (error) {
      console.error('Error fetching chat members:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Failed to fetch chat members' };
    }
  },

  // Search users
  searchUsers: async (query: string): Promise<ApiResponse<User[]>> => {
    try {
      const response = await fetch(`${API_URL}/api/search-users?query=${encodeURIComponent(query)}`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to search users');
      }

      const { users } = await response.json();
      return { success: true, data: users };
    } catch (error) {
      console.error('Error searching users:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Failed to search users' };
    }
  },

  // Create a new chat
  createChat: async (chatData: { name: string; is_group: boolean; user_ids: number[] }): Promise<ApiResponse<Chat>> => {
    try {
      const response = await fetch(`${API_URL}/api/chats/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chatData),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to create chat');
      }

      const data = await response.json();
      return { success: true, data: data.chat };
    } catch (error) {
      console.error('Error creating chat:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Failed to create chat' };
    }
  },

  // Ban a user from a chat (moderator only)
  banUser: async (chatId: number, userId: number, reason: string): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/api/chat/${chatId}/ban`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId, reason }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to ban user');
      }

      return { success: true };
    } catch (error) {
      console.error('Error banning user:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Failed to ban user' };
    }
  },
};
