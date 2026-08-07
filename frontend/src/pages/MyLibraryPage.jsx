import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import {
  FlameIcon, PlayIcon, CertificateIcon, PencilIcon, UploadIcon, ZapIcon,
} from '../components/Icons';

export default function MyLibraryPage() {
  const { user } = useAuth();
  const [enrollments, setEnrollments] = useState([]);
  const [streak, setStreak] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [completando, setCompletando] = useState(false);
  const [resumenDemo, setResumenDemo] = useState('');

  const referralLink = user ? `${window.location.origin}/registro?ref=${user.referral_code}` : '';

  const handleCopyReferral = () => {
    navigator.clipboard.writeText(referralLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const cargarCursos = () =>
    api.get('/library/my-courses/').then(({ data }) => setEnrollments(data));

  useEffect(() => {
    cargarCursos().finally(() => setLoading(false));
    api.get('/library/streak/').then(({ data }) => setStreak(data)).catch(() => {});
  }, []);

  // Atajo de la cuenta de revisión: completa todos los cursos de una vez para
  // poder ver el certificado sin recorrer las lecciones una por una.
  const handleCompletarTodo = async () => {
    setCompletando(true);
    setResumenDemo('');
    try {
      const { data } = await api.post('/library/demo/completar/');
      setResumenDemo(data.detail);
      await cargarCursos();
    } catch (err) {
      setResumenDemo(err.response?.data?.detail || 'No se pudo completar el recorrido.');
    } finally {
      setCompletando(false);
    }
  };

  const handleDownloadCertificate = async (enrollmentId, courseTitle) => {
    const { data } = await api.get(`/library/${enrollmentId}/certificate/`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `certificado-${courseTitle}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  if (loading) return <div className="page">Cargando tu biblioteca...</div>;

  return (
    <div className="page">
      <h1>Mi biblioteca</h1>

      {user?.can_autocomplete_demo && (
        <div className="aviso-demo">
          <h3>Recorrido rápido (cuenta de revisión)</h3>
          <p>
            Da por cumplidas las lecciones, el cuestionario y la entrega de todos
            tus cursos, y emite los certificados. Se generan los mismos registros
            que si los hubieras hecho a mano; las entregas quedan marcadas como
            automáticas. Solo esta cuenta puede hacerlo.
            <br />
            Cada certificado se envía por correo <strong>una sola vez</strong>, al
            emitirlo: si vuelves a pulsar el botón no se reenvía nada.
          </p>
          <button className="btn btn-primary" disabled={completando} onClick={handleCompletarTodo}>
            <ZapIcon width={16} height={16} />
            {completando ? 'Completando...' : 'Completar todos mis cursos'}
          </button>
          {resumenDemo && (
            <p style={{ marginTop: 12, marginBottom: 0, fontSize: 13 }}>{resumenDemo}</p>
          )}
        </div>
      )}

      {streak && (
        <div className="glass card" style={{ marginBottom: 16, display: 'flex', gap: 32, alignItems: 'center' }}>
          <FlameIcon width={34} height={34} style={{ color: 'var(--warning)' }} />
          <div>
            <strong style={{ fontSize: 20 }}>
              {streak.current_streak} {streak.current_streak === 1 ? 'día' : 'días'} de racha
            </strong>
            <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)' }}>
              Tu récord: {streak.longest_streak} {streak.longest_streak === 1 ? 'día' : 'días'}.
              {streak.current_streak > 0
                ? ' Completa una lección hoy para mantenerla.'
                : ' Completa una lección para empezar una racha.'}
            </p>
          </div>
        </div>
      )}

      <div className="glass card" style={{ marginBottom: 32 }}>
        <h3>Invita y gana $10</h3>
        <p>Comparte tu link — cuando alguien se registre con él, ambos reciben $10 de saldo.</p>
        <div style={{ display: 'flex', gap: 12 }}>
          <input readOnly value={referralLink} style={{ flex: 1, padding: 10, borderRadius: 8, border: '1px solid var(--surface-border)', background: 'var(--surface-2)', color: 'var(--text-primary)' }} />
          <button className="btn btn-secondary" onClick={handleCopyReferral}>{copied ? '¡Copiado!' : 'Copiar'}</button>
        </div>
      </div>

      {enrollments.length === 0 ? (
        <p>Todavía no tienes cursos. Explora el catálogo para empezar.</p>
      ) : (
        <div className="grid grid-cards">
          {enrollments.map((enrollment) => (
            <div key={enrollment.id} className="glass card">
              <h3>{enrollment.course.title}</h3>
              <p>{enrollment.course.category_name}</p>
              <div style={{ background: 'var(--surface-2)', border: '1px solid var(--surface-border)', borderRadius: 999, height: 8, overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${enrollment.progress_percentage}%`,
                    background: 'var(--accent-gradient)',
                    height: '100%',
                  }}
                />
              </div>
              <p style={{ marginTop: 8 }}>{enrollment.progress_percentage}% completado</p>
              <Link to={`/aprender/${enrollment.id}`} className="btn btn-primary btn-block" style={{ marginBottom: 8 }}>
                <PlayIcon width={16} height={16} />
                {enrollment.progress_percentage > 0 ? 'Continuar aprendiendo' : 'Empezar el curso'}
              </Link>
              {/* Qué le falta al alumno para certificarse. El orden es el del
                  recorrido: lecciones → cuestionario → entrega → certificado. */}
              {enrollment.certificate ? (
                <button
                  className="btn btn-secondary btn-block"
                  onClick={() => handleDownloadCertificate(enrollment.id, enrollment.course.slug)}
                >
                  <CertificateIcon width={16} height={16} /> Descargar certificado
                </button>
              ) : !enrollment.is_completed ? (
                <span className="badge badge-accent">En progreso</span>
              ) : enrollment.activities?.quiz?.exists && !enrollment.activities.quiz.done ? (
                <Link to={`/examen/${enrollment.course.id}`} className="btn btn-primary btn-block">
                  <PencilIcon width={16} height={16} /> Rendir el cuestionario
                </Link>
              ) : enrollment.activities?.assignment?.exists && !enrollment.activities.assignment.done ? (
                <Link to={`/aprender/${enrollment.id}`} className="btn btn-primary btn-block">
                  <UploadIcon width={16} height={16} /> Entregar el trabajo
                </Link>
              ) : (
                <span className="badge badge-accent">Actividades pendientes</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
