import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  Squares2X2Icon,
  ListBulletIcon,
  FunnelIcon,
  ArrowsUpDownIcon,
  PencilIcon,
} from '@heroicons/react/24/outline';
import EmptyState from './EmptyState';
import RecordFormModal from './RecordFormModal';
import FilterPanel from './FilterPanel';
import ListSettingsPanel from './ListSettingsPanel';
import toast from 'react-hot-toast';

export default function ObjectListPage({
  objectType,
  objectLabel,
  columns,
  api,
  actions = [],
  icon,
  iconColor = 'bg-purple-500',
  emptyTitle,
  emptyDescription,
  onImport,
  onSendEmail,
  onAssignLabel,
  selectedItems: externalSelectedItems,
  onSelectionChange,
  rowExtraProps,
}) {
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showModal, setShowModal] = useState(false);
  const [selectedItems, setSelectedItems] = useState([]);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'grid'
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [showSortMenu, setShowSortMenu] = useState(false);
  const [filters, setFilters] = useState([]);
  const [visibleColumns, setVisibleColumns] = useState(columns.map(c => c.key));
  const [density, setDensity] = useState('comfortable');
  const [activeSearch, setActiveSearch] = useState('');

  useEffect(() => {
    loadItems();
  }, [page, sortBy, sortOrder, filters, activeSearch]);

  useEffect(() => {
    onSelectionChange?.(selectedItems, items.filter(i => selectedItems.includes(i.id)));
  }, [selectedItems, items]);

  const loadItems = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 25,
        q: activeSearch || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      // Add filter params
      filters.forEach((filter, index) => {
        if (filter.field && filter.value) {
          params[`filter_${index}_field`] = filter.field;
          params[`filter_${index}_op`] = filter.operator;
          params[`filter_${index}_value`] = filter.value;
        }
      });

      const response = await api.list(params);
      // Deduplicate items by ID to prevent duplicate key errors
      const uniqueItems = [];
      const seenIds = new Set();
      for (const item of (response.data.items || [])) {
        if (!seenIds.has(item.id)) {
          seenIds.add(item.id);
          uniqueItems.push(item);
        }
      }
      setItems(uniqueItems);
      setTotalPages(response.data.pages);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Failed to load items:', error);
      toast.error('Failed to load records');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    // Set the active search which triggers the useEffect
    setActiveSearch(searchQuery);
    setPage(1);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setActiveSearch('');
    setPage(1);
  };

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  const handleSaveRecord = async (data) => {
    const response = await api.create(data);
    // Reload the list in case a record was created immediately.
    loadItems();
    return response;
  };

  const handleRowClick = (item) => {
    navigate(`/${objectType}s/${item.id}`);
  };

  const toggleSelectAll = () => {
    if (selectedItems.length === items.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(items.map(i => i.id));
    }
  };

  const toggleSelectItem = (id) => {
    if (selectedItems.includes(id)) {
      setSelectedItems(selectedItems.filter(i => i !== id));
    } else {
      setSelectedItems([...selectedItems, id]);
    }
  };

  const handleApplyFilters = (newFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  const getSelectedRecords = () => {
    return items.filter(item => selectedItems.includes(item.id));
  };

  const densityClasses = {
    compact: 'py-1.5',
    comfortable: 'py-3',
    spacious: 'py-4',
  };

  const displayColumns = columns.filter(c => visibleColumns.includes(c.key));

  const sortOptions = [
    { value: 'created_at', label: 'Date Created' },
    { value: 'updated_at', label: 'Last Modified' },
    ...columns.filter(c => c.sortable !== false).map(c => ({ value: c.key, label: c.label })),
  ];

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">{objectLabel}s</h1>
        <div className="mt-2 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button type="button" className="border-b-2 border-sf-blue-500 py-2 px-1 text-sm font-medium text-sf-blue-500 flex items-center">
              {objectLabel}s
              <ChevronDownIcon className="w-4 h-4 ml-1" />
            </button>
          </nav>
        </div>
      </div>

      {/* List Container */}
      <div className="card">
        {/* List Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-10 h-10 ${iconColor} rounded-md flex items-center justify-center`}>
                {icon}
              </div>
              <div>
                <span className="text-xs text-gray-500">{objectLabel}s</span>
                <div className="flex items-center">
                  <h2 className="text-lg font-semibold text-gray-900">Recently Viewed</h2>
                  <ChevronDownIcon className="w-4 h-4 ml-1 text-gray-500" />
                  <button type="button" className="ml-2 p-1 text-gray-400 hover:text-sf-blue-500">
                    <PencilIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-2">
              {actions.map((action, index) => {
                const isDisabled = action.requiresSelection && selectedItems.length === 0;
                return (
                  <button
                    type="button"
                    key={`${action.label}-${index}`}
                    onClick={() => {
                      if (isDisabled) {
                        toast.error(`Please select at least one ${objectLabel.toLowerCase()} first`);
                        return;
                      }
                      action.onClick(selectedItems, getSelectedRecords());
                    }}
                    className={`btn-secondary ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                    title={isDisabled ? `Select ${objectLabel.toLowerCase()}s first` : action.label}
                  >
                    {action.label}
                  </button>
                );
              })}
              <button
                type="button"
                onClick={() => setShowModal(true)}
                className="btn-secondary"
              >
                New
              </button>
            </div>
          </div>

          {/* Selection info bar */}
          {selectedItems.length > 0 && (
            <div className="mt-3 p-2 bg-sf-blue-50 rounded-lg flex items-center justify-between">
              <span className="text-sm text-sf-blue-700 font-medium">
                {selectedItems.length} item{selectedItems.length > 1 ? 's' : ''} selected
              </span>
              <button
                type="button"
                onClick={() => setSelectedItems([])}
                className="text-sm text-sf-blue-600 hover:underline"
              >
                Clear selection
              </button>
            </div>
          )}

          {/* Item Count and Controls */}
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">
                {total} item{total !== 1 ? 's' : ''} {activeSearch ? `matching "${activeSearch}"` : ''} • Updated a few seconds ago
              </span>
              {activeSearch && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-sf-blue-100 text-sf-blue-800 hover:bg-sf-blue-200"
                >
                  Search: {activeSearch}
                  <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
              {filters.length > 0 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-sf-blue-100 text-sf-blue-800">
                  {filters.length} filter{filters.length > 1 ? 's' : ''} active
                </span>
              )}
            </div>

            <div className="flex items-center space-x-2 relative">
              {/* Search */}
              <form onSubmit={handleSearch} className="relative flex items-center">
                <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search this list..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`pl-9 pr-16 py-1.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-sf-blue-500 w-52 ${
                    activeSearch ? 'border-sf-blue-500 bg-sf-blue-50' : 'border-gray-300'
                  }`}
                />
                {activeSearch && (
                  <button
                    type="button"
                    onClick={handleClearSearch}
                    className="absolute right-8 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
                    title="Clear search"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
                <button
                  type="submit"
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-sf-blue-500"
                  title="Search (Press Enter)"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
              </form>

              {/* Settings */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowSettingsPanel(!showSettingsPanel)}
                  className={`p-1.5 border border-gray-300 rounded transition-colors ${
                    showSettingsPanel ? 'text-sf-blue-500 border-sf-blue-500 bg-sf-blue-50' : 'text-gray-400 hover:text-gray-600'
                  }`}
                  title="Display Settings"
                >
                  <Cog6ToothIcon className="w-4 h-4" />
                </button>
                <ListSettingsPanel
                  isOpen={showSettingsPanel}
                  onClose={() => setShowSettingsPanel(false)}
                  columns={columns}
                  visibleColumns={visibleColumns}
                  onColumnsChange={setVisibleColumns}
                  density={density}
                  onDensityChange={setDensity}
                />
              </div>

              {/* View Toggle */}
              <button
                type="button"
                onClick={() => setViewMode(viewMode === 'table' ? 'grid' : 'table')}
                className={`p-1.5 border border-gray-300 rounded transition-colors ${
                  viewMode === 'grid' ? 'text-sf-blue-500 border-sf-blue-500 bg-sf-blue-50' : 'text-gray-400 hover:text-gray-600'
                }`}
                title={viewMode === 'table' ? 'Switch to Grid View' : 'Switch to Table View'}
              >
                {viewMode === 'table' ? (
                  <Squares2X2Icon className="w-4 h-4" />
                ) : (
                  <ListBulletIcon className="w-4 h-4" />
                )}
              </button>

              {/* Refresh */}
              <button
                type="button"
                onClick={loadItems}
                className="p-1.5 text-gray-400 hover:text-gray-600 border border-gray-300 rounded"
                title="Refresh"
              >
                <ArrowPathIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>

              {/* Sort Menu */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowSortMenu(!showSortMenu)}
                  className={`p-1.5 border border-gray-300 rounded transition-colors ${
                    showSortMenu ? 'text-sf-blue-500 border-sf-blue-500 bg-sf-blue-50' : 'text-gray-400 hover:text-gray-600'
                  }`}
                  title="Sort"
                >
                  <ArrowsUpDownIcon className="w-4 h-4" />
                </button>
                {showSortMenu && (
                  <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-xl border z-50">
                    <div className="p-2">
                      <p className="text-xs font-medium text-gray-500 px-2 mb-1">Sort by</p>
                      {sortOptions.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => {
                            setSortBy(option.value);
                            setShowSortMenu(false);
                          }}
                          className={`w-full text-left px-2 py-1.5 text-sm rounded hover:bg-gray-100 ${
                            sortBy === option.value ? 'text-sf-blue-500 font-medium' : 'text-gray-700'
                          }`}
                        >
                          {option.label}
                          {sortBy === option.value && (
                            <span className="ml-2 text-xs">
                              ({sortOrder === 'asc' ? '↑' : '↓'})
                            </span>
                          )}
                        </button>
                      ))}
                      <div className="border-t mt-1 pt-1">
                        <button
                          type="button"
                          onClick={() => {
                            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                            setShowSortMenu(false);
                          }}
                          className="w-full text-left px-2 py-1.5 text-sm text-gray-700 rounded hover:bg-gray-100"
                        >
                          {sortOrder === 'asc' ? 'Sort Descending' : 'Sort Ascending'}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Edit Columns - placeholder */}
              <button
                type="button"
                onClick={() => setShowSettingsPanel(true)}
                className="p-1.5 text-gray-400 hover:text-gray-600 border border-gray-300 rounded"
                title="Edit Columns"
              >
                <PencilIcon className="w-4 h-4" />
              </button>

              {/* Filter */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowFilterPanel(!showFilterPanel)}
                  className={`p-1.5 border border-gray-300 rounded transition-colors ${
                    showFilterPanel || filters.length > 0
                      ? 'text-sf-blue-500 border-sf-blue-500 bg-sf-blue-50'
                      : 'text-gray-400 hover:text-gray-600'
                  }`}
                  title="Filter"
                >
                  <FunnelIcon className="w-4 h-4" />
                  {filters.length > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-sf-blue-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                      {filters.length}
                    </span>
                  )}
                </button>
                <FilterPanel
                  isOpen={showFilterPanel}
                  onClose={() => setShowFilterPanel(false)}
                  objectType={objectType}
                  filters={filters}
                  onApply={handleApplyFilters}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Table/Grid View */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <ArrowPathIcon className="w-8 h-8 text-gray-400 animate-spin" />
          </div>
        ) : items.length > 0 ? (
          viewMode === 'table' ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b">
                    <th className="w-10 px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selectedItems.length === items.length && items.length > 0}
                        onChange={toggleSelectAll}
                        className="rounded border-gray-300"
                      />
                    </th>
                    {displayColumns.map((column) => (
                      <th
                        key={column.key}
                        className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                        onClick={() => column.sortable !== false && handleSort(column.key)}
                      >
                        <div className="flex items-center">
                          {column.label}
                          {sortBy === column.key && (
                            <ChevronDownIcon
                              className={`w-3 h-3 ml-1 transition-transform ${
                                sortOrder === 'asc' ? 'rotate-180' : ''
                              }`}
                            />
                          )}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {items.map((item) => (
                    <tr
                      key={`list-${objectType}-${item.id}`}
                      className={`hover:bg-gray-50 cursor-pointer ${
                        selectedItems.includes(item.id) ? 'bg-sf-blue-50' : ''
                      }`}
                      onClick={() => handleRowClick(item)}
                    >
                      <td className={`px-3 ${densityClasses[density]}`} onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedItems.includes(item.id)}
                          onChange={() => toggleSelectItem(item.id)}
                          className="rounded border-gray-300"
                        />
                      </td>
                      {displayColumns.map((column) => (
                        <td key={column.key} className={`px-3 ${densityClasses[density]} text-sm`}>
                          {column.render ? (
                            column.render(item, rowExtraProps)
                          ) : column.key === displayColumns[0].key ? (
                            <span className="text-sf-blue-500 hover:underline font-medium">
                              {item[column.key] || '-'}
                            </span>
                          ) : (
                            <span className="text-gray-700">{item[column.key] || '-'}</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            // Grid View
            <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {items.map((item) => (
                <div
                  key={`grid-${objectType}-${item.id}`}
                  className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                    selectedItems.includes(item.id) ? 'border-sf-blue-500 bg-sf-blue-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleRowClick(item)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className={`w-10 h-10 ${iconColor} rounded-full flex items-center justify-center text-white text-sm font-medium`}>
                      {(item[displayColumns[0]?.key] || '?').charAt(0).toUpperCase()}
                    </div>
                    <input
                      type="checkbox"
                      checked={selectedItems.includes(item.id)}
                      onChange={(e) => { e.stopPropagation(); toggleSelectItem(item.id); }}
                      onClick={(e) => e.stopPropagation()}
                      className="rounded border-gray-300"
                    />
                  </div>
                  <h3 className="font-medium text-sf-blue-500 hover:underline truncate">
                    {displayColumns[0]?.render ? displayColumns[0].render(item) : item[displayColumns[0]?.key]}
                  </h3>
                  {displayColumns.slice(1, 4).map((column) => (
                    <p key={column.key} className="text-sm text-gray-500 truncate">
                      {column.render ? column.render(item) : item[column.key] || '-'}
                    </p>
                  ))}
                </div>
              ))}
            </div>
          )
        ) : (
          <EmptyState
            title={emptyTitle || `No ${objectLabel}s yet`}
            description={emptyDescription}
            actionLabel={`Add a ${objectLabel}`}
            onAction={() => setShowModal(true)}
            icon={objectType}
          />
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t flex items-center justify-between">
            <span className="text-sm text-gray-500">
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* New Record Modal */}
      <RecordFormModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        objectType={objectType}
        onSave={handleSaveRecord}
      />
    </div>
  );
}
