import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  Grid,
  Card,
  CardContent,
  Paper,
  Chip,
  Button,
  Breadcrumbs,
  Link,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Search as SearchIcon,
  Article as ArticleIcon,
  Visibility as ViewIcon,
  ThumbUp as ThumbUpIcon,
  Category as CategoryIcon,
  ArrowBack as ArrowBackIcon,
  Share as ShareIcon,
  Print as PrintIcon,
  BookmarkBorder as BookmarkIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const KnowledgeBase = () => {
  const navigate = useNavigate();
  const { API_URL } = useAuth();
  const { articleId } = useParams();
  const [articles, setArticles] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [showArticleDialog, setShowArticleDialog] = useState(false);

  const fetchArticles = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (selectedCategory) params.append('category', selectedCategory);
      
      const response = await fetch(`${API_URL}/knowledge-base/?${params}`);
      const data = await response.json();
      setArticles(data);
    } catch (error) {
      console.error('Error fetching articles:', error);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedCategory, API_URL]);

  useEffect(() => {
    fetchArticles();
    fetchCategories();
  }, [fetchArticles]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (articleId) {
      fetchArticle(articleId);
    }
  }, [articleId]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_URL}/knowledge-base/categories/`);
      const data = await response.json();
      setCategories(data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchArticle = async (id) => {
    try {
      const response = await fetch(`${API_URL}/knowledge-base/${id}`);
      const data = await response.json();
      setSelectedArticle(data);
      setShowArticleDialog(true);
    } catch (error) {
      console.error('Error fetching article:', error);
    }
  };

  const markAsHelpful = async (articleId) => {
    try {
      await fetch(`${API_URL}/knowledge-base/${articleId}/helpful`, {
        method: 'POST'
      });
      // Refresh the article to show updated vote count
      if (selectedArticle && selectedArticle.id === articleId) {
        fetchArticle(articleId);
      }
      fetchArticles(); // Refresh the list
    } catch (error) {
      console.error('Error marking article as helpful:', error);
    }
  };

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

  const handleCategoryFilter = (category) => {
    setSelectedCategory(category === selectedCategory ? '' : category);
  };

  const openArticle = (article) => {
    setSelectedArticle(article);
    setShowArticleDialog(true);
    navigate(`/knowledge-base/${article.id}`);
  };

  const closeArticle = () => {
    setShowArticleDialog(false);
    setSelectedArticle(null);
    navigate('/knowledge-base');
  };

  const formatContent = (content) => {
    // Simple markdown-like formatting
    return content
      .replace(/^# (.*$)/gm, '<h1 style="color: #8B1538; margin: 20px 0 10px 0;">$1</h1>')
      .replace(/^## (.*$)/gm, '<h2 style="color: #FF8C42; margin: 15px 0 8px 0;">$1</h2>')
      .replace(/^### (.*$)/gm, '<h3 style="color: #333; margin: 12px 0 6px 0;">$1</h3>')
      .replace(/^\*\*(.*?)\*\*/gm, '<strong>$1</strong>')
      .replace(/^\* (.*$)/gm, '<li style="margin: 4px 0;">$1</li>')
      .replace(/^(\d+)\. (.*$)/gm, '<li style="margin: 4px 0; list-style-type: decimal;">$2</li>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
  };

  if (loading) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography>Loading knowledge base...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      {/* Header */}
      <Box sx={{ p: 3, backgroundColor: 'white', borderBottom: '1px solid #dee2e6' }}>
        <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
          <Link 
            color="inherit" 
            href="#" 
            onClick={(e) => { e.preventDefault(); navigate('/'); }}
            sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
          >
            Home
          </Link>
          <Typography color="text.primary">Knowledge Base</Typography>
        </Breadcrumbs>
        
        <Typography variant="h4" sx={{ mb: 2, color: '#333', fontWeight: 600 }}>
          Knowledge Base
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Browse and search for articles that could solve your issue
        </Typography>

        {/* Search Bar */}
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search knowledge base..."
          value={searchQuery}
          onChange={handleSearchChange}
          sx={{ 
            maxWidth: 600,
            '& .MuiOutlinedInput-root': {
              backgroundColor: 'white'
            }
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      <Grid container spacing={3} sx={{ p: 3 }}>
        {/* Sidebar - Categories */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, color: '#8B1538', display: 'flex', alignItems: 'center' }}>
              <CategoryIcon sx={{ mr: 1 }} />
              Categories
            </Typography>
            <List dense>
              <ListItem 
                button 
                selected={selectedCategory === ''}
                onClick={() => handleCategoryFilter('')}
                sx={{ borderRadius: 1, mb: 1 }}
              >
                <ListItemText primary="All Articles" />
                <Chip size="small" label={articles.length} />
              </ListItem>
              {categories.map((category) => (
                <ListItem 
                  key={category.name}
                  button
                  selected={selectedCategory === category.name}
                  onClick={() => handleCategoryFilter(category.name)}
                  sx={{ borderRadius: 1, mb: 1 }}
                >
                  <ListItemText primary={category.name} />
                  <Chip 
                    size="small" 
                    label={articles.filter(a => a.category === category.name).length} 
                  />
                </ListItem>
              ))}
            </List>
          </Paper>

          {/* Popular Articles */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, color: '#8B1538' }}>
              Most Viewed
            </Typography>
            <List dense>
              {articles
                .sort((a, b) => b.views - a.views)
                .slice(0, 5)
                .map((article) => (
                  <ListItem 
                    key={article.id}
                    button
                    onClick={() => openArticle(article)}
                    sx={{ borderRadius: 1, mb: 1, p: 1 }}
                  >
                    <ListItemIcon>
                      <ArticleIcon color="action" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={article.title}
                      secondary={`${article.views} views`}
                      primaryTypographyProps={{ fontSize: '0.9rem' }}
                      secondaryTypographyProps={{ fontSize: '0.8rem' }}
                    />
                  </ListItem>
                ))}
            </List>
          </Paper>
        </Grid>

        {/* Main Content - Articles */}
        <Grid item xs={12} md={9}>
          {articles.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <ArticleIcon sx={{ fontSize: 64, color: '#ccc', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No articles found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Try adjusting your search terms or category filter
              </Typography>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {articles.map((article) => (
                <Grid item xs={12} key={article.id}>
                  <Card 
                    sx={{ 
                      cursor: 'pointer',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 4,
                      }
                    }}
                    onClick={() => openArticle(article)}
                  >
                    <CardContent sx={{ p: 3 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Typography variant="h6" sx={{ color: '#8B1538', fontWeight: 600, flexGrow: 1 }}>
                          {article.title}
                        </Typography>
                        <Chip 
                          label={article.category} 
                          size="small" 
                          sx={{ 
                            backgroundColor: '#FF8C42', 
                            color: 'white',
                            ml: 2
                          }} 
                        />
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {article.summary}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ViewIcon fontSize="small" color="action" />
                          <Typography variant="caption" color="text.secondary">
                            {article.views} views
                          </Typography>
                        </Box>
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ThumbUpIcon fontSize="small" color="action" />
                          <Typography variant="caption" color="text.secondary">
                            {article.helpful_votes} helpful
                          </Typography>
                        </Box>
                        
                        <Typography variant="caption" color="text.secondary">
                          Updated: {new Date(article.updated_at).toLocaleDateString()}
                        </Typography>
                        
                        {article.tags && (
                          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {article.tags.split(',').slice(0, 3).map((tag, index) => (
                              <Chip 
                                key={index}
                                label={tag.trim()} 
                                size="small" 
                                variant="outlined"
                                sx={{ fontSize: '0.7rem', height: 20 }}
                              />
                            ))}
                          </Box>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Grid>
      </Grid>

      {/* Article Detail Dialog */}
      <Dialog 
        open={showArticleDialog} 
        onClose={closeArticle}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { minHeight: '80vh' }
        }}
      >
        {selectedArticle && (
          <>
            <DialogTitle sx={{ pb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h5" sx={{ color: '#8B1538', fontWeight: 600 }}>
                  {selectedArticle.title}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <IconButton size="small" onClick={() => window.print()}>
                    <PrintIcon />
                  </IconButton>
                  <IconButton size="small">
                    <ShareIcon />
                  </IconButton>
                  <IconButton size="small">
                    <BookmarkIcon />
                  </IconButton>
                  <IconButton onClick={closeArticle}>
                    <ArrowBackIcon />
                  </IconButton>
                </Box>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
                <Chip label={selectedArticle.category} size="small" color="primary" />
                <Typography variant="caption" color="text.secondary">
                  {selectedArticle.views} views • {selectedArticle.helpful_votes} found helpful
                </Typography>
              </Box>
            </DialogTitle>
            
            <DialogContent>
              <Typography variant="body1" sx={{ mb: 3, fontStyle: 'italic', color: '#666' }}>
                {selectedArticle.summary}
              </Typography>
              
              <Divider sx={{ mb: 3 }} />
              
              <Box 
                sx={{ 
                  '& h1, & h2, & h3': { mt: 2, mb: 1 },
                  '& p': { mb: 2 },
                  '& li': { mb: 0.5 },
                  lineHeight: 1.6
                }}
                dangerouslySetInnerHTML={{ 
                  __html: formatContent(selectedArticle.content) 
                }}
              />
            </DialogContent>
            
            <DialogActions sx={{ p: 3, pt: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <Typography variant="body2" color="text.secondary">
                  Was this article helpful?
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<ThumbUpIcon />}
                  onClick={() => markAsHelpful(selectedArticle.id)}
                  sx={{ 
                    borderColor: '#FF8C42',
                    color: '#FF8C42',
                    '&:hover': {
                      backgroundColor: '#FF8C42',
                      color: 'white'
                    }
                  }}
                >
                  Yes ({selectedArticle.helpful_votes})
                </Button>
                <Box sx={{ flexGrow: 1 }} />
                <Button onClick={closeArticle} variant="contained" color="primary">
                  Close
                </Button>
              </Box>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default KnowledgeBase;