import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { ArrowLeftIcon } from '../components/Icons';

const STATUS_BADGE = {
  PENDING: 'badge-accent',
  APPROVED: 'badge-success',
  REJECTED: 'badge-danger',
};

function SlotStat({ label, value, strong }) {
  return (
    <div className="glass card" style={{ textAlign: 'center', padding: 16 }}>
      <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)' }}>{label}</p>
      <strong style={{ fontSize: 28, color: strong ? 'var(--role-docente-strong)' : 'var(--text-primary)' }}>
        {value}
      </strong>
    </div>
  );
}

export default function TeacherSlotRequestPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({ proposed_title: '', proposed_category: '', justification: '' });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    api.get('/teacher/slot-requests/').then(({ data }) => setData(data)).catch(() => setData(null));
  };

  useEffect(() => {
    load();
    api.get('/catalog/categories/').then(({ data }) => setCategories(data)).catch(() => setCategories([]));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);
    try {
      const payload = { ...form };
      if (!payload.proposed_category) delete payload.proposed_category;
      await api.post('/teacher/slot-requests/', payload);
      setForm({ proposed_title: '', proposed_category: '', justification: '' });
      setSuccess('Solicitud enviada. El administrador la revisará pronto.');
      load();
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo enviar la solicitud.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!data) return <div className="page">Cargando espacios de curso...</div>;

  const { summary, requests } = data;
  const approvedUnused = requests.find((r) => r.status === 'APPROVED' && !r.is_consumed);

  return (
    <div className="page">
      <Link to="/panel-docente" className="icon-text" style={{ color: 'var(--role-docente-strong)', fontWeight: 600, gap: 6 }}>
        <ArrowLeftIcon width={16} height={16} /> Volver al panel
      </Link>

      <div style={{
        borderLeft: '4px solid var(--role-docente)', background: 'var(--role-docente-soft)',
        borderRadius: 10, padding: '16px 18px', margin: '12px 0 24px',
      }}>
        <span style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.04em', color: 'var(--role-docente-strong)' }}>
          Área del docente
        </span>
        <h1 style={{ margin: '4px 0 2px' }}>Espacios de curso</h1>
        <p style={{ margin: 0, fontSize: 14 }}>
          Solicita al administrador que te habilite el espacio para publicar un curso nuevo.
        </p>
      </div>

      {!summary.has_active_plan && (
        <div className="alert alert-danger">
          Necesitas un plan de docente activo para solicitar espacios.{' '}
          <Link to="/membresias" style={{ textDecoration: 'underline' }}>Ver planes de docente</Link>
        </div>
      )}

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 14, marginBottom: 24 }}>
        <SlotStat label="Plan actual" value={summary.plan_name || '—'} />
        <SlotStat label="Cupos del plan" value={summary.plan_slots >= 999 ? '∞' : summary.plan_slots} />
        <SlotStat label="Cursos creados" value={summary.courses_created} />
        <SlotStat label="Espacios disponibles" value={summary.plan_slots >= 999 ? '∞' : summary.available} strong />
      </div>

      {approvedUnused && (
        <div className="glass card" style={{ marginBottom: 24, borderLeft: '4px solid var(--role-docente)' }}>
          <h3 style={{ marginTop: 0 }}>Tienes un espacio aprobado</h3>
          <p>
            Tu solicitud para <strong>{approvedUnused.proposed_title}</strong> fue aprobada.
            Ya puedes crear el curso y armar su temario.
          </p>
          <button className="btn btn-primary" style={{ background: 'var(--role-docente)' }}
            onClick={() => navigate('/panel-docente/curso-nuevo')}>
            Crear el curso
          </button>
        </div>
      )}

      {summary.has_active_plan && summary.available > 0 && summary.pending_requests === 0 && (
        <div className="glass card" style={{ marginBottom: 24 }}>
          <h3 style={{ marginTop: 0 }}>Solicitar un espacio nuevo</h3>
          {error && <div className="alert alert-danger">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}
          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="title">Título tentativo del curso</label>
              <input id="title" required maxLength={200}
                placeholder="Ej.: Django REST Framework desde cero"
                value={form.proposed_title}
                onChange={(e) => setForm({ ...form, proposed_title: e.target.value })} />
            </div>
            <div className="field">
              <label htmlFor="category">Categoría</label>
              <select id="category" value={form.proposed_category}
                onChange={(e) => setForm({ ...form, proposed_category: e.target.value })}>
                <option value="">Selecciona una categoría</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor="justification">¿De qué trata y qué aporta al catálogo?</label>
              <textarea id="justification" required rows={4}
                placeholder="Describe el contenido, a quién va dirigido y por qué suma a la plataforma."
                value={form.justification}
                onChange={(e) => setForm({ ...form, justification: e.target.value })} />
            </div>
            <button className="btn btn-primary" style={{ background: 'var(--role-docente)' }}
              type="submit" disabled={submitting}>
              {submitting ? <span className="spinner" /> : 'Enviar solicitud'}
            </button>
          </form>
        </div>
      )}

      {summary.pending_requests > 0 && (
        <div className="alert alert-success">
          Tienes una solicitud en revisión. Espera la respuesta del administrador antes de enviar otra.
        </div>
      )}

      {summary.has_active_plan && summary.available <= 0 && summary.plan_slots < 999 && (
        <div className="glass card" style={{ marginBottom: 24 }}>
          <h3 style={{ marginTop: 0 }}>Sin cupos disponibles</h3>
          <p>Ya usaste todos los cupos de tu plan. Sube de nivel para publicar más cursos.</p>
          <Link to="/membresias" className="btn btn-primary" style={{ background: 'var(--role-docente)' }}>
            Mejorar mi plan
          </Link>
        </div>
      )}

      <h2>Mis solicitudes</h2>
      {requests.length === 0 ? (
        <div className="glass card"><p style={{ margin: 0 }}>Todavía no has solicitado ningún espacio.</p></div>
      ) : (
        <div className="glass card" style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--surface-border)', color: 'var(--text-secondary)', fontSize: 13 }}>
                <th style={{ padding: 10 }}>Curso propuesto</th>
                <th style={{ padding: 10 }}>Categoría</th>
                <th style={{ padding: 10 }}>Enviada</th>
                <th style={{ padding: 10 }}>Estado</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id} style={{ borderBottom: '1px solid var(--surface-border)', fontSize: 14 }}>
                  <td style={{ padding: 10, fontWeight: 600 }}>
                    {r.proposed_title}
                    {r.status === 'REJECTED' && r.rejection_reason && (
                      <span style={{ display: 'block', fontSize: 12, color: 'var(--danger)', fontWeight: 400 }}>
                        Motivo: {r.rejection_reason}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: 10, color: 'var(--text-secondary)' }}>{r.category_name || '—'}</td>
                  <td style={{ padding: 10 }}>{new Date(r.created_at).toLocaleDateString('es-EC')}</td>
                  <td style={{ padding: 10 }}>
                    <span className={`badge ${STATUS_BADGE[r.status] || 'badge-accent'}`}>{r.status_name}</span>
                    {r.is_consumed && <span style={{ display: 'block', fontSize: 12, color: 'var(--text-muted)' }}>Usado</span>}
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
