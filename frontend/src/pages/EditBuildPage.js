import React, { useState, useEffect, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import AuthContext from '../context/AuthContext';
import '../styles/edit-build.css';

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

const EditBuildPage = () => {
  const [buildName, setBuildName] = useState('');
  const [selectedComponents, setSelectedComponents] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [activeComponent, setActiveComponent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();

                                                    
  useEffect(() => {
    setSearchResults([]);
    setSearchQuery('');
  }, [activeComponent]);

                                 
  useEffect(() => {
    if (location.state?.build) {
      setBuildName(location.state.build.name);
      setSelectedComponents(location.state.build.components || {});
    }
  }, [location]);

                      
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!activeComponent) return;
    
    setIsLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/search_components`, {
        params: { 
          type: activeComponent,
          query: searchQuery 
        },
        headers: { 
          Authorization: `Bearer ${localStorage.getItem('token')}` 
        }
      });
      
      setSearchResults(response.data);
    } catch (error) {
      console.error('Ошибка поиска:', error);
      alert('Ошибка при выполнении поиска');
    } finally {
      setIsLoading(false);
    }
  };

                     
  const selectComponent = (component) => {
    setSelectedComponents(prev => ({
      ...prev,
      [activeComponent]: {
        id: component.id,
        name: component.name,
        price: parseFloat(component.price),
        type: component.type
      }
    }));
    setActiveComponent(null);
  };

                           
  const calculateTotal = () => {
    return Object.values(selectedComponents)
      .reduce((sum, comp) => sum + (comp?.price || 0), 0)
      .toFixed(2);
  };

                      
  const saveBuild = async () => {
    if (!buildName.trim()) {
      alert('Введите название сборки');
      return;
    }

    if (Object.keys(selectedComponents).length === 0) {
      alert('Добавьте хотя бы один компонент');
      return;
    }

    try {
      const endpoint = location.state?.build 
        ? `/builds/${location.state.build.id}`
        : '/builds';

      await axios({
        method: location.state?.build ? 'PUT' : 'POST',
        url: `http://localhost:8000${endpoint}`,
        data: {
          name: buildName,
          components: selectedComponents
        },
        headers: { 
          Authorization: `Bearer ${localStorage.getItem('token')}` 
        }
      });

      navigate('/builds');
    } catch (error) {
      console.error('Ошибка сохранения:', error.response?.data?.detail || error.message);
      alert('Ошибка сохранения сборки');
    }
  };

  if (!user) {
    navigate('/auth');
    return null;
  }

  return (
    <div className="edit-build-container">
      <div className="build-header">
        <input
          type="text"
          placeholder="Название сборки"
          value={buildName}
          onChange={(e) => setBuildName(e.target.value)}
          className="build-name-input"
        />
        <div className="total-price">
          Итоговая стоимость: {calculateTotal()} ₽
        </div>
      </div>

      <div className="components-grid">
        {Object.entries(componentTypes).map(([key, label]) => (
          <div 
            key={key}
            className={`component-card ${activeComponent === key ? 'active' : ''}`}
          >
            <div 
              className="component-header" 
              onClick={() => setActiveComponent(prev => prev === key ? null : key)}
            >
              <h4>{label}</h4>
              <div className="selected-component">
                {selectedComponents[key]?.name || 'Не выбрано'}
                {selectedComponents[key]?.price && (
                  <span className="component-price">
                    {selectedComponents[key].price.toFixed(2)} ₽
                  </span>
                )}
              </div>
            </div>

            {activeComponent === key && (
              <div className="search-section">
                <form className="search-bar" onSubmit={handleSearch}>
                  <input
                    type="text"
                    placeholder={`Поиск ${label.toLowerCase()}...`}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Поиск...' : 'Найти'}
                  </button>
                </form>

                {searchResults.length > 0 && (
                  <div className="search-results">
                    {searchResults.map((item) => (
                      <div 
                        key={item.id} 
                        className="result-item"
                        onClick={() => selectComponent(item)}
                      >
                        <div className="part-info">
                          <div className="part-name">{item.name}</div>
                          <div className="part-type">{item.type}</div>
                        </div>
                        <div className="part-price">
                          {parseFloat(item.price).toFixed(2)} ₽
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {searchResults.length === 0 && searchQuery && !isLoading && (
                  <div className="no-results">Ничего не найдено</div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="actions">
        <button onClick={saveBuild} className="save-btn">
          {location.state?.build ? 'Обновить сборку' : 'Сохранить сборку'}
        </button>
        <button onClick={() => navigate('/builds')} className="cancel-btn">
          Отмена
        </button>
      </div>
    </div>
  );
};

export default EditBuildPage;