import React from 'react';
import TenderCard from './TenderCard';
import './TenderList.css';

const TenderList = ({ tenders, onRemoveTender }) => {
  return (
    <div className="tender-list">
      {tenders.length > 0 ? (
        tenders.map(tender => (
          <TenderCard 
            key={tender.id} 
            tender={tender} 
            onRemove={onRemoveTender}
          />
        ))
      ) : (
        <div className="no-results">Нет результатов для отображения</div>
      )}
    </div>
  );
};

export default TenderList; 