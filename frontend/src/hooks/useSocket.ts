import { useEffect, useState, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { type ChatMessage } from '../services/api';

interface UseSocketOptions {
  chatId?: number;
}

export interface SocketMessage {
  id?: number;
  content: string;
  username: string;
  timestamp?: string;
  chatId?: number; // Add chatId to track which chat the message belongs to
}

interface UseSocketReturn {
  socket: Socket | null;
  connected: boolean;
  messages: SocketMessage[];
  onlineUsers: string[];
  sendMessage: (message: string) => void;
  joinChat: (chatId: number) => void;
  leaveChat: () => void;
}

const SOCKET_URL = '';

export const useSocket = (options: UseSocketOptions = {}): UseSocketReturn => {
  const optionsRef = useRef(options); // Use a ref to track options
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState<boolean>(false);
  const [messages, setMessages] = useState<SocketMessage[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<string[]>([]);

  // Keep ref updated with latest options
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  // Initialize socket connection
  useEffect(() => {
    const socketInstance = io(SOCKET_URL, {
      withCredentials: true, // Important for authentication
    });

    socketInstance.on('connect', () => {
      // Reduced logging
      setConnected(true);
    });

    socketInstance.on('disconnect', () => {
      // Reduced logging
      setConnected(false);
    });

    socketInstance.on('error', (error) => {
      console.error('Socket error:', error);
    });

    socketInstance.on('set_username', (_data) => {
      // Reduced logging - using underscore to mark unused parameter
    });

    socketInstance.on('receive_message', (data) => {
      console.log('Message received:', data);
      console.log('Current chatId:', optionsRef.current.chatId);

      // Convert backend message format to our frontend format
      const socketMessage: SocketMessage = {
        id: data.message_id,
        content: data.message,
        username: data.username,
        timestamp: new Date(data.timestamp).toISOString(),
        chatId: data.chat_id || optionsRef.current.chatId // Use chat_id from data if available, fallback to current chatId
      };

      // Only add messages to current chat's messages
      if (optionsRef.current.chatId && optionsRef.current.chatId === socketMessage.chatId) {
        console.log(`Adding message to chat ${optionsRef.current.chatId}, message chatId: ${socketMessage.chatId}`);
        setMessages((prevMessages) => {
          // Replace temporary local message if it exists
          const filteredMessages = prevMessages.filter(
            (msg) => !(msg.content === socketMessage.content && msg.username === 'You')
          );
          return [...filteredMessages, socketMessage];
        });
      } else {
        console.warn(`Ignoring message: no current chat selected or chatId mismatch. Expected chatId: ${optionsRef.current.chatId}, received chatId: ${socketMessage.chatId}`);
      }
    });

    socketInstance.on('online_users', (data) => {
      // Update online users without logging
      setOnlineUsers(data.users);
    });

    // Join chat room if chatId is provided initially
    if (options.chatId) {
      // Join without logging
      socketInstance.emit('join', { chat_id: options.chatId });

      socketInstance.on('joined_chat', (_data) => {
        // No longer logging joins
      });
    }

    setSocket(socketInstance);

    // Cleanup on unmount
    return () => {
      socketInstance.disconnect();
    };
  }, []); // Empty dependency array ensures this runs once

  // Function to send a message
  const sendMessage = (content: string) => {
    if (!socket || !connected) {
      console.error('Cannot send message: socket not connected');
      return;
    }

    if (optionsRef.current.chatId) {
      // Add local message immediately for instant feedback
      const localMessage: SocketMessage = {
        content: content,
        username: 'You', // Will be replaced by actual username when server confirms
        timestamp: new Date().toISOString(),
        chatId: optionsRef.current.chatId
      };

      setMessages(prev => [...prev, localMessage]);

      // Then send to server
      socket.emit('send_message', {
        chat_id: optionsRef.current.chatId,
        message: content, // Change content to message to match backend expectation
      });
    } else {
      console.error('Cannot send message: no chat ID provided');
    }
  };

  // Function to join a specific chat
  const joinChat = (chatId: number) => {
    if (!socket || !connected) {
      console.error('Cannot join chat: socket not connected');
      return;
    }

    // Leave current chat first if in one
    if (optionsRef.current.chatId) {
      socket.emit('leave', { chat_id: optionsRef.current.chatId });
    }

    // Clear existing socket messages when changing chats
    setMessages([]);

    // Join new chat (only if it's a valid ID)
    if (chatId > 0) {
      socket.emit('join', { chat_id: chatId });
      optionsRef.current.chatId = chatId; // Update ref directly
      console.log(`Joined chat ${chatId}`);
    } else {
      optionsRef.current.chatId = undefined;
      console.log('Left chat');
    }
  };

  // Function to leave current chat
  const leaveChat = () => {
    if (!socket || !connected || !optionsRef.current.chatId) {
      return;
    }

    socket.emit('leave', { chat_id: optionsRef.current.chatId });
    optionsRef.current.chatId = undefined;
  };

  return {
    socket,
    connected,
    messages,
    onlineUsers,
    sendMessage,
    joinChat,
    leaveChat,
  };
};

// Utility to format messages from API to our socket message format
export const formatApiMessagesToSocketMessages = (apiMessages: ChatMessage[]): SocketMessage[] => {
  return apiMessages.map(message => ({
    id: message.id,
    content: message.content || '', // Handle potentially empty content
    username: message.username || 'Unknown User', // Provide a fallback for username
    timestamp: message.timestamp || new Date().toISOString(), // Ensure we have a timestamp
    chatId: message.chat_id, // Include chat ID from API messages
  }));
};
