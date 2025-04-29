import { useState, useEffect } from 'react';
import { Container, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { useParams, useNavigate } from 'react-router-dom';
import { acceptInvitation, verifyInvitation } from '../services/authService';

interface InvitationDetails {
  email: string;
  companyName: string;
  valid: boolean;
}

const InvitationAccept = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [invitation, setInvitation] = useState<InvitationDetails | null>(null);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Verificar token de invitación al cargar
  useEffect(() => {
    const checkInvitation = async () => {
      if (!token) {
        setError('Token de invitación no proporcionado');
        setIsLoading(false);
        return;
      }

      try {
        const response = await verifyInvitation(token);
        setInvitation(response);
      } catch (err: any) {
        console.error('Error al verificar invitación:', err);
        
        // Mostrar mensaje de error más descriptivo
        if (err.status === 400) {
          setError('El token de invitación ha expirado o no es válido');
        } else if (err.status === 404) {
          setError('No se encontró el usuario invitado. La invitación puede haber sido revocada.');
        } else {
          setError(err.detail || 'Error al verificar la invitación. Por favor, solicite una nueva invitación.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    checkInvitation();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validar formulario
    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      // Enviar datos al backend
      await acceptInvitation(token as string, password);
      
      // Mostrar mensaje y redireccionar al login
      navigate('/login', { state: { message: 'Cuenta creada con éxito. Ahora puedes iniciar sesión.' } });
    } catch (err: any) {
      console.error('Error al aceptar invitación:', err);
      setError(err.detail || 'Error al procesar la invitación. Intente nuevamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Renderizar pantalla de carga
  if (isLoading) {
    return (
      <Container className="py-5 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Verificando invitación...</span>
        </Spinner>
        <p className="mt-3">Verificando invitación...</p>
      </Container>
    );
  }

  // Renderizar error si el token es inválido
  if (error && !invitation) {
    return (
      <Container className="py-5">
        <Card className="shadow-sm">
          <Card.Body className="p-4 text-center">
            <Alert variant="danger">
              <Alert.Heading>Error de Invitación</Alert.Heading>
              <p>{error}</p>
            </Alert>
            <Button variant="primary" onClick={() => navigate('/login')}>
              Ir a Iniciar Sesión
            </Button>
          </Card.Body>
        </Card>
      </Container>
    );
  }

  return (
    <Container className="py-5">
      <Card className="shadow-sm mx-auto" style={{ maxWidth: '500px' }}>
        <Card.Body className="p-4">
          <div className="text-center mb-4">
            <h1 className="h3">Bienvenido a ExpenseTracker</h1>
            <p className="text-muted">
              Has sido invitado a unirte a <strong>{invitation?.companyName}</strong>
            </p>
          </div>

          {error && (
            <Alert variant="danger" dismissible onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Correo Electrónico</Form.Label>
              <Form.Control
                type="email"
                value={invitation?.email || ''}
                disabled
              />
              <Form.Text className="text-muted">
                Este es el correo al que se envió la invitación.
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Contraseña</Form.Label>
              <Form.Control
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Ingresa una contraseña segura"
              />
              <Form.Text className="text-muted">
                La contraseña debe tener al menos 8 caracteres.
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-4">
              <Form.Label>Confirmar Contraseña</Form.Label>
              <Form.Control
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="Vuelve a ingresar tu contraseña"
              />
            </Form.Group>

            <div className="d-grid gap-2">
              <Button
                variant="primary"
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Procesando...
                  </>
                ) : (
                  'Completar Registro'
                )}
              </Button>
            </div>
          </Form>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default InvitationAccept; 