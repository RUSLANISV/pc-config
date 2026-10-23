import React from 'react';

const BuildCard = ({ build }) => {
  return (
    <div className="build-card">
      <h3>{build.name}</h3>
      <p className="build-description">{build.description}</p>
      <div className="build-details">
        <span className="build-price">{build.totalPrice.toFixed(2)} ₽</span>
      </div>
      <div className="build-parts">
        <h4>Комплектующие:</h4>
        <ul>
          {build.parts.map((part, index) => (
            <li key={index}>
              {part.name} - {part.price.toFixed(2)} ₽
            </li>
          ))}
          <a href={build.ref}>Купить здесь</a>
        </ul>
      </div>
    </div>
  );
};

export default BuildCard;