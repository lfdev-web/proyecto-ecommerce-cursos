import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

const money = (v) => `$${Number(v ?? 0).toLocaleString('es-EC', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const EVENT_LABELS = {
  COURSE_VIEW: 'Vista de curso',
  CATEGORY_VIEW: 'Vista de categoría',
  SEARCH: 'Búsqueda',
  CART_ADD: 'Agregado al carrito',
  CART_REMOVE: 'Quitado del carrito',
  CHECKOUT_START: 'Checkout iniciado',
  PURCHASE: 'Compra completada',
  WISHLIST_ADD: 'Agregado a wishlist',
  VIDEO_PLAY: 'Video reproducido',
  VIDEO_PAUSE: 'Video pausado',
};

const FUNNEL_STAGES = [
  { key: 'VIEW', label: 'Vieron un curso' },
  { key: 'CART', label: 'Agregaron al carrito' },
  { key: 'CHECKOUT', label: 'Iniciaron checkout' },
  { key: 'PURCHASE', label: 'Compraron' },
];

function StatTile({ label, value }) {
  return (
    <div className="glass card" style={{ textAlign: 'center', padding: 16 }}>
      <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)' }}>{label}</p>
      <strong style={{ fontSize: 28, color: 'var(--role-admin-strong)' }}>{value}</strong>
    </div>
  );
}

// Barra horizontal de una sola serie, con la identidad violeta del admin.
function HBarRow({ label, value, max }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="hbar-row" title={`${label}: ${value.toLocaleString('es-EC')}`}>
      <span className="hbar-label">{label}</span>
      <div style={{ background: 'var(--surface-2)', border: '1px solid var(--surface-border)', borderRadius: 4, height: 14 }}>
        <div style={{
          width: `${pct}%`, height: '100%', minWidth: value > 0 ? 4 : 0,
          background: 'var(--role-admin)', borderRadius: 4,
        }} />
      </div>
      <span style={{ fontSize: 13, fontVariantNumeric: 'tabular-nums' }}>{value.toLocaleString('es-EC')}</span>
    </div>
  );
}

export default function AnalyticsDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/analytics/dashboard/')
      .then(({ data }) => setData(data))
      .catch((err) => setError(err.response?.status === 403
        ? 'Este dashboard es solo para administradores.'
        : 'No se pudo cargar el dashboard.'));
  }, []);

  if (user && user.role !== 'ADMIN') {
    return (
      <div className="page">
        <div className="glass card">
          <p>Este dashboard es solo para administradores.</p>
          <Link to="/" className="btn btn-secondary">Ir al catálogo</Link>
        </div>
      </div>
    );
  }
  if (error) return <div className="page"><div className="glass card"><p>{error}</p></div></div>;
  if (!data) return <div className="page">Cargando dashboard...</div>;

  const events = data.events_by_type.map((e) => ({
    label: EVENT_LABELS[e.event_type] || e.event_type,
    value: e.total,
  }));
  const maxEvent = Math.max(...events.map((e) => e.value), 1);
  const funnelMax = Math.max(...FUNNEL_STAGES.map((s) => data.funnel_counts[s.key] || 0), 1);
  const maxViews = Math.max(...data.top_viewed_courses.map((c) => c.views), 1);

  return (
    <div className="page">
      <div style={{
        borderLeft: '4px solid var(--role-admin)', background: 'var(--role-admin-soft)',
        borderRadius: 10, padding: '16px 18px', marginBottom: 24,
      }}>
        <span style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.04em', color: 'var(--role-admin-strong)' }}>
          Administración
        </span>
        <h1 style={{ margin: '4px 0 2px' }}>Dashboard de analítica</h1>
        <p style={{ margin: 0, fontSize: 14 }}>Actividad de los últimos 30 días.</p>
      </div>

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 14, marginBottom: 28 }}>
        <StatTile label="Alumnos totales" value={data.kpis.total_students.toLocaleString('es-EC')} />
        <StatTile label="Alumnos nuevos (30d)" value={data.kpis.new_students_30d.toLocaleString('es-EC')} />
        <StatTile label="Órdenes (30d)" value={data.kpis.orders_30d.toLocaleString('es-EC')} />
        <StatTile label="Ingresos (30d)" value={money(data.kpis.revenue_30d)} />
        <StatTile label="Ingresos históricos" value={money(data.kpis.total_revenue)} />
        <StatTile label="Certificados emitidos" value={data.kpis.certificates_issued.toLocaleString('es-EC')} />
      </div>

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 20, alignItems: 'start' }}>
        <div className="glass card">
          <h3 style={{ marginTop: 0 }}>Funnel de conversión</h3>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: -6 }}>Sesiones únicas por etapa</p>
          {FUNNEL_STAGES.map((stage, i) => {
            const count = data.funnel_counts[stage.key] || 0;
            const rateKey = i > 0 ? `${FUNNEL_STAGES[i - 1].key}_to_${stage.key}` : null;
            return (
              <div key={stage.key} style={{ marginBottom: 10 }}>
                <HBarRow label={stage.label} value={count} max={funnelMax} />
                {rateKey && data.conversion_rates[rateKey] && (
                  <p style={{ margin: '-4px 0 0 190px', fontSize: 12, color: 'var(--text-secondary)' }}>
                    ↳ conversión: {data.conversion_rates[rateKey]}
                  </p>
                )}
              </div>
            );
          })}
        </div>

        <div className="glass card">
          <h3 style={{ marginTop: 0 }}>Eventos por tipo</h3>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: -6 }}>Total de eventos registrados</p>
          {events.map((e) => <HBarRow key={e.label} label={e.label} value={e.value} max={maxEvent} />)}
          {events.length === 0 && <p>Sin eventos en los últimos 30 días.</p>}
        </div>

        <div className="glass card">
          <h3 style={{ marginTop: 0 }}>Cursos más vistos</h3>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: -6 }}>Vistas de la página del curso</p>
          {data.top_viewed_courses.map((c) => (
            <HBarRow key={c.course_id ?? c.title} label={c.title} value={c.views} max={maxViews} />
          ))}
          {data.top_viewed_courses.length === 0 && <p>Sin vistas registradas.</p>}
        </div>
      </div>
    </div>
  );
}
