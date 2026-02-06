/**
 * SAP-styled Form Dialog Component
 * For creating/editing records with multiple fields
 */
import React, { useState } from 'react';
import '../styles/sap-theme.css';

interface FormField {
  name: string;
  label: string;
  type?: 'text' | 'number' | 'select' | 'date' | 'textarea';
  required?: boolean;
  options?: { value: string; label: string }[];
  defaultValue?: string | number;
  placeholder?: string;
}

interface SAPFormDialogProps {
  isOpen: boolean;
  title: string;
  fields: FormField[];
  onSubmit: (data: Record<string, any>) => void;
  onCancel: () => void;
  submitLabel?: string;
}

const SAPFormDialog: React.FC<SAPFormDialogProps> = ({
  isOpen,
  title,
  fields,
  onSubmit,
  onCancel,
  submitLabel = 'Create'
}) => {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  React.useEffect(() => {
    if (isOpen) {
      const initialData: Record<string, any> = {};
      fields.forEach(field => {
        initialData[field.name] = field.defaultValue || '';
      });
      setFormData(initialData);
      setErrors({});
    }
  }, [isOpen, fields]);

  const handleChange = (name: string, value: any) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    fields.forEach(field => {
      if (field.required && !formData[field.name]) {
        newErrors[field.name] = `${field.label} is required`;
      }
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validate()) {
      onSubmit(formData);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit();
    } else if (e.key === 'Escape') {
      onCancel();
    }
  };

  if (!isOpen) return null;

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
        onClick={onCancel}
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
          minWidth: '550px',
          maxWidth: '750px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
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
            onClick={onCancel}
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
          padding: '20px',
          backgroundColor: '#ffffff',
          border: '1px solid #c5d9f1',
          margin: '12px',
          overflowY: 'auto',
          flex: 1
        }}>
          <div style={{ display: 'grid', gap: '16px' }}>
            {fields.map((field) => (
              <div key={field.name} className="sap-form-group" style={{ marginBottom: 0 }}>
                <label style={{
                  display: 'block',
                  marginBottom: '6px',
                  fontWeight: 600,
                  color: '#000',
                  fontSize: '14px'
                }}>
                  {field.label}
                  {field.required && <span style={{ color: '#bb0000' }}> *</span>}
                </label>

                {field.type === 'select' ? (
                  <select
                    style={{
                      width: '100%',
                      padding: '8px 10px',
                      border: '1px solid #8db3e2',
                      borderRadius: '0',
                      fontSize: '14px',
                      fontFamily: 'inherit',
                      backgroundColor: '#fff'
                    }}
                    value={formData[field.name] || ''}
                    onChange={(e) => handleChange(field.name, e.target.value)}
                    onKeyPress={handleKeyPress}
                  >
                    <option value="">Select...</option>
                    {field.options?.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                ) : field.type === 'textarea' ? (
                  <textarea
                    style={{
                      width: '100%',
                      padding: '8px 10px',
                      border: '1px solid #8db3e2',
                      borderRadius: '0',
                      fontSize: '14px',
                      fontFamily: 'inherit',
                      backgroundColor: '#fff',
                      resize: 'vertical'
                    }}
                    value={formData[field.name] || ''}
                    onChange={(e) => handleChange(field.name, e.target.value)}
                    placeholder={field.placeholder}
                    rows={4}
                  />
                ) : (
                  <input
                    type={field.type || 'text'}
                    style={{
                      width: '100%',
                      padding: '8px 10px',
                      border: '1px solid #8db3e2',
                      borderRadius: '0',
                      fontSize: '14px',
                      fontFamily: 'inherit',
                      backgroundColor: '#fff'
                    }}
                    value={formData[field.name] || ''}
                    onChange={(e) => handleChange(field.name, e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={field.placeholder}
                  />
                )}

                {errors[field.name] && (
                  <div style={{ fontSize: '12px', color: '#bb0000', marginTop: '4px', fontWeight: 500 }}>
                    {errors[field.name]}
                  </div>
                )}
              </div>
            ))}
          </div>
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
          <button
            onClick={onCancel}
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
          <button
            onClick={handleSubmit}
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
            {submitLabel}
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

export default SAPFormDialog;
