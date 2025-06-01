import React, { useState } from 'react';
import { useChat } from '../context/ChatContext';
import { useAuth } from '../context/AuthContext';

export const ChatSidebar: React.FC = () => {
  const { chats, currentChat, selectChat, loading } = useChat();
  const { user } = useAuth();
  const [showNewChatForm, setShowNewChatForm] = useState(false);
  const [newChatName, setNewChatName] = useState('');
  const [isGroupChat, setIsGroupChat] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<{ id: number; username: string }[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<{ id: number; username: string }[]>([]);

  const { searchUsers, createChat } = useChat();

  const handleSearch = async () => {
    if (searchQuery.length < 2) return;

    const results = await searchUsers(searchQuery);
    setSearchResults(results);
  };

  const handleSelectUser = (user: { id: number; username: string }) => {
    // Don't add duplicates
    if (!selectedUsers.some(u => u.id === user.id)) {
      setSelectedUsers([...selectedUsers, user]);
    }
    setSearchResults([]);
    setSearchQuery('');
  };

  const handleRemoveUser = (userId: number) => {
    setSelectedUsers(selectedUsers.filter(user => user.id !== userId));
  };

  const handleCreateChat = async () => {
    if (!newChatName.trim()) {
      return;
    }

    // For private chats, ensure only one user is selected
    if (!isGroupChat && selectedUsers.length !== 1) {
      alert('Private chat requires exactly one user');
      return;
    }

    // For group chats, ensure at least one user is selected
    if (isGroupChat && selectedUsers.length === 0) {
      alert('Group chat requires at least one user');
      return;
    }

    const userIds = selectedUsers.map(user => user.id);

    const newChat = await createChat(newChatName, isGroupChat, userIds);
    if (newChat) {
      // Reset form and select the new chat
      setNewChatName('');
      setIsGroupChat(false);
      setSelectedUsers([]);
      setShowNewChatForm(false);
      selectChat(newChat.id);
    }
  };

  return (
    <div className="chat-sidebar">
      <div className="sidebar-header">
        <h3>Your Chats</h3>
        <button onClick={() => setShowNewChatForm(true)}>
          + New Chat
        </button>
      </div>

      {showNewChatForm && (
        <div className="new-chat-form">
          <h4>Create New Chat</h4>
          <input
            type="text"
            placeholder="Chat name"
            value={newChatName}
            onChange={(e) => setNewChatName(e.target.value)}
          />

          <div className="checkbox-group">
            <input
              type="checkbox"
              id="is-group"
              checked={isGroupChat}
              onChange={(e) => setIsGroupChat(e.target.checked)}
            />
            <label htmlFor="is-group">Group Chat</label>
          </div>

          <div className="search-users">
            <input
              type="text"
              placeholder="Search users"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button onClick={handleSearch}>Search</button>
          </div>

          {searchResults.length > 0 && (
            <ul className="search-results">
              {searchResults.map(user => (
                <li key={user.id} onClick={() => handleSelectUser(user)}>
                  {user.username}
                </li>
              ))}
            </ul>
          )}

          {selectedUsers.length > 0 && (
            <div className="selected-users">
              <h5>Selected Users:</h5>
              <ul>
                {selectedUsers.map(user => (
                  <li key={user.id}>
                    <span className="user-name">{user.username}</span>
                    <button onClick={() => handleRemoveUser(user.id)}>×</button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="form-actions">
            <button onClick={handleCreateChat}>Create</button>
            <button onClick={() => setShowNewChatForm(false)}>Cancel</button>
          </div>
        </div>
      )}

      <div className="chat-list">
        {loading ? (
          <div>Loading chats...</div>
        ) : chats.length === 0 ? (
          <div>No chats yet</div>
        ) : (
          <ul>
            {chats.map(chat => (
              <li
                key={chat.id}
                className={currentChat?.id === chat.id ? 'active' : ''}
                onClick={() => selectChat(chat.id)}
              >
                <div className="chat-item">
                  <div className={`chat-name ${chat.is_group ? 'group-chat' : 'private-chat'}`}>
                    {chat.name}
                  </div>
                  <div className="chat-meta">
                    <span className="chat-type">
                      {chat.is_group ? 'Group' : 'Private'}
                    </span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
