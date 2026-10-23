import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import AuthContext from '../context/AuthContext';
import '../styles/builds.css';

const componentTypes = {
  cpu: 'Процессор',
  gpu: 'Видеокарта',
  motherboard: 'Материнская плата',
  ram: 'Оперативная память',
  storage: 'Накопитель',
  psu: 'Блок питания',
  cpucool: 'Кулер',
  case: 'Корпус'
};

const BuildsPage = () => {
  const [builds, setBuilds] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchBuilds = async () => {
      try {
        const response = await axios.get('http://localhost:8000/userbuilds', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        const sortedBuilds = response.data.sort((a, b) => 
          a.name.localeCompare(b.name)
        );
        setBuilds(sortedBuilds);
      } catch (error) {
        console.error('Ошибка загрузки сборок:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchBuilds();
  }, []);

  const handleDeleteBuild = async (buildId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту сборку?')) return;

    try {
      await axios.delete(`http://localhost:8000/builds/${buildId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setBuilds(prev => prev.filter(build => build.id !== buildId));
    } catch (error) {
      console.error('Ошибка удаления:', error);
      alert('Не удалось удалить сборку');
    }
  };

  const renderComponent = (component) => {
    return component ? (
      <div className="component-item">
        <span className="component-name">{component.name}</span>
        <span className="component-price">{component.price?.toFixed(2)} ₽</span>
      </div>
    ) : <div className="component-empty">Пусто</div>;
  };

  if (!user) {
    navigate('/auth');
    return null;
  }

  if (loading) {
    return <div className="loading">Загрузка сборок...</div>;
  }

  return (
    <div className="builds-container">
      <div className="builds-header">
        <h1>Мои сборки</h1>
        <div className="builds-actions">
          <button 
            className="create-build-btn"
            onClick={() => navigate('/builds/edit')}
          >
            + Создать сборку
          </button>
          <button 
            className="back-btn"
            onClick={() => navigate('/profile')}
          >
            ← Назад в профиль
          </button>
        </div>
      </div>

      <div className="builds-list">
        {builds.map((build) => (
          <div key={build.id} className="build-card">
            <div className="build-header">
              <h3>{build.name}</h3>
              <div className="build-actions">
                <button
                  className="delete-btn"
                  onClick={() => handleDeleteBuild(build.id)}
                  title="Удалить сборку"
                >
                  ×
                </button>
              </div>
            </div>
            
            <div className="components-list">
              <div className="components-column">
                {Object.entries(componentTypes).map(([key, label]) => (
                  <div key={key} className="component-category">
                    <div className="component-label">{label}:</div>
                    {renderComponent(build.components?.[key])}
                  </div>
                ))}
              </div>
            </div>
            <div className="build-footer">
              <div className="total-price">
                Итого: {Object.values(build.components || {})
                  .reduce((sum, comp) => sum + (comp?.price || 0), 0)
                  .toFixed(2)} ₽
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BuildsPage;