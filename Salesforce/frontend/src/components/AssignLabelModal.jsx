import { useState } from 'react';
import { XMarkIcon, TagIcon, PlusIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const defaultLabels = [
  { id: 1, name: 'Hot Lead', color: 'bg-red-500' },
  { id: 2, name: 'Warm Lead', color: 'bg-orange-500' },
  { id: 3, name: 'Cold Lead', color: 'bg-blue-500' },
  { id: 4, name: 'VIP', color: 'bg-purple-500' },
  { id: 5, name: 'Follow Up', color: 'bg-yellow-500' },
  { id: 6, name: 'Contacted', color: 'bg-green-500' },
];

export default function AssignLabelModal({ isOpen, onClose, selectedCount = 0, onAssign }) {
  const [labels, setLabels] = useState(defaultLabels);
  const [selectedLabels, setSelectedLabels] = useState([]);
  const [showNewLabel, setShowNewLabel] = useState(false);
  const [newLabelName, setNewLabelName] = useState('');
  const [newLabelColor, setNewLabelColor] = useState('bg-gray-500');

  const colorOptions = [
    'bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500',
    'bg-blue-500', 'bg-indigo-500', 'bg-purple-500', 'bg-pink-500',
  ];

  const toggleLabel = (labelId) => {
    if (selectedLabels.includes(labelId)) {
      setSelectedLabels(selectedLabels.filter(id => id !== labelId));
    } else {
      setSelectedLabels([...selectedLabels, labelId]);
    }
  };

  const handleCreateLabel = () => {
    if (!newLabelName.trim()) {
      toast.error('Please enter a label name');
      return;
    }

    const newLabel = {
      id: Date.now(),
      name: newLabelName,
      color: newLabelColor,
    };

    setLabels([...labels, newLabel]);
    setSelectedLabels([...selectedLabels, newLabel.id]);
    setNewLabelName('');
    setShowNewLabel(false);
    toast.success('Label created');
  };

  const handleAssign = () => {
    const assignedLabels = labels.filter(l => selectedLabels.includes(l.id));
    onAssign?.(assignedLabels);
    toast.success(`${selectedLabels.length} label(s) assigned to ${selectedCount} record(s)`);
    handleClose();
  };

  const handleClose = () => {
    setSelectedLabels([]);
    setShowNewLabel(false);
    setNewLabelName('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black/50" onClick={handleClose} />

        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center space-x-2">
              <TagIcon className="w-5 h-5 text-sf-blue-500" />
              <h2 className="text-lg font-semibold text-gray-900">Assign Labels</h2>
            </div>
            <button type="button" onClick={handleClose} className="p-1 text-gray-400 hover:text-gray-600 rounded">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4">
            <p className="text-sm text-gray-600 mb-4">
              Assign labels to {selectedCount} selected record(s)
            </p>

            {/* Labels list */}
            <div className="space-y-2 max-h-64 overflow-auto">
              {labels.map(label => (
                <button
                  key={label.id}
                  type="button"
                  onClick={() => toggleLabel(label.id)}
                  className={`w-full flex items-center justify-between p-3 rounded-lg border-2 transition-colors ${
                    selectedLabels.includes(label.id)
                      ? 'border-sf-blue-500 bg-sf-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded-full ${label.color}`} />
                    <span className="text-sm font-medium text-gray-700">{label.name}</span>
                  </div>
                  {selectedLabels.includes(label.id) && (
                    <svg className="w-5 h-5 text-sf-blue-500" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              ))}
            </div>

            {/* Create new label */}
            {showNewLabel ? (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <input
                  type="text"
                  value={newLabelName}
                  onChange={(e) => setNewLabelName(e.target.value)}
                  placeholder="Label name..."
                  className="input-field mb-3"
                  autoFocus
                />
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-xs text-gray-500">Color:</span>
                  {colorOptions.map(color => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setNewLabelColor(color)}
                      className={`w-6 h-6 rounded-full ${color} ${
                        newLabelColor === color ? 'ring-2 ring-offset-2 ring-gray-400' : ''
                      }`}
                    />
                  ))}
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => setShowNewLabel(false)}
                    className="btn-outline text-sm py-1.5 flex-1"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleCreateLabel}
                    className="btn-primary text-sm py-1.5 flex-1"
                  >
                    Create
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setShowNewLabel(true)}
                className="mt-4 w-full py-2 text-sm text-sf-blue-500 hover:bg-sf-blue-50 rounded-lg flex items-center justify-center"
              >
                <PlusIcon className="w-4 h-4 mr-1" />
                Create New Label
              </button>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-4 border-t bg-gray-50 rounded-b-lg">
            <button type="button" onClick={handleClose} className="btn-outline">
              Cancel
            </button>
            <button
              type="button"
              onClick={handleAssign}
              className="btn-primary"
              disabled={selectedLabels.length === 0}
            >
              Assign {selectedLabels.length > 0 ? `(${selectedLabels.length})` : ''}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
