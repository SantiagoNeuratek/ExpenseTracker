import { ReactNode, useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spinner, Container, Alert } from 'react-bootstrap';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  adminOnly?: boolean;
}

const ProtectedRoute = ({ children, adminOnly = false }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading, user, checkAuth } = useAuth();
  const [checking, setChecking] = useState(false);
  const location = useLocation();

  useEffect(() => {
    if (!isAuthenticated || (adminOnly && !user?.is_admin)) {
      setChecking(true);
      const verify = async () => {
        try {
          await checkAuth();
        } finally {
          setChecking(false);
        }
      };
      verify();
    }
  }, [location.pathname]);

  // Mostrar loader mientras verifica autenticación
  if (isLoading || checking) {
    return (
      <Container className="d-flex align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
        <div className="text-center">
          <Spinner animation="border" variant="primary" style={{ width: '3rem', height: '3rem' }} />
          <p className="mt-3 text-secondary">Verificando acceso...</p>
        </div>
      </Container>
    );
  }

  // Verificar si el usuario está autenticado
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Verificar si el usuario tiene permisos de admin para rutas de administrador
  if (adminOnly && !user?.is_admin) {
    return (
      <Container className="py-5 text-center">
        <Alert variant="danger">
          <Alert.Heading>Acceso denegado</Alert.Heading>
          <p>No tienes permiso para acceder a esta sección.</p>
        </Alert>
        <Navigate to="/dashboard" replace />
      </Container>
    );
  }

  // Si está autenticado y tiene los permisos necesarios, renderiza el componente
  return <>{children}</>;
};

export default ProtectedRoute; 