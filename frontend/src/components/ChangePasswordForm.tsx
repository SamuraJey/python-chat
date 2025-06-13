import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEye, faEyeSlash, faLock, faCheck, faTimesCircle } from '@fortawesome/free-solid-svg-icons';
import './ChangePasswordForm.css';

interface ChangePasswordFormProps {
  onSubmit: (currentPassword: string, newPassword: string, confirmPassword: string) => Promise<void>;
  onCancel: () => void;
}

export const ChangePasswordForm: React.FC<ChangePasswordFormProps> = ({ onSubmit, onCancel }) => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate form
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('Все поля обязательны для заполнения');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Новые пароли не совпадают');
      return;
    }

    if (newPassword.length < 8) {
      setError('Пароль должен содержать не менее 8 символов');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(currentPassword, newPassword, confirmPassword);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="password-form-container">
      <h3><FontAwesomeIcon icon={faLock} /> Изменить пароль</h3>

      {error && (
        <div className="error-message">
          <FontAwesomeIcon icon={faTimesCircle} /> {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="currentPassword">Текущий пароль</label>
          <div className="password-input-wrapper">
            <input
              type={showCurrentPassword ? "text" : "password"}
              id="currentPassword"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              disabled={isSubmitting}
              autoComplete="current-password"
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowCurrentPassword(!showCurrentPassword)}
            >
              <FontAwesomeIcon icon={showCurrentPassword ? faEyeSlash : faEye} />
            </button>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="newPassword">Новый пароль</label>
          <div className="password-input-wrapper">
            <input
              type={showNewPassword ? "text" : "password"}
              id="newPassword"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              disabled={isSubmitting}
              minLength={8}
              autoComplete="new-password"
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowNewPassword(!showNewPassword)}
            >
              <FontAwesomeIcon icon={showNewPassword ? faEyeSlash : faEye} />
            </button>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="confirmPassword">Подтвердите новый пароль</label>
          <div className="password-input-wrapper">
            <input
              type={showConfirmPassword ? "text" : "password"}
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isSubmitting}
              autoComplete="new-password"
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            >
              <FontAwesomeIcon icon={showConfirmPassword ? faEyeSlash : faEye} />
            </button>
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Отмена
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Изменение...' : (
              <>
                <FontAwesomeIcon icon={faCheck} /> Изменить пароль
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
