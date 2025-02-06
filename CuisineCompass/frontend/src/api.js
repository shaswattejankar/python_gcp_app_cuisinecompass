import axios from 'axios';

const API = axios.create({
  timeout: 400000,
});

export const searchDishes = async (query) => {
  try {
    const response = await API.get('/search', { params: { dish: query } });
    return response.data.results || [];
  } catch (error) {
    console.error('API Error:', error.message);
    return [];
  }
};