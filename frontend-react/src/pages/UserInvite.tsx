import { useState, useEffect } from 'react';
import { 
  Container, 
  Card, 
  Form, 
  Button, 
  Alert, 
  Spinner, 
  Row, 
  Col,
  ListGroup,
  InputGroup
} from 'react-bootstrap';
import { Envelope, PlusCircle, PersonBadge } from 'react-bootstrap-icons';
import { useNavigate } from 'react-router-dom';
import { inviteUserToCompany } from '../services/companyService';
import { getCompanyById } from '../services/companyService';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { Company } from '../types';

const UserInvite = () => {
  const { user, currentCompany } = useAuth();
  const { addNotification } = useNotification();
  const navigate = useNavigate();
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [email, setEmail] = useState('');

  // Cargar datos de la empresa
  useEffect(() => {
    const fetchCompany = async () => {
      // Si el usuario tiene currentCompany (admin), usamos esa
      if (currentCompany) {
        setCompany(currentCompany);
        setIsLoading(false);
        return;
      }
      
      // Si no hay currentCompany pero el usuario tiene company_id (usuario normal)
      if (!user?.company_id) {
        setError('No se encontró información de la empresa. Por favor, seleccione una empresa primero.');
        setIsLoading(false);
        return;
      }

      try {
        const companyData = await getCompanyById(user.company_id);
        setCompany(companyData);
      } catch (err: any) {
        console.error('Error al cargar datos de la empresa:', err);
        setError('No se pudo cargar la información de la empresa');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCompany();
  }, [user, currentCompany]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email.trim()) {
      setError('El correo electrónico es requerido');
      return;
    }

    // Validar formato de email básico
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('El formato del correo electrónico no es válido');
      return;
    }

    if (!company) {
      setError('No se encontró una empresa a la cual invitar usuarios');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      await inviteUserToCompany(company.id, email);
      
      addNotification(`Invitación enviada a ${email}`, 'success');
      setEmail(''); // Limpiar campo después de éxito
    } catch (err: any) {
      console.error('Error al enviar invitación:', err);
      setError(err.detail || 'Error al enviar la invitación. Intente nuevamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <Container className="py-4 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Cargando...</span>
        </Spinner>
        <p className="mt-3">Cargando información de la empresa...</p>
      </Container>
    );
  }

  // Si no hay empresa seleccionada o asignada, mostrar un mensaje claro para administradores
  if (!company && user?.is_admin) {
    return (
      <Container className="py-4">
        <h1 className="mb-4">Invitar Usuarios</h1>
        <Alert variant="warning">
          <h4>No hay empresa seleccionada</h4>
          <p>
            Para invitar usuarios, primero debe seleccionar una empresa en el selector del menú lateral.
          </p>
          <Button 
            variant="primary" 
            onClick={() => navigate('/companies')}
          >
            Ir a seleccionar empresa
          </Button>
        </Alert>
      </Container>
    );
  }

  return (
    <Container className="py-4">
      <h1 className="mb-4">Invitar Usuarios</h1>
      
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-4">
          {error}
        </Alert>
      )}
      
      <Row>
        <Col md={7}>
          <Card className="shadow-sm mb-4">
            <Card.Header>
              <h3 className="mb-0">Enviar Invitación</h3>
            </Card.Header>
            <Card.Body>
              <p className="mb-4">
                Invita a usuarios a unirse a tu empresa. Recibirán un correo electrónico con instrucciones para completar su registro.
              </p>
              
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-4" controlId="email">
                  <Form.Label>Correo Electrónico</Form.Label>
                  <InputGroup>
                    <InputGroup.Text>
                      <Envelope />
                    </InputGroup.Text>
                    <Form.Control
                      type="email"
                      placeholder="ejemplo@correo.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                    <Button 
                      type="submit" 
                      variant="primary"
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? (
                        <>
                          <Spinner animation="border" size="sm" className="me-2" />
                          Enviando...
                        </>
                      ) : (
                        <>
                          <PlusCircle className="me-2" />
                          Invitar
                        </>
                      )}
                    </Button>
                  </InputGroup>
                  <Form.Text className="text-muted">
                    El usuario recibirá un correo con un enlace para unirse a {company?.name}.
                  </Form.Text>
                </Form.Group>
              </Form>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={5}>
          <Card className="shadow-sm">
            <Card.Header>
              <h4 className="mb-0">Información</h4>
            </Card.Header>
            <Card.Body>
              <div className="mb-3">
                <h5>Sobre las invitaciones</h5>
                <p className="text-muted">
                  Los usuarios invitados accederán como miembros regulares, 
                  no como administradores. Solo podrán ver y gestionar información
                  relacionada con esta empresa.
                </p>
              </div>
              
              <div>
                <h5>Empresa actual</h5>
                {company && (
                  <ListGroup variant="flush">
                    <ListGroup.Item className="d-flex align-items-center">
                      <PersonBadge className="me-2 text-primary" />
                      <div>
                        <strong>{company.name}</strong>
                        <div className="text-muted small">{company.address}</div>
                      </div>
                    </ListGroup.Item>
                  </ListGroup>
                )}
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default UserInvite; 