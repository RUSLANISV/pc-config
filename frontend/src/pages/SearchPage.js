import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import PartCard from '../components/PartCard';
import FilterPanel from '../components/FilterPanel';
import SearchBar from '../components/SearchBar';

const SearchPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [allResults, setAllResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({
    category: '',
    priceMin: '',
    priceMax: '',
    sortBy: 'name'
  });

  const query = location.state?.searchQuery || "";

  useEffect(() => {
    const controller = new AbortController();
    setSearchQuery(query);
    const load = async () => {
      setLoading(true);
      setError("");
      setAllResults([]);
      try {
        const response = await fetch(
          `http://localhost:8000/search_components?query=${encodeURIComponent(query)}`,
          { signal: controller.signal }
        );
        if (!response.ok) throw new Error("Ошибка загрузки");
        const data = await response.json();
        if (!controller.signal.aborted) {
          setAllResults(data.map(item => ({
            id: item.id,
            name: item.name,
            category: item.type,
            price: Number(item.price),
            description: item.description
          })));
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError("Не удалось загрузить каталог. Проверьте, запущен ли сервер, и повторите поиск.");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    load();
    return () => controller.abort();
  }, [query, location.key]);

  const applyFilters = () => {
    let results = [...allResults];

    if (filters.category) {
      results = results.filter(part => part.category === filters.category);
    }

    if (filters.priceMin) {
      results = results.filter(part => part.price >= Number(filters.priceMin));
    }
    
    if (filters.priceMax) {
      results = results.filter(part => part.price <= Number(filters.priceMax));
    }

    results = sortResults(results, filters.sortBy);
    
    return results;
  };

  const sortResults = (results, sortBy) => {
    switch (sortBy) {
      case 'price-asc':
        return [...results].sort((a, b) => a.price - b.price);
      case 'price-desc':
        return [...results].sort((a, b) => b.price - a.price);
      default:
        return [...results].sort((a, b) => a.name.localeCompare(b.name));
    }
  };

  const filteredResults = applyFilters();

  return (
    <div className="page">
      <h1>Результаты поиска {searchQuery && `для "${searchQuery}"`}</h1>
      
      <div className="search-page-bar">
        <SearchBar 
          initialQuery={searchQuery}
          onSearch={(query) => {
            setFilters({ category: "", priceMin: "", priceMax: "", sortBy: "name" });
            navigate('/search', { state: { searchQuery: query }, replace: true });
          }} 
        />
      </div>
      
      <FilterPanel 
        filters={filters}
        onFilterChange={setFilters}
        availableCategories={[...new Set(allResults.map(part => part.category))]}
      />
      
      {loading && <p role="status">Загрузка комплектующих…</p>}
      {!loading && error && <p role="alert">{error}</p>}
      {!loading && !error && <p role="status">Найдено: {filteredResults.length}</p>}
      <div className="parts-grid" hidden={loading || Boolean(error)}>
        {filteredResults.length > 0 ? (
          filteredResults.map(part => (
            <PartCard 
              key={part.id} 
              part={{
                ...part,
                                                                      
                price: part.price
              }}
            />
          ))
        ) : (
          <p className="no-results">
            {allResults.length === 0 
              ? "Компоненты не найдены" 
              : "Нет компонентов, соответствующих фильтрам"}
          </p>
        )}
      </div>
    </div>
  );
};

export default SearchPage;