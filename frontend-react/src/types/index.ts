// Interfaz para el usuario autenticado
export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_admin: boolean;
  company_id: number;
}

// Interfaz para la respuesta de autenticación
export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// Interfaz para la información de empresa
export interface Company {
  id: number;
  name: string;
  address: string;
  website: string;
  logo?: string;
  created_at: string;
}

// Interfaz para categorías
export interface Category {
  id: number;
  name: string;
  description: string;
  expense_limit: number | null;
  is_active: boolean;
  created_at: string;
  company_id: number;
}

// Interfaz para categorías con monto total de gastos
export interface TopCategory {
  id: number;
  name: string;
  total_amount: number;
}

// Interfaz para gastos
export interface Expense {
  id: number;
  description: string;
  amount: number;
  date_incurred: string;
  category_id: number;
  category_name?: string;
  user_id: number;
  created_at: string;
  company_id: number;
  receipt_url?: string;
}

// Interfaz para paginación
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// Interfaz para claves API
export interface ApiKey {
  id: number;
  name: string;
  is_active: boolean;
  created_at: string;
  user_id: number;
  company_id: number;
  key_preview?: string;
}

// Interfaz para la respuesta de creación de API key
export interface ApiKeyCreateResponse extends ApiKey {
  key: string;
}

// Interfaz para notificaciones
export interface Notification {
  id: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timeout?: number;
}

// Tipos de error
export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

// Interfaz para crear categorías
export interface CategoryCreate {
  name: string;
  description: string;
  expense_limit: number | null;
  is_active?: boolean;
}

// Interfaz para actualizar categorías
export interface CategoryUpdate {
  name?: string;
  description?: string;
  expense_limit?: number | null;
  is_active?: boolean;
}

// Interfaz para registros de auditoría
export interface AuditRecord {
  id: number;
  action: string;
  entity_type: string;
  entity_id: number;
  previous_data?: any;
  new_data?: any;
  user_id: number;
  expense_id?: number;
  created_at: string;
  user_email?: string;
  entity_description?: string;
}

// Interfaz para respuesta paginada de auditoría
export interface AuditRecordPagination {
  items: AuditRecord[];
  total: number;
  page: number;
  page_size: number;
} 