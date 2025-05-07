import { useState, useEffect } from 'react';
import { 
  Container, 
  Card, 
  Table, 
  Spinner, 
  Form,
  Row,
  Col,
  Button,
  Badge,
  Pagination,
  Modal,
  Alert
} from 'react-bootstrap';
import { 
  Search, 
  FilterCircle,
  ArrowClockwise,
  Eye,
  Activity
} from 'react-bootstrap-icons';
import { getAuditRecords, getAuditActions, getEntityTypes } from '../services/auditService';
import { AuditRecord } from '../types';
import DateRangePicker from '../components/DateRangePicker';
import { formatDate } from '../utils/formatters';
import ReactJson from 'react-json-view';
import { useAuth } from '../context/AuthContext';

const Audit = () => {
  // Estado para los registros de auditoría
  const [records, setRecords] = useState<AuditRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<AuditRecord | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  
  // Obtener información de la empresa actual
  const { currentCompany } = useAuth();
  
  // Estado para la paginación
  const [totalItems, setTotalItems] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  
  // Estado para filtros
  const [entityTypes, setEntityTypes] = useState<string[]>([]);
  const [actions, setActions] = useState<string[]>([]);
  const [selectedEntityType, setSelectedEntityType] = useState<string>('');
  const [selectedAction, setSelectedAction] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Estado para el rango de fechas
  const now = new Date();
  const firstDayOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const [startDate, setStartDate] = useState(firstDayOfMonth.toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(now.toISOString().split('T')[0]);
  
  // Cargar datos iniciales
  useEffect(() => {
    fetchAuditRecords();
    loadFilters();
  }, []);
  
  // Cargar registros cuando cambian los filtros o la paginación
  useEffect(() => {
    fetchAuditRecords();
  }, [currentPage, pageSize, selectedEntityType, selectedAction, startDate, endDate]);
  
  // Cargar opciones de filtros
  const loadFilters = async () => {
    try {
      // Verificar que exista una empresa seleccionada
      if (!currentCompany?.id) {
        setError('Debe seleccionar una empresa para ver los registros de auditoría.');
        return;
      }
      
      const [actionsData, entityTypesData] = await Promise.all([
        getAuditActions(currentCompany.id),
        getEntityTypes(currentCompany.id)
      ]);
      
      setActions(actionsData);
      setEntityTypes(entityTypesData);
    } catch (error) {
      console.error('Error al cargar filtros:', error);
      setError('No se pudieron cargar las opciones de filtros.');
    }
  };
  
  // Obtener registros de auditoría
  const fetchAuditRecords = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Validar que exista una empresa seleccionada
      if (!currentCompany?.id) {
        setError('Debe seleccionar una empresa para ver los registros de auditoría.');
        setIsLoading(false);
        return;
      }
      
      const data = await getAuditRecords({
        entity_type: selectedEntityType || undefined,
        action: selectedAction || undefined,
        start_date: startDate,
        end_date: endDate,
        search: searchTerm || undefined,
        page: currentPage,
        page_size: pageSize,
        company_id: currentCompany.id
      });
      
      setRecords(data.items);
      setTotalItems(data.total);
    } catch (error) {
      console.error('Error al cargar registros de auditoría:', error);
      setError('No se pudieron cargar los registros de auditoría.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Manejar cambio en el rango de fechas
  const handleDateChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
    setCurrentPage(1); // Reiniciar a la primera página
  };
  
  // Manejar clic en botón de búsqueda
  const handleSearch = () => {
    setCurrentPage(1); // Reiniciar a la primera página
    fetchAuditRecords();
  };
  
  // Limpiar filtros
  const handleClearFilters = () => {
    setSelectedEntityType('');
    setSelectedAction('');
    setSearchTerm('');
    setCurrentPage(1);
    
    // Reestablecer fechas al mes actual
    const now = new Date();
    const firstDayOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    setStartDate(firstDayOfMonth.toISOString().split('T')[0]);
    setEndDate(now.toISOString().split('T')[0]);
  };
  
  // Renderizar paginación
  const renderPagination = () => {
    const totalPages = Math.ceil(totalItems / pageSize);
    
    if (totalPages <= 1) return null;
    
    return (
      <Pagination className="justify-content-center mt-4">
        <Pagination.First 
          onClick={() => setCurrentPage(1)} 
          disabled={currentPage === 1}
        />
        <Pagination.Prev 
          onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))} 
          disabled={currentPage === 1}
        />
        
        {Array.from({ length: Math.min(5, totalPages) }).map((_, idx) => {
          // Mostrar páginas centradas alrededor de la página actual
          let pageNumber = currentPage;
          if (totalPages <= 5) {
            pageNumber = idx + 1;
          } else if (currentPage <= 3) {
            pageNumber = idx + 1;
          } else if (currentPage >= totalPages - 2) {
            pageNumber = totalPages - 4 + idx;
          } else {
            pageNumber = currentPage - 2 + idx;
          }
          
          return (
            <Pagination.Item
              key={idx}
              active={pageNumber === currentPage}
              onClick={() => setCurrentPage(pageNumber)}
            >
              {pageNumber}
            </Pagination.Item>
          );
        })}
        
        <Pagination.Next 
          onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))} 
          disabled={currentPage === totalPages}
        />
        <Pagination.Last 
          onClick={() => setCurrentPage(totalPages)} 
          disabled={currentPage === totalPages}
        />
      </Pagination>
    );
  };
  
  // Obtener variante de badge según la acción
  const getActionBadgeVariant = (action: string) => {
    switch (action) {
      case 'create':
        return 'success';
      case 'update':
        return 'primary';
      case 'delete':
        return 'danger';
      default:
        return 'secondary';
    }
  };
  
  // Obtener texto para mostrar para la acción
  const getActionLabel = (action: string) => {
    switch (action) {
      case 'create':
        return 'Creación';
      case 'update':
        return 'Actualización';
      case 'delete':
        return 'Eliminación';
      default:
        return action;
    }
  };
  
  // Obtener texto para mostrar para el tipo de entidad
  const getEntityTypeLabel = (entityType: string) => {
    switch (entityType) {
      case 'expense':
        return 'Gasto';
      case 'category':
        return 'Categoría';
      default:
        return entityType;
    }
  };
  
  // Ver detalles de un registro
  const handleViewDetails = (record: AuditRecord) => {
    setSelectedRecord(record);
    setShowDetailsModal(true);
  };
  
  // Modal de detalles
  const renderDetailsModal = () => {
    if (!selectedRecord) return null;
    
    return (
      <Modal 
        show={showDetailsModal} 
        onHide={() => setShowDetailsModal(false)}
        size="lg"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>
            Detalles de Auditoría #<span className="text-primary">{selectedRecord.id}</span>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Row className="mb-4">
            <Col md={6}>
              <p><strong>Acción:</strong> <Badge bg={getActionBadgeVariant(selectedRecord.action)}>{getActionLabel(selectedRecord.action)}</Badge></p>
              <p><strong>Tipo de Entidad:</strong> {getEntityTypeLabel(selectedRecord.entity_type)}</p>
              <p><strong>ID de Entidad:</strong> {selectedRecord.entity_id}</p>
              <p><strong>Descripción:</strong> {selectedRecord.entity_description || 'No disponible'}</p>
            </Col>
            <Col md={6}>
              <p><strong>Usuario:</strong> {selectedRecord.user_email || `ID: ${selectedRecord.user_id}`}</p>
              <p><strong>Fecha:</strong> {formatDate(selectedRecord.created_at)}</p>
              <p><strong>Hora:</strong> {new Date(selectedRecord.created_at).toLocaleTimeString()}</p>
            </Col>
          </Row>
          
          {selectedRecord.previous_data && (
            <Card className="mb-3">
              <Card.Header className="bg-light">
                <h6 className="mb-0">Datos Anteriores</h6>
              </Card.Header>
              <Card.Body className="p-0">
                <div className="p-3">
                  <ReactJson 
                    src={selectedRecord.previous_data} 
                    name={null}
                    displayDataTypes={false}
                    collapsed={1}
                    theme="rjv-default"
                  />
                </div>
              </Card.Body>
            </Card>
          )}
          
          {selectedRecord.new_data && (
            <Card>
              <Card.Header className="bg-light">
                <h6 className="mb-0">Datos Nuevos</h6>
              </Card.Header>
              <Card.Body className="p-0">
                <div className="p-3">
                  <ReactJson 
                    src={selectedRecord.new_data}
                    name={null}
                    displayDataTypes={false}
                    collapsed={1}
                    theme="rjv-default"
                  />
                </div>
              </Card.Body>
            </Card>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDetailsModal(false)}>
            Cerrar
          </Button>
        </Modal.Footer>
      </Modal>
    );
  };
  
  return (
    <Container fluid>
      <h1 className="mb-4">
        <Activity className="me-2" />
        Auditoría
      </h1>
      
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {/* Filtros */}
      <Card className="shadow-sm mb-4">
        <Card.Header>
          <h5 className="mb-0">Filtros</h5>
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={3} sm={6} className="mb-3">
              <Form.Group>
                <Form.Label>Tipo de Entidad</Form.Label>
                <Form.Select
                  value={selectedEntityType}
                  onChange={(e) => setSelectedEntityType(e.target.value)}
                >
                  <option value="">Todos</option>
                  {entityTypes.map(type => (
                    <option key={type} value={type}>
                      {getEntityTypeLabel(type)}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>
            
            <Col md={3} sm={6} className="mb-3">
              <Form.Group>
                <Form.Label>Acción</Form.Label>
                <Form.Select
                  value={selectedAction}
                  onChange={(e) => setSelectedAction(e.target.value)}
                >
                  <option value="">Todas</option>
                  {actions.map(action => (
                    <option key={action} value={action}>
                      {getActionLabel(action)}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>
            
            <Col md={6} className="mb-3">
              <Form.Group>
                <Form.Label>Período</Form.Label>
                <DateRangePicker
                  startDate={startDate}
                  endDate={endDate}
                  onDateChange={handleDateChange}
                />
              </Form.Group>
            </Col>
          </Row>
          
          <Row className="align-items-end">
            <Col md={8} className="mb-3">
              <Form.Group>
                <Form.Label>Buscar</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="Buscar en los datos..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
              </Form.Group>
            </Col>
            
            <Col md={4} className="mb-3 d-flex gap-2">
              <Button 
                variant="primary" 
                className="w-100"
                onClick={handleSearch}
              >
                <Search className="me-1" /> Buscar
              </Button>
              <Button 
                variant="outline-secondary" 
                className="w-100"
                onClick={handleClearFilters}
              >
                <FilterCircle className="me-1" /> Limpiar
              </Button>
            </Col>
          </Row>
        </Card.Body>
      </Card>
      
      {/* Tabla de registros */}
      <Card className="shadow-sm">
        <Card.Body>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h3 className="mb-0">Registros de Auditoría</h3>
            
            <div className="d-flex gap-2 align-items-center">
              <Form.Group className="d-flex align-items-center" style={{width: 'auto', marginBottom: 0}}>
                <Form.Label className="me-2 mb-0">Mostrar:</Form.Label>
                <Form.Select 
                  size="sm"
                  style={{width: '80px'}}
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                >
                  <option value="10">10</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                </Form.Select>
              </Form.Group>
              
              <Button 
                variant="outline-secondary" 
                size="sm"
                onClick={fetchAuditRecords}
                title="Actualizar"
              >
                <ArrowClockwise />
              </Button>
            </div>
          </div>
          
          {isLoading ? (
            <div className="text-center p-5">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Cargando...</span>
              </Spinner>
              <p className="mt-3 text-muted">Cargando registros de auditoría...</p>
            </div>
          ) : records.length > 0 ? (
            <>
              <div className="table-responsive">
                <Table hover>
                  <thead>
                    <tr>
                      <th style={{width: '70px'}}>ID</th>
                      <th style={{width: '140px'}}>Fecha</th>
                      <th style={{width: '130px'}}>Acción</th>
                      <th style={{width: '130px'}}>Tipo</th>
                      <th>Descripción</th>
                      <th>Usuario</th>
                      <th style={{width: '80px'}} className="text-end">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map(record => (
                      <tr key={record.id}>
                        <td>{record.id}</td>
                        <td>{formatDate(record.created_at)}</td>
                        <td>
                          <Badge bg={getActionBadgeVariant(record.action)}>
                            {getActionLabel(record.action)}
                          </Badge>
                        </td>
                        <td>{getEntityTypeLabel(record.entity_type)}</td>
                        <td className="text-truncate" style={{maxWidth: '300px'}}>{record.entity_description || `ID: ${record.entity_id}`}</td>
                        <td>{record.user_email}</td>
                        <td className="text-end">
                          <Button 
                            variant="link" 
                            size="sm"
                            onClick={() => handleViewDetails(record)}
                            title="Ver detalles"
                          >
                            <Eye />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
              
              {renderPagination()}
              
              <p className="text-muted text-end mt-2">
                Mostrando {records.length} de {totalItems} registros
              </p>
            </>
          ) : (
            <div className="text-center p-5 bg-light rounded">
              <Activity size={48} className="text-secondary mb-3" />
              <p className="mb-0">No se encontraron registros de auditoría con los filtros seleccionados.</p>
            </div>
          )}
        </Card.Body>
      </Card>
      
      {renderDetailsModal()}
    </Container>
  );
};

export default Audit; 