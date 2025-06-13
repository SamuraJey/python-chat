import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ChatSidebar } from '../components/ChatSidebar';
import { MessageList } from '../components/MessageList';
import { MessageInput } from '../components/MessageInput';
import { MembersPanel } from '../components/MembersPanel';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faSignOutAlt, faShieldAlt } from '@fortawesome/free-solid-svg-icons';


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
              <Link to="/profile" className="nav-button profile-button">
                <FontAwesomeIcon icon={faUser} /> Profile
              </Link>
              {user.is_admin && (
                <Link to="/admin" className="nav-button admin-button">
                  <FontAwesomeIcon icon={faShieldAlt} /> Admin
                </Link>
              )}
              <button onClick={handleLogout} className="nav-button logout-button">
                <FontAwesomeIcon icon={faSignOutAlt} /> Logout
              </button>
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
