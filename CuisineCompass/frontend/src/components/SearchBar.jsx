import React, { useState } from 'react';
import { Form, Button, InputGroup } from 'react-bootstrap';
import '../App.css';

const SearchBar = ({ onSearch }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <Form onSubmit={handleSubmit} className="mb-5 mt-5 w-50 mx-auto">
      <InputGroup>
        <Form.Control
          type="text"
          placeholder="Search for dishes..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button variant="primary" type="submit">
          Search
        </Button>
      </InputGroup>
    </Form>
  );
};

export default SearchBar;