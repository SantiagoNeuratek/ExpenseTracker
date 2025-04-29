import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { ApiError } from '../types';

// Crear instancia de axios con configuración base
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de solicitud para agregar el token de autenticación
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Añadir company_id como parámetro de consulta si existe en localStorage
    const currentCompany = localStorage.getItem('currentCompany');
    
    if (currentCompany) {
      try {
        const companyData = JSON.parse(currentCompany);
        if (companyData && companyData.id) {
          // Si no hay params, crear un objeto vacío
          config.params = config.params || {};
          
          // Añadir company_id a los parámetros si no está ya presente
          if (!config.params.company_id) {
            config.params.company_id = companyData.id;
          }
        }
      } catch (e) {
        console.error('Error al parsear currentCompany:', e);
      }
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor de respuesta para manejar errores comunes
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    const customError: ApiError = {
      status: error.response?.status || 500,
      message: 'Error en la solicitud',
      detail: error.response?.data && typeof error.response.data === 'object' && 'detail' in error.response.data 
        ? String(error.response.data.detail) 
        : error.message,
    };

    // Manejar errores comunes
    if (error.response) {
      switch (error.response.status) {
        case 400:
          customError.message = 'Solicitud incorrecta';
          break;
        case 401:
          customError.message = 'No autorizado';
          // No redirigir si estamos en la página de invitación
          const currentPath = window.location.pathname;
          if (!currentPath.includes('/invitation/') && currentPath !== '/login') {
            localStorage.removeItem('token');
            window.location.href = '/login';
          }
          break;
        case 403:
          customError.message = 'Acceso prohibido';
          break;
        case 404:
          customError.message = 'Recurso no encontrado';
          break;
        case 500:
          customError.message = 'Error del servidor';
          break;
        default:
          customError.message = `Error ${error.response.status}`;
      }
    } else if (error.request) {
      // La solicitud se hizo pero no se recibió respuesta
      customError.message = 'No se pudo conectar con el servidor';
    }

    return Promise.reject(customError);
  }
);

export { apiClient }; 