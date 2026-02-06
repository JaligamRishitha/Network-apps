import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ArrowPathIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import EmptyState from './EmptyState';

export default function DashboardCard({
  title,
  icon,
  iconColor = 'bg-sf-blue-500',
  items = [],
  emptyTitle,
  emptyDescription,
  emptyActionLabel,
  onEmptyAction,
  objectType,
  onNewClick,
  showSearch = true,
  loading = false,
}) {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const searchInputRef = useRef(null);

  useEffect(() => {
    if (isSearching && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isSearching]);

  const filteredItems = items.filter(item =>
    item.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getPlural = (type) => {
    if (type === 'opportunity') return 'opportunities';
    return `${type}s`;
  };

  const handleItemClick = (item) => {
    navigate(`/${getPlural(objectType)}/${item.id}`);
  };

  const handleSearchClick = () => {
    setIsSearching(true);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setIsSearching(false);
  };

  const handleSearchBlur = () => {
    if (!searchQuery) {
      setIsSearching(false);
    }
  };

  return (
    <div className="card h-full flex flex-col">
      {/* Header */}
      <div className="p-3 border-b flex items-center justify-between">
        <div className="flex items-center space-x-2 flex-1 min-w-0">
          <div className={`w-8 h-8 ${iconColor} rounded-md flex items-center justify-center flex-shrink-0`}>
            {icon}
          </div>
          <div className="flex items-center flex-1 min-w-0">
            {isSearching ? (
              <div className="flex items-center flex-1 bg-gray-100 rounded-md px-2 py-1">
                <MagnifyingGlassIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onBlur={handleSearchBlur}
                  placeholder={`Search ${title.toLowerCase()}...`}
                  className="flex-1 text-sm bg-transparent border-none focus:outline-none focus:ring-0 ml-2 min-w-0"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={handleClearSearch}
                    className="p-0.5 text-gray-400 hover:text-gray-600 flex-shrink-0"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                )}
              </div>
            ) : (
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-900 truncate">{title}</span>
                {showSearch && (
                  <button
                    type="button"
                    onClick={handleSearchClick}
                    className="ml-2 p-1 text-gray-400 hover:text-sf-blue-500 hover:bg-gray-100 rounded"
                    title={`Search ${title}`}
                  >
                    <MagnifyingGlassIcon className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-1 flex-shrink-0 ml-2">
          <button
            type="button"
            onClick={onNewClick}
            className="px-3 py-1 text-sm font-medium text-sf-blue-500 border border-sf-blue-500 rounded-md hover:bg-sf-blue-50"
          >
            New
          </button>
          <button type="button" className="p-1 text-gray-400 hover:text-gray-600 rounded">
            <ChevronDownIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Search active indicator */}
      {searchQuery && (
        <div className="px-3 py-1.5 bg-sf-blue-50 border-b text-xs text-sf-blue-700 flex items-center justify-between">
          <span>Showing results for "{searchQuery}"</span>
          <button
            type="button"
            onClick={handleClearSearch}
            className="text-sf-blue-600 hover:underline"
          >
            Clear
          </button>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <ArrowPathIcon className="w-6 h-6 text-gray-400 animate-spin" />
          </div>
        ) : filteredItems.length > 0 ? (
          <ul className="divide-y divide-gray-100">
            {filteredItems.slice(0, 5).map((item, index) => (
              <li key={`dash-${title}-${item.id}-${index}`}>
                <button
                  type="button"
                  onClick={() => handleItemClick(item)}
                  className="w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center justify-between"
                >
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-sf-blue-500 hover:underline truncate">
                      {item.name}
                    </div>
                    {item.subtitle && (
                      <div className="text-xs text-gray-500 truncate">{item.subtitle}</div>
                    )}
                  </div>
                  {item.status && (
                    <span className="text-xs text-gray-500 ml-2 flex-shrink-0">{item.status}</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        ) : searchQuery ? (
          <div className="p-4 text-center">
            <p className="text-sm text-gray-500">No {title.toLowerCase()} matching "{searchQuery}"</p>
            <button
              type="button"
              onClick={handleClearSearch}
              className="mt-2 text-sm text-sf-blue-500 hover:underline"
            >
              Clear search
            </button>
          </div>
        ) : (
          <EmptyState
            title={emptyTitle || `No ${title}`}
            description={emptyDescription}
            actionLabel={emptyActionLabel}
            onAction={onEmptyAction || onNewClick}
            icon={objectType}
          />
        )}
      </div>

      {/* Footer */}
      {(filteredItems.length > 0 || items.length > 0) && (
        <div className="p-2 border-t flex items-center justify-between text-xs text-gray-500">
          <button
            type="button"
            onClick={() => navigate(`/${getPlural(objectType)}`)}
            className="text-sf-blue-500 hover:underline"
          >
            View Report
          </button>
          <div className="flex items-center space-x-2">
            <span>As of today</span>
            <button type="button" className="text-gray-400 hover:text-gray-600">
              <ArrowPathIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
