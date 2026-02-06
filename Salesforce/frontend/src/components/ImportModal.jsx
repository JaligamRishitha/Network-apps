import { useState, useRef } from 'react';
import { XMarkIcon, CloudArrowUpIcon, DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function ImportModal({ isOpen, onClose, objectType, api, onSuccess }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState([]);
  const [mapping, setMapping] = useState({});
  const [importing, setImporting] = useState(false);
  const [step, setStep] = useState(1);
  const fileInputRef = useRef(null);

  const fieldOptions = {
    contact: ['first_name', 'last_name', 'email', 'phone', 'title', 'account_name'],
    account: ['name', 'phone', 'website', 'industry'],
    lead: ['first_name', 'last_name', 'email', 'phone', 'company', 'title', 'status'],
    opportunity: ['name', 'amount', 'stage', 'close_date'],
    case: ['subject', 'description', 'status', 'priority'],
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile);
      parseCSV(selectedFile);
    } else {
      toast.error('Please select a CSV file');
    }
  };

  const parseCSV = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const lines = text.split('\n').filter(line => line.trim());
      const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
      const rows = lines.slice(1, 6).map(line => {
        const values = line.split(',').map(v => v.trim().replace(/"/g, ''));
        const row = {};
        headers.forEach((header, index) => {
          row[header] = values[index] || '';
        });
        return row;
      });

      setPreview({ headers, rows, totalRows: lines.length - 1 });

      // Auto-map fields
      const autoMapping = {};
      headers.forEach(header => {
        const lowerHeader = header.toLowerCase().replace(/[_\s]/g, '');
        const match = fieldOptions[objectType]?.find(field => {
          const lowerField = field.toLowerCase().replace(/[_\s]/g, '');
          return lowerField === lowerHeader ||
                 lowerHeader.includes(lowerField) ||
                 lowerField.includes(lowerHeader);
        });
        if (match) {
          autoMapping[header] = match;
        }
      });
      setMapping(autoMapping);
      setStep(2);
    };
    reader.readAsText(file);
  };

  const handleImport = async () => {
    if (!file || Object.keys(mapping).length === 0) {
      toast.error('Please map at least one field');
      return;
    }

    setImporting(true);
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const text = e.target.result;
        const lines = text.split('\n').filter(line => line.trim());
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));

        let successCount = 0;
        let errorCount = 0;

        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
          const record = {};

          headers.forEach((header, index) => {
            const mappedField = mapping[header];
            if (mappedField) {
              record[mappedField] = values[index] || '';
            }
          });

          if (Object.keys(record).length > 0) {
            try {
              await api.create(record);
              successCount++;
            } catch (error) {
              errorCount++;
              console.error('Failed to import record:', error);
            }
          }
        }

        toast.success(`Imported ${successCount} records${errorCount > 0 ? `, ${errorCount} failed` : ''}`);
        onSuccess?.();
        handleClose();
      };
      reader.readAsText(file);
    } catch (error) {
      toast.error('Import failed');
    } finally {
      setImporting(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setPreview([]);
    setMapping({});
    setStep(1);
    onClose();
  };

  const downloadTemplate = () => {
    const fields = fieldOptions[objectType] || [];
    const csv = fields.join(',') + '\n' + fields.map(() => '').join(',');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${objectType}_import_template.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black/50" onClick={handleClose} />

        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">
              Import {objectType.charAt(0).toUpperCase() + objectType.slice(1)}s
            </h2>
            <button type="button" onClick={handleClose} className="p-1 text-gray-400 hover:text-gray-600 rounded">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {step === 1 && (
              <div className="text-center">
                <div
                  className="border-2 border-dashed border-gray-300 rounded-lg p-8 hover:border-sf-blue-500 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <CloudArrowUpIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">
                    Drag and drop a CSV file here, or click to browse
                  </p>
                  <p className="text-sm text-gray-400">
                    Maximum file size: 5MB
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>

                <div className="mt-4">
                  <button
                    type="button"
                    onClick={downloadTemplate}
                    className="inline-flex items-center text-sm text-sf-blue-500 hover:underline"
                  >
                    <DocumentArrowDownIcon className="w-4 h-4 mr-1" />
                    Download CSV Template
                  </button>
                </div>
              </div>
            )}

            {step === 2 && preview.headers && (
              <div>
                <div className="mb-4">
                  <p className="text-sm text-gray-600">
                    Found <strong>{preview.totalRows}</strong> records in your file.
                    Map your CSV columns to {objectType} fields:
                  </p>
                </div>

                <div className="space-y-3 max-h-64 overflow-auto">
                  {preview.headers.map((header) => (
                    <div key={header} className="flex items-center space-x-4">
                      <div className="w-1/3">
                        <span className="text-sm font-medium text-gray-700">{header}</span>
                        {preview.rows[0]?.[header] && (
                          <p className="text-xs text-gray-400 truncate">
                            e.g., {preview.rows[0][header]}
                          </p>
                        )}
                      </div>
                      <span className="text-gray-400">→</span>
                      <div className="w-1/2">
                        <select
                          value={mapping[header] || ''}
                          onChange={(e) => setMapping({ ...mapping, [header]: e.target.value })}
                          className="input-field"
                        >
                          <option value="">-- Do not import --</option>
                          {fieldOptions[objectType]?.map((field) => (
                            <option key={field} value={field}>
                              {field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">
                    Preview of first {Math.min(preview.rows.length, 5)} rows:
                  </p>
                  <div className="mt-2 overflow-x-auto">
                    <table className="text-xs w-full">
                      <thead>
                        <tr>
                          {Object.keys(mapping).filter(k => mapping[k]).map(header => (
                            <th key={header} className="px-2 py-1 text-left text-gray-600">
                              {mapping[header]}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {preview.rows.slice(0, 3).map((row, i) => (
                          <tr key={i}>
                            {Object.keys(mapping).filter(k => mapping[k]).map(header => (
                              <td key={header} className="px-2 py-1 text-gray-500">
                                {row[header]}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-4 border-t bg-gray-50 rounded-b-lg">
            {step === 2 && (
              <button
                type="button"
                onClick={() => { setStep(1); setFile(null); setPreview([]); }}
                className="btn-outline"
              >
                Back
              </button>
            )}
            <div className="flex-1" />
            <div className="flex items-center space-x-3">
              <button type="button" onClick={handleClose} className="btn-outline" disabled={importing}>
                Cancel
              </button>
              {step === 2 && (
                <button
                  type="button"
                  onClick={handleImport}
                  className="btn-primary"
                  disabled={importing || Object.values(mapping).filter(Boolean).length === 0}
                >
                  {importing ? 'Importing...' : `Import ${preview.totalRows} Records`}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
