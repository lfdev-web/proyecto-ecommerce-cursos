import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { LockIcon } from '../components/Icons';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');

  const enviar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setError('');
    try {
      const { data } = await api.post('/auth/password/reset/', { email });
      // El backend responde lo mismo exista o no la cuenta: si aquí se
      // distinguiera, cualquiera podría averiguar qué correos están
      // registrados probando direcciones.
      setMensaje(data.detail);
    } catch (err) {
      setError(
        err.response?.status === 429
          ? 'Demasiadas solicitudes. Espera un momento antes de volver a intentarlo.'
          : err.response?.data?.email?.[0] || 'No se pudo enviar el correo.'
      );
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="page" style={{ maxWidth: 440, margin: '0 auto' }}>
      <div className="glass card">
        <h1 style={{ marginTop: 0 }}>Recuperar contraseña</h1>

        {mensaje ? (
          <>
            <p style={{ color: 'var(--success)' }}>{mensaje}</p>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              El enlace caduca en una hora y solo se puede usar una vez.
            </p>
            <Link to="/login" className="btn btn-secondary btn-block">
              Volver a iniciar sesión
            </Link>
          </>
        ) : (
          <form onSubmit={enviar}>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
              Escribe el correo de tu cuenta y te mandamos un enlace para elegir
              una contraseña nueva.
            </p>
            <label htmlFor="email" style={{ display: 'block', fontSize: 13, marginBottom: 6 }}>
              Correo electrónico
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tucorreo@ejemplo.com"
              style={{
                width: '100%', padding: 12, borderRadius: 8,
                border: '1px solid var(--surface-border)',
                background: 'var(--surface-2)', color: 'var(--text-primary)',
                fontFamily: 'inherit', fontSize: 15, marginBottom: 16,
              }}
            />
            {error && <p style={{ color: 'var(--danger)', fontSize: 13 }}>{error}</p>}
            <button className="btn btn-primary btn-block" disabled={enviando}>
              <LockIcon width={16} height={16} />
              {enviando ? 'Enviando...' : 'Enviarme el enlace'}
            </button>
            <Link
              to="/login"
              style={{ display: 'block', textAlign: 'center', marginTop: 16, fontSize: 14 }}
            >
              Volver a iniciar sesión
            </Link>
          </form>
        )}
      </div>
    </div>
  );
}
