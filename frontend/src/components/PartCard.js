import React from 'react';

const PartCard = ({ part }) => {
  return (
    <div className="part-card">
      <h3>{part.name}</h3>
      <div className="part-details">
        <span className="part-category">{part.category}</span>
        <span className="part-price">{part.price.toFixed(2)} Рублей</span>
      </div>
      <span className="part-desc">{part.description}</span>
    </div>
  );
};

export default PartCard;