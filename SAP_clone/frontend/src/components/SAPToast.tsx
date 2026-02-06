/**
 * SAP-styled Toast Notification Component
 * Replaces alert() with non-blocking notifications
 */
import React, { useEffect } from 'react';
import '../styles/sap-theme.css';

interface SAPToastProps {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  isOpen: boolean;
  onClose: () => void;
  duration?: number;
}

const SAPToast: React.FC<SAPToastProps> = ({
  message,
  type,
  isOpen,
  onClose,
  duration = 4000
}) => {
  useEffect(() => {
    if (isOpen && duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [isOpen, duration, onClose]);

  if (!isOpen) return null;

  const icons = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ'
  };

  const colors = {
    success: { bg: '#d4edda', border: '#28a745', text: '#155724', headerBg: 'linear-gradient(to bottom, #a8d5ba 0%, #8bc99e 100%)' },
    error: { bg: '#f8d7da', border: '#dc3545', text: '#721c24', headerBg: 'linear-gradient(to bottom, #f5c6cb 0%, #f1aeb5 100%)' },
    warning: { bg: '#fff3cd', border: '#ffc107', text: '#856404', headerBg: 'linear-gradient(to bottom, #ffe69c 0%, #ffd966 100%)' },
    info: { bg: '#d1ecf1', border: '#17a2b8', text: '#0c5460', headerBg: 'linear-gradient(to bottom, #bee5eb 0%, #9fcddb 100%)' }
  };

  const color = colors[type];

  return (
    <div
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        backgroundColor: '#e8f0f7',
        border: `2px solid ${color.border}`,
        borderRadius: '0',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
        zIndex: 10000,
        minWidth: '350px',
        maxWidth: '550px',
        animation: 'slideInRight 0.3s ease-out',
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <div
        style={{
          background: color.headerBg,
          borderBottom: `1px solid ${color.border}`,
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          fontWeight: 700,
          fontSize: '13px',
          color: '#000',
          textShadow: '0 1px 0 rgba(255,255,255,0.5)'
        }}>
          <span style={{ fontSize: '16px' }}>{icons[type]}</span>
          <span>{type.charAt(0).toUpperCase() + type.slice(1)}</span>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'linear-gradient(to bottom, #f0f0f0 0%, #d0d0d0 100%)',
            border: '1px solid #999',
            fontSize: '14px',
            cursor: 'pointer',
            color: '#000',
            padding: '2px 6px',
            lineHeight: 1,
            fontWeight: 'bold',
            borderRadius: '2px'
          }}
        >
          ×
        </button>
      </div>
      
      {/* Content */}
      <div style={{ 
        padding: '12px 16px',
        backgroundColor: '#ffffff',
        border: `1px solid ${color.bg}`,
        margin: '8px',
        fontSize: '14px',
        color: '#000'
      }}>
        {message}
      </div>

      <style>{`
        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(100px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </div>
  );
};

export default SAPToast;
