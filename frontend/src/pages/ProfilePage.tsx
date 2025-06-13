import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faChartPie,
  faComments,
  faCommentDots,
  faUserCog,
  faKey,
  faInfoCircle,
  faTools,
  faChartLine,
  faArrowLeft,
  faShieldAlt,
  faUser,
  faHome,
  faCheck
} from '@fortawesome/free-solid-svg-icons';
import { ChangePasswordForm } from '../components/ChangePasswordForm';
import { userApi } from '../services/api';
import type { ChangePasswordRequest } from '../services/api';
import './ProfilePage.css';

interface Stats {
  chats_count: number;
  messages_count: number;
}

interface User {
  username: string;
  is_admin?: boolean;
}

export const ProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<User | null>(null);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [passwordChanged, setPasswordChanged] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      try {
        const response = await userApi.getUserStats();
        if (response.success && response.data) {
          setStats(response.data.stats);
          setProfile(response.data.user);
        } else {
          throw new Error(response.error || 'Error loading profile data');
        }
      } catch (err: any) {
        setError(err.message || 'Error loading profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  // Handle password change
  const handlePasswordChange = async (currentPassword: string, newPassword: string, confirmPassword: string) => {
    try {
      const passwordData: ChangePasswordRequest = {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      };

      const response = await userApi.changePassword(passwordData);

      if (!response.success) {
        throw new Error(response.error || 'Failed to change password');
      }

      // Reset the form and show success message
      setShowPasswordForm(false);
      setPasswordChanged(true);

      // Hide success message after 5 seconds
      setTimeout(() => {
        setPasswordChanged(false);
      }, 5000);

    } catch (err: any) {
      throw new Error(err.message || 'An error occurred while changing password');
    }
  };

  if (loading) return (
    <div className="profile-container">
      <div className="loading-spinner">
        <div className="spinner"></div>
        <p>Загрузка профиля...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="profile-container error">
      <h2>Ошибка</h2>
      <p>{error}</p>
      <Link to="/" className="btn btn-secondary">
        <FontAwesomeIcon icon={faArrowLeft} /> Вернуться к чатам
      </Link>
    </div>
  );

  if (!profile || !stats) return null;

  return (
    <div className="profile-page-wrapper">
      <header className="app-header">
        <h1>Python Chat</h1>
        <div className="user-info">
          <Link to="/" className="nav-link">
            <FontAwesomeIcon icon={faHome} /> Home
          </Link>
          {profile?.is_admin && (
            <Link to="/admin" className="nav-link admin-link">
              <FontAwesomeIcon icon={faTools} /> Admin
            </Link>
          )}
        </div>
      </header>

      <div className="profile-container">
        <div className="profile-header">
          <div className="avatar-container">
            <div className="avatar-letter">{profile.username[0].toUpperCase()}</div>
          </div>
          <div className="profile-info">
            <h1>{profile.username}</h1>
            <div className="user-badges">
              <span className={`user-badge ${profile.is_admin ? 'admin-badge' : 'user-badge'}`}>
                <FontAwesomeIcon icon={profile.is_admin ? faShieldAlt : faUser} />
                {profile.is_admin ? ' Администратор' : ' Пользователь'}
              </span>
            </div>
          </div>
        </div>

        <div className="section-title">
          <FontAwesomeIcon icon={faChartPie} />
          <h2>Статистика</h2>
        </div>

        <div className="profile-details">
          <div className="profile-stats">
            <div className="stat-item">
              <FontAwesomeIcon icon={faComments} className="stat-icon" />
              <span className="stat-label">Участие в чатах</span>
              <span className="stat-value">{stats.chats_count}</span>
            </div>
            <div className="stat-item">
              <FontAwesomeIcon icon={faCommentDots} className="stat-icon" />
              <span className="stat-label">Отправлено сообщений</span>
              <span className="stat-value">{stats.messages_count}</span>
            </div>
          </div>
        </div>

        <div className="section-title">
          <FontAwesomeIcon icon={faUserCog} />
          <h2>Настройки учётной записи</h2>
        </div>

        <div className="account-settings">
          <div className="settings-card">
            <div className="settings-header">
              <FontAwesomeIcon icon={faKey} />
              <h3>Безопасность</h3>
            </div>
            {showPasswordForm ? (
              <ChangePasswordForm
                onSubmit={handlePasswordChange}
                onCancel={() => setShowPasswordForm(false)}
              />
            ) : (
              <div className="settings-actions">
                <button
                  className="btn btn-outline"
                  onClick={() => setShowPasswordForm(true)}
                >
                  Изменить пароль
                </button>
                {passwordChanged && (
                  <div className="settings-success">
                    <FontAwesomeIcon icon={faCheck} />
                    <span>Пароль успешно изменен!</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {profile.is_admin && (
          <>
            <div className="section-title">
              <FontAwesomeIcon icon={faTools} />
              <h2>Администрирование</h2>
            </div>
            <div className="admin-links">
              <Link to="/admin" className="btn btn-primary">
                <FontAwesomeIcon icon={faChartLine} /> Перейти в панель администратора
              </Link>
            </div>
          </>
        )}

        <div className="profile-footer">
          <Link to="/" className="btn btn-secondary">
            <FontAwesomeIcon icon={faArrowLeft} /> Вернуться к списку чатов
          </Link>
        </div>
      </div>
    </div>
  );
}
