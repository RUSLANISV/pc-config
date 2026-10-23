import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import '../styles/profile.css';

const ProfilePage = () => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  return (
    <div className="profile-container">
      <div className="profile-header">
        <h1>Ваш профиль</h1>
        <button onClick={logout} className="logout-btn">
          Выйти
        </button>
      </div>

      <div className="profile-info">
        <div className="info-item">
          <span className="info-label">Email:</span>
          <span className="info-value">{user?.email}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Имя пользователя:</span>
          <span className="info-value">{user?.username}</span>
        </div>
      </div>

      <div className="profile-actions">
        <button
          onClick={() => navigate('/builds')}
          className="action-btn"
        >
          Мои Сборки
        </button>
      </div>
    </div>
  );
};

export default ProfilePage;