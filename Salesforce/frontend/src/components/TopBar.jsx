import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  QuestionMarkCircleIcon,
  Cog6ToothIcon,
  BellIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../context/AuthContext';
import { dashboardAPI } from '../services/api';
import { loggerService } from '../services/logger';

export default function TopBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const searchRef = useRef(null);
  const userMenuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowSearch(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (query.length >= 2) {
      try {
        loggerService.logSearch(query, 'global');
        const response = await dashboardAPI.search(query);
        setSearchResults(response.data.results);
        setShowSearch(true);
      } catch (error) {
        console.error('Search error:', error);
      }
    } else {
      setSearchResults([]);
      setShowSearch(false);
    }
  };

  const handleResultClick = (result) => {
    setShowSearch(false);
    setSearchQuery('');
    navigate(`/${result.record_type}s/${result.record_id}`);
  };

  const getIconForType = (type) => {
    const icons = {
      contact: 'bg-purple-500',
      account: 'bg-indigo-500',
      lead: 'bg-green-500',
      opportunity: 'bg-yellow-500',
      case: 'bg-pink-500',
    };
    return icons[type] || 'bg-gray-500';
  };

  return (
    <header className="fixed top-0 left-[72px] right-0 h-14 bg-sf-blue-500 flex items-center justify-between px-4 z-40">
      {/* Logo */}
      <div className="flex items-center">
        <img src="/salesforce-2.svg" alt="Salesforce" className="h-12" />
      </div>

      {/* Search */}
      <div className="flex-1 max-w-xl mx-8" ref={searchRef}>
        <div className="relative">
          <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            onFocus={() => searchQuery.length >= 2 && setShowSearch(true)}
            className="w-full pl-10 pr-4 py-2 rounded-md bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-white"
          />

          {/* Search Results Dropdown */}
          {showSearch && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-md shadow-lg max-h-96 overflow-auto">
              {searchResults.map((result, index) => (
                <button
                  key={`${result.record_type}-${result.record_id}`}
                  onClick={() => handleResultClick(result)}
                  className="w-full px-4 py-3 flex items-center hover:bg-gray-50 border-b last:border-b-0"
                >
                  <div className={`w-8 h-8 rounded-full ${getIconForType(result.record_type)} flex items-center justify-center text-white text-xs font-bold mr-3`}>
                    {result.record_type[0].toUpperCase()}
                  </div>
                  <div className="text-left">
                    <div className="text-sm font-medium text-gray-900">{result.name}</div>
                    {result.subtitle && (
                      <div className="text-xs text-gray-500">{result.subtitle}</div>
                    )}
                  </div>
                  <span className="ml-auto text-xs text-gray-400 capitalize">{result.record_type}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center space-x-2">
        {/* Icons */}
        <button className="p-2 text-white hover:bg-sf-blue-600 rounded-md">
          <QuestionMarkCircleIcon className="w-5 h-5" />
        </button>
        <button className="p-2 text-white hover:bg-sf-blue-600 rounded-md">
          <Cog6ToothIcon className="w-5 h-5" />
        </button>
        <button className="p-2 text-white hover:bg-sf-blue-600 rounded-md">
          <BellIcon className="w-5 h-5" />
        </button>

        {/* User Menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center p-1 text-white hover:bg-sf-blue-600 rounded-md"
          >
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-gray-600 font-bold text-sm">
              {user?.alias || user?.username?.substring(0, 2).toUpperCase() || 'U'}
            </div>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-md shadow-lg py-1 z-50">
              <div className="px-4 py-2 border-b">
                <div className="font-medium text-gray-900">
                  {user?.first_name} {user?.last_name}
                </div>
                <div className="text-sm text-gray-500">{user?.email}</div>
              </div>
              <button
                onClick={() => {
                  setShowUserMenu(false);
                  navigate('/account');
                }}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                Settings
              </button>
              <button
                onClick={() => {
                  loggerService.logAction('LOGOUT', `User ${user?.username} logged out`);
                  logout();
                  navigate('/login');
                }}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
