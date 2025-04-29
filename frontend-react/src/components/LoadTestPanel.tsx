import { useState, useEffect } from 'react';
import { Card, Row, Col, ProgressBar, Button, Alert, Spinner } from 'react-bootstrap';
import { Speedometer, ArrowClockwise } from 'react-bootstrap-icons';
import PieChart from './charts/PieChart';
import axios from 'axios';

// Datos dummy para mostrar en caso de que no existan resultados reales
const dummyResults = {
  topCategoriesP95: 28,
  categoriesExpensesP95: 29,
  errorRate: 0,
  status: "success",
  conclusion: "El sistema cumple con el RNF 1 de performance. Los endpoints RF8 (28 ms) y RF9 (29 ms) responden muy por debajo del límite de 300ms bajo una carga de 1200 req/min.",
  timestamp: new Date().toISOString()
};

// URL del backend
const API_BASE_URL = 'http://localhost:8000';
const LOAD_TEST_RESULTS_ENDPOINT = `${API_BASE_URL}/api/v1/monitoring/load-test-results`;

const LoadTestPanel = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<typeof dummyResults | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [resultsSource, setResultsSource] = useState<'real' | 'dummy'>('dummy');
  
  // Cargar resultados al montar el componente
  useEffect(() => {
    loadResults();
  }, []);
  
  // Función para cargar resultados desde el backend
  const loadResults = async (showError = false) => {
    try {
      const response = await axios.get(LOAD_TEST_RESULTS_ENDPOINT, {
        // Añadir timestamp para evitar caché
        params: { _t: new Date().getTime() }
      });
      
      if (response.data) {
        console.log('Resultados cargados:', response.data);
        setResults(response.data);
        
        // Determinar si los resultados son reales o dummy
        setResultsSource(response.data.source === 'dummy' ? 'dummy' : 'real');
      }
    } catch (err) {
      console.error('Error al cargar resultados:', err);
      
      if (showError) {
        setError('Error al cargar los resultados de las pruebas de carga.');
      } else {
        // Si no hay resultados, usar datos dummy
        setResults(dummyResults);
        setResultsSource('dummy');
      }
    }
  };
  
  // Simulación del progreso de la prueba de carga
  useEffect(() => {
    let interval: number | null = null;
    
    if (isRunning && progress < 100) {
      interval = window.setInterval(() => {
        setProgress(prevProgress => {
          const newProgress = prevProgress + 5;
          
          // Al llegar al 100%, mostrar los resultados
          if (newProgress >= 100) {
            setIsRunning(false);
            
            // Cargar resultados desde el backend
            loadResults(true);
            
            if (interval) clearInterval(interval);
            return 100;
          }
          
          return newProgress;
        });
      }, 500);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning, progress]);

  const runLoadTestHandler = () => {
    try {
      setIsLoading(true);
      setIsRunning(true);
      setError(null);
      setProgress(0);
      setResults(null);

      console.log("Simulando prueba de carga...");
      
      // La simulación del progreso se maneja en el useEffect
    } catch (err) {
      console.error('Error en simulación de prueba de carga:', err);
      setError('Error al simular la prueba de carga.');
      setIsLoading(false);
      setIsRunning(false);
      setProgress(0);
    }
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2><Speedometer className="me-2" /> Pruebas de Carga</h2>
        <div>
          <Button 
            variant="outline-secondary" 
            className="me-2"
            onClick={() => loadResults(true)}
            disabled={isRunning}
          >
            <ArrowClockwise className="me-2" />
            Actualizar Datos
          </Button>
          <Button 
            variant="primary" 
            onClick={runLoadTestHandler}
            disabled={isRunning}
          >
            {isRunning ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Ejecutando...
              </>
            ) : (
              <>
                <ArrowClockwise className="me-2" />
                Simular Prueba
              </>
            )}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {isRunning && (
        <Card className="mb-4">
          <Card.Body>
            <h5>Progreso de la simulación</h5>
            <ProgressBar 
              now={progress} 
              label={`${Math.round(progress)}%`} 
              animated 
              variant={progress < 50 ? 'info' : progress < 80 ? 'warning' : 'success'}
            />
            <small className="text-muted mt-2 d-block">
              Simulando ejecución de pruebas de carga...
            </small>
          </Card.Body>
        </Card>
      )}

      {results && !isRunning && (
        <Row>
          <Col md={6}>
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">RF8: Top Categories History</h5>
              </Card.Header>
              <Card.Body>
                <div className="text-center">
                  <PieChart
                    data={[
                      { id: 1, name: 'Tiempo de Respuesta', total_amount: results.topCategoriesP95 },
                      { id: 2, name: 'Límite Restante', total_amount: 300 - results.topCategoriesP95 }
                    ]}
                    title={`${results.topCategoriesP95} ms`}
                  />
                </div>
                <div className="mt-3">
                  <div className="d-flex justify-content-between">
                    <span>Tiempo de Respuesta</span>
                    <span className="fw-bold">{results.topCategoriesP95} ms</span>
                  </div>
                  <div className="d-flex justify-content-between">
                    <span>Límite</span>
                    <span className="fw-bold">300 ms</span>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col md={6}>
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">RF9: Expenses by Category</h5>
              </Card.Header>
              <Card.Body>
                <div className="text-center">
                  <PieChart
                    data={[
                      { id: 1, name: 'Tiempo de Respuesta', total_amount: results.categoriesExpensesP95 },
                      { id: 2, name: 'Límite Restante', total_amount: 300 - results.categoriesExpensesP95 }
                    ]}
                    title={`${results.categoriesExpensesP95} ms`}
                  />
                </div>
                <div className="mt-3">
                  <div className="d-flex justify-content-between">
                    <span>Tiempo de Respuesta</span>
                    <span className="fw-bold">{results.categoriesExpensesP95} ms</span>
                  </div>
                  <div className="d-flex justify-content-between">
                    <span>Límite</span>
                    <span className="fw-bold">300 ms</span>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col md={12}>
            <Card>
              <Card.Header>
                <h5 className="mb-0">Resumen de la Prueba</h5>
              </Card.Header>
              <Card.Body>
                <div className={`alert alert-${results.status === 'success' ? 'success' : 'danger'}`}>
                  <h6 className="mb-0">{results.conclusion}</h6>
                </div>
                <div className="mt-3">
                  <div className="d-flex justify-content-between">
                    <span>Tasa de Error</span>
                    <span className="fw-bold">{results.errorRate}%</span>
                  </div>
                  <div className="d-flex justify-content-between">
                    <span>Fecha de la Prueba</span>
                    <span className="fw-bold">{new Date(results.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="mt-3">
                    <Alert variant={resultsSource === 'real' ? 'success' : 'info'}>
                      {resultsSource === 'real' ? (
                        <>
                          <strong>Datos reales:</strong> Mostrando resultados de la última prueba de carga ejecutada.
                        </>
                      ) : (
                        <>
                          <strong>Nota:</strong> No se encontraron resultados de pruebas reales. Para ejecutar pruebas de carga reales, utiliza el script <code>run_load_tests.sh</code> directamente desde la terminal en la carpeta <code>k6/</code>.
                        </>
                      )}
                    </Alert>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default LoadTestPanel; 