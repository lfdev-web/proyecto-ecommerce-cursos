import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { StarIcon } from '../components/Icons';

export default function CheckoutPage() {
  const [cart, setCart] = useState(null);
  const [cardNumber, setCardNumber] = useState('');
  const [couponCode, setCouponCode] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();

  const [membership, setMembership] = useState(null);

  useEffect(() => {
    api.get('/orders/cart/').then(({ data }) => setCart(data)).catch(() => setCart(null));
    api.get('/memberships/my-status/').then(({ data }) => setMembership(data)).catch(() => setMembership(null));
  }, []);

  const memberPct = membership?.is_currently_active ? Number(membership.plan?.member_discount_pct || 0) : 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.post('/orders/checkout/', { card_number: cardNumber, coupon_code: couponCode });
      await refreshUser();
      navigate('/mi-biblioteca');
    } catch (err) {
      const data = err.response?.data;
      setError(
        data?.detail
        || data?.card_number?.join(' ')
        || data?.coupon_code?.join(' ')
        || 'No se pudo procesar el pago.'
      );
    } finally {
      setLoading(false);
    }
  };

  const items = cart?.items || [];

  if (cart && items.length === 0) {
    return (
      <div className="page">
        <h1>Checkout</h1>
        <div className="glass card text-center" style={{ padding: 48 }}>
          <p>No tienes cursos en el carrito.</p>
          <Link to="/" className="btn btn-primary">Explorar el catálogo</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Checkout</h1>
      <div className="grid layout-split-even" style={{ gap: 24 }}>
        {/* Resumen del pedido */}
        <div className="glass card">
          <h3 style={{ marginTop: 0 }}>Tu pedido</h3>
          {items.map((item) => (
            <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', fontSize: 14 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{item.course.title}</span>
              <span>${item.course.price}</span>
            </div>
          ))}
          {memberPct > 0 && (
            <div
              className="icon-text"
              style={{
                background: 'var(--accent-soft)', color: 'var(--accent-strong)', borderRadius: 8,
                padding: '8px 12px', fontSize: 13, fontWeight: 600, marginTop: 8, alignItems: 'flex-start',
              }}
            >
              <StarIcon filled width={16} height={16} style={{ marginTop: 2 }} />
              <span>Eres miembro: obtendrás el {memberPct}% de descuento (o el del cupón, el mayor de los dos).</span>
            </div>
          )}
          {cart && (
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
              paddingTop: 12, marginTop: 12, borderTop: '1px solid var(--surface-border)',
            }}>
              <strong>Total</strong>
              <strong style={{ fontSize: 22 }}>${cart.total_price}</strong>
            </div>
          )}
        </div>

        {/* Pago */}
        <div className="glass card">
          <h3 style={{ marginTop: 0 }}>Pago con tarjeta simulada</h3>
          <p style={{ fontSize: 14 }}>Saldo disponible: <strong style={{ color: 'var(--success)' }}>${user?.balance}</strong></p>
          {error && <div className="alert alert-danger">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="card">Número de tarjeta</label>
              <input
                id="card"
                inputMode="numeric"
                placeholder="4111 1111 1111 1111"
                required
                value={cardNumber}
                onChange={(e) => setCardNumber(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="coupon">Cupón de descuento (opcional)</label>
              <input
                id="coupon"
                placeholder="BIENVENIDA20"
                value={couponCode}
                onChange={(e) => setCouponCode(e.target.value)}
              />
            </div>
            <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
              {loading ? <span className="spinner" /> : 'Confirmar pago'}
            </button>
          </form>
          <p className="text-center" style={{ fontSize: 12, marginTop: 16, marginBottom: 0, color: 'var(--text-muted)' }}>
            Se valida el formato de la tarjeta (Luhn) y se descuenta del saldo simulado. No es un pago real.
          </p>
        </div>
      </div>
    </div>
  );
}
