import React from 'react';

const FilterPanel = ({ filters, onFilterChange, availableCategories }) => {
  const handleChange = (e) => {
    const { name, value } = e.target;
    onFilterChange({
      ...filters,
      [name]: value
    });
  };

  const clearFilters = () => {
    onFilterChange({
      category: '',
      priceMin: '',
      priceMax: '',
      sortBy: 'name'
    });
  };

  return (
    <div className="filter-panel">
      <div className="filter-group">
        <label>Category:</label>
        <select 
          name="category" 
          value={filters.category} 
          onChange={handleChange}
        >
          <option value="">All Categories</option>
          {availableCategories.map(category => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>
      </div>
      
      <div className="filter-group">
        <label>Price Range:</label>
        <div className="price-range">
          <input
            type="number"
            name="priceMin"
            placeholder="Min"
            value={filters.priceMin}
            onChange={handleChange}
            min="0"
          />
          <span>to</span>
          <input
            type="number"
            name="priceMax"
            placeholder="Max"
            value={filters.priceMax}
            onChange={handleChange}
            min="0"
          />
        </div>
      </div>
      
      <div className="filter-group">
        <label>Sort By:</label>
        <select 
          name="sortBy" 
          value={filters.sortBy} 
          onChange={handleChange}
        >
          <option value="name">Name (A-Z)</option>
          <option value="price-asc">Price (Low to High)</option>
          <option value="price-desc">Price (High to Low)</option>
        </select>
      </div>
      
      <button 
        className="clear-filters" 
        onClick={clearFilters}
      >
        Clear Filters
      </button>
    </div>
  );
};

export default FilterPanel;