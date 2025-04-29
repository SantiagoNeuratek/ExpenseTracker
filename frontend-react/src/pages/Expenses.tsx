import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Card,
  Button,
  Table,
  Spinner,
  Row,
  Col,
  Form,
  InputGroup,
  Pagination,
  Badge,
  Alert
} from 'react-bootstrap';
import { PlusCircle, Search, Funnel, Calendar, Tag } from 'react-bootstrap-icons';
import { getExpenses, getCategories } from '../services/expenseService';
import { formatCurrency } from '../utils/formatters';
import { Expense, Category, ApiError } from '../types';

const Expenses = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [totalExpenses, setTotalExpenses] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const navigate = useNavigate();
  
  // Filtros
  const [search, setSearch] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Cargar categorías solamente una vez
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const categoriesData = await getCategories();
        setCategories(categoriesData);
      } catch (error) {
        console.error('Error al cargar categorías:', error);
      }
    };
    
    fetchCategories();
  }, []);

  // Cargar gastos cuando cambien los filtros o la paginación
  useEffect(() => {
    const fetchExpenses = async () => {
      try {
        setIsLoading(true);
        setErrorMessage(null);
        
        // Cargar gastos
        const params: {
          startDate?: string,
          endDate?: string,
          categoryId?: number
        } = {};
        
        if (startDate) params.startDate = startDate;
        if (endDate) params.endDate = endDate;
        if (selectedCategory) params.categoryId = parseInt(selectedCategory);
        
        const expensesData = await getExpenses(
          params.startDate,
          params.endDate,
          params.categoryId,
          currentPage,
          pageSize
        );
        
        setExpenses(expensesData.items);
        setTotalExpenses(expensesData.total);
        setTotalPages(Math.ceil(expensesData.total / pageSize));
      } catch (error) {
        console.error('Error al cargar gastos:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchExpenses();
  }, [currentPage, pageSize, startDate, endDate, selectedCategory]);

  // Función para obtener el nombre de una categoría por su ID
  const getCategoryName = (categoryId: number): string => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.name : 'Sin categoría';
  };

  // Función para navegar a la página de agregar gasto
  const handleAddExpense = () => {
    navigate('/expenses/add');
  };
  
  // Función para cambiar de página
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };
  
  // Aplicar filtros
  const handleApplyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1); // Resetear a la primera página al filtrar
  };
  
  // Resetear filtros
  const handleResetFilters = () => {
    setStartDate('');
    setEndDate('');
    setSelectedCategory('');
    setSearch('');
    setCurrentPage(1);
  };

  // Limpiar mensaje de error
  const handleDismissError = () => {
    setErrorMessage(null);
  };
  
  // Filtro de búsqueda local (ya que la API no soporta búsqueda por texto)
  const filteredExpenses = search
    ? expenses.filter(expense => {
        const categoryName = getCategoryName(expense.category_id);
        return expense.description.toLowerCase().includes(search.toLowerCase()) ||
               categoryName.toLowerCase().includes(search.toLowerCase());
      })
    : expenses;
  
  // Formatear fecha para mostrar
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };
  
  return (
    <Container fluid>
      <h1 className="mb-4">Gestión de Gastos</h1>
      
      {errorMessage && (
        <Alert 
          variant="danger" 
          dismissible 
          onClose={handleDismissError}
          className="mb-4"
        >
          <Alert.Heading>Error</Alert.Heading>
          <p>{errorMessage}</p>
        </Alert>
      )}
      
      <Card className="shadow-sm mb-4">
        <Card.Header>
          <div className="d-flex justify-content-between align-items-center">
            <div className="d-flex align-items-center">
              <Button
                variant="link"
                className="p-0 me-2 text-muted"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Funnel className="me-2" />
                Filtros
              </Button>
              {(startDate || endDate || selectedCategory) && (
                <Badge bg="info" pill className="me-2">
                  Filtros activos
                </Badge>
              )}
            </div>
            
            <InputGroup style={{ width: '300px' }}>
              <Form.Control
                placeholder="Buscar gastos..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <Button variant="outline-secondary">
                <Search />
              </Button>
            </InputGroup>
          </div>
        </Card.Header>
        
        {showFilters && (
          <Card.Body className="border-bottom">
            <Form onSubmit={handleApplyFilters}>
              <Row>
                <Col md={4}>
                  <Form.Group className="mb-3">
                    <Form.Label>Desde</Form.Label>
                    <InputGroup>
                      <InputGroup.Text>
                        <Calendar />
                      </InputGroup.Text>
                      <Form.Control
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                      />
                    </InputGroup>
                  </Form.Group>
                </Col>
                
                <Col md={4}>
                  <Form.Group className="mb-3">
                    <Form.Label>Hasta</Form.Label>
                    <InputGroup>
                      <InputGroup.Text>
                        <Calendar />
                      </InputGroup.Text>
                      <Form.Control
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                      />
                    </InputGroup>
                  </Form.Group>
                </Col>
                
                <Col md={4}>
                  <Form.Group className="mb-3">
                    <Form.Label>Categoría</Form.Label>
                    <InputGroup>
                      <InputGroup.Text>
                        <Tag />
                      </InputGroup.Text>
                      <Form.Select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                      >
                        <option value="">Todas las categorías</option>
                        {categories.map(cat => (
                          <option key={cat.id} value={cat.id}>
                            {cat.name}
                          </option>
                        ))}
                      </Form.Select>
                    </InputGroup>
                  </Form.Group>
                </Col>
              </Row>
              
              <div className="d-flex justify-content-end">
                <Button
                  variant="outline-secondary"
                  className="me-2"
                  onClick={handleResetFilters}
                >
                  Limpiar
                </Button>
                <Button variant="primary" type="submit">
                  Aplicar filtros
                </Button>
              </div>
            </Form>
          </Card.Body>
        )}
        
        <Card.Body>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h3 className="mb-0">Listado de Gastos</h3>
            
            <Button variant="primary" onClick={handleAddExpense}>
              <PlusCircle className="me-1" /> Nuevo Gasto
            </Button>
          </div>
          
          {isLoading ? (
            <div className="text-center p-5">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Cargando...</span>
              </Spinner>
            </div>
          ) : filteredExpenses.length > 0 ? (
            <>
              <div className="table-responsive">
                <Table hover>
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Categoría</th>
                      <th>Descripción</th>
                      <th className="text-end">Monto</th>
                      <th className="text-center">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredExpenses.map(expense => (
                      <tr key={expense.id}>
                        <td>{formatDate(expense.date_incurred)}</td>
                        <td>{getCategoryName(expense.category_id)}</td>
                        <td>{expense.description}</td>
                        <td className="text-end">{formatCurrency(expense.amount)}</td>
                        <td className="text-center">
                          <Button 
                            variant="outline-primary" 
                            size="sm"
                            onClick={() => navigate(`/expenses/${expense.id}`)}
                          >
                            Ver detalle
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
              
              {/* Paginación */}
              {totalPages > 1 && (
                <div className="d-flex justify-content-between align-items-center mt-3">
                  <div className="text-muted">
                    Mostrando {(currentPage - 1) * pageSize + 1} a {Math.min(currentPage * pageSize, totalExpenses)} de {totalExpenses} gastos
                  </div>
                  
                  <Pagination>
                    <Pagination.First 
                      onClick={() => handlePageChange(1)} 
                      disabled={currentPage === 1}
                    />
                    <Pagination.Prev 
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                    />
                    
                    {[...Array(totalPages)].map((_, index) => (
                      <Pagination.Item
                        key={index + 1}
                        active={index + 1 === currentPage}
                        onClick={() => handlePageChange(index + 1)}
                      >
                        {index + 1}
                      </Pagination.Item>
                    )).slice(
                      Math.max(0, currentPage - 3),
                      Math.min(totalPages, currentPage + 2)
                    )}
                    
                    <Pagination.Next 
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    />
                    <Pagination.Last 
                      onClick={() => handlePageChange(totalPages)}
                      disabled={currentPage === totalPages}
                    />
                  </Pagination>
                </div>
              )}
            </>
          ) : (
            <div className="p-4 text-center bg-light rounded">
              <p className="mb-3">No se encontraron gastos con los filtros seleccionados.</p>
              <Button variant="outline-primary" onClick={handleAddExpense}>
                <PlusCircle className="me-1" /> Agregar un nuevo gasto
              </Button>
            </div>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default Expenses; 