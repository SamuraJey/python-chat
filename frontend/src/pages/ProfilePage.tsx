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
  faHome
} from '@fortawesome/free-solid-svg-icons';
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

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/user/stats', {
          credentials: 'include'
        });

        if (!res.ok) throw new Error('Failed to fetch profile stats');

        const data = await res.json();
        if (data.success) {
          setStats(data.stats);
          setProfile(data.user);
        } else {
          throw new Error(data.error || 'Error loading profile data');
        }
      } catch (err: any) {
        setError(err.message || 'Error loading profile');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

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
            <div className="settings-actions">
              <button className="btn btn-outline" disabled>Изменить пароль</button>
              <div className="settings-note">
                <FontAwesomeIcon icon={faInfoCircle} />
                <span>Функция изменения пароля станет доступна в будущем</span>
              </div>
            </div>
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
