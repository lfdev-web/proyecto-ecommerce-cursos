import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children, roles = null }) {
  const { user, loading } = useAuth();

  if (loading) return <div className="page text-center">Cargando...</div>;
  if (!user) return <Navigate to="/login" replace />;
  // Si la ruta exige roles concretos y el usuario no los tiene, lo mandamos al inicio.
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;

  return children;
}
