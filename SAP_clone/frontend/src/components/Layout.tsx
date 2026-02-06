/**
 * Main Layout with SAP Fiori-style navigation
 * Requirement 8.1 - SAP Fiori-style shell with sidebar
 */
import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/sap-theme.css';

const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [expandedMenus, setExpandedMenus] = useState<string[]>(['modules']);

  const menuItems = [
    { 
      id: 'home',
      path: '/', 
      label: 'My Home', 
      icon: '🏠',
      parent: null
    },
    { 
      id: 'dashboard',
      path: '/dashboard', 
      label: 'Dashboard', 
      icon: '📊',
      parent: null
    },
    { 
      id: 'tickets',
      path: '/tickets', 
      label: 'Tickets', 
      icon: '🎫',
      parent: null
    },
    {
      id: 'modules',
      label: 'SAP Modules',
      icon: '📁',
      parent: null,
      children: [
        { id: 'pm', path: '/pm', label: 'Plant Maintenance (PM)', icon: '🔧' },
        { id: 'mm', path: '/mm', label: 'Materials Management (MM)', icon: '📦' },
        { id: 'fi', path: '/fi', label: 'Financial Accounting (FI)', icon: '💰' },
      ]
    }
  ];

  const isActive = (path: string) => location.pathname === path;
  
  const toggleMenu = (id: string) => {
    setExpandedMenus(prev => 
      prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
    );
  };

  const renderMenuItem = (item: any, level = 0) => {
    if (item.children) {
      const isExpanded = expandedMenus.includes(item.id);
      return (
        <div key={item.id}>
          <div
            onClick={() => toggleMenu(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '10px 20px',
              paddingLeft: `${20 + level * 16}px`,
              color: 'white',
              cursor: 'pointer',
              backgroundColor: 'transparent',
              borderLeft: '3px solid transparent'
            }}
          >
            <span style={{ marginRight: '8px', fontSize: '12px' }}>
              {isExpanded ? '▼' : '▶'}
            </span>
            <span style={{ marginRight: '12px' }}>{item.icon}</span>
            <span style={{ fontSize: '14px' }}>{item.label}</span>
          </div>
          {isExpanded && (
            <div>
              {item.children.map((child: any) => renderMenuItem(child, level + 1))}
            </div>
          )}
        </div>
      );
    }

    return (
      <Link
        key={item.id}
        to={item.path}
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '10px 20px',
          paddingLeft: `${20 + level * 16}px`,
          color: 'white',
          textDecoration: 'none',
          backgroundColor: isActive(item.path) ? '#4a6178' : 'transparent',
          borderLeft: isActive(item.path) ? '3px solid #0a6ed1' : '3px solid transparent',
          fontSize: '14px'
        }}
      >
        <span style={{ marginRight: '12px' }}>{item.icon}</span>
        {item.label}
      </Link>
    );
  };

  const currentPage = menuItems.find(m => m.path && isActive(m.path))?.label || 
                      menuItems.flatMap(m => m.children || []).find(c => isActive(c.path))?.label ||
                      'SAP ERP';

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: "'72', 'Segoe UI', Arial, sans-serif" }}>
      {/* SAP Shell Sidebar */}
      <div style={{
        width: '260px',
        backgroundColor: '#354a5f',
        color: 'white',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '2px 0 8px rgba(0,0,0,0.15)'
      }}>
        {/* SAP Logo Header */}
        <div style={{ 
          padding: '16px 20px', 
          borderBottom: '1px solid #4a6178',
          backgroundColor: '#2c3e50'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              backgroundColor: '#0a6ed1',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              fontSize: '18px'
            }}>
              SAP
            </div>
            <div>
              <div style={{ fontSize: '16px', fontWeight: 600 }}>ERP System</div>
              <div style={{ fontSize: '11px', opacity: 0.8 }}>Demo Environment</div>
            </div>
          </div>
        </div>

        {/* Navigation Tree */}
        <nav style={{ flex: 1, padding: '8px 0', overflowY: 'auto' }}>
          {menuItems.map(item => renderMenuItem(item))}
        </nav>

        {/* User Info Footer */}
        <div style={{ 
          padding: '16px 20px', 
          borderTop: '1px solid #4a6178',
          backgroundColor: '#2c3e50'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center',
            marginBottom: '12px',
            gap: '10px'
          }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: '#0a6ed1',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px'
            }}>
              👤
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '13px', fontWeight: 500 }}>
                {user?.username || 'Guest'}
              </div>
              <div style={{ fontSize: '11px', opacity: 0.7 }}>
                System User
              </div>
            </div>
          </div>
          <button
            onClick={logout}
            style={{
              width: '100%',
              padding: '8px 12px',
              backgroundColor: 'transparent',
              color: 'white',
              border: '1px solid #4a6178',
              borderRadius: '3px',
              cursor: 'pointer',
              fontSize: '13px',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#4a6178'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, backgroundColor: '#f7f7f7', display: 'flex', flexDirection: 'column' }}>
        {/* SAP Header Bar */}
        <header style={{
          backgroundColor: 'white',
          borderBottom: '1px solid #d9d9d9',
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)'
        }}>
          {/* Top Bar */}
          <div style={{
            padding: '8px 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid #f0f0f0'
          }}>
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: '#6a6d70' }}>
                System: PRD | Client: 100
              </span>
            </div>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: '#6a6d70' }}>🔔</span>
              <span style={{ fontSize: '12px', color: '#6a6d70' }}>⚙️</span>
              <span style={{ fontSize: '12px', color: '#6a6d70' }}>❓</span>
            </div>
          </div>
          
          {/* Page Title Bar */}
          <div style={{ padding: '12px 24px' }}>
            <h1 style={{ 
              margin: 0, 
              fontSize: '20px', 
              fontWeight: 400,
              color: '#32363a'
            }}>
              {currentPage}
            </h1>
          </div>
        </header>

        {/* Page Content */}
        <main style={{ 
          flex: 1,
          padding: '20px 24px',
          overflowY: 'auto'
        }}>
          <Outlet />
        </main>

        {/* Footer */}
        <footer style={{
          padding: '8px 24px',
          backgroundColor: '#ffffff',
          borderTop: '1px solid #e5e5e5',
          fontSize: '11px',
          color: '#6a6d70',
          textAlign: 'center'
        }}>
          SAP ERP Demo System © 2026 | Version 1.0.0
        </footer>
      </div>
    </div>
  );
};

export default Layout;
