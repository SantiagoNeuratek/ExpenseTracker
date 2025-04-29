import { apiClient } from '../utils/apiClient';
import { Company } from '../types';

// Obtener todas las empresas (solo para admin)
export const getCompanies = async (): Promise<Company[]> => {
  try {
    const response = await apiClient.get<Company[]>('/companies');
    return response.data;
  } catch (error) {
    console.error('Error al obtener empresas:', error);
    throw error;
  }
};

// Obtener una empresa por ID
export const getCompanyById = async (id: number): Promise<Company> => {
  try {
    const response = await apiClient.get<Company>(`/companies/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error al obtener empresa con ID ${id}:`, error);
    throw error;
  }
};

// Crear una nueva empresa
export interface CompanyCreateData {
  name: string;
  address: string;
  website: string;
  logo: string; // Base64 encoded
}

export const createCompany = async (data: CompanyCreateData): Promise<Company> => {
  try {
    const response = await apiClient.post<Company>('/companies', data);
    return response.data;
  } catch (error) {
    console.error('Error al crear empresa:', error);
    throw error;
  }
};

// Invitar a un usuario a una empresa
export const inviteUserToCompany = async (companyId: number, email: string): Promise<void> => {
  try {
    await apiClient.post(`/companies/${companyId}/invite`, { email });
  } catch (error) {
    console.error(`Error al invitar usuario al a empresa ${companyId}:`, error);
    throw error;
  }
}; 