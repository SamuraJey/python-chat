import React, { useState } from 'react';
import { useChat } from '../context/ChatContext';

export const MessageInput: React.FC = () => {
  const [message, setMessage] = useState('');
  const { sendMessage, currentChat } = useChat();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim()) return;

    sendMessage(message);
    setMessage('');
  };

  if (!currentChat) {
    return null; // Don't render input if no chat is selected
  }

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <input
        type="text"
        className="input-modern"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your message..."
        disabled={!currentChat}
      />
      <button
        type="submit"
        className="btn-primary btn-icon"
        disabled={!message.trim()}
        title="Send message"
      >
        Send
      </button>
    </form>
  );
};
