import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

const STATUS_UI = {
  PENDING: {
    badge: 'badge-accent',
    title: 'Tu solicitud está en revisión',
    text: 'Un administrador revisará tus datos y documentos. Te avisaremos cuando haya una decisión.',
  },
  APPROVED: {
    badge: 'badge-success',
    title: '¡Felicidades, ya eres docente!',
    text: 'Tu solicitud fue aprobada. Ya puedes acceder a tu panel de instructor.',
  },
  REJECTED: {
    badge: 'badge-danger',
    title: 'Tu solicitud fue rechazada',
    text: 'Puedes revisar el motivo y volver a postular con la información corregida.',
  },
};

export default function TeacherApplicationPage() {
  const { user } = useAuth();
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ headline: '', bio: '' });
  const [idDoc, setIdDoc] = useState(null);
  const [credDoc, setCredDoc] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const loadApplication = () => {
    api.get('/auth/teacher-application/')
      .then(({ data }) => setApplication(data.has_application ? data : null))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadApplication(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!idDoc) { setError('La cédula es obligatoria.'); return; }
    setSubmitting(true);

    const payload = new FormData();
    payload.append('headline', form.headline);
    payload.append('bio', form.bio);
    payload.append('id_document', idDoc);
    if (credDoc) payload.append('credentials_document', credDoc);

    try {
      await api.post('/auth/teacher-application/', payload);
      setShowForm(false);
      loadApplication();
    } catch (err) {
      const data = err.response?.data;
      setError(
        data?.detail
        || data?.id_document?.join(' ')
        || 'No se pudo enviar la solicitud. Revisa los datos e intenta de nuevo.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="page">Cargando...</div>;

  // Ya es docente o admin: no necesita postular.
  if (user && (user.role === 'DOCENTE' || user.role === 'ADMIN')) {
    return (
      <div className="page container-narrow">
        <div className="glass card text-center">
          <h2>Ya eres docente</h2>
          <p>Tienes acceso al panel de instructor.</p>
          <Link to="/panel-docente" className="btn btn-primary">Ir a mi panel docente</Link>
        </div>
      </div>
    );
  }

  const status = application?.status;
  const canApply = !application || status === 'REJECTED';
  const ui = status ? STATUS_UI[status] : null;

  return (
    <div className="page container-narrow">
      <h1>Enseña en la plataforma</h1>
      <p>
        Comparte lo que sabes y genera ingresos con cada venta (te llevas el 70% de cada curso).
        Postula, sube tu cédula y, si quieres, tus certificados; un administrador revisará tu solicitud.
      </p>

      {application && ui && !showForm && (
        <div className="glass card">
          <span className={`badge ${ui.badge}`}>{application.status_name}</span>
          <h3 style={{ marginTop: 12 }}>{ui.title}</h3>
          <p>{ui.text}</p>

          {status === 'REJECTED' && application.rejection_reason && (
            <div className="alert alert-danger">
              <strong>Motivo:</strong> {application.rejection_reason}
            </div>
          )}

          {status === 'APPROVED' && (
            <Link to="/panel-docente" className="btn btn-primary">Ir a mi panel docente</Link>
          )}
          {status === 'REJECTED' && (
            <button className="btn btn-primary" onClick={() => setShowForm(true)}>Volver a postular</button>
          )}
        </div>
      )}

      {canApply && (showForm || !application) && (
        <form className="glass card" onSubmit={handleSubmit}>
          {error && <div className="alert alert-danger">{error}</div>}

          <div className="field">
            <label htmlFor="headline">Especialidad o titular profesional</label>
            <input
              id="headline"
              required
              maxLength={150}
              placeholder="Ej.: Ingeniero de software · 8 años enseñando Python"
              value={form.headline}
              onChange={(e) => setForm({ ...form, headline: e.target.value })}
            />
          </div>

          <div className="field">
            <label htmlFor="bio">Experiencia y motivación</label>
            <textarea
              id="bio"
              required
              rows={5}
              placeholder="Cuéntanos tu experiencia docente y qué cursos te gustaría dictar."
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
            />
          </div>

          <div className="field">
            <label htmlFor="idDoc">Cédula (obligatoria)</label>
            <input id="idDoc" type="file" required
              accept="image/*,application/pdf"
              onChange={(e) => setIdDoc(e.target.files[0] || null)} />
          </div>

          <div className="field">
            <label htmlFor="credDoc">Certificados (opcional)</label>
            <input id="credDoc" type="file"
              accept="image/*,application/pdf"
              onChange={(e) => setCredDoc(e.target.files[0] || null)} />
          </div>

          <button className="btn btn-primary btn-block" type="submit" disabled={submitting}>
            {submitting ? <span className="spinner" /> : 'Enviar solicitud'}
          </button>
        </form>
      )}
    </div>
  );
}
