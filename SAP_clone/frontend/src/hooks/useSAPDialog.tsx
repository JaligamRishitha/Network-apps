import { useState, useCallback } from 'react';

interface DialogState {
  isOpen: boolean;
  title: string;
  message: string;
  type: 'alert' | 'confirm' | 'prompt';
  defaultValue?: string;
  inputLabel?: string;
  onResolve?: (result?: string | boolean) => void;
}

export const useSAPDialog = () => {
  const [dialogState, setDialogState] = useState<DialogState>({
    isOpen: false,
    title: '',
    message: '',
    type: 'alert'
  });

  const showAlert = useCallback((title: string, message: string): Promise<void> => {
    return new Promise((resolve) => {
      setDialogState({
        isOpen: true,
        title,
        message,
        type: 'alert',
        onResolve: () => resolve()
      });
    });
  }, []);

  const showConfirm = useCallback((title: string, message: string): Promise<boolean> => {
    return new Promise((resolve) => {
      setDialogState({
        isOpen: true,
        title,
        message,
        type: 'confirm',
        onResolve: (result) => resolve(result as boolean)
      });
    });
  }, []);

  const showPrompt = useCallback((
    title: string,
    message: string,
    defaultValue = '',
    inputLabel = ''
  ): Promise<string | undefined> => {
    return new Promise((resolve) => {
      setDialogState({
        isOpen: true,
        title,
        message,
        type: 'prompt',
        defaultValue,
        inputLabel,
        onResolve: (result) => resolve(result as string | undefined)
      });
    });
  }, []);

  const handleClose = useCallback((result?: string | boolean) => {
    if (dialogState.onResolve) {
      dialogState.onResolve(result);
    }
    setDialogState(prev => ({ ...prev, isOpen: false }));
  }, [dialogState]);

  return {
    dialogState,
    showAlert,
    showConfirm,
    showPrompt,
    handleClose
  };
};
