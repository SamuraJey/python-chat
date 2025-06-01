import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../context/ChatContext';
import type { SocketMessage } from '../hooks/useSocket';

export const MessageList: React.FC = () => {
  const { messages, currentChat, loading } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!currentChat) {
    return <div className="no-chat-selected">Select a chat to start messaging</div>;
  }

  if (loading) {
    return <div className="loading">Loading messages...</div>;
  }

  return (
    <div className="message-list">
      <div className="chat-header">
        <h3>{currentChat.name}</h3>
        <div className="chat-type">
          {currentChat.is_group ? 'Group Chat' : 'Private Chat'}
        </div>
      </div>

      <div className="messages">
        {messages.length === 0 ? (
          <div className="no-messages">No messages yet</div>
        ) : (
          messages.map((message, index) => (
            <MessageItem
              key={message.id || `msg-${index}-${message.username}-${Date.now()}`}
              message={message}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

interface MessageItemProps {
  message: SocketMessage;
}

const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  // Format timestamp if available
  const formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString()
    : '';

  // Handle potential null or undefined content
  const messageContent = message.content || '';

  // Skip rendering empty messages
  if (!messageContent.trim()) {
    console.warn('Empty message skipped', message);
    return null;
  }

  return (
    <div className="message-item">
      <div className="message-header">
        <span className="message-author">{message.username || 'Unknown'}</span>
        {formattedTime && <span className="message-time">{formattedTime}</span>}
      </div>
      <div className="message-content">{messageContent}</div>
    </div>
  );
};
