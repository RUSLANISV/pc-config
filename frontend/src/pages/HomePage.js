import React from 'react';
import { useNavigate } from 'react-router-dom';
import BuildCard from '../components/BuildCard';
import SearchBar from '../components/SearchBar';
import { sampleBuilds } from '../data/sampleBuilds';

const HomePage = () => {
  const navigate = useNavigate();

  const handleSearch = (query) => {
    navigate('/search', { state: { searchQuery: query } });
  };

  return (
    <div className="page">
      <h1>Популярные сборки ПК</h1>
      <SearchBar onSearch={handleSearch} />
      <div className="builds-grid">
        {sampleBuilds.map(build => (
          <BuildCard key={build.id} build={build} />
        ))}
      </div>
    </div>
  );
};

export default HomePage;