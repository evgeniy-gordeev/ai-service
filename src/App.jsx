import React, { useState, useEffect } from 'react';
import './App.css';
import SearchBar from './components/SearchBar';
import TenderList from './components/TenderList';
import { searchTenders } from './services/api';

function App() {
  const [searchTerm, setSearchTerm] = useState('Тестовый поиск');
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (searchTerm) {
      fetchTenders(searchTerm);
    }
  }, []);

  const fetchTenders = async (query) => {
    setLoading(true);
    try {
      const data = await searchTenders(query);
      setTenders(data);
    } catch (error) {
      console.error('Failed to fetch tenders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (term) => {
    setSearchTerm(term);
    fetchTenders(term);
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setTenders([]);
  };

  return (
    <div className="app">
      <SearchBar 
        searchTerm={searchTerm}
        onSearch={handleSearch}
        onClearSearch={handleClearSearch}
      />
      {loading ? (
        <div className="loading">Загрузка...</div>
      ) : (
        <TenderList tenders={tenders} />
      )}
    </div>
  );
}

export default App; 