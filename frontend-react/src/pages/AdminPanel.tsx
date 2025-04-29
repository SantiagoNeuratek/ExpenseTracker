import { useState, useEffect } from 'react';
import {
  Container,
  Card,
  Row,
  Col,
  Table,
  Alert,
  Spinner,
  Badge,
  ProgressBar,
  Tabs,
  Tab,
  Button
} from 'react-bootstrap';
import {
  GearFill,
  Server,
  HddRack,
  Cpu,
  Memory,
  Speedometer,
  Database,
  People,
  CloudArrowUp,
  ClockHistory,
  ExclamationTriangle,
  ArrowClockwise
} from 'react-bootstrap-icons';
import { getSystemHealth, getSystemMetrics, SystemHealth, SystemMetrics, EndpointMetric } from '../services/monitoringService';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import LoadTestPanel from '../components/LoadTestPanel';

const AdminPanel = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [activeTab, setActiveTab] = useState<string>("system");
  const [refreshInterval, setRefreshInterval] = useState<number | null>(null);
  
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // Verificar que el usuario sea administrador
  useEffect(() => {
    if (user && !user.is_admin) {
      navigate('/dashboard');
    }
  }, [user, navigate]);
  
  // Cargar datos iniciales
  useEffect(() => {
    fetchData();
  }, []);
  
  // Configurar intervalo de actualización
  useEffect(() => {
    if (refreshInterval) {
      const intervalId = setInterval(fetchData, refreshInterval * 1000);
      return () => clearInterval(intervalId);
    }
  }, [refreshInterval]);
  
  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Obtener métricas en paralelo
      const [healthData, metricsData] = await Promise.all([
        getSystemHealth(),
        getSystemMetrics()
      ]);
      
      setSystemHealth(healthData);
      setSystemMetrics(metricsData);
    } catch (err) {
      console.error('Error al cargar datos del sistema:', err);
      setError('No se pudieron cargar los datos del sistema. Verifica que tengas permisos de administrador.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Formatear tiempo
  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m ${Math.floor(seconds % 60)}s`;
    }
  };
  
  // Formatear tamaño
  const formatSize = (size: number, unit: string): string => {
    return `${size.toFixed(2)} ${unit}`;
  };
  
  // Obtener color basado en valor
  const getProgressColor = (value: number): string => {
    if (value < 60) return 'success';
    if (value < 80) return 'warning';
    return 'danger';
  };
  
  // Formatear milisegundos
  const formatMs = (seconds: number): string => {
    return `${(seconds * 1000).toFixed(2)} ms`;
  };
  
  // Obtener tiempo relativo
  const getRelativeTime = (timestamp: string): string => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true, locale: es });
    } catch (e) {
      return timestamp;
    }
  };
  
  // Ordenar endpoints por conteo
  const getSortedEndpoints = (): [string, EndpointMetric][] => {
    if (!systemMetrics) return [];
    
    return Object.entries(systemMetrics)
      .filter(([key]) => key !== '_global')
      .filter((entry): entry is [string, EndpointMetric] => {
        // Type guard para asegurar que solo se incluyan EndpointMetric
        const [_, value] = entry;
        return '_global' in value === false;
      })
      .sort((a, b) => b[1].count - a[1].count);
  };
  
  if (isLoading && !systemHealth && !systemMetrics) {
    return (
      <Container fluid className="py-4 text-center">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Cargando métricas del sistema...</p>
      </Container>
    );
  }
  
  return (
    <Container fluid>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Panel de Administración</h1>
        <div>
          <Button 
            variant="outline-secondary" 
            size="sm" 
            onClick={fetchData}
            className="me-2"
          >
            <ArrowClockwise className="me-1" /> Actualizar
          </Button>
          
          <select 
            className="form-select form-select-sm d-inline-block" 
            style={{ width: 'auto' }}
            value={refreshInterval || ''}
            onChange={(e) => setRefreshInterval(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Actualización manual</option>
            <option value="10">Cada 10 segundos</option>
            <option value="30">Cada 30 segundos</option>
            <option value="60">Cada minuto</option>
            <option value="300">Cada 5 minutos</option>
          </select>
        </div>
      </div>
      
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          <Alert.Heading>Error</Alert.Heading>
          <p>{error}</p>
        </Alert>
      )}
      
      <Tabs
        activeKey={activeTab}
        onSelect={(k) => k && setActiveTab(k)}
        className="mb-4"
      >
        <Tab eventKey="system" title={<><HddRack className="me-2" /> Sistema</>}>
          {systemHealth && (
            <Row>
              {/* Sistema */}
              <Col md={6} className="mb-4">
                <Card className="h-100 shadow-sm">
                  <Card.Header className="bg-primary text-white d-flex justify-content-between align-items-center">
                    <h5 className="mb-0"><Server className="me-2" /> Recursos del Sistema</h5>
                    <Badge bg="light" text="dark">Host: {systemHealth?.system?.cpu_count} CPUs</Badge>
                  </Card.Header>
                  <Card.Body>
                    <Row className="mb-3">
                      <Col sm={4}>
                        <div className="text-center mb-3">
                          <Cpu size={24} className="text-primary mb-2" />
                          <h6>CPU</h6>
                          <div className="d-flex justify-content-center">
                            <div style={{ width: '80px', height: '80px' }} className="position-relative">
                              <div className="progress-circle">
                                <ProgressBar 
                                  variant={getProgressColor(systemHealth.process.cpu_percent)}
                                  now={systemHealth.process.cpu_percent} 
                                  label={`${systemHealth.process.cpu_percent}%`}
                                  style={{ height: '8px' }}
                                />
                              </div>
                              <div className="text-center mt-1">
                                <small className="text-muted">Uso</small>
                              </div>
                            </div>
                          </div>
                        </div>
                      </Col>
                      <Col sm={4}>
                        <div className="text-center mb-3">
                          <Memory size={24} className="text-success mb-2" />
                          <h6>Memoria</h6>
                          <div className="d-flex justify-content-center">
                            <div style={{ width: '80px', height: '80px' }} className="position-relative">
                              <div className="progress-circle">
                                <ProgressBar 
                                  variant={getProgressColor(systemHealth.system.memory_percent)}
                                  now={systemHealth.system.memory_percent} 
                                  label={`${systemHealth.system.memory_percent}%`}
                                  style={{ height: '8px' }}
                                />
                              </div>
                              <div className="text-center mt-1">
                                <small className="text-muted">
                                  {formatSize(systemHealth.process.memory_usage_mb, "MB")}
                                </small>
                              </div>
                            </div>
                          </div>
                        </div>
                      </Col>
                      <Col sm={4}>
                        <div className="text-center mb-3">
                          <Database size={24} className="text-warning mb-2" />
                          <h6>Disco</h6>
                          <div className="d-flex justify-content-center">
                            <div style={{ width: '80px', height: '80px' }} className="position-relative">
                              <div className="progress-circle">
                                <ProgressBar 
                                  variant={getProgressColor(systemHealth.system.disk_percent)}
                                  now={systemHealth.system.disk_percent} 
                                  label={`${systemHealth.system.disk_percent}%`}
                                  style={{ height: '8px' }}
                                />
                              </div>
                              <div className="text-center mt-1">
                                <small className="text-muted">
                                  {formatSize(systemHealth.system.disk_used_gb, "GB")}
                                </small>
                              </div>
                            </div>
                          </div>
                        </div>
                      </Col>
                    </Row>
                    
                    <hr />
                    
                    <Row className="mt-3">
                      <Col sm={6}>
                        <div className="mb-3">
                          <div className="small text-muted">Memoria Total</div>
                          <div>{formatSize(systemHealth.system.memory_total_mb, "MB")}</div>
                        </div>
                        <div className="mb-3">
                          <div className="small text-muted">Memoria Disponible</div>
                          <div>{formatSize(systemHealth.system.memory_available_mb, "MB")}</div>
                        </div>
                      </Col>
                      <Col sm={6}>
                        <div className="mb-3">
                          <div className="small text-muted">Disco Total</div>
                          <div>{formatSize(systemHealth.system.disk_total_gb, "GB")}</div>
                        </div>
                        <div className="mb-3">
                          <div className="small text-muted">Uptime</div>
                          <div>{formatUptime(systemHealth.process.uptime_seconds)}</div>
                        </div>
                      </Col>
                    </Row>
                    
                    {systemHealth.system.load_1m !== null && (
                      <div className="mt-3">
                        <div className="small text-muted">Carga del Sistema</div>
                        <div className="d-flex align-items-center">
                          <div className="me-4">
                            <span className="small me-1">1m:</span>
                            <span className={`fw-bold ${getProgressColor(systemHealth.system.load_1m / 4)}`}>
                              {systemHealth.system.load_1m?.toFixed(2) || "N/A"}
                            </span>
                          </div>
                          <div className="me-4">
                            <span className="small me-1">5m:</span>
                            <span className={`fw-bold ${getProgressColor(systemHealth.system.load_5m !== null && systemHealth.system.load_5m !== undefined ? systemHealth.system.load_5m / 4 : 0)}`}>
                              {systemHealth.system.load_5m !== null && systemHealth.system.load_5m !== undefined ? systemHealth.system.load_5m.toFixed(2) : "N/A"}
                            </span>
                          </div>
                          <div>
                            <span className="small me-1">15m:</span>
                            <span className={`fw-bold ${getProgressColor(systemHealth.system.load_15m !== null && systemHealth.system.load_15m !== undefined ? systemHealth.system.load_15m / 4 : 0)}`}>
                              {systemHealth.system.load_15m !== null && systemHealth.system.load_15m !== undefined ? systemHealth.system.load_15m.toFixed(2) : "N/A"}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </Card.Body>
                </Card>
              </Col>
              
              {/* Proceso */}
              <Col md={6} className="mb-4">
                <Card className="h-100 shadow-sm">
                  <Card.Header className="bg-success text-white">
                    <h5 className="mb-0"><CloudArrowUp className="me-2" /> Servidor</h5>
                  </Card.Header>
                  <Card.Body>
                    <Row>
                      <Col sm={6}>
                        <div className="mb-3">
                          <div className="small text-muted">Hilos</div>
                          <div>{systemHealth.process.threads}</div>
                        </div>
                        <div className="mb-3">
                          <div className="small text-muted">Archivos Abiertos</div>
                          <div>{systemHealth.process.open_files}</div>
                        </div>
                        <div className="mb-3">
                          <div className="small text-muted">Conexiones</div>
                          <div>{systemHealth.process.connections}</div>
                        </div>
                      </Col>
                      <Col sm={6}>
                        {systemMetrics && systemMetrics._global && (
                          <>
                            <div className="mb-3">
                              <div className="small text-muted">Solicitudes Totales</div>
                              <div>{systemMetrics._global.total_requests.toLocaleString()}</div>
                            </div>
                            <div className="mb-3">
                              <div className="small text-muted">Errores</div>
                              <div>
                                {systemMetrics._global.total_errors.toLocaleString()} 
                                <small className="text-muted ms-2">
                                  ({systemMetrics._global.error_rate.toFixed(2)}%)
                                </small>
                              </div>
                            </div>
                            <div className="mb-3">
                              <div className="small text-muted">Solicitudes por Minuto</div>
                              <div>{systemMetrics._global.requests_per_minute.toFixed(2)}</div>
                            </div>
                          </>
                        )}
                      </Col>
                    </Row>
                    
                    {systemMetrics && systemMetrics._global && (
                      <div className="mt-3">
                        <hr />
                        <h6>Estadísticas Globales</h6>
                        
                        <div className="mt-3">
                          <div className="small text-muted">Uptime</div>
                          <div>{formatUptime(systemMetrics._global.uptime_seconds)}</div>
                        </div>
                        
                        <div className="mt-3">
                          <div className="small text-muted">Solicitudes Lentas (&gt;500ms)</div>
                          <div className="d-flex align-items-center">
                            <span className="me-2">
                              {systemMetrics._global.slow_requests_count}
                            </span>
                            {systemMetrics._global.slow_requests_count > 10 && (
                              <Badge bg="warning">
                                <ExclamationTriangle className="me-1" /> Alto
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          )}
        </Tab>
        
        <Tab eventKey="requests" title={<><Speedometer className="me-2" /> Rendimiento</>}>
          {systemMetrics && (
            <Card className="shadow-sm">
              <Card.Header>
                <h5 className="mb-0">Métricas por Endpoint</h5>
              </Card.Header>
              <Card.Body>
                <div className="table-responsive">
                  <Table hover className="align-middle">
                    <thead>
                      <tr>
                        <th>Endpoint</th>
                        <th>Solicitudes</th>
                        <th>Tiempo Promedio</th>
                        <th>Tiempo P95</th>
                        <th>Errores</th>
                      </tr>
                    </thead>
                    <tbody>
                      {getSortedEndpoints().map(([endpoint, metrics]) => (
                        <tr key={endpoint}>
                          <td>
                            <code>{endpoint}</code>
                          </td>
                          <td>{metrics.count.toLocaleString()}</td>
                          <td>
                            <Badge 
                              bg={metrics.avg_time > 0.5 ? 'warning' : 'success'}
                            >
                              {formatMs(metrics.avg_time)}
                            </Badge>
                          </td>
                          <td>
                            {metrics.p95_time ? (
                              <Badge 
                                bg={metrics.p95_time > 1 ? 'danger' : 
                                   metrics.p95_time > 0.5 ? 'warning' : 'success'}
                              >
                                {formatMs(metrics.p95_time)}
                              </Badge>
                            ) : (
                              <span className="text-muted">N/A</span>
                            )}
                          </td>
                          <td>
                            {metrics.errors > 0 ? (
                              <Badge bg="danger">
                                {metrics.errors} ({metrics.error_rate.toFixed(1)}%)
                              </Badge>
                            ) : (
                              <Badge bg="success">0</Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>
              </Card.Body>
            </Card>
          )}
        </Tab>
        
        <Tab eventKey="info" title={<><GearFill className="me-2" /> Información</>}>
          <Row>
            <Col md={12}>
              <Card className="shadow-sm mb-4">
                <Card.Header className="bg-info text-white">
                  <h5 className="mb-0"><People className="me-2" /> Información del Sistema</h5>
                </Card.Header>
                <Card.Body>
                  <p>Este panel de administración proporciona métricas y estadísticas sobre el rendimiento del sistema.</p>
                  
                  <h5 className="mt-4">Métricas Principales</h5>
                  <ul>
                    <li><strong>CPU:</strong> Uso de CPU del proceso de la aplicación.</li>
                    <li><strong>Memoria:</strong> Consumo de memoria RAM de la aplicación y del sistema.</li>
                    <li><strong>Disco:</strong> Uso de almacenamiento del servidor.</li>
                    <li><strong>Solicitudes:</strong> Estadísticas de solicitudes HTTP a la API.</li>
                  </ul>
                  
                  <h5 className="mt-4">Métodos de Actualización</h5>
                  <p>
                    Puede actualizar los datos manualmente usando el botón "Actualizar" o configurar
                    una frecuencia de actualización automática mediante el selector en la parte superior.
                  </p>
                  
                  <div className="alert alert-info mt-4">
                    <h6>Nota:</h6>
                    <p className="mb-0">
                      Para acceder a este panel se requieren permisos de administrador. 
                      Las métricas se recopilan en tiempo real y pueden variar según la carga del sistema.
                    </p>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>

        <Tab eventKey="load-tests" title={<><Speedometer className="me-2" /> Pruebas de Carga</>}>
          <LoadTestPanel />
        </Tab>
      </Tabs>
    </Container>
  );
};

export default AdminPanel; 