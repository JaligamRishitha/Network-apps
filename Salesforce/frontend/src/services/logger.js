import api from './api';

export const loggerService = {
  /**
   * Log frontend click events
   */
  logClick: async (element, details) => {
    try {
      await api.post('/api/logs/frontend-click', {
        action_type: 'CLICK',
        element,
        details,
      });
    } catch (error) {
      console.error('Failed to log click:', error);
    }
  },

  /**
   * Log any action from frontend
   */
  logAction: async (actionType, details) => {
    try {
      await api.post('/api/logs/action', {
        action_type: actionType,
        details,
      });
    } catch (error) {
      console.error('Failed to log action:', error);
    }
  },

  /**
   * Log page navigation
   */
  logPageView: async (pageName) => {
    try {
      await api.post('/api/logs/action', {
        action_type: 'PAGE_VIEW',
        details: `Navigated to ${pageName}`,
      });
    } catch (error) {
      console.error('Failed to log page view:', error);
    }
  },

  /**
   * Log form submission
   */
  logFormSubmit: async (formName, action) => {
    try {
      await api.post('/api/logs/action', {
        action_type: 'FORM_SUBMIT',
        details: `Form: ${formName} | Action: ${action}`,
      });
    } catch (error) {
      console.error('Failed to log form submit:', error);
    }
  },

  /**
   * Log button click
   */
  logButtonClick: async (buttonName, details = '') => {
    try {
      await api.post('/api/logs/frontend-click', {
        action_type: 'BUTTON_CLICK',
        element: buttonName,
        details: details || `Clicked ${buttonName}`,
      });
    } catch (error) {
      console.error('Failed to log button click:', error);
    }
  },

  /**
   * Log search action
   */
  logSearch: async (searchTerm, searchType) => {
    try {
      await api.post('/api/logs/action', {
        action_type: 'SEARCH',
        details: `Search: ${searchTerm} | Type: ${searchType}`,
      });
    } catch (error) {
      console.error('Failed to log search:', error);
    }
  },

  /**
   * Log filter action
   */
  logFilter: async (filterName, filterValue) => {
    try {
      await api.post('/api/logs/action', {
        action_type: 'FILTER',
        details: `Filter: ${filterName} = ${filterValue}`,
      });
    } catch (error) {
      console.error('Failed to log filter:', error);
    }
  },
};

export default loggerService;
