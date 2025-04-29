import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Card,
  Button,
  Spinner,
  Row,
  Col,
  Form,
  Alert,
  Modal
} from 'react-bootstrap';
import { ArrowLeft, Pencil, Trash, Check, X } from 'react-bootstrap-icons';
import { getExpense, getCategories, updateExpense, deleteExpense } from '../services/expenseService';
import { Expense, Category } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';

const ExpenseDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { addNotification } = useNotification();
  const [isLoading, setIsLoading] = useState(true);
  const [expense, setExpense] = useState<Expense | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Estados para edición
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    amount: '',
    description: '',
    date_incurred: '',
    category_id: ''
  });
  
  // Estados para eliminación
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Cargar gasto y categorías
  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;
      
      try {
        setIsLoading(true);
        setErrorMessage(null);
        
        // Cargar en paralelo
        const [expenseData, categoriesData] = await Promise.all([
          getExpense(parseInt(id)),
          getCategories()
        ]);
        
        setExpense(expenseData);
        setCategories(categoriesData);
        
        // Preparar datos para el formulario
        setFormData({
          amount: expenseData.amount.toString(),
          description: expenseData.description,
          date_incurred: expenseData.date_incurred.split('T')[0],
          category_id: expenseData.category_id.toString()
        });
      } catch (error) {
        console.error('Error al cargar datos:', error);
        setErrorMessage('No se pudo cargar el gasto. Verifique que existe y que tiene permisos para verlo.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [id]);
  
  // Función para obtener el nombre de una categoría por su ID
  const getCategoryName = (categoryId: number): string => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.name : 'Sin categoría';
  };
  
  // Manejador para cambios en el formulario
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Manejador para guardar cambios
  const handleSaveChanges = async () => {
    if (!expense || !id) return;
    
    try {
      const updateData = {
        amount: parseFloat(formData.amount),
        description: formData.description,
        date_incurred: formData.date_incurred,
        category_id: parseInt(formData.category_id)
      };
      
      const updatedExpense = await updateExpense(parseInt(id), updateData);
      setExpense(updatedExpense);
      setIsEditing(false);
      addNotification('Gasto actualizado correctamente', 'success');
    } catch (error) {
      console.error('Error al actualizar gasto:', error);
      addNotification('Error al actualizar gasto', 'error');
    }
  };
  
  // Manejador para eliminar gasto
  const handleDelete = async () => {
    if (!expense || !id) return;
    
    try {
      setIsDeleting(true);
      await deleteExpense(parseInt(id));
      setShowDeleteModal(false);
      addNotification('Gasto eliminado correctamente', 'success');
      navigate('/expenses');
    } catch (error) {
      console.error('Error al eliminar gasto:', error);
      addNotification('Error al eliminar gasto', 'error');
      setIsDeleting(false);
    }
  };
  
  // Verificar si el usuario es administrador
  const isAdmin = user?.is_admin === true;
  
  return (
    <Container>
      <div className="mb-4">
        <Button variant="outline-secondary" onClick={() => navigate('/expenses')}>
          <ArrowLeft className="me-2" /> Volver a Gastos
        </Button>
      </div>
      
      {isLoading ? (
        <div className="text-center p-5">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Cargando...</span>
          </Spinner>
        </div>
      ) : errorMessage ? (
        <Alert variant="danger">{errorMessage}</Alert>
      ) : expense ? (
        <Card className="shadow-sm">
          <Card.Header className="d-flex justify-content-between align-items-center">
            <h3 className="mb-0">Detalle del Gasto</h3>
            
            {isAdmin && !isEditing && (
              <div>
                <Button 
                  variant="outline-primary" 
                  className="me-2"
                  onClick={() => setIsEditing(true)}
                >
                  <Pencil className="me-1" /> Editar
                </Button>
                <Button 
                  variant="outline-danger"
                  onClick={() => setShowDeleteModal(true)}
                >
                  <Trash className="me-1" /> Eliminar
                </Button>
              </div>
            )}
            
            {isAdmin && isEditing && (
              <div>
                <Button 
                  variant="outline-success" 
                  className="me-2"
                  onClick={handleSaveChanges}
                >
                  <Check className="me-1" /> Guardar
                </Button>
                <Button 
                  variant="outline-danger"
                  onClick={() => {
                    setIsEditing(false);
                    // Reset form data
                    setFormData({
                      amount: expense.amount.toString(),
                      description: expense.description,
                      date_incurred: expense.date_incurred.split('T')[0],
                      category_id: expense.category_id.toString()
                    });
                  }}
                >
                  <X className="me-1" /> Cancelar
                </Button>
              </div>
            )}
          </Card.Header>
          
          <Card.Body>
            {isEditing ? (
              // Vista de edición (solo para administradores)
              <Form>
                <Row className="mb-3">
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Importe</Form.Label>
                      <Form.Control
                        type="number"
                        step="0.01"
                        name="amount"
                        value={formData.amount}
                        onChange={handleInputChange}
                        required
                      />
                    </Form.Group>
                    
                    <Form.Group className="mb-3">
                      <Form.Label>Fecha</Form.Label>
                      <Form.Control
                        type="date"
                        name="date_incurred"
                        value={formData.date_incurred}
                        onChange={handleInputChange}
                        required
                      />
                    </Form.Group>
                  </Col>
                  
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Categoría</Form.Label>
                      <Form.Select
                        name="category_id"
                        value={formData.category_id}
                        onChange={handleInputChange}
                        required
                      >
                        <option value="">Seleccionar categoría</option>
                        {categories.map(category => (
                          <option key={category.id} value={category.id}>
                            {category.name}
                          </option>
                        ))}
                      </Form.Select>
                    </Form.Group>
                    
                    <Form.Group className="mb-3">
                      <Form.Label>Descripción</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={3}
                        name="description"
                        value={formData.description}
                        onChange={handleInputChange}
                      />
                    </Form.Group>
                  </Col>
                </Row>
              </Form>
            ) : (
              // Vista de detalles (para todos los usuarios)
              <Row>
                <Col md={6}>
                  <dl>
                    <dt>Importe</dt>
                    <dd className="text-primary fs-4">{formatCurrency(expense.amount)}</dd>
                    
                    <dt>Fecha</dt>
                    <dd>{formatDate(expense.date_incurred)}</dd>
                    
                    <dt>Categoría</dt>
                    <dd>{getCategoryName(expense.category_id)}</dd>
                  </dl>
                </Col>
                
                <Col md={6}>
                  <dl>
                    <dt>Descripción</dt>
                    <dd>{expense.description || 'Sin descripción'}</dd>
                    
                    <dt>Fecha de Creación</dt>
                    <dd>{formatDate(expense.created_at)}</dd>
                  </dl>
                </Col>
              </Row>
            )}
          </Card.Body>
        </Card>
      ) : (
        <Alert variant="warning">No se encontró el gasto solicitado.</Alert>
      )}
      
      {/* Modal de confirmación para eliminar */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirmar eliminación</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p className="mb-0">
            ¿Está seguro que desea eliminar este gasto? Esta acción no se puede deshacer.
          </p>
          <p className="mt-3 mb-0"><strong>Importe:</strong> {expense ? formatCurrency(expense.amount) : ''}</p>
          <p className="mb-0"><strong>Descripción:</strong> {expense?.description || 'Sin descripción'}</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancelar
          </Button>
          <Button 
            variant="danger" 
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Eliminando...
              </>
            ) : (
              'Confirmar Eliminación'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default ExpenseDetail; 