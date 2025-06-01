import React, { useState } from 'react';
import { useChat } from '../context/ChatContext';

export const MembersPanel: React.FC = () => {
  const { currentChat, members, banUser } = useChat();
  const [showBanDialog, setShowBanDialog] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [banReason, setBanReason] = useState('');

  if (!currentChat) {
    return null;
  }

  // Find current user (to check if moderator)
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

  return (
    <div className="members-panel">
      <h3>Members ({members.length})</h3>

      <ul className="members-list">
        {members.map(member => (
          <li key={member.id} className={member.is_moderator ? 'moderator' : ''}>
            {member.username} {member.is_moderator && '(Moderator)'}

            {isModerator && !member.is_moderator && (
              <button onClick={() => handleBanClick(member.id)}>Ban</button>
            )}
          </li>
        ))}
      </ul>

      {showBanDialog && (
        <div className="ban-dialog">
          <h4>Ban User</h4>
          <input
            type="text"
            placeholder="Reason for ban"
            value={banReason}
            onChange={(e) => setBanReason(e.target.value)}
          />
          <div className="dialog-actions">
            <button onClick={handleBanConfirm}>Confirm</button>
            <button onClick={() => setShowBanDialog(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
};
