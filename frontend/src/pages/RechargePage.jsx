import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { ArrowLeftIcon } from '../components/Icons';

const MONTOS_RAPIDOS = [10, 25, 50, 100];
const MIN = 5;
const MAX = 500;

export default function RechargePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [monto, setMonto] = useState('25');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  const valor = Number(monto);
  const montoValido = !Number.isNaN(valor) && valor >= MIN && valor <= MAX;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!montoValido) {
      setError(`El monto debe estar entre $${MIN} y $${MAX}.`);
      return;
    }
    setEnviando(true);
    setError('');
    try {
      // Paso 1: se crea la intención. El monto queda guardado en el servidor;
      // la pantalla de la pasarela lo lee de ahí, no del navegador.
      const { data } = await api.post('/auth/wallet/recharge/', { amount: valor.toFixed(2) });
      navigate(`/pasarela/${data.token}`);
    } catch (err) {
      const detalle = err.response?.data;
      if (err.response?.status === 429) {
        setError('Demasiados intentos seguidos. Espera un minuto y vuelve a intentarlo.');
      } else {
        setError(detalle?.amount?.[0] || detalle?.detail || 'No se pudo iniciar la recarga.');
      }
      setEnviando(false);
    }
  };

  return (
    <div className="page container-narrow">
      <Link to="/perfil" className="icon-text" style={{ color: 'var(--accent)', fontWeight: 600, gap: 6 }}>
        <ArrowLeftIcon width={16} height={16} /> Volver a mi perfil
      </Link>

      <h1 className="mt-lg">Recargar saldo</h1>
      <p>Tu saldo actual es <strong>${user?.balance}</strong>.</p>

      <form onSubmit={handleSubmit} className="glass card">
        {error && <div className="alert alert-danger">{error}</div>}

        <label className="recarga-etiqueta">Elige un monto</label>
        <div className="recarga-montos">
          {MONTOS_RAPIDOS.map((m) => (
            <button
              key={m}
              type="button"
              className={`recarga-monto${Number(monto) === m ? ' is-activo' : ''}`}
              onClick={() => { setMonto(String(m)); setError(''); }}
            >
              ${m}
            </button>
          ))}
        </div>

        <div className="field mt-lg">
          <label htmlFor="monto">O escribe otro monto (entre ${MIN} y ${MAX})</label>
          <input
            id="monto"
            type="number"
            min={MIN}
            max={MAX}
            step="0.01"
            value={monto}
            onChange={(e) => { setMonto(e.target.value); setError(''); }}
          />
        </div>

        <button type="submit" className="btn btn-primary btn-block" disabled={enviando || !montoValido}>
          {enviando ? 'Conectando...' : `Continuar al pago — $${montoValido ? valor.toFixed(2) : '0.00'}`}
        </button>

        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 14, marginBottom: 0 }}>
          Al continuar te llevaremos a la pasarela de pago para autorizar el cobro.
        </p>
      </form>
    </div>
  );
}
