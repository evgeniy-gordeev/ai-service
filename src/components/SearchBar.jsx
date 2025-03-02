import React from 'react';
import './SearchBar.css';

const SearchBar = ({ searchTerm, onSearch, onClearSearch }) => {
  return (
    <div className="search-bar">
      <div className="search-input-container">
        <span className="search-term">{searchTerm}</span>
        {searchTerm && (
          <button className="clear-button" onClick={onClearSearch}>
            ×
          </button>
        )}
      </div>
      <button className="add-button">+</button>
    </div>
  );
};

export default SearchBar; 