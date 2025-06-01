import React, { useState, useEffect } from 'react';
import { ChatSidebar } from '../components/ChatSidebar';
import { MessageList } from '../components/MessageList';
import { MessageInput } from '../components/MessageInput';
import { MembersPanel } from '../components/MembersPanel';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';

export const ChatPage: React.FC = () => {
  const { user, logout } = useAuth();
  const { clearChat } = useChat();
  const [showMembers, setShowMembers] = useState(false);

  // Cleanup effect: clear chat state when unmounting
  useEffect(() => {
    // This effect only runs on mount/unmount
    return () => {
      // We're removing console.log to reduce noise
      clearChat();
    };
  }, []); // Empty dependency array - only run on mount/unmount

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="chat-page fade-in">
      <header className="app-header">
        <h1>Python Chat</h1>
        <div className="user-info">
          {user && (
            <>
              <span>Logged in as {user.username}</span>
              <button onClick={handleLogout}>Logout</button>
            </>
          )}
        </div>
      </header>

      <main className="chat-container">
        <ChatSidebar />

        <div className="chat-area">
          <MessageList showMembers={showMembers} setShowMembers={setShowMembers} />
          <MessageInput />
        </div>

        {showMembers && (
          <div className="members-area slide-in-right">
            <MembersPanel setShowMembers={setShowMembers} />
          </div>
        )}
      </main>
    </div>
  );
};
