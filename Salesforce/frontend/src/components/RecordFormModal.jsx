import { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { authAPI, accountsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

const salutationOptions = ['--None--', 'Mr.', 'Ms.', 'Mrs.', 'Dr.', 'Prof.'];
const leadStatusOptions = ['New', 'Contacted', 'Qualified', 'Unqualified'];
const leadSourceOptions = ['--None--', 'Web', 'Phone Inquiry', 'Partner Referral', 'Purchased List', 'Other'];
const industryOptions = ['--None--', 'Agriculture', 'Apparel', 'Banking', 'Biotechnology', 'Chemicals', 'Communications', 'Construction', 'Consulting', 'Education', 'Electricity Distribution', 'Electronics', 'Energy', 'Engineering', 'Entertainment', 'Environmental', 'Finance', 'Food & Beverage', 'Government', 'Healthcare', 'Hospitality', 'Insurance', 'Machinery', 'Manufacturing', 'Media', 'Not For Profit', 'Recreation', 'Retail', 'Shipping', 'Technology', 'Telecommunications', 'Transportation', 'Utilities', 'Other'];
const countryOptions = ['--None--', 'United States', 'Canada', 'United Kingdom', 'Australia', 'Germany', 'France', 'India', 'Japan', 'China', 'Brazil', 'Mexico', 'Other'];
const stateOptions = ['--None--', 'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'];

const formConfigs = {
  contact: {
    title: 'New Contact',
    sections: [
      {
        title: 'Contact Information',
        fields: [
          { name: 'salutation', label: 'Salutation', type: 'select', options: salutationOptions },
          { name: 'first_name', label: 'First Name', type: 'text' },
          { name: 'last_name', label: 'Last Name', type: 'text', required: true },
          { name: 'account_id', label: 'Account', type: 'select', options: 'accounts' },
          { name: 'title', label: 'Title', type: 'text' },
          { name: 'department', label: 'Department', type: 'text' },
        ],
      },
      {
        title: 'Contact Details',
        fields: [
          { name: 'phone', label: 'Phone', type: 'tel' },
          { name: 'mobile', label: 'Mobile', type: 'tel' },
          { name: 'email', label: 'Email', type: 'email' },
        ],
      },
      {
        title: 'Address',
        fields: [
          { name: 'mailing_street', label: 'Mailing Street', type: 'textarea', rows: 2 },
          { name: 'mailing_city', label: 'Mailing City', type: 'text' },
          { name: 'mailing_state', label: 'Mailing State/Province', type: 'select', options: stateOptions },
          { name: 'mailing_postal_code', label: 'Mailing Zip/Postal Code', type: 'text' },
          { name: 'mailing_country', label: 'Mailing Country', type: 'select', options: countryOptions },
        ],
      },
    ],
  },
  account: {
    title: 'New Account',
    sections: [
      {
        title: 'Account Information',
        fields: [
          { name: 'name', label: 'Account Name', type: 'text', required: true },
          { name: 'phone', label: 'Phone', type: 'tel' },
          { name: 'email', label: 'Email', type: 'email', required: true },
          { name: 'website', label: 'Website', type: 'url' },
          { name: 'industry', label: 'Industry', type: 'select', options: industryOptions },
        ],
      },
      {
        title: 'Address',
        fields: [
          { name: 'street', label: 'Street', type: 'textarea', rows: 2 },
          { name: 'zip_code', label: 'Zip/Postal Code', type: 'text' },
          { name: 'country', label: 'Country', type: 'select', options: countryOptions },
        ],
      },
      {
        title: 'Additional Information',
        fields: [
          { name: 'employees', label: 'Employees', type: 'number' },
          { name: 'annual_revenue', label: 'Annual Revenue', type: 'number' },
          { name: 'description', label: 'Description', type: 'textarea' },
        ],
      },
    ],
  },
  lead: {
    title: 'New Lead',
    sections: [
      {
        title: 'About',
        fields: [
          { name: 'salutation', label: 'Salutation', type: 'select', options: salutationOptions },
          { name: 'first_name', label: 'First Name', type: 'text' },
          { name: 'last_name', label: 'Last Name', type: 'text', required: true },
          { name: 'company', label: 'Company', type: 'text', required: true },
          { name: 'title', label: 'Title', type: 'text' },
          { name: 'website', label: 'Website', type: 'url' },
          { name: 'description', label: 'Description', type: 'textarea' },
          { name: 'status', label: 'Lead Status', type: 'select', options: leadStatusOptions, required: true, defaultValue: 'New' },
          { name: 'owner_id', label: 'Lead Owner', type: 'owner', disabled: true },
        ],
      },
      {
        title: 'Get in Touch',
        fields: [
          { name: 'phone', label: 'Phone', type: 'tel' },
          { name: 'email', label: 'Email', type: 'email' },
          { name: 'country', label: 'Country', type: 'select', options: countryOptions },
          { name: 'street', label: 'Street', type: 'textarea', rows: 2 },
          { name: 'city', label: 'City', type: 'text' },
          { name: 'postal_code', label: 'Zip/Postal Code', type: 'text', half: true },
          { name: 'state', label: 'State/Province', type: 'select', options: stateOptions, half: true },
        ],
      },
      {
        title: 'Segment',
        fields: [
          { name: 'number_of_employees', label: 'No. of Employees', type: 'number' },
          { name: 'annual_revenue', label: 'Annual Revenue', type: 'number' },
          { name: 'lead_source', label: 'Lead Source', type: 'select', options: leadSourceOptions },
          { name: 'industry', label: 'Industry', type: 'select', options: industryOptions },
        ],
      },
    ],
  },
  opportunity: {
    title: 'New Opportunity',
    sections: [
      {
        title: 'Opportunity Information',
        fields: [
          { name: 'name', label: 'Opportunity Name', type: 'text', required: true },
          { name: 'account_id', label: 'Account', type: 'select', options: 'accounts' },
          { name: 'amount', label: 'Amount', type: 'number' },
          { name: 'stage', label: 'Stage', type: 'select', options: ['Prospecting', 'Qualification', 'Needs Analysis', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'], required: true },
          { name: 'close_date', label: 'Close Date', type: 'date', required: true },
          { name: 'probability', label: 'Probability (%)', type: 'number' },
          { name: 'lead_source', label: 'Lead Source', type: 'select', options: leadSourceOptions },
          { name: 'description', label: 'Description', type: 'textarea' },
        ],
      },
    ],
  },
  case: {
    title: 'New Case',
    sections: [
      {
        title: 'Case Information',
        fields: [
          { name: 'subject', label: 'Subject', type: 'text', required: true },
          { name: 'description', label: 'Description', type: 'textarea' },
          { name: 'status', label: 'Status', type: 'select', options: ['New', 'Working', 'Escalated', 'Closed'], defaultValue: 'New' },
          { name: 'priority', label: 'Priority', type: 'select', options: ['Low', 'Medium', 'High', 'Critical'], defaultValue: 'Medium' },
          { name: 'account_id', label: 'Account', type: 'select', options: 'accounts' },
          { name: 'contact_id', label: 'Contact', type: 'select', options: 'contacts' },
        ],
      },
    ],
  },
};

export default function RecordFormModal({ isOpen, onClose, objectType, onSave, initialData = null }) {
  const { user } = useAuth();
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [saveAndNew, setSaveAndNew] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [users, setUsers] = useState([]);

  const config = formConfigs[objectType];

  const getAllFields = () => {
    if (!config) return [];
    if (config.sections) {
      return config.sections.flatMap(s => s.fields);
    }
    return config.fields || [];
  };

  useEffect(() => {
    if (isOpen && config) {
      // Set default values
      const defaults = {};
      getAllFields().forEach(field => {
        if (field.defaultValue) {
          defaults[field.name] = field.defaultValue;
        }
      });
      setFormData(initialData || defaults);
      setErrors({});

      // Load related data if needed
      const allFields = getAllFields();
      if (allFields.some(f => f.options === 'accounts')) {
        loadAccounts();
      }
      if (allFields.some(f => f.options === 'contacts')) {
        loadContacts();
      }
      loadUsers();
    }
  }, [isOpen, objectType, initialData]);

  const loadAccounts = async () => {
    try {
      const response = await accountsAPI.list({ page_size: 100 });
      setAccounts(response.data.items);
    } catch (error) {
      console.error('Failed to load accounts:', error);
    }
  };

  const loadContacts = async () => {
    try {
      const { contactsAPI } = await import('../services/api');
      const response = await contactsAPI.list({ page_size: 100 });
      setContacts(response.data.items);
    } catch (error) {
      console.error('Failed to load contacts:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await authAPI.getUsers();
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const handleChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};
    getAllFields().forEach(field => {
      if (field.required && !formData[field.name]) {
        newErrors[field.name] = `${field.label} is required`;
      }
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e, createAnother = false) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setSaveAndNew(createAnother);
    try {
      const result = await onSave(formData);
      const statusCode = result?.status;

      if (objectType === 'account' && statusCode === 202) {
        toast.success('Account request submitted for approval');
      } else {
        toast.success(`${config.title.replace('New ', '')} created successfully`);
      }

      if (createAnother) {
        // Reset form for new entry
        const defaults = {};
        getAllFields().forEach(field => {
          if (field.defaultValue) {
            defaults[field.name] = field.defaultValue;
          }
        });
        setFormData(defaults);
        setErrors({});
      } else {
        onClose();
      }
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to save';
      toast.error(typeof message === 'string' ? message : 'Failed to save');
    } finally {
      setLoading(false);
      setSaveAndNew(false);
    }
  };

  if (!isOpen || !config) return null;

  const renderField = (field) => {
    // Handle owner display field
    if (field.type === 'owner') {
      return (
        <div className="flex items-center py-2 px-3 bg-gray-50 rounded-md border">
          <div className="w-6 h-6 bg-sf-blue-500 rounded-full flex items-center justify-center text-white text-xs font-medium mr-2">
            {user?.first_name?.[0] || user?.username?.[0] || 'U'}
          </div>
          <span className="text-sm text-gray-700">
            {user?.first_name && user?.last_name
              ? `${user.first_name} ${user.last_name}`
              : user?.username || 'Current User'}
          </span>
        </div>
      );
    }

    const commonProps = {
      id: field.name,
      name: field.name,
      value: formData[field.name] || '',
      onChange: (e) => handleChange(field.name, e.target.value),
      className: `input-field ${errors[field.name] ? 'border-red-500' : ''}`,
      disabled: field.disabled,
    };

    switch (field.type) {
      case 'select':
        let options = [];
        if (field.options === 'accounts') {
          options = accounts.map(a => ({ value: a.id, label: a.name }));
        } else if (field.options === 'contacts') {
          options = contacts.map(c => ({
            value: c.id,
            label: c.full_name || `${c.first_name || ''} ${c.last_name || ''}`.trim()
          }));
        } else if (field.options === 'users') {
          options = users.map(u => ({ value: u.id, label: `${u.first_name} ${u.last_name}` }));
        } else if (Array.isArray(field.options)) {
          options = field.options.map(o => ({ value: o === '--None--' ? '' : o, label: o }));
        }

        return (
          <select {...commonProps}>
            {!field.options?.includes?.('--None--') && <option value="">--None--</option>}
            {options.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        );

      case 'textarea':
        return <textarea {...commonProps} rows={field.rows || 3} />;

      case 'number':
        return <input {...commonProps} type="number" step="0.01" min="0" />;

      default:
        return <input {...commonProps} type={field.type} placeholder={field.placeholder} />;
    }
  };

  const renderSectionFields = (fields) => {
    const result = [];
    let i = 0;
    while (i < fields.length) {
      const field = fields[i];
      const nextField = fields[i + 1];

      // Check if current and next fields should be displayed side by side
      if (field.half && nextField?.half) {
        result.push(
          <div key={`${field.name}-row`} className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor={field.name} className="label">
                {field.label}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              {renderField(field)}
              {errors[field.name] && (
                <p className="mt-1 text-sm text-red-500">{errors[field.name]}</p>
              )}
            </div>
            <div>
              <label htmlFor={nextField.name} className="label">
                {nextField.label}
                {nextField.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              {renderField(nextField)}
              {errors[nextField.name] && (
                <p className="mt-1 text-sm text-red-500">{errors[nextField.name]}</p>
              )}
            </div>
          </div>
        );
        i += 2;
      } else {
        result.push(
          <div key={field.name}>
            <label htmlFor={field.name} className="label">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            {renderField(field)}
            {errors[field.name] && (
              <p className="mt-1 text-sm text-red-500">{errors[field.name]}</p>
            )}
          </div>
        );
        i += 1;
      }
    }
    return result;
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 py-8">
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black/50" onClick={onClose} />

        {/* Modal */}
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">{config.title}</h2>
            <button
              type="button"
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={(e) => handleSubmit(e, false)}>
            <div className="max-h-[65vh] overflow-auto">
              {config.sections ? (
                // Render sections
                config.sections.map((section, index) => (
                  <div key={section.title} className={index > 0 ? 'border-t' : ''}>
                    <div className="px-4 py-3 bg-gray-50 border-b">
                      <h3 className="text-sm font-medium text-gray-700">{section.title}</h3>
                    </div>
                    <div className="p-4 space-y-4">
                      {renderSectionFields(section.fields)}
                    </div>
                  </div>
                ))
              ) : (
                // Fallback for configs without sections
                <div className="p-4 space-y-4">
                  {(config.fields || []).map(field => (
                    <div key={field.name}>
                      <label htmlFor={field.name} className="label">
                        {field.label}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      {renderField(field)}
                      {errors[field.name] && (
                        <p className="mt-1 text-sm text-red-500">{errors[field.name]}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end space-x-3 p-4 border-t bg-gray-50 rounded-b-lg">
              <button
                type="button"
                onClick={onClose}
                className="btn-outline"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={(e) => handleSubmit(e, true)}
                className="btn-secondary"
                disabled={loading}
              >
                {loading && saveAndNew ? 'Saving...' : 'Save & New'}
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={loading}
              >
                {loading && !saveAndNew ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
