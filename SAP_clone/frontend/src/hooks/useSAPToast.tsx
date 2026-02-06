import { useState, useCallback } from 'react';

interface ToastState {
  isOpen: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

export const useSAPToast = () => {
  const [toastState, setToastState] = useState<ToastState>({
    isOpen: false,
    message: '',
    type: 'info'
  });

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    setToastState({
      isOpen: true,
      message,
      type
    });
  }, []);

  const showSuccess = useCallback((message: string) => {
    showToast(message, 'success');
  }, [showToast]);

  const showError = useCallback((message: string) => {
    showToast(message, 'error');
  }, [showToast]);

  const showWarning = useCallback((message: string) => {
    showToast(message, 'warning');
  }, [showToast]);

  const showInfo = useCallback((message: string) => {
    showToast(message, 'info');
  }, [showToast]);

  const handleClose = useCallback(() => {
    setToastState(prev => ({ ...prev, isOpen: false }));
  }, []);

  return {
    toastState,
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    handleClose
  };
};
