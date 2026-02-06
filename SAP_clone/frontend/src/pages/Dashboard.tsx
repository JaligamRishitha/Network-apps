/**
 * Dashboard Page - SAP Fiori Launchpad (Exact Replica)
 * Matches the SAP Fiori screenshot layout
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ticketsApi } from '../services/api';
import '../styles/sap-theme.css';

interface DashboardStats {
  totalTickets: number;
  openTickets: number;
  inProgressTickets: number;
  resolvedTickets: number;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    totalTickets: 0,
    openTickets: 0,
    inProgressTickets: 0,
    resolvedTickets: 0,
  });
  const [loading, setLoading] = useState(true);
  const [activeAppsTab, setActiveAppsTab] = useState('favorites');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await ticketsApi.list();
      const tickets = response.data.tickets || [];
      
      setStats({
        totalTickets: tickets.length,
        openTickets: tickets.filter((t: any) => t.status === 'open').length,
        inProgressTickets: tickets.filter((t: any) => t.status === 'in_progress').length,
        resolvedTickets: tickets.filter((t: any) => t.status === 'resolved').length,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#f7f7f7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f7f7f7', padding: '20px' }}>
      {/* My Home Section */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '20px', fontWeight: 400, marginBottom: '16px', color: '#32363a' }}>My Home</h1>
        
        {/* System Status Tiles */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
          <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <div style={{ fontSize: '11px', color: '#6a6d70', marginBottom: '4px' }}>Launch System</div>
            <div style={{ fontSize: '11px', color: '#6a6d70', marginBottom: '8px' }}>Directory</div>
            <div style={{ fontSize: '32px', fontWeight: 300, color: '#32363a', marginBottom: '4px' }}>2</div>
            <div style={{ fontSize: '10px', color: '#6a6d70' }}>Systems in Enterprise</div>
          </div>

          <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <div style={{ fontSize: '11px', color: '#6a6d70', marginBottom: '4px' }}>Launch Alert Monitor</div>
            <div style={{ fontSize: '11px', color: '#6a6d70', marginBottom: '8px' }}></div>
            <div style={{ fontSize: '32px', fontWeight: 300, color: '#d9534f', marginBottom: '4px' }}>2</div>
            <div style={{ fontSize: '10px', color: '#6a6d70' }}>2 HP / 0 LP</div>
          </div>

          <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <div style={{ fontSize: '11px', color: '#6a6d70', marginBottom: '4px' }}>Start & Stop</div>
            <div style={{ fontSize: '11px', color: '#6a6d70', marginBottom: '8px' }}>Systems</div>
            <div style={{ fontSize: '32px', fontWeight: 300, color: '#6a6d70', marginBottom: '4px' }}>0</div>
            <div style={{ fontSize: '10px', color: '#6a6d70' }}>Systems Stopped</div>
          </div>

          <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <div style={{ fontSize: '11px', color: '#6a6d70', marginBottom: '4px' }}>Monitor Enterprise</div>
            <div style={{ fontSize: '11px', color: '#6a6d70', marginBottom: '8px' }}>Health</div>
            <div style={{ fontSize: '32px', fontWeight: 300, color: '#32363a', marginBottom: '4px' }}>2</div>
            <div style={{ fontSize: '10px', color: '#6a6d70' }}>Systems Running</div>
          </div>
        </div>
      </div>

      {/* SAP ERP Modules */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 400, marginBottom: '12px', color: '#32363a' }}>SAP ERP Modules</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <div 
            onClick={() => navigate('/pm')}
            style={{ backgroundColor: 'white', padding: '16px', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', cursor: 'pointer', transition: 'box-shadow 0.2s', minHeight: '120px' }}
            onMouseOver={(e) => e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)'}
            onMouseOut={(e) => e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)'}
          >
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#32363a' }}>Plant Maintenance</div>
              <div style={{ fontSize: '11px', color: '#6a6d70' }}>(PM)</div>
            </div>
            <div style={{ borderTop: '1px solid #e5e5e5', paddingTop: '12px' }}>
              <div style={{ fontSize: '28px', fontWeight: 300, color: '#32363a' }}>{stats.totalTickets}</div>
              <div style={{ fontSize: '11px', color: '#6a6d70' }}>Active Work Orders</div>
            </div>
          </div>

          <div 
            onClick={() => navigate('/mm')}
            style={{ backgroundColor: 'white', padding: '16px', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', cursor: 'pointer', transition: 'box-shadow 0.2s', minHeight: '120px' }}
            onMouseOver={(e) => e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)'}
            onMouseOut={(e) => e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)'}
          >
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#32363a' }}>Materials Management</div>
              <div style={{ fontSize: '11px', color: '#6a6d70' }}>(MM)</div>
            </div>
            <div style={{ borderTop: '1px solid #e5e5e5', paddingTop: '12px' }}>
              <div style={{ fontSize: '28px', fontWeight: 300, color: '#32363a' }}>7</div>
              <div style={{ fontSize: '11px', color: '#6a6d70' }}>Materials in Stock</div>
            </div>
          </div>

          <div 
            onClick={() => navigate('/fi')}
            style={{ backgroundColor: 'white', padding: '16px', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', cursor: 'pointer', transition: 'box-shadow 0.2s', minHeight: '120px' }}
            onMouseOver={(e) => e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)'}
            onMouseOut={(e) => e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)'}
          >
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#32363a' }}>Financial Accounting</div>
              <div style={{ fontSize: '11px', color: '#6a6d70' }}>(FI)</div>
            </div>
            <div style={{ borderTop: '1px solid #e5e5e5', paddingTop: '12px' }}>
              <div style={{ fontSize: '28px', fontWeight: 300, color: '#32363a' }}>5</div>
              <div style={{ fontSize: '11px', color: '#6a6d70' }}>Cost Centers</div>
            </div>
          </div>

          <div 
            onClick={() => navigate('/electricity')}
            style={{ backgroundColor: 'white', padding: '16px', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', cursor: 'pointer', transition: 'box-shadow 0.2s', minHeight: '120px', border: '2px solid #1890ff' }}
            onMouseOver={(e) => e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)'}
            onMouseOut={(e) => e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)'}
          >
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#1890ff' }}>⚡ Electricity Load Requests</div>
              <div style={{ fontSize: '11px', color: '#6a6d70' }}>MuleSoft Integration</div>
            </div>
            <div style={{ borderTop: '1px solid #e5e5e5', paddingTop: '12px' }}>
              <div style={{ fontSize: '28px', fontWeight: 300, color: '#1890ff' }}>NEW</div>
              <div style={{ fontSize: '11px', color: '#6a6d70' }}>Load Enhancement Portal</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
