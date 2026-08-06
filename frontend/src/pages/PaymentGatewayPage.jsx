import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { CheckIcon, CreditCardIcon, LockIcon, XIcon } from '../components/Icons';

// Pantalla que simula una pasarela de pago externa. Tiene identidad visual
// propia (fondo oscuro, marca "PasarelaPay") para que se note que el usuario
// "salió" del sitio, igual que ocurre con PayPal o Payphone.
//
// Lleva un aviso permanente de que es una simulación: no procesa pagos reales
// y no debe confundirse con una pasarela de verdad.

function formatearNumero(valor) {
  const soloDigitos = valor.replace(/\D/g, '').slice(0, 19);
  return soloDigitos.replace(/(.{4})/g, '$1 ').trim();
}

export default function PaymentGatewayPage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  const [recarga, setRecarga] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [form, setForm] = useState({ card_number: '', card_holder: '', expiry_date: '', cvv: '' });
  const [error, setError] = useState('');
  const [procesando, setProcesando] = useState(false);
  const [resultado, setResultado] = useState(null);

  useEffect(() => {
    api.get(`/auth/wallet/recharge/${token}/`)
      .then(({ data }) => setRecarga(data))
      .catch(() => setError('No se encontró esta solicitud de pago.'))
      .finally(() => setCargando(false));
  }, [token]);

  const autorizar = async (e) => {
    e.preventDefault();
    setProcesando(true);
    setError('');
    try {
      const { data } = await api.post(`/auth/wallet/recharge/${token}/authorize/`, {
        ...form,
        card_number: form.card_number.replace(/\s/g, ''),
      });
      await refreshUser();
      setResultado({ aprobada: true, ...data });
    } catch (err) {
      const datos = err.response?.data;
      if (err.response?.status === 402) {
        setResultado({ aprobada: false, motivo: datos?.detail, recharge: datos?.recharge });
      } else {
        setError(datos?.detail || Object.values(datos || {}).flat().join(' ') || 'No se pudo procesar el pago.');
      }
    } finally {
      setProcesando(false);
    }
  };

  const cancelar = async () => {
    try { await api.post(`/auth/wallet/recharge/${token}/cancel/`); } catch { /* ya estaba cerrada */ }
    navigate('/perfil');
  };

  if (cargando) return <div className="pasarela"><div className="pasarela-caja">Cargando...</div></div>;

  // --- Resultado del intento ---
  if (resultado) {
    return (
      <div className="pasarela">
        <div className="pasarela-caja text-center">
          <div className={`pasarela-resultado ${resultado.aprobada ? 'es-ok' : 'es-error'}`}>
            {resultado.aprobada ? <CheckIcon width={34} height={34} /> : <XIcon width={34} height={34} />}
          </div>
          <h2 style={{ marginTop: 16 }}>
            {resultado.aprobada ? 'Pago autorizado' : 'Pago rechazado'}
          </h2>

          {resultado.aprobada ? (
            <>
              <p>Se acreditaron <strong>${resultado.recharge.amount}</strong> a tu saldo.</p>
              <dl className="pasarela-comprobante">
                <div><dt>Comprobante</dt><dd>{resultado.recharge.reference}</dd></div>
                <div><dt>Tarjeta</dt><dd>•••• {resultado.recharge.card_last4}</dd></div>
                <div><dt>Saldo actual</dt><dd>${resultado.balance}</dd></div>
              </dl>
            </>
          ) : (
            <p className="pasarela-motivo">{resultado.motivo}</p>
          )}

          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 20, flexWrap: 'wrap' }}>
            {!resultado.aprobada && (
              <button className="btn btn-primary" onClick={() => navigate('/recargar')}>
                Intentar de nuevo
              </button>
            )}
            <button className="btn btn-secondary" onClick={() => navigate('/perfil')}>
              Volver a CursosTech
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- Formulario de pago ---
  return (
    <div className="pasarela">
      <div className="pasarela-caja">
        <div className="pasarela-aviso">
          Modo simulación — no se procesan pagos reales
        </div>

        <header className="pasarela-marca">
          <LockIcon width={20} height={20} />
          <span>PasarelaPay</span>
        </header>

        <div className="pasarela-cobro">
          <span>CursosTech solicita</span>
          <strong>${recarga?.amount}</strong>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={autorizar}>
          <div className="field">
            <label htmlFor="card_number">Número de tarjeta</label>
            <div className="pasarela-input-icono">
              <CreditCardIcon width={18} height={18} />
              <input
                id="card_number"
                inputMode="numeric"
                autoComplete="off"
                placeholder="4242 4242 4242 4242"
                value={form.card_number}
                onChange={(e) => setForm({ ...form, card_number: formatearNumero(e.target.value) })}
                required
              />
            </div>
          </div>

          <div className="field">
            <label htmlFor="card_holder">Titular</label>
            <input
              id="card_holder"
              autoComplete="off"
              placeholder="Como aparece en la tarjeta"
              value={form.card_holder}
              onChange={(e) => setForm({ ...form, card_holder: e.target.value })}
              required
            />
          </div>

          <div className="two-col">
            <div className="field" style={{ marginBottom: 0 }}>
              <label htmlFor="expiry_date">Vencimiento</label>
              <input
                id="expiry_date"
                placeholder="MM/AA"
                maxLength={5}
                value={form.expiry_date}
                onChange={(e) => {
                  let v = e.target.value.replace(/\D/g, '').slice(0, 4);
                  if (v.length > 2) v = `${v.slice(0, 2)}/${v.slice(2)}`;
                  setForm({ ...form, expiry_date: v });
                }}
                required
              />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label htmlFor="cvv">CVV</label>
              <input
                id="cvv"
                inputMode="numeric"
                placeholder="123"
                maxLength={4}
                value={form.cvv}
                onChange={(e) => setForm({ ...form, cvv: e.target.value.replace(/\D/g, '') })}
                required
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-block mt-lg" disabled={procesando}>
            {procesando ? 'Procesando...' : `Autorizar $${recarga?.amount}`}
          </button>
          <button type="button" className="btn btn-secondary btn-block" style={{ marginTop: 10 }} onClick={cancelar}>
            Cancelar
          </button>
        </form>

        {/* Ayuda para probar: números que aprueban y números que fallan */}
        {recarga?.test_cards && (
          <details className="pasarela-ayuda">
            <summary>Tarjetas de prueba</summary>
            <p className="pasarela-ayuda-titulo">Aprueban</p>
            <ul>
              {recarga.test_cards.aprobadas.map((n) => (
                <li key={n}><code>{n}</code></li>
              ))}
            </ul>
            <p className="pasarela-ayuda-titulo">Fallan</p>
            <ul>
              {recarga.test_cards.rechazadas.map((t) => (
                <li key={t.numero}><code>{t.numero}</code> — {t.motivo}</li>
              ))}
            </ul>
            <p style={{ fontSize: 12, margin: '10px 0 0' }}>
              Cualquier fecha futura y cualquier CVV de 3 dígitos sirven.
            </p>
          </details>
        )}
      </div>
    </div>
  );
}
