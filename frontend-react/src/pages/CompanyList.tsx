import { useState, useEffect } from 'react';
import { 
  Container, 
  Card, 
  Button, 
  Table, 
  Spinner, 
  Alert,
  Badge,
  Image
} from 'react-bootstrap';
import { PlusCircle, Building, GeoAlt, Link45deg, Calendar3 } from 'react-bootstrap-icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { getCompanies } from '../services/companyService';
import { Company } from '../types';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { refreshCompaniesList } from '../components/Sidebar';

const CompanyList = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { setCurrentCompany } = useAuth();
  const { addNotification } = useNotification();

  const fetchCompanies = async () => {
    try {
      setIsLoading(true);
      const data = await getCompanies();
      setCompanies(data);
    } catch (error) {
      console.error('Error al cargar empresas:', error);
      setError('No se pudieron cargar las empresas. Por favor, intente nuevamente.');
    } finally {
      setIsLoading(false);
    }
  };

  // Cargar empresas cuando se monta el componente
  useEffect(() => {
    fetchCompanies();
    // También actualizar la lista en el sidebar, por si se agregó una nueva empresa
    refreshCompaniesList();
  }, [location.pathname]);

  const handleAddCompany = () => {
    navigate('/companies/register');
  };

  const handleViewCompany = (companyId: number) => {
    // Buscar la empresa entre las cargadas
    const selectedCompany = companies.find(company => company.id === companyId);
    
    if (selectedCompany) {
      // Actualizar la empresa seleccionada en el contexto
      setCurrentCompany(selectedCompany);
      
      // Notificar al usuario
      addNotification(`Empresa seleccionada: ${selectedCompany.name}`, 'success');
      
      // Navegar al dashboard en lugar de la vista de detalles específica
      navigate('/dashboard');
    } else {
      console.error(`No se encontró la empresa con ID ${companyId}`);
      addNotification('No se pudo seleccionar la empresa', 'error');
    }
  };

  // Formatear URL para mostrar más amigable
  const formatUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname;
    } catch (e) {
      return url;
    }
  };

  // Formatear fecha
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  return (
    <Container fluid>
      <h1 className="mb-4">Gestión de Empresas</h1>
      
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      <Card className="shadow-sm mb-4">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Empresas</h3>
          <Button variant="primary" onClick={handleAddCompany}>
            <PlusCircle className="me-2" /> Registrar Nueva Empresa
          </Button>
        </Card.Header>
        
        <Card.Body>
          {isLoading ? (
            <div className="text-center p-5">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Cargando...</span>
              </Spinner>
              <p className="mt-3 text-muted">Cargando empresas...</p>
            </div>
          ) : companies.length > 0 ? (
            <div className="table-responsive">
              <Table hover>
                <thead>
                  <tr>
                    <th>Logo</th>
                    <th>Nombre</th>
                    <th>Dirección</th>
                    <th>Sitio Web</th>
                    <th>Fecha de Registro</th>
                    <th className="text-end">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map(company => (
                    <tr key={company.id}>
                      <td style={{ width: '80px' }}>
                        {company.logo ? (
                          <Image 
                            src={`data:image/png;base64,${company.logo}`} 
                            alt={`${company.name} logo`} 
                            width={50} 
                            height={50}
                            className="border rounded"
                          />
                        ) : (
                          <Building size={50} className="text-secondary" />
                        )}
                      </td>
                      <td className="align-middle">
                        <strong>{company.name}</strong>
                      </td>
                      <td className="align-middle">
                        <GeoAlt className="me-1 text-secondary" />
                        {company.address}
                      </td>
                      <td className="align-middle">
                        <Link45deg className="me-1 text-secondary" />
                        <a href={company.website} target="_blank" rel="noopener noreferrer">
                          {formatUrl(company.website)}
                        </a>
                      </td>
                      <td className="align-middle">
                        <Calendar3 className="me-1 text-secondary" />
                        {formatDate(company.created_at)}
                      </td>
                      <td className="text-end align-middle">
                        <Button 
                          variant="outline-primary" 
                          size="sm"
                          onClick={() => handleViewCompany(company.id)}
                        >
                          Seleccionar
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          ) : (
            <div className="text-center p-5 bg-light rounded">
              <Building className="mb-3" size={48} />
              <p className="mb-3">No hay empresas registradas.</p>
              <Button variant="primary" onClick={handleAddCompany}>
                <PlusCircle className="me-2" /> Registrar Primera Empresa
              </Button>
            </div>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default CompanyList; 