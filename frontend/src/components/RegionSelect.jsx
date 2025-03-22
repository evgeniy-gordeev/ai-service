import React, { useState, useEffect, useRef } from 'react';
import './RegionSelect.css';
import { REGIONS } from '../constants/regions';

const RegionSelect = ({ selectedRegion, onRegionChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredRegions, setFilteredRegions] = useState(REGIONS);
  const dropdownRef = useRef(null);

  // Обработка закрытия при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Фильтрация регионов при вводе поиска
  useEffect(() => {
    const lowercasedSearchTerm = searchTerm.toLowerCase().trim();
    if (!lowercasedSearchTerm) {
      setFilteredRegions(REGIONS);
      return;
    }

    const filtered = REGIONS.filter(
      region => 
        region.name.toLowerCase().includes(lowercasedSearchTerm) || 
        (region.code && region.code.includes(lowercasedSearchTerm))
    );
    
    setFilteredRegions(filtered);
  }, [searchTerm]);

  const handleRegionSelect = (region) => {
    onRegionChange(region);
    setIsOpen(false);
    setSearchTerm('');
  };

  const selectedRegionDisplay = selectedRegion 
    ? `${selectedRegion.code ? selectedRegion.code + ' - ' : ''}${selectedRegion.name}` 
    : 'Выберите регион';

  return (
    <div className="region-select-container" ref={dropdownRef}>
      <div 
        className="region-select-header" 
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="selected-region">{selectedRegionDisplay}</div>
        <div className="dropdown-arrow">{isOpen ? '▲' : '▼'}</div>
      </div>
      
      {isOpen && (
        <div className="region-dropdown">
          <div className="region-search">
            <input
              type="text"
              placeholder="Поиск региона..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
          <div className="region-list">
            {filteredRegions.length > 0 ? (
              filteredRegions.map(region => (
                <div 
                  key={region.code || 'all'} 
                  className={`region-item ${selectedRegion?.code === region.code ? 'selected' : ''}`}
                  onClick={() => handleRegionSelect(region)}
                >
                  {region.code ? (
                    <>
                      <span className="region-code">{region.code}</span>
                      <span className="region-name">{region.name}</span>
                    </>
                  ) : (
                    <span className="region-name">{region.name}</span>
                  )}
                </div>
              ))
            ) : (
              <div className="no-regions-found">Регионы не найдены</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RegionSelect; 