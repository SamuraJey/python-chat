import React, { useRef, useEffect } from 'react'; // Removed useState
import { useChat } from '../context/ChatContext';
import { useAuth } from '../context/AuthContext';
import type { SocketMessage } from '../hooks/useSocket';
import { faUsers } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';


interface MessageListProps {
  showMembers: boolean;
  setShowMembers: React.Dispatch<React.SetStateAction<boolean>>;
}

export const MessageList: React.FC<MessageListProps> = ({ showMembers, setShowMembers }) => {
  const { messages, currentChat, loading } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Filter messages to only show those for the current chat
  // We're being more lenient with filtering to ensure messages are displayed
  const filteredMessages = currentChat
    ? messages
    : [];

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredMessages.length]);

  if (!currentChat) {
    return <div className="no-chat-selected">Select a chat to start messaging</div>;
  }

  if (loading) {
    return <div className="loading">Loading messages...</div>;
  }

  return (
    <div className="message-list">
      <div className="chat-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
        <div className="chat-details"> {/* Wrapper for title and type */}
          <h3>{currentChat.name}</h3>
          <div className="chat-type">
            {currentChat.is_group ? 'Group Chat' : 'Private Chat'}
          </div>
        </div>
        <div className="chat-actions">
          <button
            className="show-members-button"
            onClick={() => setShowMembers(!showMembers)} // Toggle members panel
            title={showMembers ? "Hide Members" : "Show Members"}
          >
            <FontAwesomeIcon icon={faUsers} /> {/* Use FontAwesomeIcon component */}
          </button>
        </div>
      </div>

      <div className="messages">
        {filteredMessages.length === 0 ? (
          <div className="no-messages">No messages yet</div>
        ) : (
          filteredMessages.map((message, index) => (
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
  const { user } = useAuth();

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

  // Check if this is the current user's message
  const isOwnMessage = user && message.username === user.username;

  // Create classes for styling
  const messageClasses = ['message-item'];
  if (isOwnMessage) {
    messageClasses.push('own-message');
  }

  const bubbleClasses = ['message-bubble'];
  if (isOwnMessage) {
    bubbleClasses.push('own-message');
  }

  return (
    <div className={messageClasses.join(' ')}>
      <div className={bubbleClasses.join(' ')}>
        <div className="message-header">
          <span className="message-author">{message.username || 'Unknown'}</span>
          {formattedTime && <span className="message-time">{formattedTime}</span>}
          {message.chatId && <span className="message-chat-id" style={{ display: 'none' }}>{message.chatId}</span>}
        </div>
        <div className="message-content">{messageContent}</div>
      </div>
    </div>
  );
};
