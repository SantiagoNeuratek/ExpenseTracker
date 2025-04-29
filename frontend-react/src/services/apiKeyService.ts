import { ApiKey, ApiKeyCreateResponse } from '../types';
import { apiClient } from '../utils/apiClient';
import { TopCategory, Expense } from '../types';

// Obtener todas las API keys del usuario
export const getApiKeys = async (): Promise<ApiKey[]> => {
  try {
    const response = await apiClient.get<ApiKey[]>('/apikeys');
    return response.data;
  } catch (error) {
    console.error('Error al obtener API keys:', error);
    throw error;
  }
};

// Crear una nueva API key
export const createApiKey = async (data: { name: string }): Promise<ApiKeyCreateResponse> => {
  try {
    const response = await apiClient.post<ApiKeyCreateResponse>('/apikeys', data);
    return response.data;
  } catch (error) {
    console.error('Error al crear API key:', error);
    throw error;
  }
};

// Desactivar (eliminar) una API key
export const deleteApiKey = async (id: number): Promise<void> => {
  try {
    await apiClient.delete(`/apikeys/${id}`);
  } catch (error) {
    console.error(`Error al desactivar API key con ID ${id}:`, error);
    throw error;
  }
};

/**
 * Obtener las 3 categorías con más gastos históricos usando una API Key
 * @param apiKey La API Key para autenticación
 * @returns Un array con hasta 3 categorías ordenadas por monto total
 */
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

/**
 * Obtener gastos por categoría y rango de fechas usando una API Key
 * @param apiKey La API Key para autenticación
 * @param categoryId ID de la categoría a consultar
 * @param startDate Fecha de inicio (YYYY-MM-DD)
 * @param endDate Fecha de fin (YYYY-MM-DD)
 * @returns Lista de gastos que cumplen con los criterios
 */
export const getExpensesByCategoryRest = async (
  apiKey: string,
  categoryId: number,
  startDate: string,
  endDate: string
): Promise<Expense[]> => {
  try {
    const response = await apiClient.get<Expense[]>('/expenses/by-category', {
      headers: {
        'api-key': apiKey
      },
      params: {
        category_id: categoryId,
        start_date: startDate,
        end_date: endDate
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error al obtener gastos por categoría:', error);
    return [];
  }
}; 