import React, { useState, useEffect } from 'react';
import './SearchBar.css';
import RegionSelect from './RegionSelect';

const SearchBar = ({ 
  tabs, 
  activeTabId, 
  onTabChange, 
  onSearch, 
  onClearSearch, 
  onAddTab,
  onCloseTab 
}) => {
  const activeTab = tabs.find(tab => tab.id === activeTabId) || tabs[0];
  const [inputValue, setInputValue] = useState('');
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [tenderCount, setTenderCount] = useState(10);
  
  // Синхронизируем inputValue с изменением активной вкладки
  useEffect(() => {
    if (activeTab) {
      setInputValue(activeTab.searchTerm || '');
      setSelectedRegion(activeTab.selectedRegion || null);
      setTenderCount(activeTab.tenderCount || 10);
    }
  }, [activeTab]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (inputValue.trim()) {
      onSearch(inputValue, activeTabId, selectedRegion, tenderCount);
    }
  };
  
  const handleClear = () => {
    setInputValue('');
    onClearSearch();
  };

  const handleRegionChange = (region) => {
    setSelectedRegion(region);
  };

  const handleTenderCountChange = (e) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setTenderCount(value);
    } else if (e.target.value === '') {
      setTenderCount('');
    }
  };

  const handleTenderCountBlur = () => {
    if (tenderCount === '' || isNaN(tenderCount) || tenderCount < 1) {
      setTenderCount(10);
    }
  };

  return (
    <div className="search-container">
      <div className="tabs-container">
        {tabs.map(tab => (
          <div 
            key={tab.id} 
            className={`tab ${tab.id === activeTabId ? 'active-tab' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span className="tab-text">
              {tab.searchTerm ? tab.searchTerm : 'Без названия'}
            </span>
            {tabs.length > 1 && (
              <button 
                className="close-tab-button" 
                onClick={(e) => {
                  e.stopPropagation();
                  onCloseTab(tab.id);
                }}
              >
                ×
              </button>
            )}
          </div>
        ))}
        <button className="add-tab-button" onClick={onAddTab}>+</button>
      </div>
      
      <form className="search-bar" onSubmit={handleSubmit}>
        <div className="search-inputs">
          <RegionSelect 
            selectedRegion={selectedRegion}
            onRegionChange={handleRegionChange}
          />
          
          <div className="search-input-container">
            <input
              type="text"
              className="search-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Введите запрос..."
            />
            {inputValue && (
              <button 
                type="button" 
                className="clear-button" 
                onClick={handleClear}
              >
                ×
              </button>
            )}
          </div>
          
          <div className="tender-count-container">
            <label htmlFor="tenderCount">Количество тендеров:</label>
            <input
              id="tenderCount"
              type="number"
              min="1"
              className="tender-count-input"
              value={tenderCount}
              onChange={handleTenderCountChange}
              onBlur={handleTenderCountBlur}
            />
          </div>
        </div>
        
        <button type="submit" className="search-button">Поиск</button>
      </form>
    </div>
  );
};

export default SearchBar; 