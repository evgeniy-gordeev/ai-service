import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import SearchBar from './components/SearchBar';
import TenderList from './components/TenderList';
import { searchTenders } from './services/api';

// Константа для ключа localStorage
const STORAGE_KEY = 'tenders_search_tabs';

function App() {
  // Загружаем вкладки из localStorage или используем значение по умолчанию
  const [tabs, setTabs] = useState(() => {
    try {
      const savedTabs = localStorage.getItem(STORAGE_KEY);
      return savedTabs ? JSON.parse(savedTabs) : [
        { id: 1, searchTerm: '', tenders: [], loading: false, selectedRegion: null }
      ];
    } catch (error) {
      console.error('Ошибка при загрузке данных из localStorage:', error);
      return [{ id: 1, searchTerm: '', tenders: [], loading: false, selectedRegion: null }];
    }
  });
  
  // Загружаем активную вкладку из localStorage или используем первую вкладку
  const [activeTabId, setActiveTabId] = useState(() => {
    try {
      const savedTabId = localStorage.getItem(`${STORAGE_KEY}_active`);
      return savedTabId ? parseInt(savedTabId, 10) : 1;
    } catch (error) {
      return 1;
    }
  });
  
  const activeTab = tabs.find(tab => tab.id === activeTabId) || tabs[0];

  // Сохраняем вкладки в localStorage при их изменении
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tabs));
    } catch (error) {
      console.error('Ошибка при сохранении данных в localStorage:', error);
    }
  }, [tabs]);

  // Сохраняем активную вкладку при ее изменении
  useEffect(() => {
    try {
      localStorage.setItem(`${STORAGE_KEY}_active`, activeTabId.toString());
    } catch (error) {
      console.error('Ошибка при сохранении активной вкладки:', error);
    }
  }, [activeTabId]);

  const fetchTenders = useCallback(async (query, tabId, region) => {
    setTabs(prevTabs => 
      prevTabs.map(tab => 
        tab.id === tabId ? { ...tab, loading: true } : tab
      )
    );

    try {
      // Передаем код региона в API
      const data = await searchTenders(query, region.code);
      
      setTabs(prevTabs => 
        prevTabs.map(tab => 
          tab.id === tabId ? 
            { ...tab, tenders: data, loading: false, searchTerm: query, selectedRegion: region } : 
            tab
        )
      );
    } catch (error) {
      console.error('Failed to fetch tenders:', error);
      setTabs(prevTabs => 
        prevTabs.map(tab => 
          tab.id === tabId ? { ...tab, loading: false } : tab
        )
      );
    }
  }, []);

  useEffect(() => {
    if (activeTab.searchTerm && 
        activeTab.selectedRegion &&
        !activeTab.loading && 
        activeTab.tenders.length === 0) {
      fetchTenders(activeTab.searchTerm, activeTabId, activeTab.selectedRegion);
    }
  }, [activeTabId, activeTab, fetchTenders]);

  const handleSearch = useCallback((term, tabId = activeTabId, region) => {
    if (!term.trim() || !region) return;
    
    setTabs(prevTabs => 
      prevTabs.map(tab => 
        tab.id === tabId ? { ...tab, searchTerm: term, selectedRegion: region } : tab
      )
    );
    
    fetchTenders(term, tabId, region);
  }, [activeTabId, fetchTenders]);

  const handleClearSearch = useCallback((tabId) => {
    setTabs(prevTabs => 
      prevTabs.map(tab => 
        tab.id === tabId ? { ...tab, searchTerm: '', tenders: [], selectedRegion: null } : tab
      )
    );
  }, []);

  const addNewTab = useCallback(() => {
    const newTabId = Math.max(...tabs.map(tab => tab.id), 0) + 1;
    setTabs(prevTabs => [...prevTabs, { 
      id: newTabId, 
      searchTerm: '',
      tenders: [], 
      loading: false,
      selectedRegion: null
    }]);
    setActiveTabId(newTabId);
  }, [tabs]);

  const closeTab = useCallback((tabId) => {
    const newTabs = tabs.filter(tab => tab.id !== tabId);
    
    if (newTabs.length === 0) {
      // Если удалили последнюю вкладку, создаем новую пустую
      const newTabId = Math.max(...tabs.map(tab => tab.id), 0) + 1;
      setTabs([{ 
        id: newTabId, 
        searchTerm: '',
        tenders: [], 
        loading: false,
        selectedRegion: null
      }]);
      setActiveTabId(newTabId);
    } else {
      // Иначе обновляем список вкладок
      setTabs(newTabs);
      
      // Если была активна удаляемая вкладка, активируем последнюю в списке
      if (tabId === activeTabId) {
        setActiveTabId(newTabs[newTabs.length - 1].id);
      }
    }
  }, [tabs, activeTabId]);

  // Функция для удаления тендера из результатов
  const removeTender = useCallback((tenderId) => {
    setTabs(prevTabs => 
      prevTabs.map(tab => {
        if (tab.id === activeTabId) {
          // Фильтруем список тендеров, удаляя тендер с соответствующим id
          const updatedTenders = tab.tenders.filter(tender => tender.id !== tenderId);
          return { ...tab, tenders: updatedTenders };
        }
        return tab;
      })
    );
  }, [activeTabId]);

  return (
    <div className="app">
      <SearchBar 
        tabs={tabs}
        activeTabId={activeTabId}
        onTabChange={setActiveTabId}
        onSearch={handleSearch}
        onClearSearch={() => handleClearSearch(activeTabId)}
        onAddTab={addNewTab}
        onCloseTab={closeTab}
      />
      {activeTab.loading ? (
        <div className="loading">Загрузка...</div>
      ) : (
        <TenderList 
          tenders={activeTab.tenders} 
          onRemoveTender={removeTender}
        />
      )}
    </div>
  );
}

export default App; 