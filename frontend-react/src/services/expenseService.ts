import { PaginatedResponse, Expense, Category } from '../types';
import { apiClient } from '../utils/apiClient';

// ======== SERVICIOS PARA GASTOS =========

// Obtener gastos con filtros
export const getExpenses = async (
  startDate?: string,
  endDate?: string,
  categoryId?: number,
  page: number = 1,
  pageSize: number = 10
): Promise<PaginatedResponse<Expense>> => {
  try {
    // Preparar parámetros
    const params: Record<string, string | number> = { 
      page, 
      page_size: pageSize 
    };
    
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (categoryId) params.category_id = categoryId;
    
    const response = await apiClient.get<PaginatedResponse<Expense>>('/expenses', { params });
    return response.data;
  } catch (error) {
    console.error('Error al obtener gastos:', error);
    throw error; // Propagar el error para manejarlo en el componente
  }
};

// Obtener estadísticas de gastos
export interface ExpenseMetrics {
  total: number;
  average: number;
  max: number;
  min: number;
  count: number;
}

export const getExpenseMetrics = async (
  startDate?: string,
  endDate?: string,
  categoryId?: number
): Promise<ExpenseMetrics> => {
  try {
    // Preparar parámetros
    const params: Record<string, string | number> = {};
    
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (categoryId) params.category_id = categoryId;
    
    const response = await apiClient.get<ExpenseMetrics>('/expenses/metrics', { params });
    return response.data;
  } catch (error) {
    console.error('Error al obtener métricas de gastos:', error);
    // Devolver valores por defecto en caso de error
    return { total: 0, average: 0, max: 0, min: 0, count: 0 };
  }
};

// Obtener distribución de gastos por categoría
export interface CategoryDistribution {
  category_id: number;
  category_name: string;
  amount: number;
  percentage: number;
}

export const getExpenseDistribution = async (
  startDate?: string,
  endDate?: string
): Promise<CategoryDistribution[]> => {
  try {
    // Preparar parámetros
    const params: Record<string, string> = {};
    
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    
    const response = await apiClient.get<CategoryDistribution[]>('/expenses/distribution', { params });
    return response.data;
  } catch (error) {
    console.error('Error al obtener distribución de gastos:', error);
    return [];
  }
};

// Obtener un gasto por ID
export const getExpenseById = async (id: number): Promise<Expense> => {
  try {
    const response = await apiClient.get<Expense>(`/expenses/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error al obtener gasto con ID ${id}:`, error);
    throw error;
  }
};

// Alias de getExpenseById para mantener consistencia con la interfaz
export const getExpense = getExpenseById;

// Crear un nuevo gasto
export const createExpense = async (
  expenseData: {
    amount: number;
    date_incurred: string;
    description: string;
    category_id: number;
  }
): Promise<Expense> => {
  try {
    const response = await apiClient.post<Expense>('/expenses', expenseData);
    return response.data;
  } catch (error) {
    console.error('Error al crear gasto:', error);
    throw error; // Propagar el error para manejarlo en el componente
  }
};

// Actualizar un gasto existente
export const updateExpense = async (
  id: number, 
  expenseData: {
    amount?: number;
    date_incurred?: string;
    description?: string;
    category_id?: number;
  }
): Promise<Expense> => {
  try {
    const response = await apiClient.put<Expense>(`/expenses/${id}`, expenseData);
    return response.data;
  } catch (error) {
    console.error(`Error al actualizar gasto con ID ${id}:`, error);
    throw error;
  }
};

// Eliminar un gasto
export const deleteExpense = async (id: number): Promise<void> => {
  try {
    await apiClient.delete(`/expenses/${id}`);
  } catch (error) {
    console.error(`Error al eliminar gasto con ID ${id}:`, error);
    throw error;
  }
};

// Obtener las categorías principales por monto gastado
export interface TopCategory {
  id: number;
  name: string;
  total_amount: number;
}

export const getTopCategories = async (
  startDate?: string,
  endDate?: string,
  limit: number = 5
): Promise<TopCategory[]> => {
  try {
    const params: Record<string, string | number> = {
      limit
    };
    
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    
    const response = await apiClient.get<TopCategory[]>('/expenses/top-categories', { params });
    return response.data;
  } catch (error) {
    console.error('Error al obtener top categorías:', error);
    return [];
  }
};

// Obtener gastos por categoría y rango de fechas
export const getExpensesByCategory = async (
  categoryId: number,
  startDate: string,
  endDate: string
): Promise<Expense[]> => {
  try {
    const params = {
      category_id: categoryId,
      start_date: startDate,
      end_date: endDate
    };
    
    const response = await apiClient.get<Expense[]>('/expenses/by-category', { params });
    return response.data;
  } catch (error) {
    console.error('Error al obtener gastos por categoría:', error);
    return [];
  }
};

// Obtener las principales categorías históricas usando API Key
export const getTopCategoriesHistory = async (apiKey: string): Promise<TopCategory[]> => {
  try {
    const response = await apiClient.get<TopCategory[]>('/expenses/top-categories-history', {
      headers: {
        'api-key': apiKey
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error al obtener top categorías históricas:', error);
    return [];
  }
};

// ======== SERVICIOS PARA CATEGORÍAS =========

// Obtener todas las categorías
export const getCategories = async (): Promise<Category[]> => {
  try {
    const response = await apiClient.get<Category[]>('/categories');
    return response.data;
  } catch (error) {
    console.error('Error al obtener categorías:', error);
    return [];
  }
};

// Obtener una categoría por ID
export const getCategoryById = async (id: number): Promise<Category> => {
  try {
    const response = await apiClient.get<Category>(`/categories/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error al obtener categoría con ID ${id}:`, error);
    throw error;
  }
};

// Crear una nueva categoría
export const createCategory = async (
  categoryData: {
    name: string;
    description: string;
    expense_limit: number | null;
    is_active?: boolean;
  }
): Promise<Category> => {
  try {
    const response = await apiClient.post<Category>('/categories', categoryData);
    return response.data;
  } catch (error) {
    console.error('Error al crear categoría:', error);
    throw error;
  }
};

// Actualizar una categoría existente
export const updateCategory = async (
  id: number, 
  categoryData: {
    name?: string;
    description?: string;
    expense_limit?: number | null;
    is_active?: boolean;
  }
): Promise<Category> => {
  try {
    const response = await apiClient.put<Category>(`/categories/${id}`, categoryData);
    return response.data;
  } catch (error) {
    console.error(`Error al actualizar categoría con ID ${id}:`, error);
    throw error;
  }
};

// Eliminar una categoría
export const deleteCategory = async (id: number): Promise<Category> => {
  try {
    const response = await apiClient.delete<Category>(`/categories/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error al eliminar categoría con ID ${id}:`, error);
    throw error;
  }
};
