import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import CatalogPage from './pages/CatalogPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import './App.css';

// El catálogo y el login van en el bundle principal: son la primera pantalla
// que ve cualquier visitante y no conviene que esperen una descarga extra.
//
// El resto se carga bajo demanda. Antes todo viajaba en un solo archivo de
// 635 kB: un alumno que solo mira el catálogo se descargaba también el panel
// del docente y el dashboard del administrador, que nunca va a abrir.
const CourseDetailPage = lazy(() => import('./pages/CourseDetailPage'));
const CartPage = lazy(() => import('./pages/CartPage'));
const CheckoutPage = lazy(() => import('./pages/CheckoutPage'));
const MyLibraryPage = lazy(() => import('./pages/MyLibraryPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const RechargePage = lazy(() => import('./pages/RechargePage'));
const PaymentGatewayPage = lazy(() => import('./pages/PaymentGatewayPage'));
const WishlistPage = lazy(() => import('./pages/WishlistPage'));
const MembershipsPage = lazy(() => import('./pages/MembershipsPage'));
const ExamPage = lazy(() => import('./pages/ExamPage'));
const CoursePlayerPage = lazy(() => import('./pages/CoursePlayerPage'));
const TeacherApplicationPage = lazy(() => import('./pages/TeacherApplicationPage'));
const TeacherPanelPage = lazy(() => import('./pages/TeacherPanelPage'));
const TeacherSlotRequestPage = lazy(() => import('./pages/TeacherSlotRequestPage'));
const TeacherCourseEditorPage = lazy(() => import('./pages/TeacherCourseEditorPage'));
const TeacherCourseStudentsPage = lazy(() => import('./pages/TeacherCourseStudentsPage'));
const AnalyticsDashboardPage = lazy(() => import('./pages/AnalyticsDashboardPage'));

function Cargando() {
  return <div className="page">Cargando...</div>;
}

function App() {
  return (
    <Suspense fallback={<Cargando />}>
      <Routes>
        {/* La pasarela va FUERA del Layout: sin navbar ni pie de página, para
            que se perciba como un sitio externo igual que una pasarela real. */}
        <Route
          path="/pasarela/:token"
          element={<ProtectedRoute><PaymentGatewayPage /></ProtectedRoute>}
        />

        <Route element={<Layout />}>
          <Route path="/" element={<CatalogPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/registro" element={<RegisterPage />} />
          <Route path="/recuperar" element={<ForgotPasswordPage />} />
          {/* uid y token los pone el enlace del correo */}
          <Route path="/restablecer/:uid/:token" element={<ResetPasswordPage />} />
          <Route path="/cursos/:slug" element={<CourseDetailPage />} />
          <Route path="/carrito" element={<ProtectedRoute><CartPage /></ProtectedRoute>} />
          <Route path="/checkout" element={<ProtectedRoute><CheckoutPage /></ProtectedRoute>} />
          <Route path="/mi-biblioteca" element={<ProtectedRoute><MyLibraryPage /></ProtectedRoute>} />
          <Route path="/perfil" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/recargar" element={<ProtectedRoute><RechargePage /></ProtectedRoute>} />
          <Route path="/wishlist" element={<ProtectedRoute><WishlistPage /></ProtectedRoute>} />
          <Route path="/membresias" element={<MembershipsPage />} />
          <Route path="/ser-docente" element={<ProtectedRoute><TeacherApplicationPage /></ProtectedRoute>} />
          <Route path="/examen/:courseId" element={<ProtectedRoute><ExamPage /></ProtectedRoute>} />
          <Route path="/aprender/:enrollmentId" element={<ProtectedRoute><CoursePlayerPage /></ProtectedRoute>} />
          <Route path="/panel-docente" element={<ProtectedRoute roles={['DOCENTE', 'ADMIN']}><TeacherPanelPage /></ProtectedRoute>} />
          <Route path="/panel-docente/espacios" element={<ProtectedRoute roles={['DOCENTE', 'ADMIN']}><TeacherSlotRequestPage /></ProtectedRoute>} />
          <Route path="/panel-docente/curso-nuevo" element={<ProtectedRoute roles={['DOCENTE', 'ADMIN']}><TeacherCourseEditorPage /></ProtectedRoute>} />
          <Route path="/panel-docente/curso/:courseId/editar" element={<ProtectedRoute roles={['DOCENTE', 'ADMIN']}><TeacherCourseEditorPage /></ProtectedRoute>} />
          <Route path="/panel-docente/curso/:courseId" element={<ProtectedRoute roles={['DOCENTE', 'ADMIN']}><TeacherCourseStudentsPage /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute roles={['ADMIN']}><AnalyticsDashboardPage /></ProtectedRoute>} />
        </Route>
      </Routes>
    </Suspense>
  );
}

export default App;
