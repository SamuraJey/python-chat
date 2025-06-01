import React, { useState, useEffect } from 'react';
import { useChat } from '../context/ChatContext';
import { faTimes } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

interface MembersPanelProps {
  setShowMembers: React.Dispatch<React.SetStateAction<boolean>>;
}

interface BannedUser {
  id: number;
  username: string;
  banned_at: string | null;
  reason: string | null;
}

export const MembersPanel: React.FC<MembersPanelProps> = ({ setShowMembers }) => {
  const { currentChat, members, banUser } = useChat();
  const [activeTab, setActiveTab] = useState<'members' | 'banned'>('members');
  const [showBanDialog, setShowBanDialog] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [banReason, setBanReason] = useState('');
  const [bannedUsers, setBannedUsers] = useState<BannedUser[]>([]);
  const [loadingBannedUsers, setLoadingBannedUsers] = useState(false);

  if (!currentChat) {
    return null;
  }

  const currentUserMember = members.find(member => member.is_moderator);
  const isModerator = Boolean(currentUserMember?.is_moderator);

  const handleBanClick = (userId: number) => {
    setSelectedUserId(userId);
    setShowBanDialog(true);
  };

  const handleBanConfirm = async () => {
    if (selectedUserId === null) return;

    const success = await banUser(selectedUserId, banReason);
    if (success) {
      setShowBanDialog(false);
      setBanReason('');
      setSelectedUserId(null);
    }
  };

  useEffect(() => {
    if (currentChat && activeTab === 'banned') {
      setLoadingBannedUsers(true);
      fetch(`/api/chat/${currentChat.id}/banned`)
        .then((response) => response.json())
        .then((data) => {
          if (data.banned_users) {
            setBannedUsers(data.banned_users);
          }
        })
        .catch((error) => console.error('Error loading banned users:', error))
        .finally(() => setLoadingBannedUsers(false));
    }
  }, [currentChat, activeTab]);

  const handleUnban = (userId: number) => {
    fetch(`/api/chat/${currentChat?.id}/unban`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          setBannedUsers((prev) => prev.filter((user) => user.id !== userId));
        }
      })
      .catch((error) => console.error('Error unbanning user:', error));
  };

  return (
    <div className="members-panel">
      <div className="members-panel-header">
        <h3>Members Panel</h3>
        <button
          className="btn-icon"
          onClick={() => setShowMembers(false)}
          title="Close Members Panel"
        >
          <FontAwesomeIcon icon={faTimes} />
        </button>
      </div>

      <div className="members-tabs">
        <button
          className={`tab-button ${activeTab === 'members' ? 'active' : ''}`}
          onClick={() => setActiveTab('members')}
        >
          Members
        </button>
        <button
          className={`tab-button ${activeTab === 'banned' ? 'active' : ''}`}
          onClick={() => setActiveTab('banned')}
        >
          Banned Users
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'members' && (
          <div className="members-list">
            {members.map(member => (
              <div key={member.id} className={`member-item ${member.is_moderator ? 'moderator' : ''}`}>
                <div className="member-info">
                  <span className="member-name">{member.username}</span>
                  {member.is_moderator && <span className="member-role">Moderator</span>}
                </div>
                {isModerator && !member.is_moderator && (
                  <button
                    className="btn-danger btn-sm"
                    onClick={() => handleBanClick(member.id)}
                  >
                    Ban
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'banned' && (
          <div className="banned-users">
            {loadingBannedUsers ? (
              <div className="loading-state">Loading banned users...</div>
            ) : bannedUsers.length === 0 ? (
              <div className="empty-state">No banned users</div>
            ) : (
              <div className="banned-users-list">
                {bannedUsers.map(user => (
                  <div key={user.id} className="banned-user-item">
                    <div className="banned-user-info">
                      <div className="banned-user-name">{user.username}</div>
                      <div className="banned-user-details">
                        <div className="banned-date">
                          Banned: {user.banned_at ? new Date(user.banned_at).toLocaleDateString() : 'Unknown'}
                        </div>
                        <div className="ban-reason">
                          Reason: {user.reason || 'No reason provided'}
                        </div>
                      </div>
                    </div>
                    <button
                      className="btn-success btn-sm"
                      onClick={() => handleUnban(user.id)}
                    >
                      Unban
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {showBanDialog && (
        <div className="modal-overlay">
          <div className="modal-dialog">
            <div className="modal-header">
              <h4>Ban User</h4>
              <button
                className="btn-icon"
                onClick={() => setShowBanDialog(false)}
              >
                <FontAwesomeIcon icon={faTimes} />
              </button>
            </div>
            <div className="modal-body">
              <input
                type="text"
                className="input-modern"
                placeholder="Reason for ban (optional)"
                value={banReason}
                onChange={(e) => setBanReason(e.target.value)}
              />
            </div>
            <div className="modal-footer">
              <button
                className="btn-danger"
                onClick={handleBanConfirm}
              >
                Confirm Ban
              </button>
              <button
                className="btn-secondary"
                onClick={() => setShowBanDialog(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
