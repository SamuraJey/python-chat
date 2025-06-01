import { createContext, useContext, useState, type ReactNode, useEffect } from 'react';
import { chatApi, type Chat, type ChatMessage, type ChatMember } from '../services/api';
import { useSocket, formatApiMessagesToSocketMessages, type SocketMessage } from '../hooks/useSocket';
import { useAuth } from './AuthContext';

interface ChatContextType {
  chats: Chat[];
  currentChat: Chat | null;
  messages: SocketMessage[];
  members: ChatMember[];
  loading: boolean;
  error: string | null;
  selectChat: (chatId: number) => void;
  clearChat: () => void; // Add a method to clear current chat state
  sendMessage: (content: string) => void;
  createChat: (name: string, isGroup: boolean, userIds: number[]) => Promise<Chat | null>;
  searchUsers: (query: string) => Promise<{ id: number; username: string }[]>;
  banUser: (userId: number, reason: string) => Promise<boolean>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [apiMessages, setApiMessages] = useState<ChatMessage[]>([]);
  const [members, setMembers] = useState<ChatMember[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const { isAuthenticated } = useAuth();
  const {
    messages: socketMessages,
    sendMessage: socketSendMessage,
    joinChat,
    leaveChat
  } = useSocket({
    chatId: currentChat?.id,
  });  // Combine API messages and socket messages
  const apiSocketMessages = formatApiMessagesToSocketMessages(apiMessages);

  // Add current chat ID to socket messages if not already present
  const taggedSocketMessages = socketMessages.map(msg => {
    if (!msg.chatId && currentChat) {
      return { ...msg, chatId: currentChat.id };
    }
    return msg;
  });

  const combinedMessages = [...apiSocketMessages, ...taggedSocketMessages];

  // Create a Map to deduplicate messages based on ID - handles the case where we might receive
  // the same message from both API and socket
  const messagesMap = new Map();
  combinedMessages.forEach(msg => {
    if (msg.id) {
      messagesMap.set(msg.id, msg);
    } else if (msg.content) {
      // For messages without IDs (e.g., temporary ones), just include them
      // Use content + username + timestamp + chatId as a pseudo-id
      const pseudoId = `${msg.content}-${msg.username}-${msg.timestamp || Date.now()}-${msg.chatId || 'unknown'}`;
      messagesMap.set(pseudoId, msg);
    }
  });

  // Convert back to array and sort by timestamp
  const messages = Array.from(messagesMap.values())
    .sort((a, b) => {
      const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
      const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
      return timeA - timeB;
    });

  // Removed debug logging effect

  // Load user chats on mount if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadChats();
    }
  }, [isAuthenticated]);

  // Load chat messages and members when current chat changes
  useEffect(() => {
    if (currentChat) {
      loadChatMessages(currentChat.id);
      loadChatMembers(currentChat.id);
    }
  }, [currentChat]);

  // Reload messages when we receive new ones via socket
  // This ensures we have the complete message data with ID
  useEffect(() => {
    if (socketMessages.length > 0 && currentChat) {
      console.log(`Received new socket message for chat ${currentChat.id}`);
      // No API call here; rely on WebSocket updates
    }
  }, [socketMessages]);

  // Load messages for the selected chat
  useEffect(() => {
    if (currentChat) {
      setLoading(true);
      chatApi
        .getChatMessages(currentChat.id) // Use the correct method
        .then((response) => {
          setApiMessages(response.data || []); // Provide fallback for undefined data
        })
        .catch((err: Error) => {
          setError('Failed to load messages');
          console.error(err);
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setApiMessages([]); // Clear messages when no chat is selected
    }
  }, [currentChat]);

  const loadChats = async () => {
    setLoading(true);
    try {
      const response = await chatApi.getUserChats();
      if (response.success && response.data) {
        setChats(response.data);
      } else {
        setError(response.error || 'Failed to load chats');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while loading chats');
    } finally {
      setLoading(false);
    }
  };

  const loadChatMessages = async (chatId: number) => {
    setLoading(true);
    try {
      const response = await chatApi.getChatMessages(chatId);
      if (response.success && response.data) {
        setApiMessages(response.data);
      } else {
        setError(response.error || 'Failed to load chat messages');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while loading messages');
    } finally {
      setLoading(false);
    }
  };

  const loadChatMembers = async (chatId: number) => {
    setLoading(true);
    try {
      const response = await chatApi.getChatMembers(chatId);
      if (response.success && response.data) {
        setMembers(response.data);
      } else {
        setError(response.error || 'Failed to load chat members');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while loading members');
    } finally {
      setLoading(false);
    }
  };

  const selectChat = (chatId: number) => {
    // Check if the selected chat is already the current chat
    if (currentChat?.id === chatId) {
      console.log('Already in the selected chat, no action taken');
      return;
    }

    const chat = chats.find((c) => c.id === chatId);
    if (chat) {
      // Leave current chat if any
      if (currentChat) {
        leaveChat();
      }

      // Clear any existing API messages
      setApiMessages([]);

      // Set new current chat
      setCurrentChat(chat);

      // Join new chat room
      joinChat(chatId);
    }
  };

  // Function to clear current chat state
  const clearChat = () => {
    if (currentChat) {
      // Leave current chat room via socket
      leaveChat();

      // Clear current chat and related data
      setCurrentChat(null);
      setApiMessages([]);
      // Removed console.log to reduce noise
    }
  };

  const sendMessage = (content: string) => {
    if (!currentChat) {
      setError('No chat selected');
      return;
    }

    if (!content.trim()) {
      setError('Cannot send empty message');
      return;
    }

    // Send the message via socket
    socketSendMessage(content);

    console.log('Message sent, waiting for server echo');
  };

  const createChat = async (name: string, isGroup: boolean, userIds: number[]): Promise<Chat | null> => {
    setLoading(true);
    try {
      const response = await chatApi.createChat({
        name,
        is_group: isGroup,
        user_ids: userIds,
      });

      if (response.success && response.data) {
        // Add the new chat to the list
        setChats((prev) => [...prev, response.data!]);
        return response.data;
      } else {
        setError(response.error || 'Failed to create chat');
        return null;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while creating chat');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const searchUsers = async (query: string): Promise<{ id: number; username: string }[]> => {
    if (query.length < 2) {
      return [];
    }

    try {
      const response = await chatApi.searchUsers(query);
      if (response.success && response.data) {
        return response.data;
      } else {
        setError(response.error || 'Failed to search users');
        return [];
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while searching users');
      return [];
    }
  };

  const banUser = async (userId: number, reason: string): Promise<boolean> => {
    if (!currentChat) {
      setError('No chat selected');
      return false;
    }

    setLoading(true);
    try {
      const response = await chatApi.banUser(currentChat.id, userId, reason);
      if (response.success) {
        // Update members list to reflect the ban
        loadChatMembers(currentChat.id);
        return true;
      } else {
        setError(response.error || 'Failed to ban user');
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while banning user');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const value = {
    chats,
    currentChat,
    messages,
    members,
    loading,
    error,
    selectChat,
    clearChat, // Add the new method to the context value
    sendMessage,
    createChat,
    searchUsers,
    banUser,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
