/**
 * Top Navigation Layout - SAP Fiori Style
 * Horizontal navigation bar instead of sidebar
 */
import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const TopNavLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const navItems = [
    { label: 'My Home', path: '/dashboard' },
    { label: 'Plant Maintenance (PM)', path: '/pm' },
    { label: 'Materials Management (MM)', path: '/mm' },
    { label: 'Financial Accounting (FI)', path: '/fi' },
    { label: '🎫 Tickets', path: '/tickets' },
    { label: '👥 User Management', path: '/user-management' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* SAP Header */}
      <header style={{
        backgroundColor: '#354a5f',
        color: 'white',
        height: '44px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <img 
            src="/sap-logo.png" 
            alt="SAP" 
            style={{ 
              height: '28px',
              width: 'auto',
              objectFit: 'contain'
            }} 
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button 
            onClick={handleLogout}
            style={{
              background: 'none',
              border: 'none',
              color: 'white',
              fontSize: '13px',
              cursor: 'pointer',
              padding: '4px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              borderRadius: '4px'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <span>{user?.username || 'User'}</span>
            <span style={{ fontSize: '10px' }}>▼</span>
          </button>
        </div>
      </header>

      {/* Navigation Bar */}
      <nav style={{
        backgroundColor: '#f7f7f7',
        borderBottom: '1px solid #d9d9d9',
        padding: '0 16px',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        overflowX: 'auto',
        whiteSpace: 'nowrap'
      }}>
        {navItems.map((item, index) => (
          <button
            key={index}
            onClick={() => navigate(item.path)}
            style={{
              background: location.pathname === item.path ? 'white' : 'transparent',
              border: 'none',
              borderBottom: location.pathname === item.path ? '3px solid #0070f2' : '3px solid transparent',
              padding: '12px 16px',
              fontSize: '13px',
              color: location.pathname === item.path ? '#0070f2' : '#32363a',
              cursor: 'pointer',
              fontWeight: location.pathname === item.path ? 600 : 400,
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main style={{ flex: 1, backgroundColor: '#f7f7f7' }}>
        <Outlet />
      </main>
    </div>
  );
};

export default TopNavLayout;
