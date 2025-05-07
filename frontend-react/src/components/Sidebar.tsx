import { useState, useEffect } from 'react';
import { Nav, Button, Image, Form } from 'react-bootstrap';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  HouseFill, 
  BoxArrowRight, 
  CreditCard, 
  Tag, 
  People, 
  Gear, 
  Key,
  Building,
  EnvelopePlus,
  Activity
} from 'react-bootstrap-icons';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { getCompanies, getCompanyById } from '../services/companyService';
import { Company } from '../types';
import logoImage from '../assets/expensia_logo.svg';

// Variable global para almacenar la función de actualización
let refreshCompaniesCallback: (() => void) | null = null;

// Función para refrescar la lista de empresas desde cualquier componente
export const refreshCompaniesList = () => {
  if (refreshCompaniesCallback) {
    refreshCompaniesCallback();
  }
};

const Sidebar = () => {
  const { user, logout, currentCompany, setCurrentCompany } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { addNotification } = useNotification();
  
  const [companies, setCompanies] = useState<Company[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Función para cargar las empresas desde la API
  const fetchCompanies = async () => {
    if (user?.is_admin) {
      try {
        setIsLoading(true);
        const companiesData = await getCompanies();
        
        // Procesar logos de empresas para asegurar formato correcto
        const processedCompanies = companiesData.map(company => {
          if (company.logo && !company.logo.startsWith('data:')) {
            // Convertir a formato data URL si no lo es ya
            return {
              ...company,
              logo: `data:image/png;base64,${company.logo}`
            };
          }
          return company;
        });
        
        setCompanies(processedCompanies);
      } catch (error) {
        console.error('Error al cargar empresas:', error);
      } finally {
        setIsLoading(false);
      }
    } else if (user?.company_id) {
      // Para usuarios no admin, cargar su empresa asignada
      try {
        setIsLoading(true);
        const companyData = await getCompanyById(user.company_id);
        
        // Procesar logo si existe
        if (companyData.logo && !companyData.logo.startsWith('data:')) {
          companyData.logo = `data:image/png;base64,${companyData.logo}`;
        }
        
        // Actualizar la empresa actual con datos completos, incluso si ya existe
        setCurrentCompany(companyData);
      } catch (error) {
        console.error('Error al cargar empresa:', error);
        // En caso de error, asegurar que al menos el company_id esté en localStorage
        if (!currentCompany && user.company_id) {
          const basicCompanyData = {
            id: user.company_id,
            name: 'Empresa asignada',
            address: '',
            website: '',
            created_at: ''
          };
          setCurrentCompany(basicCompanyData);
        }
      } finally {
        setIsLoading(false);
      }
    }
  };
  
  // Registrar la función de actualización en la variable global
  useEffect(() => {
    refreshCompaniesCallback = fetchCompanies;
    
    // Al desmontar el componente, eliminar la referencia
    return () => {
      refreshCompaniesCallback = null;
    };
  }, [user]);
  
  // Cargar empresas al iniciar o cuando cambia el usuario
  useEffect(() => {
    if (user) {
      fetchCompanies();
    }
  }, [user]);

  // Manejar cambio de empresa seleccionada
  const handleCompanyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const companyId = parseInt(e.target.value);
    if (!companyId) {
      setCurrentCompany(null);
      return;
    }
    
    const company = companies.find(c => c.id === companyId) || null;
    setCurrentCompany(company);
    
    // Redireccionar al dashboard para mostrar datos de la nueva empresa
    navigate('/dashboard');
  };
  
  // Estructura del menú
  const menu = {
    'Principal': [
      { title: 'Dashboard', icon: HouseFill, path: '/dashboard' }
    ],
    'Operaciones': [
      { title: 'Categorías', icon: Tag, path: '/categories' },
      { title: 'Gastos', icon: CreditCard, path: '/expenses' },
      { title: 'API Keys', icon: Key, path: '/apikeys' }
    ],
    'Administración': [
      { title: 'Empresas', icon: Building, path: '/companies' },
      { title: 'Invitar Usuarios', icon: EnvelopePlus, path: '/users/invite' },
      { title: 'Gestión de Usuarios', icon: People, path: '/usermanagement' },
      { title: 'Auditoría', icon: Activity, path: '/audit' },
      { title: 'Panel de Administración', icon: Gear, path: '/adminpanel' }
    ],
    'Cuenta': [
      { title: 'Cerrar Sesión', icon: BoxArrowRight, path: '/logout' }
    ]
  };
  
  // Manejar clic en elemento de menú
  const handleMenuClick = (path: string) => {
    if (path === '/logout') {
      logout();
      addNotification('Has cerrado sesión correctamente', 'success');
      navigate('/login');
    } else {
      navigate(path);
    }
  };
  
  // Verificar si un elemento está activo
  const isActive = (path: string) => location.pathname === path;
  
  // Verificar si se debe mostrar una sección para administradores
  const isAdmin = user?.is_admin || false;
  
  return (
    <div 
      className="sidebar bg-white border-end shadow-sm"
      style={{
        width: '260px',
        height: '100vh',
        position: 'fixed',
        overflowY: 'auto',
        paddingTop: '1.5rem',
        paddingBottom: '1.5rem'
      }}
    >
      {/* Cabecera del sidebar */}
      <div className="mb-4 px-3">
        <div className="text-center">
          <Image src={logoImage} alt="Expensia Logo" style={{ maxWidth: '160px', marginBottom: '1rem' }} />
        </div>
        
        {isAdmin ? (
          <div className="mb-2">
            <Form.Group>
              <Form.Label className="mb-1 small text-muted">Seleccionar Empresa</Form.Label>
              <Form.Select 
                size="sm"
                onChange={handleCompanyChange}
                value={currentCompany?.id || ''}
                disabled={isLoading || companies.length === 0}
              >
                <option value="">Seleccione una empresa</option>
                {companies.map(company => (
                  <option key={company.id} value={company.id}>
                    {company.name}
                  </option>
                ))}
              </Form.Select>
              <div className="d-flex justify-content-between align-items-center mt-2">
                <span className="badge bg-primary">Administrador</span>
                <Button 
                  variant="outline-secondary" 
                  size="sm" 
                  onClick={() => navigate('/companies')}
                  className="py-0 px-2"
                >
                  <Building className="me-1" size={12} />
                  <span className="small">Gestionar</span>
                </Button>
              </div>
            </Form.Group>
          </div>
        ) : (
          <div>
            <h5 className="mb-0 fw-bold">
              {currentCompany?.name || 'Expense Tracker'}
            </h5>
            <p className="text-muted small mt-1 mb-0">
              {user?.email}
            </p>
          </div>
        )}
      </div>
      
      <hr className="my-3" />
      
      {/* Mostrar advertencia si el admin no ha seleccionado empresa */}
      {isAdmin && !currentCompany && (
        <div className="alert alert-warning mx-3 py-2 small">
          <div className="d-flex align-items-center">
            <i className="bi bi-exclamation-triangle-fill me-2"></i>
            <span>Seleccione una empresa para ver sus datos</span>
          </div>
        </div>
      )}
      
      {/* Menú de navegación */}
      <Nav className="flex-column px-3">
        {Object.entries(menu).map(([category, items]) => {
          // Solo mostrar la sección de administración si el usuario es admin
          if (category === 'Administración' && !isAdmin) {
            return null;
          }
          
          // Para operaciones, verificar si hay empresa seleccionada en caso de admin
          if (category === 'Operaciones' && isAdmin && !currentCompany) {
            return (
              <div key={category} className="mb-3">
                <small className="text-uppercase fw-bold text-muted mb-2 d-block" style={{ letterSpacing: '0.5px' }}>
                  {category}
                </small>
                <div className="text-muted small fst-italic px-2">
                  Seleccione una empresa para acceder a las operaciones
                </div>
              </div>
            );
          }
          
          return (
            <div key={category} className="mb-3">
              <small className="text-uppercase fw-bold text-muted mb-2 d-block" style={{ letterSpacing: '0.5px' }}>
                {category}
              </small>
              
              {items.map(item => {
                const IconComponent = item.icon;
                const active = isActive(item.path);
                
                // Deshabilitar operaciones si es admin y no hay empresa seleccionada
                const disabled = isAdmin && !currentCompany && category === 'Operaciones';
                
                return (
                  <Nav.Item key={item.path} className="mb-1">
                    <Button
                      variant={active ? "primary" : "light"}
                      className={`w-100 text-start d-flex align-items-center ${active ? '' : 'text-dark'}`}
                      onClick={() => handleMenuClick(item.path)}
                      disabled={disabled}
                    >
                      <IconComponent className="me-2" />
                      {item.title}
                    </Button>
                  </Nav.Item>
                );
              })}
            </div>
          );
        })}
      </Nav>
    </div>
  );
};

export default Sidebar; 