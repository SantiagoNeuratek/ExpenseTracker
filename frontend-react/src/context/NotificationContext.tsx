import { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import { Notification } from '../types';
import { v4 as uuidv4 } from 'uuid';

interface NotificationContextType {
  notifications: Notification[];
  addNotification: (message: string, type: Notification['type'], timeout?: number) => void;
  removeNotification: (id: string) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function useNotification() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
}

interface NotificationProviderProps {
  children: ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Función para agregar una notificación
  const addNotification = useCallback((
    message: string, 
    type: Notification['type'] = 'info', 
    timeout = 5000
  ) => {
    const id = uuidv4();
    const newNotification: Notification = {
      id,
      message,
      type,
      timeout
    };

    setNotifications(prev => [...prev, newNotification]);

    // Eliminar automáticamente después del tiempo especificado
    if (timeout !== 0) {
      setTimeout(() => {
        removeNotification(id);
      }, timeout);
    }
  }, []);

  // Función para eliminar una notificación
  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const value = {
    notifications,
    addNotification,
    removeNotification
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
} 