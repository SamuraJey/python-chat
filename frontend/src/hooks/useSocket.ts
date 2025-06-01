import { useEffect, useState } from 'react';
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
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState<boolean>(false);
  const [messages, setMessages] = useState<SocketMessage[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<string[]>([]);

  // Initialize socket connection
  useEffect(() => {
    const socketInstance = io(SOCKET_URL, {
      withCredentials: true, // Important for authentication
    });

    socketInstance.on('connect', () => {
      console.log('Socket connected successfully');
      setConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('Socket disconnected');
      setConnected(false);
    });

    socketInstance.on('error', (error) => {
      console.error('Socket error:', error);
    });

    socketInstance.on('set_username', (data) => {
      console.log('Username set:', data.username);
    });

    socketInstance.on('receive_message', (data) => {
      console.log('Message received:', data);
      // Convert backend message format to our frontend format
      const socketMessage: SocketMessage = {
        id: data.message_id,
        content: data.message,
        username: data.username,
        timestamp: new Date(data.timestamp).toISOString()
      };
      setMessages((prevMessages) => [...prevMessages, socketMessage]);
    });

    socketInstance.on('online_users', (data) => {
      console.log('Online users:', data.users);
      setOnlineUsers(data.users);
    });

    // Join chat room if chatId is provided initially
    if (options.chatId) {
      console.log(`Joining chat ${options.chatId}`);
      socketInstance.emit('join', { chat_id: options.chatId });

      socketInstance.on('joined_chat', (data) => {
        console.log('Successfully joined chat room:', data.chat_id);
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

    if (options.chatId) {
      socket.emit('send_message', {
        chat_id: options.chatId,
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
    if (options.chatId) {
      socket.emit('leave', { chat_id: options.chatId });
    }

    // Join new chat
    socket.emit('join', { chat_id: chatId });

    // Update options
    options.chatId = chatId;
  };

  // Function to leave current chat
  const leaveChat = () => {
    if (!socket || !connected || !options.chatId) {
      return;
    }

    socket.emit('leave', { chat_id: options.chatId });
    options.chatId = undefined;
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
  }));
};
