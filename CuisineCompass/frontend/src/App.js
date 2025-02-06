import React, { useState } from 'react';
import { Container, Spinner  } from 'react-bootstrap';
import SearchBar from './components/SearchBar';
import RestaurantList from './components/RestaurantList';
import { searchDishes } from './api';
import './App.css';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (query) => {
    setIsLoading(true);
    try {
      const data = await searchDishes(query);
      setResults(data);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div>
        <h1 className="mx-0 mb-4 heading">🍽️ Cuisine Compass 🧭</h1>
      </div>
      <Container className="p-0">
        <SearchBar onSearch={handleSearch} />
        {isLoading ? (
          <div className="text-center my-5">
            <Spinner animation="border" role="status" variant="primary">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
          </div>
        ) : (
          <RestaurantList results={results} />
        )}
      </Container>
    </div>
  );
}

export default App;