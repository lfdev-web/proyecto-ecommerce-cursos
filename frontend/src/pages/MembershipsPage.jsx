import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { CheckIcon } from '../components/Icons';

const money = (v) => `$${Number(v ?? 0).toFixed(2)}`;

// Beneficios que muestra cada tarjeta según la familia del plan.
function planBenefits(plan) {
  if (plan.audience === 'DOCENTE') {
    const slots = plan.course_slots >= 999 ? 'Cursos ilimitados' : `Hasta ${plan.course_slots} curso${plan.course_slots === 1 ? '' : 's'} publicados`;
    return [
      slots,
      `Te llevas el ${Math.round(Number(plan.instructor_commission_pct) * 100)}% de cada venta`,
      'Panel de instructor con alumnos e ingresos',
      'Solicitud de espacios para cursos nuevos',
    ];
  }
  return [
    `${Number(plan.member_discount_pct)}% de descuento en todos los cursos`,
    'El descuento se aplica solo en cada compra',
    'Se usa el mejor descuento disponible (membresía o cupón)',
    'Cancela cuando quieras; conservas el acceso pagado',
  ];
}

function PlanCard({ plan, highlighted, onSubscribe, isCurrent }) {
  const accent = plan.audience === 'DOCENTE' ? 'var(--role-docente)' : 'var(--accent)';
  const accentSoft = plan.audience === 'DOCENTE' ? 'var(--role-docente-soft)' : 'var(--accent-soft)';
  const accentStrong = plan.audience === 'DOCENTE' ? 'var(--role-docente-strong)' : 'var(--accent-strong)';

  return (
    <div
      className="glass card"
      style={{
        display: 'flex', flexDirection: 'column',
        border: highlighted ? `2px solid ${accent}` : undefined,
      }}
    >
      {highlighted && (
        <span className="badge" style={{ background: accentSoft, color: accentStrong, alignSelf: 'flex-start', marginBottom: 8 }}>
          Más popular
        </span>
      )}
      <h3 style={{ marginBottom: 2 }}>{plan.name}</h3>
      <p style={{ fontSize: 13, margin: '0 0 10px' }}>{plan.tier_name}</p>

      <div style={{ margin: '4px 0 14px' }}>
        <span style={{ fontSize: 30, fontWeight: 800 }}>{money(plan.price)}</span>
        <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>
          {' '}/{plan.billing_cycle === 'MONTHLY' ? 'mes' : 'año'}
        </span>
      </div>

      <ul style={{ margin: '0 0 18px', paddingLeft: 0, listStyle: 'none', fontSize: 14, lineHeight: 1.9 }}>
        {planBenefits(plan).map((benefit) => (
          <li key={benefit} style={{ display: 'flex', gap: 8 }}>
            <CheckIcon width={16} height={16} style={{ color: accent, flexShrink: 0, marginTop: 5 }} />
            <span style={{ color: 'var(--text-secondary)' }}>{benefit}</span>
          </li>
        ))}
      </ul>

      {isCurrent ? (
        <span className="badge badge-success" style={{ marginTop: 'auto', textAlign: 'center', padding: 10 }}>
          Tu plan actual
        </span>
      ) : (
        <button
          className="btn btn-primary btn-block"
          style={{ marginTop: 'auto', background: accent }}
          onClick={() => onSubscribe(plan)}
        >
          Suscribirme
        </button>
      )}
    </div>
  );
}

