import React from 'react';
import './TenderList.css';
import TenderCard from './TenderCard';

const TenderList = ({ tenders, onRemoveTender }) => {
  // Проверяем на специальный случай "Тендеры не найдены"
  if (tenders.length === 1 && tenders[0].no_results) {
    return (
      <div className="no-results">
        <h3>Тендеры не найдены</h3>
        <p>Попробуйте изменить условия поиска</p>
      </div>
    );
  }

  return (
    <div className="tender-list">
      {tenders.map(tender => (
        <TenderCard 
          key={tender.id} 
          tender={tender} 
          onRemove={() => onRemoveTender(tender.id)}
        />
      ))}
    </div>
  );
};

export default TenderList; 