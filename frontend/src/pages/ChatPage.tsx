import React, { useState } from 'react';
import { ChatSidebar } from '../components/ChatSidebar';
import { MessageList } from '../components/MessageList';
import { MessageInput } from '../components/MessageInput';
import { MembersPanel } from '../components/MembersPanel';
import { useAuth } from '../context/AuthContext';

export const ChatPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [showMembers, setShowMembers] = useState(false);

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="chat-page">
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
          <MessageList />
          <MessageInput />

          <div className="members-toggle">
            <button onClick={() => setShowMembers(!showMembers)}>
              {showMembers ? 'Hide Members' : 'Show Members'}
            </button>
          </div>
        </div>

        {showMembers && (
          <div className="members-area">
            <MembersPanel />
          </div>
        )}
      </main>
    </div>
  );
};
