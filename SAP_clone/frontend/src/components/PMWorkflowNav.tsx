/**
 * PM Workflow Navigation Component
 * Provides tab-based navigation between the 6 workflow screens
 * Requirements: All screens
 */
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../styles/sap-theme.css';

interface PMWorkflowNavProps {
  orderNumber?: string;
  currentScreen?: number;
}

const PMWorkflowNav: React.FC<PMWorkflowNavProps> = ({ orderNumber, currentScreen }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const screens = [
    { number: 1, name: 'Order Planning', path: '/pm-workflow/screen1', icon: '📋' },
    { number: 2, name: 'Procurement', path: orderNumber ? `/pm-workflow/screen2/${orderNumber}` : '/pm-workflow/screen2', icon: '🛒', requiresOrder: true },
    { number: 3, name: 'Order Release', path: '/pm-workflow/screen3', icon: '✅' },
    { number: 4, name: 'Material Receipt', path: '/pm-workflow/screen4', icon: '📦' },
    { number: 5, name: 'Work Execution', path: orderNumber ? `/pm-workflow/screen5/${orderNumber}` : '/pm-workflow/screen5', icon: '🔧', requiresOrder: true },
    { number: 6, name: 'Completion', path: orderNumber ? `/pm-workflow/screen6/${orderNumber}` : '/pm-workflow/screen6', icon: '✓', requiresOrder: true }
  ];

  const handleScreenClick = (screen: typeof screens[0]) => {
    if (screen.requiresOrder && !orderNumber) {
      // Don't navigate if order is required but not provided
      return;
    }
    navigate(screen.path);
  };

  const isActive = (screenNum: number) => {
    if (currentScreen) {
      return currentScreen === screenNum;
    }
    // Fallback to path matching
    return location.pathname.includes(`screen${screenNum}`);
  };

  return (
    <div className="pm-workflow-nav" style={{
      display: 'flex',
      gap: '8px',
      padding: '16px',
      backgroundColor: '#f5f5f5',
      borderBottom: '2px solid #0070f2',
      overflowX: 'auto'
    }}>
      {screens.map((screen) => {
        const active = isActive(screen.number);
        const disabled = screen.requiresOrder && !orderNumber;
        
        return (
          <button
            key={screen.number}
            onClick={() => handleScreenClick(screen)}
            disabled={disabled}
            className={`pm-workflow-tab ${active ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '12px 20px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: active ? '#0070f2' : disabled ? '#e0e0e0' : '#ffffff',
              color: active ? '#ffffff' : disabled ? '#999999' : '#333333',
              cursor: disabled ? 'not-allowed' : 'pointer',
              minWidth: '120px',
              transition: 'all 0.2s',
              boxShadow: active ? '0 2px 8px rgba(0,112,242,0.3)' : '0 1px 3px rgba(0,0,0,0.1)',
              opacity: disabled ? 0.5 : 1
            }}
            onMouseEnter={(e) => {
              if (!disabled && !active) {
                e.currentTarget.style.backgroundColor = '#f0f0f0';
                e.currentTarget.style.boxShadow = '0 2px 6px rgba(0,0,0,0.15)';
              }
            }}
            onMouseLeave={(e) => {
              if (!disabled && !active) {
                e.currentTarget.style.backgroundColor = '#ffffff';
                e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
              }
            }}
          >
            <div style={{ fontSize: '24px', marginBottom: '4px' }}>{screen.icon}</div>
            <div style={{ fontSize: '11px', fontWeight: 600, marginBottom: '2px' }}>
              Screen {screen.number}
            </div>
            <div style={{ fontSize: '12px', textAlign: 'center' }}>
              {screen.name}
            </div>
          </button>
        );
      })}
      
      {orderNumber && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          marginLeft: 'auto',
          padding: '8px 16px',
          backgroundColor: '#ffffff',
          borderRadius: '4px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <span style={{ fontSize: '12px', color: '#666', marginRight: '8px' }}>Order:</span>
          <span style={{ fontSize: '14px', fontWeight: 600, color: '#0070f2' }}>{orderNumber}</span>
        </div>
      )}
    </div>
  );
};

export default PMWorkflowNav;
