import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip
} from '@mui/material';
import { ShoppingCart as RequestIcon } from '@mui/icons-material';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const ServiceCatalog = () => {
  const [items, setItems] = useState([]);
  const { API_URL } = useAuth();

  const fetchServiceCatalogItems = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/service-catalog/`);
      setItems(response.data);
    } catch (error) {
      console.error('Failed to fetch service catalog items:', error);
    }
  }, [API_URL]);

  useEffect(() => {
    fetchServiceCatalogItems();
  }, [fetchServiceCatalogItems]);

  const handleRequest = (item) => {
    // In a real application, this would open a request form
    alert(`Requesting: ${item.name}`);
  };

  const getCategoryColor = (category) => {
    switch (category.toLowerCase()) {
      case 'hardware': return 'primary';
      case 'software': return 'secondary';
      case 'access': return 'success';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Service Catalog
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Browse and request IT services and resources
      </Typography>

      <Grid container spacing={3}>
        {items.map((item) => (
          <Grid item xs={12} sm={6} md={4} key={item.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" component="h2">
                    {item.name}
                  </Typography>
                  <Chip
                    label={item.category}
                    color={getCategoryColor(item.category)}
                    size="small"
                  />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {item.description}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<RequestIcon />}
                  onClick={() => handleRequest(item)}
                  fullWidth
                >
                  Request
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {items.length === 0 && (
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="h6" color="text.secondary">
            No service catalog items available
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default ServiceCatalog;