import { useEffect } from 'react';
import { Toast, ToastContainer } from 'react-bootstrap';
import { Notification } from '../types';
import { useNotification } from '../context/NotificationContext';
import { XLg, InfoCircle, CheckCircle, ExclamationTriangle, ExclamationCircle } from 'react-bootstrap-icons';

interface ToastProps {
  notification: Notification;
}

export const NotificationToast = ({ notification }: ToastProps) => {
  const { removeNotification } = useNotification();

  // Auto-eliminar después del tiempo especificado
  useEffect(() => {
    if (notification.timeout && notification.timeout > 0) {
      const timer = setTimeout(() => {
        removeNotification(notification.id);
      }, notification.timeout);
      return () => clearTimeout(timer);
    }
  }, [notification, removeNotification]);

  // Determinar el icono y clase según el tipo de notificación
  const getIconAndClass = () => {
    switch (notification.type) {
      case 'info':
        return { icon: <InfoCircle className="me-2" />, bgClass: 'bg-info text-white' };
      case 'success':
        return { icon: <CheckCircle className="me-2" />, bgClass: 'bg-success text-white' };
      case 'warning':
        return { icon: <ExclamationTriangle className="me-2" />, bgClass: 'bg-warning text-dark' };
      case 'error':
        return { icon: <ExclamationCircle className="me-2" />, bgClass: 'bg-danger text-white' };
      default:
        return { icon: <InfoCircle className="me-2" />, bgClass: 'bg-primary text-white' };
    }
  };

  const { icon, bgClass } = getIconAndClass();

  return (
    <Toast 
      className="mb-3 shadow-sm" 
      onClose={() => removeNotification(notification.id)}
      animation={true}
    >
      <Toast.Header className={bgClass}>
        {icon}
        <strong className="me-auto">{notification.type.toUpperCase()}</strong>
        <small>ahora</small>
      </Toast.Header>
      <Toast.Body>{notification.message}</Toast.Body>
    </Toast>
  );
};

// Componente contenedor para todas las notificaciones
export const NotificationContainer = () => {
  const { notifications } = useNotification();

  return (
    <ToastContainer 
      className="p-3" 
      position="top-end" 
      style={{ zIndex: 1060 }}
    >
      {notifications.map((notification) => (
        <NotificationToast key={notification.id} notification={notification} />
      ))}
    </ToastContainer>
  );
}; 