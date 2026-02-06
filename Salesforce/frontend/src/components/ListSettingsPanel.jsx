import { useState } from 'react';
import { XMarkIcon, Bars3Icon } from '@heroicons/react/24/outline';

export default function ListSettingsPanel({ isOpen, onClose, columns, visibleColumns, onColumnsChange, density, onDensityChange }) {
  const [localVisible, setLocalVisible] = useState(visibleColumns || columns.map(c => c.key));
  const [localDensity, setLocalDensity] = useState(density || 'comfortable');

  const toggleColumn = (key) => {
    if (localVisible.includes(key)) {
      if (localVisible.length > 1) {
        setLocalVisible(localVisible.filter(k => k !== key));
      }
    } else {
      setLocalVisible([...localVisible, key]);
    }
  };

  const handleApply = () => {
    onColumnsChange?.(localVisible);
    onDensityChange?.(localDensity);
    onClose();
  };

  const handleReset = () => {
    setLocalVisible(columns.map(c => c.key));
    setLocalDensity('comfortable');
  };

  if (!isOpen) return null;

  return (
    <div className="absolute right-0 top-full mt-2 w-72 bg-white rounded-lg shadow-xl border z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b">
        <h3 className="font-medium text-gray-900">Display Settings</h3>
        <button type="button" onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600 rounded">
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Density */}
      <div className="p-3 border-b">
        <label className="text-sm font-medium text-gray-700 mb-2 block">Row Density</label>
        <div className="flex space-x-2">
          {['compact', 'comfortable', 'spacious'].map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setLocalDensity(d)}
              className={`flex-1 py-1.5 px-2 text-xs font-medium rounded border transition-colors ${
                localDensity === d
                  ? 'bg-sf-blue-500 text-white border-sf-blue-500'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-gray-400'
              }`}
            >
              {d.charAt(0).toUpperCase() + d.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Columns */}
      <div className="p-3">
        <label className="text-sm font-medium text-gray-700 mb-2 block">Visible Columns</label>
        <div className="space-y-1 max-h-48 overflow-auto">
          {columns.map((column) => (
            <label
              key={column.key}
              className="flex items-center p-2 hover:bg-gray-50 rounded cursor-pointer"
            >
              <input
                type="checkbox"
                checked={localVisible.includes(column.key)}
                onChange={() => toggleColumn(column.key)}
                className="rounded border-gray-300 text-sf-blue-500 focus:ring-sf-blue-500 mr-3"
              />
              <Bars3Icon className="w-4 h-4 text-gray-400 mr-2 cursor-grab" />
              <span className="text-sm text-gray-700">{column.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-3 border-t bg-gray-50 rounded-b-lg">
        <button type="button" onClick={handleReset} className="text-sm text-gray-600 hover:text-gray-800">
          Reset
        </button>
        <div className="flex items-center space-x-2">
          <button type="button" onClick={onClose} className="btn-outline text-sm py-1.5">
            Cancel
          </button>
          <button type="button" onClick={handleApply} className="btn-primary text-sm py-1.5">
            Apply
          </button>
        </div>
      </div>
    </div>
  );
}