export default function MembershipsPage() {
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();

  const [plans, setPlans] = useState([]);
  const [studentMembership, setStudentMembership] = useState(null);
  const [teacherMembership, setTeacherMembership] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [cardNumber, setCardNumber] = useState('');
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const isDocente = user?.role === 'DOCENTE' || user?.role === 'ADMIN';

  const loadMemberships = () => {
    api.get('/memberships/my-status/?audience=ALUMNO')
      .then(({ data }) => setStudentMembership(data)).catch(() => setStudentMembership(null));
    if (isDocente) {
      api.get('/memberships/my-status/?audience=DOCENTE')
        .then(({ data }) => setTeacherMembership(data)).catch(() => setTeacherMembership(null));
    }
  };

  useEffect(() => {
    api.get('/memberships/plans/').then(({ data }) => setPlans(data));
    if (user) loadMemberships();
  }, [user]);

  const handleSubscribe = async (e) => {
    e.preventDefault();
    setMessage(null);
    setLoading(true);
    try {
      await api.post('/memberships/subscribe/', { plan_id: selectedPlan.id, card_number: cardNumber });
      setMessage({ type: 'success', text: 'Membresía activada correctamente.' });
      setCardNumber('');
      setSelectedPlan(null);
      await refreshUser();
      loadMemberships();
    } catch (err) {
      const data = err.response?.data;
      setMessage({ type: 'danger', text: data?.detail || data?.card_number?.join(' ') || 'No se pudo procesar la suscripción.' });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (audience) => {
    await api.post('/memberships/cancel/', { audience });
    loadMemberships();
  };

  const onSubscribe = (plan) => (user ? setSelectedPlan(plan) : navigate('/login'));

  const studentPlans = plans.filter((p) => p.audience === 'ALUMNO');
  const teacherPlans = plans.filter((p) => p.audience === 'DOCENTE');

  const renderCurrent = (membership, audience, label) => {
    if (!membership) return null;
    return (
      <div className="glass card" style={{ marginBottom: 20 }}>
        <h3 style={{ marginTop: 0 }}>{label}</h3>
        <p style={{ margin: 0 }}>
          Plan: <strong>{membership.plan.name}</strong>{' '}
          <span className={`badge ${membership.is_currently_active ? 'badge-success' : 'badge-danger'}`}>
            {membership.is_currently_active ? 'Activa' : membership.status}
          </span>
        </p>
        <p style={{ margin: '6px 0 12px', fontSize: 14 }}>
          Vence el {new Date(membership.expires_at).toLocaleDateString('es-EC')}
        </p>
        {membership.is_currently_active && membership.status !== 'CANCELLED' && (
          <button className="btn btn-secondary" onClick={() => handleCancel(audience)}>Cancelar membresía</button>
        )}
      </div>
    );
  };

  return (
    <div className="page">
      <h1>Membresías</h1>
      <p>Elige el plan que se ajuste a lo que quieres hacer en la plataforma.</p>

      {renderCurrent(studentMembership, 'ALUMNO', 'Tu membresía de alumno')}
      {renderCurrent(teacherMembership, 'DOCENTE', 'Tu plan de docente')}

      <h2 className="mt-lg">Para aprender</h2>
      <p style={{ fontSize: 14 }}>Mientras tu membresía esté activa, obtienes descuento en cada curso que compres.</p>
      <div className="grid grid-cards">
        {studentPlans.map((plan) => (
          <PlanCard
            key={plan.id}
            plan={plan}
            highlighted={plan.tier === 'PLATA'}
            isCurrent={studentMembership?.is_currently_active && studentMembership.plan.id === plan.id}
            onSubscribe={onSubscribe}
          />
        ))}
      </div>

      {isDocente ? (
        <>
          <h2 className="mt-lg">Para enseñar</h2>
          <p style={{ fontSize: 14 }}>
            Tu plan define cuántos cursos puedes publicar y qué porcentaje de cada venta te llevas.
          </p>
          <div className="grid grid-cards">
            {teacherPlans.map((plan) => (
              <PlanCard
                key={plan.id}
                plan={plan}
                highlighted={plan.tier === 'ORO'}
                isCurrent={teacherMembership?.is_currently_active && teacherMembership.plan.id === plan.id}
                onSubscribe={onSubscribe}
              />
            ))}
          </div>
        </>
      ) : (
        <div className="glass card mt-lg">
          <h3 style={{ marginTop: 0 }}>¿Quieres enseñar en la plataforma?</h3>
          <p>
            Los planes de docente (con cupos para publicar cursos y mejor comisión) están disponibles
            para instructores aprobados. Postula primero y, una vez aprobado, podrás contratarlos.
          </p>
          <button className="btn btn-secondary" onClick={() => navigate(user ? '/ser-docente' : '/login')}>
            Postular como docente
          </button>
        </div>
      )}

      {selectedPlan && (
        <div className="glass card mt-lg container-narrow">
          <h3 style={{ marginTop: 0 }}>Confirmar suscripción</h3>
          <p style={{ fontSize: 14 }}>
            Plan <strong>{selectedPlan.name}</strong> — {money(selectedPlan.price)}<br />
            Saldo disponible: <strong style={{ color: 'var(--success)' }}>${user?.balance}</strong>
          </p>
          {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}
          <form onSubmit={handleSubscribe}>
            <div className="field">
              <label htmlFor="card">Número de tarjeta (simulado)</label>
              <input id="card" required placeholder="4111 1111 1111 1111"
                value={cardNumber} onChange={(e) => setCardNumber(e.target.value)} />
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-primary" style={{ flex: 1 }} type="submit" disabled={loading}>
                {loading ? <span className="spinner" /> : 'Confirmar pago'}
              </button>
              <button className="btn btn-secondary" type="button" onClick={() => setSelectedPlan(null)}>
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {message && !selectedPlan && (
        <div className={`alert alert-${message.type} mt-lg`}>{message.text}</div>
      )}
    </div>
  );
}
