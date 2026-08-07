import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { SearchIcon, GraduationCapIcon, SparklesIcon } from '../components/Icons';
import Rating from '../components/Rating';
import Precio from '../components/Precio';
import PromoCarousel from '../components/PromoCarousel';

// Códigos de la tabla catálogo CourseLevel
const LEVELS = [
  { code: '', label: 'Todos los niveles' },
  { code: 'BASICO', label: 'Básico' },
  { code: 'INTERMEDIO', label: 'Intermedio' },
  { code: 'AVANZADO', label: 'Avanzado' },
];

const ORDERINGS = [
  { code: '', label: 'Relevancia' },
  { code: '-rating', label: 'Mejor calificados' },
  { code: 'price', label: 'Precio: menor a mayor' },
  { code: '-price', label: 'Precio: mayor a menor' },
  { code: '-created', label: 'Más recientes' },
];

function CourseCard({ course }) {
  return (
    <Link to={`/cursos/${course.slug}`} className="glass card">
      <div className="course-card-img">
        {course.cover_image
          ? <img src={course.cover_image} alt={course.title} />
          : <GraduationCapIcon width={44} height={44} strokeWidth={1.5} />}
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
        {course.level_name && <span className="badge badge-accent">{course.level_name}</span>}
        {course.is_best_seller && (
          <span className="badge" style={{ background: 'var(--warning-soft)', color: '#92400E' }}>Best seller</span>
        )}
      </div>
      <h3 style={{ marginBottom: 4 }}>{course.title}</h3>
      <p style={{ margin: '0 0 8px', fontSize: 13 }}>
        {(course.category?.name || course.category_name || '')}{course.instructor_name ? ` · ${course.instructor_name}` : ''}
      </p>
      {'avg_rating' in course && <Rating value={course.avg_rating} count={course.review_count} />}
      <div className="course-card-price">
        <Precio curso={course} />
      </div>
    </Link>
  );
}

export default function CatalogPage() {
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [recommended, setRecommended] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();

  const search = searchParams.get('search') || '';
  const category = searchParams.get('category') || '';
  const level = searchParams.get('level') || '';
  const priceMin = searchParams.get('price_min') || '';
  const priceMax = searchParams.get('price_max') || '';
  const ordering = searchParams.get('ordering') || '';
  const hasFilters = Boolean(search || category || level || priceMin || priceMax || ordering);

  const setParam = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next);
  };

  useEffect(() => {
    api.get('/catalog/categories/').then(({ data }) => setCategories(data)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = {};
    for (const [key, value] of searchParams.entries()) if (value) params[key] = value;
    api.get('/catalog/courses/', { params })
      .then(({ data }) => setCourses(data))
      .finally(() => setLoading(false));
  }, [searchParams]);

  useEffect(() => {
    if (!user) { setRecommended([]); return; }
    api.get('/recommendations/for-me/').then(({ data }) => setRecommended(data.results || [])).catch(() => setRecommended([]));
  }, [user]);

  return (
    <div className="page">
      {/* Hero: en el patrón marketplace la búsqueda ES el llamado a la acción */}
      <section className="catalog-hero">
        <h1>Aprende tecnología a tu ritmo</h1>
        <p>Lecciones en video, cuestionario, trabajo práctico y certificado verificable.</p>
        <form
          className="hero-search"
          onSubmit={(e) => {
            e.preventDefault();
            setParam('search', new FormData(e.target).get('q'));
          }}
        >
          <SearchIcon />
          <input
            name="q"
            type="text"
            placeholder="¿Qué quieres aprender? (Python, React, SQL...)"
            defaultValue={search}
            aria-label="Buscar cursos"
          />
          <button type="submit" className="btn btn-primary">Buscar</button>
        </form>
      </section>

      {/* El carrete de ofertas solo en la vista sin filtros: si el usuario ya
          está buscando algo concreto, estorba en vez de ayudar. */}
      {!hasFilters && <PromoCarousel />}

      {recommended.length > 0 && !hasFilters && (
        <>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <SparklesIcon style={{ color: 'var(--accent)' }} /> Recomendados para ti
          </h2>
          <div className="grid grid-cards" style={{ margin: '16px 0 36px' }}>
            {recommended.map((course) => <CourseCard key={course.id} course={course} />)}
          </div>
        </>
      )}

      <h2>Catálogo de cursos</h2>

      {/* Filtros: categoría, nivel, rango de precio y orden */}
      <div className="filter-bar">
        <label>
          Categoría
          <select value={category} onChange={(e) => setParam('category', e.target.value)}>
            <option value="">Todas</option>
            {categories.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
          </select>
        </label>
        <label>
          Nivel
          <select value={level} onChange={(e) => setParam('level', e.target.value)}>
            {LEVELS.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
          </select>
        </label>
        <label>
          Precio mín.
          <input
            className="filter-price" type="number" min="0" placeholder="$0"
            defaultValue={priceMin} onBlur={(e) => setParam('price_min', e.target.value)}
          />
        </label>
        <label>
          Precio máx.
          <input
            className="filter-price" type="number" min="0" placeholder="$100"
            defaultValue={priceMax} onBlur={(e) => setParam('price_max', e.target.value)}
          />
        </label>
        <label>
          Ordenar por
          <select value={ordering} onChange={(e) => setParam('ordering', e.target.value)}>
            {ORDERINGS.map((o) => <option key={o.code} value={o.code}>{o.label}</option>)}
          </select>
        </label>
        {hasFilters && (
          <button type="button" className="filter-clear" onClick={() => setSearchParams({})}>
            Limpiar filtros
          </button>
        )}
      </div>

      {loading ? (
        <p>Cargando cursos...</p>
      ) : courses.length === 0 ? (
        <div className="glass card text-center" style={{ padding: 40 }}>
          <p style={{ marginBottom: 12 }}>No se encontraron cursos con esos filtros.</p>
          <button type="button" className="btn btn-secondary" onClick={() => setSearchParams({})}>
            Quitar filtros
          </button>
        </div>
      ) : (
        <div className="grid grid-cards">
          {courses.map((course) => <CourseCard key={course.id} course={course} />)}
        </div>
      )}
    </div>
  );
}
