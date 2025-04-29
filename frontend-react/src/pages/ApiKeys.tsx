import { useState, useEffect } from 'react';
import {
  Container,
  Card,
  Button,
  Table,
  Modal,
  Form,
  Alert,
  Spinner,
  Badge,
  OverlayTrigger,
  Tooltip,
  InputGroup
} from 'react-bootstrap';
import { 
  KeyFill, 
  PlusCircle, 
  Trash, 
  Calendar, 
  InfoCircle,
  ClipboardCheck 
} from 'react-bootstrap-icons';
import { getApiKeys, createApiKey, deleteApiKey } from '../services/apiKeyService';
import { ApiKey, ApiError } from '../types';
import { useNotification } from '../context/NotificationContext';

const ApiKeys = () => {
  const { addNotification } = useNotification();
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyData, setNewKeyData] = useState<{ key: string; name: string } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Cargar lista de API keys
  const fetchApiKeys = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getApiKeys();
      setApiKeys(data);
    } catch (error) {
      console.error('Error al cargar API keys:', error);
      setError('No se pudieron cargar las claves API. Por favor, intente nuevamente.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  // Abrir modal para crear nueva API key
  const handleOpenModal = () => {
    setNewKeyName('');
    setNewKeyData(null);
    setShowModal(true);
  };

  // Cerrar modal
  const handleCloseModal = () => {
    setShowModal(false);
  };

  // Copiar clave al portapapeles
  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key)
      .then(() => {
        addNotification('Clave API copiada al portapapeles', 'success');
      })
      .catch(err => {
        console.error('Error al copiar la clave:', err);
        addNotification('No se pudo copiar la clave', 'error');
      });
  };

  // Crear nueva API key
  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newKeyName.trim()) {
      setError('El nombre de la clave API es requerido.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      const response = await createApiKey({ name: newKeyName });
      
      // Guardar la clave generada para mostrarla una única vez
      setNewKeyData({ 
        key: response.key,
        name: response.name
      });
      
      // Actualizar la lista de claves
      fetchApiKeys();
      
      // Mostrar notificación
      addNotification('API key creada con éxito', 'success');
      
    } catch (err: any) {
      console.error('Error al crear API key:', err);
      const apiError = err as ApiError;
      setError(apiError.detail || 'Ocurrió un error al crear la clave API.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Desactivar API key
  const handleDeleteApiKey = async (id: number, name: string) => {
    if (!window.confirm(`¿Está seguro que desea desactivar la API key "${name}"? Esta acción no se puede deshacer.`)) {
      return;
    }

    try {
      await deleteApiKey(id);
      
      // Actualizar la lista de claves
      fetchApiKeys();
      
      // Mostrar notificación
      addNotification('API key desactivada con éxito', 'success');
    } catch (error) {
      console.error('Error al desactivar API key:', error);
      addNotification('Error al desactivar la clave API', 'error');
    }
  };

  // Formatear fecha
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <Container fluid>
      <h1 className="mb-4">Gestión de API Keys</h1>
      
      {error && !newKeyData && (
        <Alert variant="danger" dismissible onClose={() => setError(null)} className="mb-4">
          {error}
        </Alert>
      )}
      
      <Card className="shadow-sm mb-4">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Claves API</h3>
          <Button variant="primary" onClick={handleOpenModal}>
            <PlusCircle className="me-2" /> Nueva API Key
          </Button>
        </Card.Header>
        
        <Card.Body>
          <div className="alert alert-info mb-4">
            <InfoCircle className="me-2" />
            Las claves API permiten a aplicaciones externas acceder a datos específicos de forma segura.
            Por seguridad, las claves sólo se muestran una vez en el momento de su creación.
            Si pierdes una clave API, deberás crear una nueva y actualizar tus integraciones.
          </div>
          
          {isLoading ? (
            <div className="text-center p-5">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Cargando...</span>
              </Spinner>
              <p className="mt-3 text-muted">Cargando API keys...</p>
            </div>
          ) : apiKeys.length > 0 ? (
            <div className="table-responsive">
              <Table hover>
                <thead>
                  <tr>
                    <th>Nombre</th>
                    <th>Clave API</th>
                    <th>Estado</th>
                    <th>Fecha de creación</th>
                    <th className="text-end">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {apiKeys.map(key => (
                    <tr key={key.id}>
                      <td>{key.name}</td>
                      <td style={{ minWidth: '350px', maxWidth: '450px' }}>
                        <div className="text-monospace">
                          {key.key_preview || '••••••••••••••••'}
                          <small className="text-muted ms-2">(Oculta por seguridad)</small>
                        </div>
                      </td>
                      <td>
                        <Badge bg={key.is_active ? "success" : "danger"}>
                          {key.is_active ? "Activa" : "Inactiva"}
                        </Badge>
                      </td>
                      <td>
                        <Calendar className="me-2" />
                        {formatDate(key.created_at)}
                      </td>
                      <td className="text-end">
                        {key.is_active && (
                          <Button 
                            variant="outline-danger" 
                            size="sm"
                            onClick={() => handleDeleteApiKey(key.id, key.name)}
                          >
                            <Trash className="me-1" /> Desactivar
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          ) : (
            <div className="text-center p-5 bg-light rounded">
              <KeyFill className="mb-3" size={32} />
              <p>No tienes claves API creadas.</p>
              <Button variant="primary" onClick={handleOpenModal}>
                <PlusCircle className="me-2" /> Crear primera API Key
              </Button>
            </div>
          )}
        </Card.Body>
      </Card>
      
      {/* Modal para crear nueva API key */}
      <Modal show={showModal} onHide={handleCloseModal} backdrop="static" centered>
        <Modal.Header closeButton>
          <Modal.Title>{newKeyData ? 'API Key Creada' : 'Crear nueva API Key'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {newKeyData ? (
            <>
              <Alert variant="success" className="mb-4">
                <Alert.Heading>¡API key creada con éxito!</Alert.Heading>
                <p>Guarda esta clave en un lugar seguro. <strong>No se volverá a mostrar.</strong></p>
              </Alert>
              
              <Form.Group className="mb-3">
                <Form.Label>Nombre</Form.Label>
                <Form.Control 
                  type="text" 
                  value={newKeyData.name} 
                  readOnly
                />
              </Form.Group>
              
              <Form.Group className="mb-3">
                <Form.Label>API Key</Form.Label>
                <InputGroup>
                  <Form.Control 
                    as="textarea" 
                    rows={3} 
                    value={newKeyData.key} 
                    readOnly
                    onFocus={(e) => e.target.select()}
                    style={{ fontFamily: 'monospace' }}
                  />
                  <Button 
                    variant="outline-success"
                    onClick={() => handleCopyKey(newKeyData.key)}
                    className="position-absolute end-0 top-0 m-2"
                    style={{ zIndex: 5 }}
                  >
                    <ClipboardCheck />
                  </Button>
                </InputGroup>
                <Form.Text className="text-danger fw-bold">
                  Esta es la única vez que podrás ver la clave completa. Cópiala ahora.
                </Form.Text>
              </Form.Group>
            </>
          ) : (
            <Form onSubmit={handleCreateApiKey}>
              <Form.Group className="mb-3">
                <Form.Label>Nombre de la API Key</Form.Label>
                <Form.Control 
                  type="text" 
                  placeholder="Ej: Integración con sistema contable" 
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  required
                />
                <Form.Text className="text-muted">
                  Use un nombre descriptivo que indique para qué se utilizará esta clave.
                </Form.Text>
              </Form.Group>
              
              {error && (
                <Alert variant="danger" className="mt-3">
                  {error}
                </Alert>
              )}
              
              <div className="d-flex justify-content-end gap-2 mt-4">
                <Button variant="secondary" onClick={handleCloseModal}>
                  Cancelar
                </Button>
                <Button 
                  variant="primary" 
                  type="submit"
                  disabled={isSubmitting || !newKeyName.trim()}
                >
                  {isSubmitting ? 'Generando...' : 'Generar API Key'}
                </Button>
              </div>
            </Form>
          )}
        </Modal.Body>
        {newKeyData && (
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCloseModal}>
              Cerrar
            </Button>
          </Modal.Footer>
        )}
      </Modal>
    </Container>
  );
};

export default ApiKeys; 