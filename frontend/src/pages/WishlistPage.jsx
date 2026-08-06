import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { GraduationCapIcon, HeartIcon } from '../components/Icons';

export default function WishlistPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);

  const load = () => {
    setLoading(true);
    api.get('/library/wishlist/').then(({ data }) => setItems(data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleRemove = async (courseId) => {
    await api.delete(`/library/wishlist/remove/${courseId}/`);
    load();
  };

  const handleAddToCart = async (courseId) => {
    setMessage(null);
    try {
      await api.post(`/orders/cart/add/${courseId}/`);
      setMessage({ type: 'success', text: 'Curso agregado al carrito.' });
    } catch (err) {
      setMessage({ type: 'danger', text: err.response?.data?.detail || 'No se pudo agregar al carrito.' });
    }
  };

  if (loading) return <div className="page">Cargando wishlist...</div>;

  if (items.length === 0) {
    return (
      <div className="page">
        <h1>Mi wishlist</h1>
        <div className="glass card text-center" style={{ padding: 48 }}>
          <HeartIcon width={44} height={44} strokeWidth={1.5} style={{ color: 'var(--text-muted)', marginBottom: 8 }} />
          <p>No has guardado cursos todavía.</p>
          <Link to="/" className="btn btn-primary">Explorar el catálogo</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Mi wishlist</h1>
      {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}
      <div className="grid grid-cards">
        {items.map((item) => (
          <div key={item.id} className="glass card">
            <Link to={`/cursos/${item.course.slug}`}>
              <div className="course-card-img">
                {item.course.cover_image
                  ? <img src={item.course.cover_image} alt={item.course.title} />
                  : <GraduationCapIcon width={44} height={44} strokeWidth={1.5} />}
              </div>
            </Link>
            {item.course.level_name && <span className="badge badge-accent">{item.course.level_name}</span>}
            <h3 style={{ margin: '8px 0 4px' }}>
              <Link to={`/cursos/${item.course.slug}`}>{item.course.title}</Link>
            </h3>
            {item.course.instructor_name && (
              <p style={{ margin: '0 0 8px', fontSize: 13 }}>{item.course.instructor_name}</p>
            )}
            <div className="course-card-price">
              <strong style={{ fontSize: 18 }}>${item.course.price}</strong>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => handleAddToCart(item.course.id)}>
                Al carrito
              </button>
              <button className="btn btn-secondary" onClick={() => handleRemove(item.course.id)}>Quitar</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
