import React from 'react';
import './TenderCard.css';

const TenderCard = ({ tender, onRemove }) => {
  // Форматирование цены с разделителями тысяч
  const formatPrice = (price) => {
    return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  };

  return (
    <div className="tender-card">
      <div className="tender-header">
        <div className="tender-id">{tender.id}</div>
        {tender.score !== null && (
          <div className="tender-score">
            <i className="score-icon"></i>
            Релевантность: {tender.score}
          </div>
        )}
        <button 
          className="remove-tender-button" 
          onClick={() => onRemove(tender.id)}
          title="Удалить из результатов"
        >
          ×
        </button>
      </div>
      <h2 className="tender-title">{tender.title}</h2>
      <div className="tender-details">
        <div className="tender-date">
          <i className="calendar-icon"></i>
          {tender.date}
        </div>
        <div className="tender-price">
          <i className="price-icon"></i>
          {formatPrice(tender.price)} ₽
        </div>
        <div className="tender-customer">
          <i className="building-icon"></i>
          {tender.customer}
        </div>
      </div>
    </div>
  );
};

export default TenderCard; 