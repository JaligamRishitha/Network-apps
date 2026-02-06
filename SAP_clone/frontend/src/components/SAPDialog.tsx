/**
 * SAP-styled Dialog Component
 * Replaces browser alert() and prompt() with SAP Fiori dialogs
 */
import React, { useState, useEffect } from 'react';
import '../styles/sap-theme.css';

interface SAPDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  type: 'alert' | 'confirm' | 'prompt';
  onClose: (result?: string | boolean) => void;
  defaultValue?: string;
  inputLabel?: string;
}

const SAPDialog: React.FC<SAPDialogProps> = ({
  isOpen,
  title,
  message,
  type,
  onClose,
  defaultValue = '',
  inputLabel = ''
}) => {
  const [inputValue, setInputValue] = useState(defaultValue);

  useEffect(() => {
    setInputValue(defaultValue);
  }, [defaultValue, isOpen]);

  if (!isOpen) return null;

  const handleOk = () => {
    if (type === 'prompt') {
      onClose(inputValue);
    } else if (type === 'confirm') {
      onClose(true);
    } else {
      onClose();
    }
  };

  const handleCancel = () => {
    if (type === 'confirm') {
      onClose(false);
    } else if (type === 'prompt') {
      onClose(undefined);
    } else {
      onClose();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleOk();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  return (
    <>
      {/* Overlay */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 9998,
          animation: 'fadeIn 0.2s ease-in-out'
        }}
        onClick={handleCancel}
      />

      {/* Dialog */}
      <div
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          backgroundColor: '#e8f0f7',
          border: '2px solid #4f81bd',
          borderRadius: '0',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
          zIndex: 9999,
          minWidth: '450px',
          maxWidth: '650px',
          animation: 'slideIn 0.2s ease-out'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '10px 16px',
            background: 'linear-gradient(to bottom, #b4c7e7 0%, #8db3e2 100%)',
            borderBottom: '2px solid #4f81bd',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <h3 style={{ 
            margin: 0, 
            fontSize: '14px', 
            fontWeight: 700, 
            color: '#000',
            textShadow: '0 1px 0 rgba(255,255,255,0.5)'
          }}>
            {title}
          </h3>
          <button
            onClick={handleCancel}
            style={{
              background: 'linear-gradient(to bottom, #f0f0f0 0%, #d0d0d0 100%)',
              border: '1px solid #999',
              fontSize: '14px',
              cursor: 'pointer',
              color: '#000',
              padding: '2px 8px',
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
          padding: '24px 20px',
          backgroundColor: '#ffffff',
          border: '1px solid #c5d9f1',
          margin: '12px'
        }}>
          <div style={{ fontSize: '14px', color: '#000', marginBottom: type === 'prompt' ? '16px' : '0' }}>
            {message}
          </div>

          {type === 'prompt' && (
            <div className="sap-form-group" style={{ marginTop: '16px', marginBottom: 0 }}>
              {inputLabel && (
                <label className="sap-form-label" style={{ color: '#000', fontWeight: 600 }}>
                  {inputLabel}
                </label>
              )}
              <input
                type="text"
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  border: '1px solid #8db3e2',
                  borderRadius: '0',
                  fontSize: '14px',
                  fontFamily: 'inherit',
                  backgroundColor: '#fff'
                }}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                autoFocus
                placeholder="Enter value..."
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '12px 16px',
            background: 'linear-gradient(to bottom, #dae8f5 0%, #c5d9f1 100%)',
            borderTop: '1px solid #4f81bd',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '8px'
          }}
        >
          {(type === 'confirm' || type === 'prompt') && (
            <button
              onClick={handleCancel}
              style={{
                background: 'linear-gradient(to bottom, #f5f5f5 0%, #e0e0e0 100%)',
                border: '1px solid #999',
                padding: '6px 20px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                borderRadius: '2px',
                color: '#000',
                minWidth: '80px'
              }}
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleOk}
            style={{
              background: 'linear-gradient(to bottom, #5b9bd5 0%, #4472c4 100%)',
              border: '1px solid #2e5c8a',
              padding: '6px 20px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 600,
              borderRadius: '2px',
              color: '#fff',
              minWidth: '80px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.2)'
            }}
          >
            OK
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translate(-50%, -48%);
          }
          to {
            opacity: 1;
            transform: translate(-50%, -50%);
          }
        }
      `}</style>
    </>
  );
};

export default SAPDialog;
