import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faChartLine,
  faTachometerAlt,
  faUsers,
  faComments,
  faUserCheck,
  faCommentDots,
  faChartBar,
  faArrowLeft,
  faHome
} from '@fortawesome/free-solid-svg-icons';
import { Chart, registerables } from 'chart.js';
import './AdminPage.css';
import { analyticsApi } from '../services/api';

// Register Chart.js components
Chart.register(...registerables);

// Define interfaces for type safety
interface AnalyticsOverview {
  total_users: number;
  total_chats: number;
  total_messages: number;
  active_users: number;
  messages_today: number;
}

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
  }[];
}

export const AdminPage: React.FC = () => {
  const { user } = useAuth();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [chatActivity, setChatActivity] = useState<ChartData | null>(null);
  const [userActivity, setUserActivity] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Refs for chart instances
  const chatChartRef = useRef<Chart | null>(null);
  const userChartRef = useRef<Chart | null>(null);

  useEffect(() => {
    const fetchAdminData = async () => {
      try {
        setLoading(true);

        // Fetch overview data using the API service
        const overviewResponse = await analyticsApi.getOverview();
        if (!overviewResponse.success || !overviewResponse.data) {
          throw new Error(overviewResponse.error || 'Failed to fetch overview data');
        }
        setOverview(overviewResponse.data);

        // Fetch chat activity data using the API service
        const chatActivityResponse = await analyticsApi.getChatActivity();
        if (!chatActivityResponse.success) {
          throw new Error(chatActivityResponse.error || 'Failed to fetch chat activity');
        }

        // Ensure we have valid chart data structure
        if (chatActivityResponse.data) {
          // Create a default structure if needed - this ensures the chart has something to display
          if (!chatActivityResponse.data.labels || chatActivityResponse.data.labels.length === 0) {
            console.warn("Empty chat activity data detected, using dummy data");
            setChatActivity({
              labels: ["Нет данных"],
              datasets: [{ label: "Количество сообщений", data: [0] }]
            });
          } else {
            setChatActivity(chatActivityResponse.data);
          }
        } else {
          setChatActivity({
            labels: ["Ошибка данных"],
            datasets: [{ label: "Количество сообщений", data: [0] }]
          });
        }

        // Fetch user activity data using the API service
        const userActivityResponse = await analyticsApi.getUserActivity();
        if (!userActivityResponse.success) {
          throw new Error(userActivityResponse.error || 'Failed to fetch user activity');
        }

        // Ensure we have valid chart data structure
        if (userActivityResponse.data) {
          // Create a default structure if needed - this ensures the chart has something to display
          if (!userActivityResponse.data.labels || userActivityResponse.data.labels.length === 0) {
            console.warn("Empty user activity data detected, using dummy data");
            setUserActivity({
              labels: ["Нет данных"],
              datasets: [{ label: "Количество сообщений", data: [0] }]
            });
          } else {
            setUserActivity(userActivityResponse.data);
          }
        } else {
          setUserActivity({
            labels: ["Ошибка данных"],
            datasets: [{ label: "Количество сообщений", data: [0] }]
          });
        }

      } catch (err: any) {
        setError(err.message || 'Error loading admin data');
      } finally {
        setLoading(false);
      }
    };

    fetchAdminData();
  }, []);

  useEffect(() => {
    // Function to create/update chart
    const renderChart = () => {
      if (!chatActivity) return;

      console.log('Attempting to render chat activity chart with data:', chatActivity);

      try {
        // Get canvas element
        const chartElement = document.getElementById('chatActivityChart');
        if (!chartElement) {
          console.error('Chart canvas element not found!');
          return;
        }

        // Clear any existing chart first
        if (chatChartRef.current) {
          chatChartRef.current.destroy();
          chatChartRef.current = null;
        }

        // Also check with Chart.getChart in case it wasn't properly cleaned up
        const existingChart = Chart.getChart(chartElement as HTMLCanvasElement);
        if (existingChart) {
          console.log('Found existing chart instance, destroying it');
          existingChart.destroy();
        }

        if (!chatActivity.labels || !chatActivity.datasets ||
            !chatActivity.datasets[0] || !chatActivity.datasets[0].data) {
          console.error('Invalid chart data structure:', chatActivity);
          return;
        }

        // Create the new chart
        console.log('Creating new chat activity chart with explicit dimensions');

        chatChartRef.current = new Chart(chartElement as HTMLCanvasElement, {
          type: 'bar',
          data: {
            labels: chatActivity.labels,
            datasets: [{
              label: 'Количество сообщений',
              data: chatActivity.datasets[0].data,
              backgroundColor: 'rgba(102, 126, 234, 0.5)',
              borderColor: 'rgba(102, 126, 234, 1)',
              borderWidth: 1
            }]
          },
          options: {
            indexAxis: 'y' as const,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: true
              }
            }
          }
        });

        console.log('Chat activity chart created successfully', chatChartRef.current);
      } catch (err) {
        console.error('Error creating chart:', err);
      }
    };

    // Call render function after DOM is fully rendered
    if (!loading && chatActivity) {
      const timer = setTimeout(() => {
        renderChart();
      }, 300); // Slightly longer delay to ensure DOM is ready

      return () => {
        clearTimeout(timer);
        if (chatChartRef.current) {
          chatChartRef.current.destroy();
          chatChartRef.current = null;
        }
      };
    }
  }, [chatActivity, loading]);

  useEffect(() => {
    // Function to create/update chart
    const renderChart = () => {
      if (!userActivity) return;

      console.log('Attempting to render user activity chart with data:', userActivity);

      try {
        // Get canvas element
        const chartElement = document.getElementById('userActivityChart');
        if (!chartElement) {
          console.error('User activity chart canvas element not found!');
          return;
        }

        // Clear any existing chart first
        if (userChartRef.current) {
          userChartRef.current.destroy();
          userChartRef.current = null;
        }

        // Also check with Chart.getChart in case it wasn't properly cleaned up
        const existingChart = Chart.getChart(chartElement as HTMLCanvasElement);
        if (existingChart) {
          console.log('Found existing user chart instance, destroying it');
          existingChart.destroy();
        }

        if (!userActivity.labels || !userActivity.datasets ||
            !userActivity.datasets[0] || !userActivity.datasets[0].data) {
          console.error('Invalid user chart data structure:', userActivity);
          return;
        }

        // Create the new chart
        console.log('Creating new user activity chart with explicit dimensions');

        userChartRef.current = new Chart(chartElement as HTMLCanvasElement, {
          type: 'line',
          data: {
            labels: userActivity.labels,
            datasets: [{
              label: 'Количество сообщений',
              data: userActivity.datasets[0].data,
              fill: false,
              borderColor: 'rgb(102, 126, 234)',
              tension: 0.1
            }]
          },
          options: {
            scales: {
              y: {
                beginAtZero: true
              }
            },
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: true
              }
            }
          }
        });

        console.log('User activity chart created successfully', userChartRef.current);
      } catch (err) {
        console.error('Error creating user chart:', err);
      }
    };

    // Call render function after DOM is fully rendered
    if (!loading && userActivity) {
      const timer = setTimeout(() => {
        renderChart();
      }, 300); // Slightly longer delay to ensure DOM is ready

      return () => {
        clearTimeout(timer);
        if (userChartRef.current) {
          userChartRef.current.destroy();
          userChartRef.current = null;
        }
      };
    }
  }, [userActivity, loading]);

  if (loading) return (
    <div className="admin-container">
      <div className="loading-spinner">
        <div className="spinner"></div>
        <p>Загрузка данных...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="admin-container error">
      <h2>Ошибка</h2>
      <p>{error}</p>
      <Link to="/" className="btn btn-secondary">
        <FontAwesomeIcon icon={faArrowLeft} /> Вернуться к чатам
      </Link>
    </div>
  );

  if (!user?.is_admin) return (
    <div className="admin-container error">
      <h2>Доступ запрещен</h2>
      <p>У вас нет прав администратора для просмотра этой страницы.</p>
      <Link to="/" className="btn btn-secondary">
        <FontAwesomeIcon icon={faArrowLeft} /> Вернуться к чатам
      </Link>
    </div>
  );

  return (
    <div className="admin-page-wrapper">
      <header className="app-header">
        <h1>Python Chat</h1>
        <div className="user-info">
          <Link to="/" className="nav-link">
            <FontAwesomeIcon icon={faHome} /> Home
          </Link>
          <Link to="/profile" className="nav-link">
            Profile
          </Link>
        </div>
      </header>

      <div className="admin-container">
        <div className="admin-header">
          <FontAwesomeIcon icon={faChartLine} />
          <h1>Панель администратора</h1>
        </div>

        <div className="section-title">
          <FontAwesomeIcon icon={faTachometerAlt} />
          <h2>Основные показатели</h2>
        </div>

        <div className="analytics-overview">
          <div className="analytics-card" id="total-users">
            <FontAwesomeIcon icon={faUsers} className="card-icon" />
            <h3>Всего пользователей</h3>
            <div className="analytics-value">{overview?.total_users || 0}</div>
          </div>

          <div className="analytics-card" id="total-chats">
            <FontAwesomeIcon icon={faComments} className="card-icon" />
            <h3>Всего чатов</h3>
            <div className="analytics-value">{overview?.total_chats || 0}</div>
          </div>

          <div className="analytics-card" id="active-users">
            <FontAwesomeIcon icon={faUserCheck} className="card-icon" />
            <h3>Активных пользователей</h3>
            <div className="analytics-value">{overview?.active_users || 0}</div>
          </div>

          <div className="analytics-card" id="messages-today">
            <FontAwesomeIcon icon={faCommentDots} className="card-icon" />
            <h3>Сообщений сегодня</h3>
            <div className="analytics-value">{overview?.messages_today || 0}</div>
          </div>
        </div>

        <div className="section-title">
          <FontAwesomeIcon icon={faChartBar} />
          <h2>Аналитика</h2>
        </div>

        <div className="charts-section">
          <div className="chart-container">
            <h2>Активность по чатам</h2>
            {loading ? (
              <div className="loading-indicator">Загрузка данных...</div>
            ) : error ? (
              <div className="error-message">Ошибка загрузки данных: {error}</div>
            ) : !chatActivity || !chatActivity.labels || chatActivity.labels.length === 0 ? (
              <div className="no-data-message">Нет данных для отображения</div>
            ) : (
              <div className="chart-wrapper">
                <canvas
                  id="chatActivityChart"
                  width="400"
                  height="300"
                  data-testid="chat-activity-chart"
                ></canvas>
              </div>
            )}
          </div>

          <div className="chart-container">
            <h2>Активность за неделю</h2>
            {loading ? (
              <div className="loading-indicator">Загрузка данных...</div>
            ) : error ? (
              <div className="error-message">Ошибка загрузки данных: {error}</div>
            ) : !userActivity || !userActivity.labels || userActivity.labels.length === 0 ? (
              <div className="no-data-message">Нет данных для отображения</div>
            ) : (
              <div className="chart-wrapper">
                <canvas
                  id="userActivityChart"
                  width="400"
                  height="300"
                  data-testid="user-activity-chart"
                ></canvas>
              </div>
            )}
          </div>
        </div>

        <div className="admin-footer">
          <Link to="/" className="btn btn-secondary">
            <FontAwesomeIcon icon={faArrowLeft} /> Вернуться к списку чатов
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
