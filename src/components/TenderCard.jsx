import React from 'react';
import './TenderCard.css';

const TenderCard = ({ tender, onRemove }) => {
  // Форматирование цены с разделителями тысяч
  const formatPrice = (price) => {
    return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  };

  const handleRemoveClick = (e) => {
    e.stopPropagation(); // Предотвращаем всплытие события
    onRemove(tender.id); // Удаляем тендер
  };

  return (
    <div className="tender-card">
      <div className="tender-header">
        <div className="tender-id">{tender.id}</div>
        <button 
          className="remove-tender-button" 
          onClick={handleRemoveClick}
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