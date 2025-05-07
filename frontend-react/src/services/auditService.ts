import { apiClient } from '../utils/apiClient';
import { AuditRecord, AuditRecordPagination } from '../types';

// Obtener registros de auditoría con filtros opcionales
interface AuditFilters {
  entity_type?: string;
  action?: string;
  user_id?: number;
  start_date?: string;
  end_date?: string;
  search?: string;
  page?: number;
  page_size?: number;
  company_id?: number;
}

export const getAuditRecords = async (filters: AuditFilters = {}): Promise<AuditRecordPagination> => {
  try {
    // Construir parámetros de consulta
    const params = new URLSearchParams();
    
    if (filters.entity_type) params.append('entity_type', filters.entity_type);
    if (filters.action) params.append('action', filters.action);
    if (filters.user_id) params.append('user_id', filters.user_id.toString());
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    if (filters.search) params.append('search', filters.search);
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.page_size) params.append('page_size', filters.page_size.toString());
    if (filters.company_id) params.append('company_id', filters.company_id.toString());
    
    const response = await apiClient.get<AuditRecordPagination>('/audit', { params });
    return response.data;
  } catch (error) {
    console.error('Error al obtener registros de auditoría:', error);
    throw error;
  }
};

// Obtener un registro de auditoría por ID
export const getAuditRecordById = async (id: number): Promise<AuditRecord> => {
  try {
    const response = await apiClient.get<AuditRecord>(`/audit/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error al obtener registro de auditoría con ID ${id}:`, error);
    throw error;
  }
};

// Obtener acciones de auditoría disponibles
export const getAuditActions = async (companyId?: number): Promise<string[]> => {
  try {
    const params = new URLSearchParams();
    if (companyId) params.append('company_id', companyId.toString());
    
    const response = await apiClient.get<string[]>('/audit/actions', { params });
    return response.data;
  } catch (error) {
    console.error('Error al obtener acciones de auditoría:', error);
    throw error;
  }
};

// Obtener tipos de entidades disponibles
export const getEntityTypes = async (companyId?: number): Promise<string[]> => {
  try {
    const params = new URLSearchParams();
    if (companyId) params.append('company_id', companyId.toString());
    
    const response = await apiClient.get<string[]>('/audit/entity-types', { params });
    return response.data;
  } catch (error) {
    console.error('Error al obtener tipos de entidades:', error);
    throw error;
  }
}; 