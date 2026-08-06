import { useEffect, useState } from 'react';
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { GraduationCapIcon, MenuIcon, UserIcon, XIcon } from './Icons';

// En desarrollo el frontend corre en :3000 y Django Admin en :8000.
// En producción (detrás de nginx, mismo dominio) es simplemente /admin/.
const djangoAdminUrl =
  window.location.port === '3000'
    ? `${window.location.protocol}//${window.location.hostname}:8000/admin/`
    : '/admin/';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  // Al cambiar de página el menú móvil se cierra solo (si no, tapa el contenido).
  useEffect(() => { setMenuOpen(false); }, [location.pathname]);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const role = user?.role;
  // El admin es solo supervisión: no comparte la experiencia de compra/estudio.
  const isAdmin = role === 'ADMIN';
  const isDocente = role === 'DOCENTE';

  return (
    <>
      <nav className="navbar glass">
        <Link to={isAdmin ? '/dashboard' : '/'} className="navbar-brand">
          <GraduationCapIcon width={24} height={24} /> CursosTech
        </Link>
        <button
          type="button"
          className="navbar-toggle"
          aria-expanded={menuOpen}
          aria-controls="navbar-links"
          aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <XIcon width={22} height={22} /> : <MenuIcon width={22} height={22} />}
        </button>
        <div id="navbar-links" className={`navbar-links${menuOpen ? ' is-open' : ''}`}>
          {!user && (
            <>
              <Link to="/">Catálogo</Link>
              <Link to="/membresias">Membresías</Link>
              <Link to="/login">Ingresar</Link>
              <Link to="/registro" className="btn btn-primary">Crear cuenta</Link>
            </>
          )}

          {user && isAdmin && (
            <>
              <Link to="/dashboard">Dashboard</Link>
              <a href={djangoAdminUrl} target="_blank" rel="noopener noreferrer">Django Admin</a>
              <button className="btn btn-secondary" onClick={handleLogout}>Salir</button>
            </>
          )}

          {user && !isAdmin && (
            <>
              <Link to="/">Catálogo</Link>
              <Link to="/membresias">Membresías</Link>
              {isDocente && <Link to="/panel-docente">Panel docente</Link>}
              <Link to="/mi-biblioteca">Mi biblioteca</Link>
              <Link to="/wishlist">Wishlist</Link>
              <Link to="/carrito">Carrito</Link>
              {!isDocente && <Link to="/ser-docente">Enseña con nosotros</Link>}
              <Link
                to="/perfil"
                className="navbar-balance"
                title="Mi perfil"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
              >
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt=""
                    style={{ width: 24, height: 24, borderRadius: '50%', objectFit: 'cover' }}
                  />
                ) : <UserIcon width={16} height={16} />}
                ${user.balance}
              </Link>
              <button className="btn btn-secondary" onClick={handleLogout}>Salir</button>
            </>
          )}
        </div>
      </nav>
      <main>
        <Outlet />
      </main>
    </>
  );
}
