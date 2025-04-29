import { createContext, useContext, useState, useEffect, ReactNode, useCallback, useMemo } from 'react';
import { User, AuthResponse, Company } from '../types';
import { loginUser, getCurrentUser, logoutUser } from '../services/authService';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  currentCompany: Company | null;
  login: (email: string, password: string) => Promise<{ success: boolean; message: string }>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
  setCurrentCompany: (company: Company | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Hook para usar el contexto de autenticación
const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!token);
  const [lastAuthCheck, setLastAuthCheck] = useState<number>(0);
  
  // Intentar cargar la compañía actual desde localStorage
  const getStoredCompany = (): Company | null => {
    const storedCompany = localStorage.getItem('currentCompany');
    if (storedCompany) {
      try {
        return JSON.parse(storedCompany);
      } catch (e) {
        console.error('Error al parsear currentCompany:', e);
      }
    }
    return null;
  };
  
  const [currentCompany, setCurrentCompanyState] = useState<Company | null>(getStoredCompany());

  // Guardar la compañía actual en localStorage
  const setCurrentCompany = (company: Company | null) => {
    setCurrentCompanyState(company);
    if (company) {
      localStorage.setItem('currentCompany', JSON.stringify(company));
    } else {
      localStorage.removeItem('currentCompany');
    }
  };

  // Función para verificar la autenticación de manera eficiente
  const checkAuth = useCallback(async (): Promise<boolean> => {
    // Si no hay token, no estamos autenticados
    if (!token) {
      setIsAuthenticated(false);
      setUser(null);
      return false;
    }

    // Si ya verificamos recientemente (en los últimos 5 minutos), no volver a verificar
    const now = Date.now();
    const FIVE_MINUTES = 5 * 60 * 1000;
    if (isAuthenticated && user && (now - lastAuthCheck < FIVE_MINUTES)) {
      return true;
    }

    try {
      setIsLoading(true);
      const userData = await getCurrentUser();
      setUser(userData);
      
      // Almacenar el estado de admin en localStorage
      localStorage.setItem('isAdmin', String(userData.is_admin));
      
      // Si es administrador, borrar la empresa actual para forzar la selección manual
      if (userData.is_admin) {
        // Solo borrar la empresa actual si ya no está definida
        if (!currentCompany) {
          localStorage.removeItem('currentCompany');
          setCurrentCompanyState(null);
        }
      } else if (userData.company_id) {
        // Para usuarios no administradores, guardar la empresa asignada directamente en localStorage
        // incluso si no tenemos los detalles completos de la empresa
        const companyData = {
          id: userData.company_id,
          name: 'Empresa asignada', // Nombre temporal
          address: '',
          website: '',
          created_at: ''
        };
        localStorage.setItem('currentCompany', JSON.stringify(companyData));
        setCurrentCompanyState(companyData);
      }
      
      setIsAuthenticated(true);
      setLastAuthCheck(now);
      return true;
    } catch (error) {
      localStorage.removeItem('token');
      localStorage.removeItem('isAdmin');
      localStorage.removeItem('currentCompany');
      setToken(null);
      setUser(null);
      setCurrentCompany(null);
      setIsAuthenticated(false);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [token, user, isAuthenticated, lastAuthCheck, currentCompany]);

  // Verificar autenticación solo al inicio
  useEffect(() => {
    // Solo verificar si hay token y no tenemos usuario
    if (token && !user && !isLoading) {
      checkAuth();
    }
  }, [token, user, isLoading, checkAuth]);

  // Función para iniciar sesión
  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const response: AuthResponse = await loginUser(email, password);
      
      if (response && response.access_token) {
        localStorage.setItem('token', response.access_token);
        setToken(response.access_token);
        
        // Obtener la información del usuario
        const userData = await getCurrentUser();
        setUser(userData);
        
        // Almacenar el estado de admin en localStorage
        localStorage.setItem('isAdmin', String(userData.is_admin));
        
        // Si es administrador, eliminar la empresa actual guardada
        if (userData.is_admin) {
          localStorage.removeItem('currentCompany');
          setCurrentCompanyState(null);
        } else if (userData.company_id) {
          // Para usuarios no administradores, guardar la empresa asignada
          const companyData = {
            id: userData.company_id,
            name: 'Empresa asignada', // Nombre temporal
            address: '',
            website: '',
            created_at: ''
          };
          localStorage.setItem('currentCompany', JSON.stringify(companyData));
          setCurrentCompanyState(companyData);
        }
        
        setIsAuthenticated(true);
        setLastAuthCheck(Date.now());
        
        return { success: true, message: "Inicio de sesión exitoso" };
      } else {
        throw new Error("No se recibió un token de acceso");
      }
    } catch (error) {
      console.error('Error de inicio de sesión:', error);
      return { 
        success: false, 
        message: error instanceof Error 
          ? error.message 
          : "Error al iniciar sesión. Por favor, inténtalo de nuevo." 
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Función para cerrar sesión
  const logout = useCallback(() => {
    logoutUser();
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    localStorage.removeItem('currentCompany');
    setToken(null);
    setUser(null);
    setCurrentCompany(null);
    setIsAuthenticated(false);
    setLastAuthCheck(0);
  }, []);

  // Memoizar el valor del contexto para evitar re-renders innecesarios
  const value = useMemo(() => ({
    user,
    token,
    isLoading,
    isAuthenticated,
    currentCompany,
    setCurrentCompany,
    login,
    logout,
    checkAuth
  }), [user, token, isLoading, isAuthenticated, currentCompany, login, logout, checkAuth]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export { AuthProvider, useAuth }; 