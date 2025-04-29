import { User, AuthResponse } from '../types';
import { apiClient } from '../utils/apiClient';

// Función para iniciar sesión
export const loginUser = async (email: string, password: string): Promise<AuthResponse> => {
  try {
    // El backend espera application/x-www-form-urlencoded para OAuth2PasswordRequestForm
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await apiClient.post<AuthResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error en login:', error);
    throw new Error('Credenciales inválidas');
  }
};

// Función para obtener el usuario actual
export const getCurrentUser = async (): Promise<User> => {
  try {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  } catch (error) {
    throw new Error('No se pudo obtener la información del usuario');
  }
};

// Función para cerrar sesión
export const logoutUser = async (): Promise<void> => {
  try {
    // Muchas implementaciones solo requieren eliminar el token del cliente
    // pero si el backend tiene un endpoint para cerrar sesión, se puede llamar aquí
    // await apiClient.post('/auth/logout');
    return;
  } catch (error) {
    console.error('Error al cerrar sesión:', error);
  }
};

// Función para verificar si el token está vigente
export const checkTokenValidity = async (): Promise<boolean> => {
  try {
    await apiClient.get('/auth/me');
    return true;
  } catch (error) {
    return false;
  }
};

// Función para verificar un token de invitación
export const verifyInvitation = async (token: string): Promise<{email: string; companyName: string; valid: boolean}> => {
  try {
    const response = await apiClient.get(`/auth/invitation/verify/${token}`, {
      // No usar credenciales para evitar interferencia con el token de autenticación
      headers: { 'Authorization': '' }
    });
    return response.data;
  } catch (error) {
    console.error('Error al verificar invitación:', error);
    throw error;
  }
};

// Función para aceptar una invitación y establecer contraseña
export const acceptInvitation = async (token: string, password: string): Promise<void> => {
  try {
    const data = { password };
    await apiClient.post(`/auth/invitation/accept/${token}`, data, {
      // No usar credenciales para evitar interferencia con el token de autenticación
      headers: { 'Authorization': '' }
    });
  } catch (error) {
    console.error('Error al aceptar invitación:', error);
    throw error;
  }
}; 