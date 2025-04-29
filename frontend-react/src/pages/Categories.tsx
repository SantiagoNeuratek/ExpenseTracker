import { useState, useEffect } from 'react';
import {
  Container,
  Button,
  Table,
  Card,
  Form,
  Badge,
  Modal,
  Spinner,
  Row,
  Col,
  InputGroup
} from 'react-bootstrap';
import { PencilFill, TrashFill, PlusCircle, Funnel } from 'react-bootstrap-icons';
import { Category } from '../types';
import { getCategories, createCategory, updateCategory, deleteCategory } from '../services/expenseService';
import { useNotification } from '../context/NotificationContext';

const Categories = () => {
  // Estados
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showInactive, setShowInactive] = useState(false);
  
  // Estado para modales
  const [showModal, setShowModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  
  // Estado para el formulario de categoría
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    expense_limit: 0 as number | null,
    is_active: true,
    has_limit: false,
  });
  
  const { addNotification } = useNotification();

  // Cargar categorías
  useEffect(() => {
    fetchCategories();
  }, []);

  // Función para cargar categorías
  const fetchCategories = async () => {
    try {
      setIsLoading(true);
      const data = await getCategories();
      setCategories(data);
    } catch (error) {
      console.error('Error al cargar categorías:', error);
      addNotification('Error al cargar categorías', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Filtrar categorías según búsqueda y estado
  const filteredCategories = categories.filter(cat => {
    const matchesTerm = cat.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                         cat.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = showInactive ? true : cat.is_active;
    return matchesTerm && matchesStatus;
  });

  // Abrir modal para crear/editar
  const handleOpenModal = (category: Category | null = null) => {
    if (category) {
      // Modo edición
      setEditingCategory(category);
      setFormData({
        name: category.name,
        description: category.description,
        expense_limit: category.expense_limit,
        is_active: category.is_active,
        has_limit: category.expense_limit !== null,
      });
    } else {
      // Modo creación
      setEditingCategory(null);
      setFormData({
        name: '',
        description: '',
        expense_limit: null,
        is_active: true,
        has_limit: false,
      });
    }
    setShowModal(true);
  };

  // Cerrar modal
  const handleCloseModal = () => {
    setShowModal(false);
  };

  // Manejar cambios en el formulario
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Manejar cambio de límite de gasto
  const handleExpenseLimitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    setFormData(prev => ({ ...prev, expense_limit: isNaN(value) ? 0 : value }));
  };

  // Manejar cambio de estado activo
  const handleActiveChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, is_active: e.target.checked }));
  };

  // Manejar cambio de "tiene límite"
  const handleHasLimitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const hasLimit = e.target.checked;
    setFormData(prev => ({ 
      ...prev, 
      has_limit: hasLimit,
      expense_limit: hasLimit ? (prev.expense_limit || 0) : null
    }));
  };

  // Guardar categoría (crear o actualizar)
  const handleSaveCategory = async () => {
    try {
      setIsSubmitting(true);
      
      // Preparar los datos para guardar
      const categoryData = {
        name: formData.name,
        description: formData.description,
        is_active: formData.is_active,
        expense_limit: formData.has_limit ? formData.expense_limit : null
      };
      
      if (editingCategory) {
        // Actualizar categoría existente
        await updateCategory(editingCategory.id, categoryData);
        addNotification('Categoría actualizada correctamente', 'success');
      } else {
        // Crear nueva categoría
        await createCategory(categoryData);
        addNotification('Categoría creada correctamente', 'success');
      }
      
      handleCloseModal();
      fetchCategories();
    } catch (error) {
      console.error('Error al guardar categoría:', error);
      addNotification(
        `Error al ${editingCategory ? 'actualizar' : 'crear'} categoría`, 
        'error'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Confirmar eliminación
  const handleDeleteClick = (category: Category) => {
    setEditingCategory(category);
    setShowDeleteModal(true);
  };

  // Cerrar modal de eliminación
  const handleCloseDeleteModal = () => {
    setShowDeleteModal(false);
  };

  // Eliminar categoría
  const handleDeleteCategory = async () => {
    if (!editingCategory) return;
    
    try {
      setIsSubmitting(true);
      await deleteCategory(editingCategory.id);
      addNotification('Categoría eliminada correctamente', 'success');
      handleCloseDeleteModal();
      fetchCategories();
    } catch (error) {
      console.error('Error al eliminar categoría:', error);
      addNotification('Error al eliminar categoría', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container fluid>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Categorías de Gastos</h1>
        <Button variant="primary" onClick={() => handleOpenModal()}>
          <PlusCircle className="me-2" /> Nueva Categoría
        </Button>
      </div>

      {/* Filtros */}
      <Row className="mb-4">
        <Col md={6}>
          <Form.Control
            placeholder="Buscar categorías..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </Col>
        <Col md={6}>
          <Form.Check 
            type="switch"
            id="show-inactive"
            label="Mostrar inactivas"
            checked={showInactive}
            onChange={() => setShowInactive(!showInactive)}
          />
        </Col>
      </Row>

      {/* Tabla de categorías */}
      <Card className="shadow-sm">
        <Card.Body>
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
                    <th>Nombre</th>
                    <th>Descripción</th>
                    <th className="text-end">Límite de Gasto</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCategories.length > 0 ? (
                    filteredCategories.map((category) => (
                      <tr key={category.id}>
                        <td className="fw-medium">{category.name}</td>
                        <td>{category.description}</td>
                        <td className="text-end">
                          {category.expense_limit !== null 
                            ? `$${category.expense_limit.toFixed(2)}` 
                            : <span className="text-muted">Sin límite</span>
                          }
                        </td>
                        <td>
                          <Badge bg={category.is_active ? 'success' : 'danger'}>
                            {category.is_active ? 'Activa' : 'Inactiva'}
                          </Badge>
                        </td>
                        <td>
                          <div className="d-flex">
                            <Button
                              size="sm"
                              variant="outline-primary"
                              className="me-2"
                              onClick={() => handleOpenModal(category)}
                            >
                              <PencilFill />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline-danger"
                              onClick={() => handleDeleteClick(category)}
                            >
                              <TrashFill />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="text-center py-4">
                        No se encontraron categorías
                      </td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Modal para crear/editar categoría */}
      <Modal show={showModal} onHide={handleCloseModal}>
        <Modal.Header closeButton>
          <Modal.Title>{editingCategory ? 'Editar Categoría' : 'Nueva Categoría'}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Nombre</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                disabled={isSubmitting}
                required
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Descripción</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                disabled={isSubmitting}
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Límite de Gasto</Form.Label>
              <Form.Check 
                type="switch"
                id="has_limit"
                label="Establecer un límite para esta categoría"
                name="has_limit"
                checked={formData.has_limit}
                onChange={handleHasLimitChange}
                disabled={isSubmitting}
                className="mb-2"
              />
              {formData.has_limit && (
                <InputGroup>
                  <InputGroup.Text>$</InputGroup.Text>
                  <Form.Control
                    type="number"
                    name="expense_limit"
                    value={formData.expense_limit || ''}
                    onChange={handleExpenseLimitChange}
                    disabled={isSubmitting}
                    min="0"
                    step="0.01"
                  />
                </InputGroup>
              )}
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Check 
                type="switch"
                id="is_active"
                label="Categoría Activa"
                name="is_active"
                checked={formData.is_active}
                onChange={handleActiveChange}
                disabled={isSubmitting}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button 
            variant="primary" 
            onClick={handleSaveCategory}
            disabled={isSubmitting || !formData.name.trim()}
          >
            {isSubmitting ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Guardando...
              </>
            ) : (
              'Guardar'
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Modal para confirmar eliminación */}
      <Modal show={showDeleteModal} onHide={handleCloseDeleteModal}>
        <Modal.Header closeButton>
          <Modal.Title>Confirmar Eliminación</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          ¿Está seguro que desea eliminar la categoría <strong>{editingCategory?.name}</strong>?
          Esta acción no puede deshacerse.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseDeleteModal} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button 
            variant="danger" 
            onClick={handleDeleteCategory}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
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
              'Eliminar'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default Categories; 