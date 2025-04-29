import { useState, useRef } from 'react';
import { 
  Container, 
  Card, 
  Form, 
  Button, 
  Alert, 
  Spinner, 
  Row, 
  Col,
  InputGroup 
} from 'react-bootstrap';
import { Building, Link45deg, GeoAlt, FileImage } from 'react-bootstrap-icons';
import { createCompany } from '../services/companyService';
import { useNotification } from '../context/NotificationContext';
import { useNavigate } from 'react-router-dom';
import { refreshCompaniesList } from '../components/Sidebar';

const CompanyRegistration = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addNotification } = useNotification();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '',
    address: '',
    website: '',
    logo: null as File | null,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Validar que sea una imagen
      if (!file.type.startsWith('image/')) {
        setError('El archivo debe ser una imagen (PNG, JPG, etc.)');
        return;
      }
      
      // Validar tamaño (máximo 1MB)
      if (file.size > 1024 * 1024) {
        setError('La imagen no debe superar 1MB de tamaño');
        return;
      }

      setFormData({ ...formData, logo: file });
      
      // Mostrar preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setLogoPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
      
      setError(null);
    }
  };

  const validateForm = () => {
    if (!formData.name.trim()) return 'El nombre de la empresa es obligatorio';
    if (!formData.address.trim()) return 'La dirección es obligatoria';
    if (!formData.website.trim()) return 'El sitio web es obligatorio';
    if (!formData.logo) return 'El logo es obligatorio';
    
    // Validar formato URL
    try {
      new URL(formData.website);
    } catch (err) {
      return 'El sitio web debe ser una URL válida (ej. https://ejemplo.com)';
    }
    
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      // Convertir logo a base64
      const base64Logo = await convertFileToBase64(formData.logo as File);
      
      // Enviar datos al backend
      await createCompany({
        name: formData.name,
        address: formData.address,
        website: formData.website,
        logo: base64Logo,
      });
      
      // Actualizar la lista de empresas en el sidebar
      refreshCompaniesList();
      
      addNotification('Empresa registrada con éxito', 'success');
      navigate('/companies');
    } catch (err: any) {
      console.error('Error al registrar empresa:', err);
      setError(err.detail || 'Error al registrar la empresa. Intente nuevamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Función para convertir File a base64
  const convertFileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Eliminar la parte inicial (data:image/jpeg;base64,)
        const base64String = reader.result as string;
        const base64Content = base64String.split(',')[1];
        resolve(base64Content);
      };
      reader.onerror = (error) => reject(error);
    });
  };

  return (
    <Container className="py-4">
      <h1 className="mb-4">Registro de Empresa</h1>
      
      <Card className="shadow-sm">
        <Card.Body>
          {error && (
            <Alert variant="danger" dismissible onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          
          <Form onSubmit={handleSubmit}>
            <Row className="mb-3">
              <Col md={6}>
                <Form.Group controlId="name">
                  <Form.Label>Nombre de la Empresa *</Form.Label>
                  <InputGroup>
                    <InputGroup.Text>
                      <Building />
                    </InputGroup.Text>
                    <Form.Control
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      placeholder="Ingrese el nombre de la empresa"
                      required
                    />
                  </InputGroup>
                </Form.Group>
              </Col>
              
              <Col md={6}>
                <Form.Group controlId="website">
                  <Form.Label>Sitio Web *</Form.Label>
                  <InputGroup>
                    <InputGroup.Text>
                      <Link45deg />
                    </InputGroup.Text>
                    <Form.Control
                      type="url"
                      name="website"
                      value={formData.website}
                      onChange={handleChange}
                      placeholder="https://ejemplo.com"
                      required
                    />
                  </InputGroup>
                </Form.Group>
              </Col>
            </Row>
            
            <Form.Group className="mb-3" controlId="address">
              <Form.Label>Dirección *</Form.Label>
              <InputGroup>
                <InputGroup.Text>
                  <GeoAlt />
                </InputGroup.Text>
                <Form.Control
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  placeholder="Ingrese la dirección de la empresa"
                  required
                />
              </InputGroup>
            </Form.Group>
            
            <Form.Group className="mb-4" controlId="logo">
              <Form.Label>Logo de la Empresa *</Form.Label>
              
              <div className="d-flex mb-3">
                <Button 
                  variant="outline-secondary" 
                  onClick={() => fileInputRef.current?.click()}
                >
                  <FileImage className="me-2" />
                  Seleccionar Logo
                </Button>
                <Form.Control
                  type="file"
                  ref={fileInputRef}
                  accept="image/*"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
                <span className="ms-3 text-muted mt-1">
                  {formData.logo ? formData.logo.name : 'Ningún archivo seleccionado'}
                </span>
              </div>
              
              {logoPreview && (
                <div className="text-center mb-3">
                  <p className="text-muted mb-2">Vista previa:</p>
                  <img 
                    src={logoPreview} 
                    alt="Logo preview" 
                    style={{ maxHeight: '150px', maxWidth: '300px' }}
                    className="border rounded p-2"
                  />
                </div>
              )}
              
              <Form.Text className="text-muted">
                Seleccione un archivo de imagen (PNG, JPG) de máximo 1MB.
              </Form.Text>
            </Form.Group>
            
            <div className="d-flex justify-content-end mt-4">
              <Button 
                variant="primary" 
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Registrando...
                  </>
                ) : (
                  'Registrar Empresa'
                )}
              </Button>
            </div>
          </Form>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default CompanyRegistration; 