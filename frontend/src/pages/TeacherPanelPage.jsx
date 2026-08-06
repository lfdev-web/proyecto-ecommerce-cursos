import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { StarIcon } from '../components/Icons';

const money = (v) => `$${Number(v ?? 0).toFixed(2)}`;

// Calificación compacta para las tablas del panel (— si el curso aún no tiene reseñas).
function RatingCell({ value }) {
  if (!value) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
  return (
    <span className="icon-text" style={{ gap: 4 }}>
      <StarIcon filled width={15} height={15} style={{ color: 'var(--warning)' }} />
      {Number(value).toFixed(1)}
    </span>
  );
}

// Encabezado con identidad de rol docente (verde).
function DocenteHeader({ title, subtitle }) {
  return (
    <div style={{
      borderLeft: '4px solid var(--role-docente)', background: 'var(--role-docente-soft)',
      borderRadius: 10, padding: '16px 18px', marginBottom: 24,
    }}>
      <span style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.04em', color: 'var(--role-docente-strong)' }}>
        Área del docente
      </span>
      <h1 style={{ margin: '4px 0 2px' }}>{title}</h1>
      {subtitle && <p style={{ margin: 0, fontSize: 14 }}>{subtitle}</p>}
    </div>
  );
}

function Kpi({ label, value }) {
  return (
    <div className="glass card" style={{ textAlign: 'center' }}>
      <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)' }}>{label}</p>
      <strong style={{ fontSize: 30, color: 'var(--role-docente-strong)' }}>{value}</strong>
    </div>
  );
}

const STATUS_BADGE = {
  DRAFT: 'badge-accent',
  IN_REVIEW: 'badge-accent',
  PUBLISHED: 'badge-success',
  REJECTED: 'badge-danger',
};

export default function TeacherPanelPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [courses, setCourses] = useState([]);
  const [slots, setSlots] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.get('/teacher/summary/'), api.get('/teacher/courses/')])
      .then(([s, c]) => { setSummary(s.data); setCourses(c.data); })
      .finally(() => setLoading(false));
    api.get('/teacher/slot-requests/')
      .then(({ data }) => setSlots(data))
      .catch(() => setSlots(null));
  }, []);

  if (user && user.role !== 'DOCENTE' && user.role !== 'ADMIN') {
    return (
      <div className="page">
        <div className="glass card">
          <p>Este panel es solo para docentes.</p>
          <Link to="/" className="btn btn-secondary">Ir al catálogo</Link>
        </div>
      </div>
    );
  }

  if (loading) return <div className="page">Cargando panel docente...</div>;

  return (
    <div className="page">
      <DocenteHeader
        title="Panel del docente"
        subtitle="Tus cursos, alumnos e ingresos. La creación de cursos nuevos se gestiona con el administrador de la plataforma."
      />

      {summary && (
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 32 }}>
          <Kpi label="Cursos publicados" value={summary.total_courses} />
          <Kpi label="Alumnos inscritos" value={summary.total_students} />
          <Kpi
            label={`Ingresos totales${summary.commission_rate ? ` (${Math.round(Number(summary.commission_rate) * 100)}%)` : ''}`}
            value={money(summary.total_earnings)}
          />
          <Kpi label="Últimos 30 días" value={money(summary.earnings_last_30_days)} />
          <Kpi
            label="Calificación promedio"
            value={
              summary.average_rating ? (
                <span className="icon-text" style={{ justifyContent: 'center', gap: 6 }}>
                  <StarIcon filled width={24} height={24} style={{ color: 'var(--warning)' }} />
                  {Number(summary.average_rating).toFixed(1)}
                </span>
              ) : '—'
            }
          />
        </div>
      )}

      {/* Espacios de curso del plan */}
      {slots && (
        <div className="glass card" style={{ marginBottom: 28, borderLeft: '4px solid var(--role-docente)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h3 style={{ margin: '0 0 4px' }}>Espacios para publicar</h3>
              <p style={{ margin: 0, fontSize: 14 }}>
                {slots.summary.has_active_plan ? (
                  <>
                    Plan <strong>{slots.summary.plan_name}</strong> —{' '}
                    {slots.summary.plan_slots >= 999
                      ? 'cursos ilimitados'
                      : `${slots.summary.courses_created} de ${slots.summary.plan_slots} cupos usados`}
                    {slots.summary.approved_unused > 0 && ' · tienes un espacio aprobado sin usar'}
                  </>
                ) : (
                  'No tienes un plan de docente activo. Contrata uno para publicar cursos.'
                )}
              </p>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              {slots.summary.approved_unused > 0 && (
                <Link to="/panel-docente/curso-nuevo" className="btn btn-primary" style={{ background: 'var(--role-docente)' }}>
                  Crear curso
                </Link>
              )}
              <Link to="/panel-docente/espacios" className="btn btn-secondary">Gestionar espacios</Link>
            </div>
          </div>
        </div>
      )}

      <h2>Mis cursos</h2>
      {courses.length === 0 ? (
        <div className="glass card">
          <p style={{ margin: 0 }}>
            Aún no tienes cursos. Solicita un espacio al administrador para publicar tu primer curso.
          </p>
        </div>
      ) : (
        <div className="glass card" style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--surface-border)', color: 'var(--text-secondary)', fontSize: 13 }}>
                <th style={{ padding: 10 }}>Curso</th>
                <th style={{ padding: 10 }}>Estado</th>
                <th style={{ padding: 10 }}>Categoría</th>
                <th style={{ padding: 10 }}>Precio</th>
                <th style={{ padding: 10 }}>Alumnos</th>
                <th style={{ padding: 10 }}>Calificación</th>
                <th style={{ padding: 10 }}>Ingresos</th>
                <th style={{ padding: 10 }}></th>
              </tr>
            </thead>
            <tbody>
              {courses.map((course) => (
                <tr key={course.id} style={{ borderBottom: '1px solid var(--surface-border)', fontSize: 14 }}>
                  <td style={{ padding: 10, fontWeight: 600 }}>
                    {course.title}{' '}
                    {course.is_best_seller && (
                      <span className="badge" style={{ background: 'var(--warning-soft)', color: '#92400E' }}>Best seller</span>
                    )}
                  </td>
                  <td style={{ padding: 10 }}>
                    <span className={`badge ${STATUS_BADGE[course.status] || 'badge-accent'}`}>
                      {course.status_name || '—'}
                    </span>
                  </td>
                  <td style={{ padding: 10, color: 'var(--text-secondary)' }}>{course.category_name}</td>
                  <td style={{ padding: 10 }}>{money(course.price)}</td>
                  <td style={{ padding: 10 }}>{course.students_count}</td>
                  <td style={{ padding: 10 }}><RatingCell value={course.average_rating} /></td>
                  <td style={{ padding: 10, fontWeight: 600, color: 'var(--role-docente-strong)' }}>{money(course.total_earned)}</td>
                  <td style={{ padding: 10, whiteSpace: 'nowrap' }}>
                    <Link to={`/panel-docente/curso/${course.id}/editar`} className="btn btn-secondary"
                      style={{ marginRight: 8 }}>
                      Editar
                    </Link>
                    <Link to={`/panel-docente/curso/${course.id}`} className="btn btn-secondary">Ver alumnos</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
