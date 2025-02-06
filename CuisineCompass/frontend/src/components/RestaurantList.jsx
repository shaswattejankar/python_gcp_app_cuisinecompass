import React from 'react';
import { Card, ListGroup } from 'react-bootstrap';
import '../App.css';

const RestaurantList = ({ results }) => {
  return (
    <div className="mt-3">
      {results.map((restaurant, index) => (
        <Card key={index} className="mb-3 mt-5 shadow">
          <Card.Body>
            <Card.Title>{restaurant.restaurant} - {restaurant.rating} / 5 ⭐    </Card.Title> 
            <Card.Subtitle className="mb-2 text-muted">
              {restaurant.address}
            </Card.Subtitle>
            <ListGroup variant="flush">
              {restaurant.matching_dishes?.map((dish, i) => (
                <ListGroup.Item key={i}>{dish}</ListGroup.Item>
              ))}
            </ListGroup>
          </Card.Body>
        </Card>
      ))}
    </div>
  );
};

export default RestaurantList;