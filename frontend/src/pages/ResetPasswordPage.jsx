import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import api from '../api/client';
import { CheckCircleIcon, LockIcon } from '../components/Icons';

const campo = {
  width: '100%', padding: 12, borderRadius: 8,
  border: '1px solid var(--surface-border)',
  background: 'var(--surface-2)', color: 'var(--text-primary)',
  fontFamily: 'inherit', fontSize: 15, marginBottom: 16,
};

export default function ResetPasswordPage() {
  // uid y token vienen del enlace del correo; la SPA los lee de su ruta y los
  // reenvía a la API. El navegador nunca los interpreta, solo los transporta.
  const { uid, token } = useParams();
  const navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [repetir, setRepetir] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');
  const [listo, setListo] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    if (password !== repetir) return setError('Las dos contraseñas no coinciden.');

    setGuardando(true);
    setError('');
    try {
      await api.post('/auth/password/reset/confirm/', { uid, token, password });
      setListo(true);
      setTimeout(() => navigate('/login'), 2500);
    } catch (err) {
      const datos = err.response?.data;
      setError(
        datos?.detail
        // El backend devuelve los mensajes de los validadores de Django
        // (longitud, contraseña común, solo números) en este campo.
        || datos?.password?.[0]
        || 'No se pudo cambiar la contraseña.'
      );
    } finally {
      setGuardando(false);
    }
  };

  if (listo) {
    return (
      <div className="page" style={{ maxWidth: 440, margin: '0 auto' }}>
        <div className="glass card" style={{ textAlign: 'center' }}>
          <CheckCircleIcon width={44} height={44} strokeWidth={1.5}
                           style={{ color: 'var(--success)' }} />
          <h1>Contraseña actualizada</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Te llevamos a iniciar sesión...
          </p>
          <Link to="/login" className="btn btn-primary btn-block">Ir ahora</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page" style={{ maxWidth: 440, margin: '0 auto' }}>
      <div className="glass card">
        <h1 style={{ marginTop: 0 }}>Elige una contraseña nueva</h1>
        <form onSubmit={enviar}>
          <label htmlFor="pass" style={{ display: 'block', fontSize: 13, marginBottom: 6 }}>
            Contraseña nueva
          </label>
          <input
            id="pass" type="password" required minLength={8} autoComplete="new-password"
            value={password} onChange={(e) => setPassword(e.target.value)} style={campo}
          />

          <label htmlFor="pass2" style={{ display: 'block', fontSize: 13, marginBottom: 6 }}>
            Repítela
          </label>
          <input
            id="pass2" type="password" required minLength={8} autoComplete="new-password"
            value={repetir} onChange={(e) => setRepetir(e.target.value)} style={campo}
          />

          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 0 }}>
            Mínimo 8 caracteres. No puede ser solo números ni una contraseña
            demasiado común.
          </p>

          {error && <p style={{ color: 'var(--danger)', fontSize: 13 }}>{error}</p>}

          <button className="btn btn-primary btn-block" disabled={guardando}>
            <LockIcon width={16} height={16} />
            {guardando ? 'Guardando...' : 'Guardar contraseña'}
          </button>
        </form>

        <Link to="/recuperar"
              style={{ display: 'block', textAlign: 'center', marginTop: 16, fontSize: 14 }}>
          ¿El enlace caducó? Pide uno nuevo
        </Link>
      </div>
    </div>
  );
}
