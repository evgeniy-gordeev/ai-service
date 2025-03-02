import React from 'react';
import TenderCard from './TenderCard';
import './TenderList.css';

const TenderList = ({ tenders }) => {
  return (
    <div className="tender-list">
      {tenders.map(tender => (
        <TenderCard key={tender.id} tender={tender} />
      ))}
    </div>
  );
};

export default TenderList; 