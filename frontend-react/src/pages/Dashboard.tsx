import { useState, useEffect } from 'react';
import { 
  Container,
  Row,
  Col,
  Card,
  Table,
  Form,
  Button,
  InputGroup,
  Tab,
  Tabs,
  Spinner,
  Pagination
} from 'react-bootstrap';
import { Search, Download, PlusCircle } from 'react-bootstrap-icons';
import { useNavigate } from 'react-router-dom';
import { getExpenses, getTopCategories, getCategories } from '../services/expenseService';
import { formatCurrency } from '../utils/formatters';
import { Expense, Category } from '../types';
import DateRangePicker from '../components/DateRangePicker';
import PieChart from '../components/charts/PieChart';
import { useAuth } from '../context/AuthContext';

const Dashboard = () => {
  // Obtener la empresa actual del contexto de autenticación
  const { currentCompany } = useAuth();
  
  // Estado para fechas (mes actual por defecto)
  const now = new Date();
  const firstDayOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const lastDayOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  
  const [startDate, setStartDate] = useState(firstDayOfMonth.toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(lastDayOfMonth.toISOString().split('T')[0]);

  // Estado para datos y paginación
  const [isLoading, setIsLoading] = useState(true);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [totalExpenses, setTotalExpenses] = useState<number>(0);
  const [avgExpense, setAvgExpense] = useState<number>(0);
  const [maxExpense, setMaxExpense] = useState<number>(0);
  const [topCategories, setTopCategories] = useState<{id: number, name: string, total_amount: number}[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [totalItems, setTotalItems] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);
  
  const navigate = useNavigate();
  
  // Cargar datos al montar el componente o cuando cambia el rango de fechas o la empresa
  useEffect(() => {
    fetchData();
  }, [startDate, endDate, currentPage, pageSize, currentCompany]);
  
  const fetchData = async () => {
    try {
      setIsLoading(true);
      
      // Cargar categorías para asignar nombres
      const categoriesData = await getCategories();
      setCategories(categoriesData);
      
      // Obtener listado de gastos paginado
      const expensesData = await getExpenses(startDate, endDate, undefined, currentPage, pageSize);
      
      // Actualizar el total de items para la paginación
      setTotalItems(expensesData.total);
      
      // Asignar nombres de categorías a cada gasto
      const expensesWithCategoryNames = expensesData.items.map(expense => {
        // Buscar la categoría correspondiente
        const category = categoriesData.find(cat => cat.id === expense.category_id);
        
        // Devolver el gasto con el nombre de categoría
        return {
          ...expense,
          category_name: category ? category.name : 'Sin categoría'
        };
      });
      
      setExpenses(expensesWithCategoryNames);
      
      // Obtener los datos para calcular métricas (usando el máximo page_size permitido: 100)
      const allExpensesData = await getExpenses(startDate, endDate, undefined, 1, 100);
      const allExpenses = allExpensesData.items;
      
      // Calcular métricas a partir de todos los gastos del período
      // Si hay muchos gastos, esto podría ser una aproximación basada en los primeros 100
      if (allExpenses.length > 0) {
        const total = allExpenses.reduce((sum, expense) => sum + expense.amount, 0);
        
        // Si tenemos menos de 100 gastos, usamos los datos reales
        // Si hay más de 100, estimamos el total basado en el promedio
        if (allExpensesData.total <= 100) {
          setTotalExpenses(total);
          setAvgExpense(total / allExpenses.length);
        } else {
          // Calculamos el promedio de los gastos que tenemos
          const avg = total / allExpenses.length;
          setAvgExpense(avg);
          
          // Estimamos el total multiplicando el promedio por el número total de gastos
          const estimatedTotal = avg * allExpensesData.total;
          setTotalExpenses(estimatedTotal);
        }
        
        // El máximo siempre es el máximo de los gastos que tenemos
        const max = Math.max(...allExpenses.map(expense => expense.amount));
        setMaxExpense(max);
      } else {
        // Si no hay gastos, establecer todo a cero
        setTotalExpenses(0);
        setAvgExpense(0);
        setMaxExpense(0);
      }
      
      // Obtener top categorías para el gráfico
      const topCatsData = await getTopCategories(startDate, endDate);
      setTopCategories(topCatsData);
    } catch (error) {
      console.error('Error al cargar datos del dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Función para manejar cambios en el rango de fechas
  const handleDateChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
    setCurrentPage(1); // Reiniciar a la primera página cuando cambian las fechas
  };
  
  // Función para navegar a la página de agregar gasto
  const handleAddExpense = () => {
    navigate('/expenses/add');
  };

  // Función para obtener el nombre de una categoría por su ID
  const getCategoryName = (categoryId: number): string => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.name : 'Sin categoría';
  };

  // Filtrar los gastos según término de búsqueda
  const filteredExpenses = expenses.filter(expense => {
    const categoryName = getCategoryName(expense.category_id);
    return expense.description.toLowerCase().includes(searchTerm.toLowerCase()) || 
           categoryName.toLowerCase().includes(searchTerm.toLowerCase());
  });
  
  // Formatear fecha para mostrar
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };
  
  // Generar la paginación
  const totalPages = Math.ceil(totalItems / pageSize);
  
  const renderPagination = () => {
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
  
  return (
    <Container fluid>
      <h1 className="mb-4">Dashboard de Gastos</h1>
      
      {currentCompany ? (
        <>
          {/* Selector de fechas */}
          <Card className="shadow-sm mb-4">
            <Card.Body>
              <h5 className="mb-3">Filtrar por período</h5>
              <DateRangePicker 
                startDate={startDate}
                endDate={endDate}
                onDateChange={handleDateChange}
              />
            </Card.Body>
          </Card>
          
          {/* Métricas resumen */}
          <Row className="mb-4">
            <Col md={4}>
              <Card className="h-100 shadow-sm" bg="primary" text="white">
                <Card.Body>
                  <Card.Title>Total de Gastos</Card.Title>
                  <Card.Text className="fs-2 fw-bold">{formatCurrency(totalExpenses)}</Card.Text>
                  <Card.Text className="small text-white-50">Período: {formatDate(startDate)} - {formatDate(endDate)}</Card.Text>
                </Card.Body>
              </Card>
            </Col>
            
            <Col md={4}>
              <Card className="h-100 shadow-sm" bg="success" text="white">
                <Card.Body>
                  <Card.Title>Gasto Promedio</Card.Title>
                  <Card.Text className="fs-2 fw-bold">{formatCurrency(avgExpense)}</Card.Text>
                  <Card.Text className="small text-white-50">Promedio por registro</Card.Text>
                </Card.Body>
              </Card>
            </Col>
            
            <Col md={4}>
              <Card className="h-100 shadow-sm" bg="warning" text="dark">
                <Card.Body>
                  <Card.Title>Gasto Máximo</Card.Title>
                  <Card.Text className="fs-2 fw-bold">{formatCurrency(maxExpense)}</Card.Text>
                  <Card.Text className="small text-black-50">Gasto más alto del período</Card.Text>
                </Card.Body>
              </Card>
            </Col>
          </Row>
          
          {/* Gráfico de distribución de gastos */}
          <Row className="mb-4">
            <Col>
              <PieChart 
                data={topCategories}
                title="Distribución de Gastos por Categoría"
              />
            </Col>
          </Row>
          
          {/* Tabla de gastos */}
          <Card className="shadow-sm">
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h3 className="mb-0">Gastos del Período</h3>
                
                <div className="d-flex gap-2">
                  <InputGroup>
                    <Form.Control 
                      placeholder="Buscar gastos..." 
                      aria-label="Buscar gastos"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <Button variant="outline-secondary">
                      <Search />
                    </Button>
                  </InputGroup>
                  
                  <Button variant="outline-primary">
                    <Download className="me-1" /> Exportar
                  </Button>
                  
                  <Button variant="primary" onClick={handleAddExpense}>
                    <PlusCircle className="me-1" /> Nuevo Gasto
                  </Button>
                </div>
              </div>
              
              {/* Control de pageSize */}
              <div className="d-flex justify-content-end mb-3">
                <Form.Group className="d-flex align-items-center" style={{width: 'auto'}}>
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
                    <option value="5">5</option>
                    <option value="10">10</option>
                    <option value="25">25</option>
                    <option value="50">50</option>
                  </Form.Select>
                  <span className="ms-2">registros</span>
                </Form.Group>
              </div>
              
              {isLoading ? (
                <div className="text-center p-5">
                  <Spinner animation="border" role="status">
                    <span className="visually-hidden">Cargando...</span>
                  </Spinner>
                </div>
              ) : (
                <div className="table-responsive">
                  <Table hover>
                    <thead>
                      <tr>
                        <th>Fecha</th>
                        <th>Categoría</th>
                        <th>Descripción</th>
                        <th className="text-end">Monto</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredExpenses.length > 0 ? (
                        filteredExpenses.map(expense => (
                          <tr key={expense.id}>
                            <td>{formatDate(expense.date_incurred)}</td>
                            <td>{getCategoryName(expense.category_id)}</td>
                            <td>{expense.description}</td>
                            <td className="text-end">{formatCurrency(expense.amount)}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={4} className="text-center py-4">
                            No se encontraron gastos en este período
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </Table>
                  
                  {/* Paginación */}
                  {renderPagination()}
                  
                  {expenses.length > 0 && (
                    <div className="text-end mt-3">
                      <Button 
                        variant="link" 
                        onClick={() => navigate('/expenses')}
                      >
                        Ver todos los gastos
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </Card.Body>
          </Card>
        </>
      ) : (
        <Card className="shadow-sm">
          <Card.Body className="text-center p-5">
            <div className="alert alert-warning mb-4">
              <h4>No hay empresa seleccionada</h4>
              <p>Por favor seleccione una empresa en el menú lateral para ver su dashboard de gastos.</p>
            </div>
            {localStorage.getItem('isAdmin') === 'true' && (
              <Button 
                variant="primary" 
                onClick={() => navigate('/companies')}
              >
                Ir a Gestión de Empresas
              </Button>
            )}
          </Card.Body>
        </Card>
      )}
    </Container>
  );
};

export default Dashboard; 