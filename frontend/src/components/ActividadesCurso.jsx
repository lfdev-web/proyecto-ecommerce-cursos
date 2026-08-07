import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import {
  BookIcon, CheckCircleIcon, CertificateIcon, CircleIcon, LockIcon,
  PencilIcon, UploadIcon,
} from './Icons';

// Debe coincidir con EXTENSIONES_ENTREGA y TAMANO_MAX_ENTREGA del backend.
// El servidor vuelve a validar: esto solo evita subir en vano un archivo grande.
const EXTENSIONES = ['pdf', 'zip', 'png', 'jpg', 'jpeg', 'txt', 'md', 'docx', 'ipynb'];
const TAMANO_MAX = 5 * 1024 * 1024;

function Encabezado({ numero, titulo, hecha, bloqueada }) {
  const Icono = hecha ? CheckCircleIcon : bloqueada ? LockIcon : CircleIcon;
  const color = hecha ? 'var(--success)' : bloqueada ? 'var(--text-muted)' : 'var(--accent)';
  return (
    <div className="icon-text" style={{ alignItems: 'flex-start', gap: 10 }}>
      <Icono width={20} height={20} style={{ color, flexShrink: 0, marginTop: 2 }} />
      <div>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'block' }}>
          Actividad {numero}
        </span>
        <strong style={{ fontSize: 16 }}>{titulo}</strong>
      </div>
    </div>
  );
}

/**
 * Las dos actividades evaluadas del curso. Sin ellas, terminar un curso era
 * pulsar "completada" en cada lección; ahora el certificado exige además
 * aprobar el cuestionario y entregar el trabajo práctico.
 */
export default function ActividadesCurso({ enrollmentId, courseId, actividades, onCambio }) {
  const inputArchivo = useRef(null);
  const [archivo, setArchivo] = useState(null);
  const [comentario, setComentario] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [exito, setExito] = useState('');

  if (!actividades) return null;
  const { lessons, quiz, assignment } = actividades;

  const elegirArchivo = (e) => {
    const file = e.target.files?.[0];
    setError('');
    if (!file) return setArchivo(null);
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!EXTENSIONES.includes(ext)) {
      setArchivo(null);
      return setError(`Formato no permitido. Acepta: ${EXTENSIONES.join(', ')}.`);
    }
    if (file.size > TAMANO_MAX) {
      setArchivo(null);
      return setError('El archivo supera los 5 MB.');
    }
    setArchivo(file);
  };

  const entregar = async () => {
    if (!archivo) return setError('Adjunta el archivo de tu entrega.');
    setEnviando(true);
    setError('');
    try {
      const form = new FormData();
      form.append('file', archivo);
      form.append('comment', comentario);
      const { data } = await api.post(`/library/${enrollmentId}/entrega/`, form);
      setExito(data.certificate_issued
        ? '¡Trabajo entregado y certificado emitido! Te lo enviamos también por correo.'
        : 'Trabajo entregado.');
      setArchivo(null);
      setComentario('');
      if (inputArchivo.current) inputArchivo.current.value = '';
      onCambio?.(data.activities);
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo enviar la entrega.');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="glass card" style={{ marginTop: 24 }}>
      <h3 style={{ marginTop: 0 }}>Actividades del curso</h3>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 0 }}>
        Ver las lecciones no basta para certificarse: hay que aprobar el
        cuestionario y entregar el trabajo práctico.
      </p>

      {/* ---------- Actividad 1: cuestionario ---------- */}
      {quiz.exists && (
        <div className="actividad">
          <Encabezado numero={1} titulo="Cuestionario" hecha={quiz.done} bloqueada={!quiz.unlocked} />
          {quiz.done ? (
            <span className="badge badge-success" style={{ marginTop: 10 }}>Aprobado</span>
          ) : !quiz.unlocked ? (
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '10px 0 0' }}>
              Se habilita al completar el 100% de las lecciones (vas {lessons.progress_percentage}%).
            </p>
          ) : (
            <>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '10px 0' }}>
                Necesitas {quiz.passing_score}% para aprobar. Tienes 3 intentos.
              </p>
              <Link to={`/examen/${courseId}`} className="btn btn-primary">
                <PencilIcon width={16} height={16} /> Rendir el cuestionario
              </Link>
            </>
          )}
        </div>
      )}

      {/* ---------- Actividad 2: trabajo práctico ---------- */}
      {assignment.exists && (
        <div className="actividad">
          <Encabezado
            numero={quiz.exists ? 2 : 1}
            titulo={assignment.title}
            hecha={assignment.done}
            bloqueada={!assignment.unlocked}
          />

          <p style={{ whiteSpace: 'pre-line', marginTop: 12, fontSize: 14 }}>
            {assignment.instructions}
          </p>

          {assignment.resource_url && (
            <p className="icon-text" style={{ fontSize: 13, marginTop: 4 }}>
              <BookIcon width={16} height={16} style={{ color: 'var(--accent)' }} />
              Material de apoyo:{' '}
              <a href={assignment.resource_url} target="_blank" rel="noopener noreferrer">
                {assignment.resource_label || assignment.resource_url}
              </a>
            </p>
          )}

          {assignment.done ? (
            <div style={{ marginTop: 12 }}>
              <span className="badge badge-success">Entregado</span>
              {assignment.file_url && (
                <a href={assignment.file_url} target="_blank" rel="noopener noreferrer"
                   style={{ marginLeft: 12, fontSize: 13 }}>
                  Ver mi entrega
                </a>
              )}
              {assignment.is_auto && (
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 0 }}>
                  Generada por el recorrido rápido de demostración.
                </p>
              )}
            </div>
          ) : !assignment.unlocked ? (
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              Se habilita cuando completes todas las lecciones.
            </p>
          ) : (
            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <input
                ref={inputArchivo}
                type="file"
                onChange={elegirArchivo}
                accept={EXTENSIONES.map((e) => `.${e}`).join(',')}
                aria-label="Archivo de la entrega"
                style={{ fontSize: 13 }}
              />
              <textarea
                value={comentario}
                onChange={(e) => setComentario(e.target.value)}
                placeholder="Comentario para el docente (opcional)"
                rows={3}
                style={{
                  padding: 10, borderRadius: 8, border: '1px solid var(--surface-border)',
                  background: 'var(--surface-2)', color: 'var(--text-primary)',
                  fontFamily: 'inherit', fontSize: 14, resize: 'vertical',
                }}
              />
              <button className="btn btn-primary" disabled={enviando || !archivo} onClick={entregar}>
                <UploadIcon width={16} height={16} />
                {enviando ? 'Enviando...' : 'Entregar trabajo'}
              </button>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Máximo 5 MB. Formatos: {EXTENSIONES.join(', ')}.
              </span>
            </div>
          )}
        </div>
      )}

      {error && <p style={{ color: 'var(--danger)', fontSize: 13 }}>{error}</p>}
      {exito && <p style={{ color: 'var(--success)', fontSize: 13 }}>{exito}</p>}

      {lessons.done && quiz.done && assignment.done && (
        <Link to="/mi-biblioteca" className="btn btn-secondary btn-block" style={{ marginTop: 8 }}>
          <CertificateIcon width={16} height={16} /> Curso terminado — descargar certificado
        </Link>
      )}
    </div>
  );
}
