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
  const [showRegionError, setShowRegionError] = useState(false);
  
  // Синхронизируем inputValue с изменением активной вкладки
  useEffect(() => {
    if (activeTab) {
      setInputValue(activeTab.searchTerm || '');
      setSelectedRegion(activeTab.selectedRegion || null);
    }
  }, [activeTab]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Проверка выбран ли регион
    if (!selectedRegion) {
      setShowRegionError(true);
      setTimeout(() => setShowRegionError(false), 3000); // Скрыть ошибку через 3 секунды
      return;
    }
    
    if (inputValue.trim()) {
      onSearch(inputValue, activeTabId, selectedRegion);
    }
  };
  
  const handleClear = () => {
    setInputValue('');
    setSelectedRegion(null);
    onClearSearch();
  };

  const handleRegionChange = (region) => {
    setSelectedRegion(region);
    setShowRegionError(false); // Скрыть ошибку при выборе региона
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
        </div>
        
        {showRegionError && (
          <div className="region-error">
            Пожалуйста, выберите регион для поиска
          </div>
        )}
        
        <button type="submit" className="search-button">Поиск</button>
      </form>
    </div>
  );
};

export default SearchBar; 