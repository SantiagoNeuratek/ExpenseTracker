import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Card, 
  Form, 
  Button, 
  Row, 
  Col,
  InputGroup,
  Alert,
  Spinner
} from 'react-bootstrap';
import { Calendar3, CurrencyDollar, Tag, FileText } from 'react-bootstrap-icons';
import { getCategories, createExpense } from '../services/expenseService';
import { Category, ApiError } from '../types';
import { useNotification } from '../context/NotificationContext';

const AddExpense = () => {
  const navigate = useNavigate();
  const { addNotification } = useNotification();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [categories, setCategories] = useState<Category[]>([]);
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    category_id: '',
    notes: ''
  });

  // Cargar categorías al montar el componente
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        setIsLoading(true);
        const data = await getCategories();
        // Filtrar solo categorías activas
        setCategories(data.filter(cat => cat.is_active));
      } catch (error) {
        console.error('Error al cargar categorías:', error);
        setError('No se pudieron cargar las categorías. Por favor, recargue la página.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCategories();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const validateForm = () => {
    if (!formData.description.trim()) return 'La descripción es requerida';
    if (!formData.amount || isNaN(Number(formData.amount)) || Number(formData.amount) <= 0) {
      return 'Ingrese un monto válido';
    }
    if (!formData.date) return 'La fecha es requerida';
    if (!formData.category_id) return 'Seleccione una categoría';
    return '';
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
      setError('');

      // Preparar datos para enviar a la API
      const expenseData = {
        description: formData.description,
        amount: parseFloat(formData.amount),
        date_incurred: formData.date,
        category_id: parseInt(formData.category_id)
      };

      // Enviar datos a la API
      await createExpense(expenseData);
      
      // Mostrar notificación y redireccionar
      addNotification('Gasto registrado con éxito', 'success');
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Error al guardar el gasto:', err);
      
      // Verificar si el error contiene el mensaje específico de exceder el límite
      if (err.detail && err.detail.includes('excede el límite de gastos de la categoría')) {
        setError(err.detail);
      } else {
        setError('Ocurrió un error al guardar el gasto. Intente nuevamente.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container className="py-4">
      <h1 className="mb-4">Registrar Nuevo Gasto</h1>
      
      <Card className="shadow-sm">
        <Card.Body>
          {error && (
            <Alert variant="danger" className="mb-4">
              {error}
            </Alert>
          )}
          
          {isLoading ? (
            <div className="text-center p-5">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Cargando...</span>
              </Spinner>
              <p className="mt-3 text-muted">Cargando categorías...</p>
            </div>
          ) : (
            <Form onSubmit={handleSubmit}>
              <Row className="mb-3">
                <Col md={6}>
                  <Form.Group controlId="description">
                    <Form.Label>Descripción</Form.Label>
                    <InputGroup>
                      <InputGroup.Text>
                        <FileText />
                      </InputGroup.Text>
                      <Form.Control 
                        type="text"
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        placeholder="Descripción del gasto"
                        required
                      />
                    </InputGroup>
                  </Form.Group>
                </Col>
                
                <Col md={6}>
                  <Form.Group controlId="amount">
                    <Form.Label>Monto</Form.Label>
                    <InputGroup>
                      <InputGroup.Text>
                        <CurrencyDollar />
                      </InputGroup.Text>
                      <Form.Control 
                        type="number"
                        name="amount"
                        value={formData.amount}
                        onChange={handleChange}
                        placeholder="0.00"
                        min="0.01"
                        step="0.01"
                        required
                      />
                    </InputGroup>
                  </Form.Group>
                </Col>
              </Row>
              
              <Row className="mb-3">
                <Col md={6}>
                  <Form.Group controlId="date">
                    <Form.Label>Fecha</Form.Label>
                    <InputGroup>
                      <InputGroup.Text>
                        <Calendar3 />
                      </InputGroup.Text>
                      <Form.Control 
                        type="date"
                        name="date"
                        value={formData.date}
                        onChange={handleChange}
                        required
                      />
                    </InputGroup>
                  </Form.Group>
                </Col>
                
                <Col md={6}>
                  <Form.Group controlId="category_id">
                    <Form.Label>Categoría</Form.Label>
                    <InputGroup>
                      <InputGroup.Text>
                        <Tag />
                      </InputGroup.Text>
                      <Form.Select
                        name="category_id"
                        value={formData.category_id}
                        onChange={handleChange}
                        required
                      >
                        <option value="">Seleccione una categoría</option>
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
              
              <Form.Group className="mb-4" controlId="notes">
                <Form.Label>Notas adicionales</Form.Label>
                <Form.Control
                  as="textarea"
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  placeholder="Notas opcionales sobre el gasto"
                  rows={3}
                />
              </Form.Group>
              
              <div className="d-flex justify-content-end gap-2">
                <Button 
                  variant="outline-secondary" 
                  onClick={() => navigate('/dashboard')}
                >
                  Cancelar
                </Button>
                <Button 
                  variant="primary" 
                  type="submit"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Guardando...' : 'Guardar Gasto'}
                </Button>
              </div>
            </Form>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default AddExpense; 