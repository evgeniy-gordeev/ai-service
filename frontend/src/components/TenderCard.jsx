import React from 'react';
import './TenderCard.css';

const TenderCard = ({ tender, onRemove }) => {
  // Форматирование цены с разделителями тысяч
  const formatPrice = (price) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      maximumFractionDigits: 0
    }).format(price);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Дата не указана';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="tender-card">
      <div className="tender-header">
        <div className="tender-id">№ {tender.id}</div>
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
      <h3 className="tender-title">{tender.title}</h3>
      <div className="tender-info">
        <div className="tender-detail">
          <span className="detail-label">
            <i className="building-icon"></i>
            Заказчик:
          </span>
          <span className="detail-value">{tender.customer}</span>
        </div>
        <div className="tender-detail">
          <span className="detail-label">
            <i className="purchase-icon"></i>
            Этап:
          </span>
          <span className="detail-value">{tender.stage}</span>
        </div>
        <div className="tender-detail">
          <span className="detail-label">
            <i className="location-icon"></i>
            Регион:
          </span>
          <span className="detail-value">{tender.region || 'Не указан'}</span>
        </div>
        <div className="tender-detail">
          <span className="detail-label">
            <i className="price-icon"></i>
            Сумма:
          </span>
          <span className="detail-value">{formatPrice(tender.price)}</span>
        </div>
        <div className="tender-detail">
          <span className="detail-label">
            <i className="calendar-icon"></i>
            Дата публикации:
          </span>
          <span className="detail-value">{formatDate(tender.publish_date)}</span>
        </div>
      </div>
    </div>
  );
};

export default TenderCard; 