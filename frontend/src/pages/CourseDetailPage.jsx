import { useEffect, useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Stars } from '../components/Rating';
import { CheckIcon, GraduationCapIcon, HeartIcon } from '../components/Icons';

// Convierte un TextField multilínea ("- item\n- item") en una lista limpia.
function textToList(text) {
  if (!text) return [];
  return text
    .split('\n')
    .map((line) => line.replace(/^[\s\-•*]+/, '').trim())
    .filter(Boolean);
}

export default function CourseDetailPage() {
  const { slug } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [message, setMessage] = useState(null);
  const [adding, setAdding] = useState(false);
  const [wishlisting, setWishlisting] = useState(false);
  const [reviewForm, setReviewForm] = useState({ rating: 5, comment: '' });
  const [reviewError, setReviewError] = useState(null);

  const loadCourse = () => {
    api.get(`/catalog/courses/${slug}/`).then(({ data }) => {
      setCourse(data);
      api.get(`/recommendations/similar/${data.id}/`)
        .then(({ data: rec }) => setSimilar(rec.results || []))
        .catch(() => setSimilar([]));
    });
  };

  useEffect(() => { loadCourse(); }, [slug]);

  const handleAddToCart = async () => {
    if (!user) { navigate('/login'); return; }
    setAdding(true);
    setMessage(null);
    try {
      await api.post(`/orders/cart/add/${course.id}/`);
      setMessage({ type: 'success', text: 'Curso agregado al carrito.' });
    } catch (err) {
      setMessage({ type: 'danger', text: err.response?.data?.detail || 'No se pudo agregar el curso.' });
    } finally {
      setAdding(false);
    }
  };

  const handleAddToWishlist = async () => {
    if (!user) { navigate('/login'); return; }
    setWishlisting(true);
    setMessage(null);
    try {
      await api.post(`/library/wishlist/add/${course.id}/`);
      setMessage({ type: 'success', text: 'Curso agregado a tu wishlist.' });
    } catch (err) {
      setMessage({ type: 'danger', text: err.response?.data?.detail || 'No se pudo agregar a la wishlist.' });
    } finally {
      setWishlisting(false);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    setReviewError(null);
    try {
      await api.post(`/catalog/courses/${course.id}/reviews/`, reviewForm);
      setReviewForm({ rating: 5, comment: '' });
      loadCourse();
    } catch (err) {
      const detail = err.response?.data;
      setReviewError(
        typeof detail === 'object' ? Object.values(detail).flat().join(' ') : 'No se pudo enviar la reseña.'
      );
    }
  };

  if (!course) return <div className="page">Cargando...</div>;

  const outcomes = textToList(course.learning_outcomes);
  const requirements = textToList(course.requirements);
  const meta = [
    course.level_name,
    course.language,
    course.lessons?.length ? `${course.lessons.length} lecciones` : null,
  ].filter(Boolean);

  return (
    <div className="page">
      {/* --- Cabecera --- */}
      <div className="grid layout-split" style={{ gap: 28 }}>
        <div>
          <span className="badge badge-accent">{course.category?.name}</span>
          <h1 style={{ margin: '12px 0 8px' }}>{course.title}</h1>
          <p style={{ fontSize: 16, color: 'var(--text-secondary)' }}>{course.description}</p>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center', fontSize: 14, marginTop: 8 }}>
            {course.avg_rating != null && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Stars value={course.avg_rating} />
                <strong>{course.avg_rating.toFixed(1)}</strong>
                <span style={{ color: 'var(--text-muted)' }}>({course.review_count})</span>
              </span>
            )}
            {course.instructor_name && (
              <span style={{ color: 'var(--text-secondary)' }}>Instructor: <strong>{course.instructor_name}</strong></span>
            )}
          </div>

          {meta.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 14 }}>
              {meta.map((m) => (
                <span key={m} className="badge" style={{ background: 'var(--surface-2)', color: 'var(--text-secondary)' }}>{m}</span>
              ))}
            </div>
          )}

          {/* Lo que aprenderás */}
          {outcomes.length > 0 && (
            <>
              <h3 className="mt-lg">Lo que aprenderás</h3>
              <div className="glass card">
                <div className="two-col" style={{ gap: '10px 20px' }}>
                  {outcomes.map((item, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, fontSize: 14 }}>
                      <CheckIcon width={16} height={16} style={{ color: 'var(--success)', flexShrink: 0, marginTop: 2 }} />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Requisitos */}
          {requirements.length > 0 && (
            <>
              <h3 className="mt-lg">Requisitos</h3>
              <div className="glass card">
                <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                  {requirements.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
            </>
          )}

          {/* Temario */}
          <h3 className="mt-lg">Contenido del curso</h3>
          <div className="glass card">
            {course.lessons?.length ? (
              course.lessons.map((lesson, i) => (
                <div key={lesson.id} style={{
                  display: 'flex', justifyContent: 'space-between', padding: '10px 0',
                  borderBottom: i < course.lessons.length - 1 ? '1px solid var(--surface-border)' : 'none',
                }}>
                  <span style={{ fontSize: 14 }}>
                    <span style={{ color: 'var(--text-muted)', marginRight: 8 }}>{i + 1}.</span>
                    {lesson.title}
                  </span>
                  <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{lesson.duration_minutes} min</span>
                </div>
              ))
            ) : (
              <p style={{ margin: 0 }}>Este curso aún no tiene lecciones publicadas.</p>
            )}
          </div>

          {/* Reseñas */}
          <h3 className="mt-lg">Reseñas</h3>
          <div className="glass card">
            {course.reviews?.length ? (
              course.reviews.map((review) => (
                <div key={review.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--surface-border)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Stars value={review.rating} />
                    <strong style={{ fontSize: 14 }}>{review.user_name || 'Alumno'}</strong>
                  </div>
                  {review.comment && <p style={{ margin: '4px 0 0', fontSize: 14 }}>{review.comment}</p>}
                </div>
              ))
            ) : (
              <p style={{ margin: 0 }}>Aún no hay reseñas.</p>
            )}

            {user && !course.is_enrolled && (
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 12, marginBottom: 0 }}>
                Inscríbete en el curso para dejar tu reseña.
              </p>
            )}
            {user && course.is_enrolled && (
              <form onSubmit={handleReviewSubmit} className="mt-lg">
                {reviewError && <div className="alert alert-danger">{reviewError}</div>}
                <div className="field">
                  <label htmlFor="rating">Tu calificación</label>
                  <select
                    id="rating"
                    value={reviewForm.rating}
                    onChange={(e) => setReviewForm({ ...reviewForm, rating: Number(e.target.value) })}
                  >
                    {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{n} estrellas</option>)}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="comment">Comentario</label>
                  <textarea
                    id="comment"
                    rows={3}
                    value={reviewForm.comment}
                    onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })}
                  />
                </div>
                <button className="btn btn-primary" type="submit">Enviar reseña</button>
              </form>
            )}
          </div>
        </div>

        {/* --- Tarjeta de compra (sticky) --- */}
        <div className="glass sticky-side" style={{ overflow: 'hidden' }}>
          <div className="course-card-img" style={{ margin: 0, borderRadius: 0, height: 170 }}>
            {course.cover_image
              ? <img src={course.cover_image} alt={course.title} />
              : <GraduationCapIcon width={44} height={44} strokeWidth={1.5} />}
          </div>
          <div style={{ padding: 20 }}>
            <div style={{ fontSize: 30, fontWeight: 800, marginBottom: 14 }}>${course.price}</div>
            {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}
            {course.is_enrolled ? (
              <Link to="/mi-biblioteca" className="btn btn-primary btn-block">Ya estás inscrito — ir a mi biblioteca</Link>
            ) : (
              <>
                <button className="btn btn-primary btn-block" onClick={handleAddToCart} disabled={adding}>
                  {adding ? <span className="spinner" /> : 'Agregar al carrito'}
                </button>
                <button className="btn btn-secondary btn-block" style={{ marginTop: 10 }} onClick={handleAddToWishlist} disabled={wishlisting}>
                  <HeartIcon width={16} height={16} /> Guardar en wishlist
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* --- Cursos similares --- */}
      {similar.length > 0 && (
        <>
          <h3 className="mt-lg">Cursos similares</h3>
          <div className="grid grid-cards">
            {similar.map((c) => (
              <Link key={c.id} to={`/cursos/${c.slug}`} className="glass card">
                <div className="course-card-img">
                  {c.cover_image
                    ? <img src={c.cover_image} alt={c.title} />
                    : <GraduationCapIcon width={40} height={40} strokeWidth={1.5} />}
                </div>
                <h4 style={{ margin: '0 0 6px' }}>{c.title}</h4>
                <strong>${c.price}</strong>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
