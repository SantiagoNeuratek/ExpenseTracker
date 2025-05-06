import { Routes, Route, Navigate } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import { useAuth } from './context/AuthContext';
import { NotificationContainer } from './components/NotificationToast';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';

// Importar páginas
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Categories from './pages/Categories';
import Expenses from './pages/Expenses';
import ApiKeys from './pages/ApiKeys';
import UserManagement from './pages/UserManagement';
import AdminPanel from './pages/AdminPanel';
import AddExpense from './pages/AddExpense';
import CompanyRegistration from './pages/CompanyRegistration';
import CompanyList from './pages/CompanyList';
import UserInvite from './pages/UserInvite';
import InvitationAccept from './pages/InvitationAccept';
import ExpenseDetail from './pages/ExpenseDetail';
import Audit from './pages/Audit';

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="app-container">
      {/* Contenedor de notificaciones */}
      <NotificationContainer />

      <Routes>
        {/* Ruta pública: Login */}
        <Route 
          path="/login" 
          element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} 
        />

        {/* Ruta para aceptar invitaciones */}
        <Route path="/invitation/:token" element={<InvitationAccept />} />

        {/* Ruta por defecto: redirigir a login o dashboard según estado de autenticación */}
        <Route 
          path="/" 
          element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} 
        />

        {/* Rutas protegidas con layout */}
        <Route
          path="*"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}

// Layout para rutas protegidas (con sidebar)
function Layout() {
  return (
    <div className="d-flex">
      <Sidebar />
      
      {/* Contenido principal con padding para evitar que el sidebar lo cubra */}
      <main 
        className="flex-grow-1 bg-light min-vh-100"
        style={{ marginLeft: '260px', padding: '1.5rem' }}
      >
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/categories" element={<Categories />} />
          <Route path="/expenses" element={<Expenses />} />
          <Route path="/expenses/add" element={<AddExpense />} />
          <Route path="/expenses/:id" element={<ExpenseDetail />} />
          <Route path="/apikeys" element={<ApiKeys />} />
          
          {/* Rutas para empresas */}
          <Route path="/companies" element={
            <ProtectedRoute adminOnly>
              <CompanyList />
            </ProtectedRoute>
          } />
          <Route path="/companies/register" element={
            <ProtectedRoute adminOnly>
              <CompanyRegistration />
            </ProtectedRoute>
          } />
          
          {/* Ruta para invitar usuarios */}
          <Route path="/users/invite" element={
            <ProtectedRoute adminOnly>
              <UserInvite />
            </ProtectedRoute>
          } />
          
          {/* Rutas de administrador */}
          <Route 
            path="/usermanagement" 
            element={
              <ProtectedRoute adminOnly>
                <UserManagement />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/adminpanel" 
            element={
              <ProtectedRoute adminOnly>
                <AdminPanel />
              </ProtectedRoute>
            } 
          />
          
          {/* Ruta para auditoría */}
          <Route 
            path="/audit" 
            element={
              <ProtectedRoute adminOnly>
                <Audit />
              </ProtectedRoute>
            } 
          />
          
          {/* Ruta para cualquier otra URL */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
