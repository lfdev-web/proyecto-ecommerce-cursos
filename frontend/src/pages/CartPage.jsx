import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { CartIcon, GraduationCapIcon } from '../components/Icons';

export default function CartPage() {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const loadCart = () => {
    setLoading(true);
    api.get('/orders/cart/').then(({ data }) => setCart(data)).finally(() => setLoading(false));
  };

  useEffect(() => { loadCart(); }, []);

  const handleRemove = async (courseId) => {
    await api.delete(`/orders/cart/remove/${courseId}/`);
    loadCart();
  };

  if (loading) return <div className="page">Cargando carrito...</div>;

  const items = cart?.items || [];

  if (items.length === 0) {
    return (
      <div className="page">
        <h1>Tu carrito</h1>
        <div className="glass card text-center" style={{ padding: 48 }}>
          <CartIcon width={44} height={44} strokeWidth={1.5} style={{ color: 'var(--text-muted)', marginBottom: 8 }} />
          <p>Tu carrito está vacío.</p>
          <Link to="/" className="btn btn-primary">Explorar el catálogo</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Tu carrito</h1>
      <div className="grid layout-split" style={{ gap: 24 }}>
        <div className="glass card">
          {items.map((item, i) => (
            <div key={item.id} style={{
              display: 'flex', alignItems: 'center', gap: 14, padding: '12px 0',
              borderBottom: i < items.length - 1 ? '1px solid var(--surface-border)' : 'none',
            }}>
              <div style={{
                width: 80, height: 52, borderRadius: 8, flexShrink: 0, overflow: 'hidden',
                background: 'var(--accent-soft)', color: 'var(--accent)', display: 'flex',
                alignItems: 'center', justifyContent: 'center', fontSize: 22,
              }}>
                {item.course.cover_image
                  ? <img src={item.course.cover_image} alt={item.course.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <GraduationCapIcon width={24} height={24} strokeWidth={1.5} />}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <Link to={`/cursos/${item.course.slug}`} style={{ fontWeight: 600, fontSize: 15 }}>
                  {item.course.title}
                </Link>
                {item.course.instructor_name && (
                  <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{item.course.instructor_name}</div>
                )}
              </div>
              <strong style={{ fontSize: 16 }}>${item.course.price}</strong>
              <button className="btn btn-secondary" onClick={() => handleRemove(item.course.id)}>Quitar</button>
            </div>
          ))}
        </div>

        <div className="glass card sticky-side">
          <h3 style={{ marginTop: 0 }}>Resumen</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', marginBottom: 8 }}>
            <span>{items.length} curso{items.length !== 1 ? 's' : ''}</span>
            <span>${cart.total_price}</span>
          </div>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
            paddingTop: 12, borderTop: '1px solid var(--surface-border)', marginBottom: 16,
          }}>
            <strong>Total</strong>
            <strong style={{ fontSize: 22 }}>${cart.total_price}</strong>
          </div>
          <button className="btn btn-primary btn-block" onClick={() => navigate('/checkout')}>Ir a pagar</button>
        </div>
      </div>
    </div>
  );
}
