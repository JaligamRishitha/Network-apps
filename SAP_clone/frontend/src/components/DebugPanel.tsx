/**
 * Debug Panel Component
 * Shows logs and performance metrics in development mode
 */
import React, { useState, useEffect } from 'react';
import logger from '../utils/logger';
import performanceMonitor from '../utils/performance';

interface DebugPanelProps {
  isVisible: boolean;
  onToggle: () => void;
}

const DebugPanel: React.FC<DebugPanelProps> = ({ isVisible, onToggle }) => {
  const [activeTab, setActiveTab] = useState<'logs' | 'performance' | 'api'>('logs');
  const [logs, setLogs] = useState<any[]>([]);
  const [performanceStats, setPerformanceStats] = useState<any>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (!isVisible || !autoRefresh) return;

    const interval = setInterval(() => {
      setLogs(logger.getLogs());
      setPerformanceStats(performanceMonitor.getStats());
    }, 1000);

    return () => clearInterval(interval);
  }, [isVisible, autoRefresh]);

  useEffect(() => {
    if (isVisible) {
      setLogs(logger.getLogs());
      setPerformanceStats(performanceMonitor.getStats());
    }
  }, [isVisible]);

  if (!isVisible) {
    return (
      <button
        onClick={onToggle}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          backgroundColor: '#1890ff',
          color: 'white',
          border: 'none',
          borderRadius: '50%',
          width: '50px',
          height: '50px',
          cursor: 'pointer',
          fontSize: '20px',
          zIndex: 9999,
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        }}
        title="Open Debug Panel"
      >
        🐛
      </button>
    );
  }

  const clearLogs = () => {
    logger.clearLogs();
    setLogs([]);
  };

  const clearPerformance = () => {
    performanceMonitor.clear();
    setPerformanceStats(performanceMonitor.getStats());
  };

  const exportLogs = () => {
    const data = {
      logs: logger.getLogs(),
      performance: performanceMonitor.export(),
      timestamp: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debug-logs-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getLogsByLevel = (level: string) => {
    return logs.filter(log => log.level === level);
  };

  const getApiLogs = () => {
    return logs.filter(log => log.context === 'API');
  };

  return (
    <div
      style={{
        position: 'fixed',
     