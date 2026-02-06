import { useState } from 'react';
import { XMarkIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

const filterFields = {
  contact: [
    { key: 'first_name', label: 'First Name', type: 'text' },
    { key: 'last_name', label: 'Last Name', type: 'text' },
    { key: 'email', label: 'Email', type: 'text' },
    { key: 'phone', label: 'Phone', type: 'text' },
    { key: 'account_name', label: 'Account', type: 'text' },
    { key: 'created_at', label: 'Created Date', type: 'date' },
  ],
  account: [
    { key: 'name', label: 'Account Name', type: 'text' },
    { key: 'industry', label: 'Industry', type: 'select', options: ['Technology', 'Finance', 'Healthcare', 'Manufacturing', 'Retail', 'Electricity Distribution', 'Energy', 'Utilities', 'Other'] },
    { key: 'phone', label: 'Phone', type: 'text' },
    { key: 'website', label: 'Website', type: 'text' },
    { key: 'created_at', label: 'Created Date', type: 'date' },
  ],
  lead: [
    { key: 'first_name', label: 'First Name', type: 'text' },
    { key: 'last_name', label: 'Last Name', type: 'text' },
    { key: 'company', label: 'Company', type: 'text' },
    { key: 'status', label: 'Status', type: 'select', options: ['New', 'Contacted', 'Qualified', 'Unqualified', 'Converted'] },
    { key: 'email', label: 'Email', type: 'text' },
    { key: 'created_at', label: 'Created Date', type: 'date' },
  ],
  opportunity: [
    { key: 'name', label: 'Opportunity Name', type: 'text' },
    { key: 'stage', label: 'Stage', type: 'select', options: ['Prospecting', 'Qualification', 'Needs Analysis', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'] },
    { key: 'amount_min', label: 'Amount (Min)', type: 'number' },
    { key: 'amount_max', label: 'Amount (Max)', type: 'number' },
    { key: 'close_date', label: 'Close Date', type: 'date' },
  ],
  case: [
    { key: 'subject', label: 'Subject', type: 'text' },
    { key: 'status', label: 'Status', type: 'select', options: ['New', 'Working', 'Escalated', 'Closed'] },
    { key: 'priority', label: 'Priority', type: 'select', options: ['Low', 'Medium', 'High', 'Critical'] },
    { key: 'is_escalated', label: 'Escalated', type: 'boolean' },
    { key: 'created_at', label: 'Created Date', type: 'date' },
  ],
};

const operators = {
  text: [
    { value: 'contains', label: 'contains' },
    { value: 'equals', label: 'equals' },
    { value: 'starts_with', label: 'starts with' },
    { value: 'ends_with', label: 'ends with' },
    { value: 'is_empty', label: 'is empty' },
    { value: 'is_not_empty', label: 'is not empty' },
  ],
  select: [
    { value: 'equals', label: 'equals' },
    { value: 'not_equals', label: 'not equals' },
  ],
  number: [
    { value: 'equals', label: 'equals' },
    { value: 'greater_than', label: 'greater than' },
    { value: 'less_than', label: 'less than' },
    { value: 'between', label: 'between' },
  ],
  date: [
    { value: 'equals', label: 'equals' },
    { value: 'before', label: 'before' },
    { value: 'after', label: 'after' },
    { value: 'last_7_days', label: 'last 7 days' },
    { value: 'last_30_days', label: 'last 30 days' },
    { value: 'this_month', label: 'this month' },
    { value: 'this_year', label: 'this year' },
  ],
  boolean: [
    { value: 'equals', label: 'is' },
  ],
};

export default function FilterPanel({ isOpen, onClose, objectType, filters, onApply }) {
  const [localFilters, setLocalFilters] = useState(filters || []);
  const fields = filterFields[objectType] || [];

  const addFilter = () => {
    setLocalFilters([
      ...localFilters,
      { field: fields[0]?.key || '', operator: 'contains', value: '' },
    ]);
  };

  const updateFilter = (index, updates) => {
    const newFilters = [...localFilters];
    newFilters[index] = { ...newFilters[index], ...updates };
    setLocalFilters(newFilters);
  };

  const removeFilter = (index) => {
    setLocalFilters(localFilters.filter((_, i) => i !== index));
  };

  const handleApply = () => {
    const validFilters = localFilters.filter(f => f.field && f.operator && (f.value || ['is_empty', 'is_not_empty', 'last_7_days', 'last_30_days', 'this_month', 'this_year'].includes(f.operator)));
    onApply(validFilters);
    onClose();
  };

  const handleClear = () => {
    setLocalFilters([]);
    onApply([]);
    onClose();
  };

  const getFieldType = (fieldKey) => {
    const field = fields.find(f => f.key === fieldKey);
    return field?.type || 'text';
  };

  const getFieldOptions = (fieldKey) => {
    const field = fields.find(f => f.key === fieldKey);
    return field?.options || [];
  };

  if (!isOpen) return null;

  return (
    <div className="absolute right-0 top-full mt-2 w-96 bg-white rounded-lg shadow-xl border z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b">
        <h3 className="font-medium text-gray-900">Filter {objectType}s</h3>
        <button type="button" onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600 rounded">
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Filters */}
      <div className="p-3 space-y-3 max-h-80 overflow-auto">
        {localFilters.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">
            No filters applied. Click "Add Filter" to get started.
          </p>
        ) : (
          localFilters.map((filter, index) => {
            const fieldType = getFieldType(filter.field);
            const fieldOperators = operators[fieldType] || operators.text;
            const fieldOptions = getFieldOptions(filter.field);

            return (
              <div key={index} className="flex items-start space-x-2 p-2 bg-gray-50 rounded-lg">
                <div className="flex-1 space-y-2">
                  {/* Field selector */}
                  <select
                    value={filter.field}
                    onChange={(e) => updateFilter(index, { field: e.target.value, value: '' })}
                    className="input-field text-sm"
                  >
                    {fields.map(field => (
                      <option key={field.key} value={field.key}>{field.label}</option>
                    ))}
                  </select>

                  {/* Operator selector */}
                  <select
                    value={filter.operator}
                    onChange={(e) => updateFilter(index, { operator: e.target.value })}
                    className="input-field text-sm"
                  >
                    {fieldOperators.map(op => (
                      <option key={op.value} value={op.value}>{op.label}</option>
                    ))}
                  </select>

                  {/* Value input */}
                  {!['is_empty', 'is_not_empty', 'last_7_days', 'last_30_days', 'this_month', 'this_year'].includes(filter.operator) && (
                    fieldType === 'select' ? (
                      <select
                        value={filter.value}
                        onChange={(e) => updateFilter(index, { value: e.target.value })}
                        className="input-field text-sm"
                      >
                        <option value="">Select...</option>
                        {fieldOptions.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    ) : fieldType === 'boolean' ? (
                      <select
                        value={filter.value}
                        onChange={(e) => updateFilter(index, { value: e.target.value })}
                        className="input-field text-sm"
                      >
                        <option value="true">Yes</option>
                        <option value="false">No</option>
                      </select>
                    ) : fieldType === 'date' ? (
                      <input
                        type="date"
                        value={filter.value}
                        onChange={(e) => updateFilter(index, { value: e.target.value })}
                        className="input-field text-sm"
                      />
                    ) : fieldType === 'number' ? (
                      <input
                        type="number"
                        value={filter.value}
                        onChange={(e) => updateFilter(index, { value: e.target.value })}
                        placeholder="Enter value..."
                        className="input-field text-sm"
                      />
                    ) : (
                      <input
                        type="text"
                        value={filter.value}
                        onChange={(e) => updateFilter(index, { value: e.target.value })}
                        placeholder="Enter value..."
                        className="input-field text-sm"
                      />
                    )
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => removeFilter(index)}
                  className="p-1 text-gray-400 hover:text-red-500"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            );
          })
        )}

        <button
          type="button"
          onClick={addFilter}
          className="w-full py-2 text-sm text-sf-blue-500 hover:bg-sf-blue-50 rounded-lg flex items-center justify-center"
        >
          <PlusIcon className="w-4 h-4 mr-1" />
          Add Filter
        </button>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-3 border-t bg-gray-50 rounded-b-lg">
        <button type="button" onClick={handleClear} className="text-sm text-gray-600 hover:text-gray-800">
          Clear All
        </button>
        <div className="flex items-center space-x-2">
          <button type="button" onClick={onClose} className="btn-outline text-sm py-1.5">
            Cancel
          </button>
          <button type="button" onClick={handleApply} className="btn-primary text-sm py-1.5">
            Apply Filters
          </button>
        </div>
      </div>
    </div>
  );
}
