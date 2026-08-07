import { useCallback, useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import ActividadesCurso from '../components/ActividadesCurso';
import { CheckCircleIcon, CheckIcon, CircleIcon, VideoIcon } from '../components/Icons';

// Convierte links de YouTube en su versión embebible; otros links se devuelven igual.
function toEmbedUrl(url) {
  if (!url) return null;
  const youtube = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})/);
  if (youtube) return `https://www.youtube.com/embed/${youtube[1]}`;
  return url;
}

export default function CoursePlayerPage() {
  const { enrollmentId } = useParams();

  const [syllabus, setSyllabus] = useState(null);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [loadingLesson, setLoadingLesson] = useState(false);
  const [marking, setMarking] = useState(false);
  const [error, setError] = useState('');

  const loadSyllabus = useCallback(() => {
    return api.get(`/library/${enrollmentId}/lessons/`)
      .then(({ data }) => { setSyllabus(data); return data; })
      .catch(() => setError('No se pudo cargar el curso. ¿Está en tu biblioteca?'));
  }, [enrollmentId]);

  const openLesson = useCallback((lessonId) => {
    setLoadingLesson(true);
    api.get(`/library/${enrollmentId}/lessons/${lessonId}/content/`)
      .then(({ data }) => setCurrentLesson(data))
      .catch(() => setError('No se pudo cargar la lección.'))
      .finally(() => setLoadingLesson(false));
  }, [enrollmentId]);

  useEffect(() => {
    loadSyllabus().then((data) => {
      if (!data?.lessons?.length) return;
      // Abrir la primera lección pendiente (o la primera si ya terminó todo)
      const next = data.lessons.find((l) => !l.is_completed) || data.lessons[0];
      openLesson(next.id);
    });
  }, [loadSyllabus, openLesson]);

  const handleMarkCompleted = async () => {
    setMarking(true);
    try {
      await api.post(`/library/${enrollmentId}/progress/${currentLesson.id}/`, {
        is_completed: true,
        watch_percentage: 100.0,
      });
      const data = await loadSyllabus();
      setCurrentLesson({ ...currentLesson, is_completed: true });
      // Avanzar automáticamente a la siguiente lección pendiente
      const next = data?.lessons?.find((l) => !l.is_completed);
      if (next) openLesson(next.id);
    } catch {
      setError('No se pudo guardar el progreso.');
    } finally {
      setMarking(false);
    }
  };

  if (error) {
    return (
      <div className="page">
        <div className="glass card">
          <p>{error}</p>
          <Link to="/mi-biblioteca" className="btn btn-secondary">Volver a mi biblioteca</Link>
        </div>
      </div>
    );
  }
  if (!syllabus) return <div className="page">Cargando curso...</div>;

  const embedUrl = toEmbedUrl(currentLesson?.video_url);

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <h1 style={{ margin: 0 }}>{syllabus.course_title}</h1>
        <span className="badge badge-accent">{syllabus.progress_percentage}% completado</span>
      </div>

      <div className="grid layout-split-wide" style={{ gap: 24, marginTop: 24 }}>
        {/* Lección actual */}
        <div className="glass card">
          {loadingLesson || !currentLesson ? (
            <p>Cargando lección...</p>
          ) : (
            <>
              <h2 style={{ marginTop: 0 }}>{currentLesson.title}</h2>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                Lección {currentLesson.order} · {currentLesson.duration_minutes} min
              </p>

              {embedUrl ? (
                <>
                  <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0, borderRadius: 12, overflow: 'hidden' }}>
                    <iframe
                      src={embedUrl}
                      title={currentLesson.title}
                      style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 0 }}
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  </div>
                  {/* Atribución: el video es de su autor original, no de la
                      plataforma. El enlace permite verificarlo en su canal. */}
                  <p className="video-atribucion">
                    Video alojado en YouTube y propiedad de su autor original.{' '}
                    <a href={currentLesson.video_url} target="_blank" rel="noopener noreferrer">
                      Ver en YouTube
                    </a>
                  </p>
                </>
              ) : (
                <div
                  className="icon-text"
                  style={{
                    padding: 24, borderRadius: 12, background: 'var(--surface-2)',
                    color: 'var(--text-secondary)', justifyContent: 'center',
                  }}
                >
                  <VideoIcon width={20} height={20} />
                  Esta lección no tiene video — revisa el material de lectura.
                </div>
              )}

              {currentLesson.content && (
                <p style={{ marginTop: 16, whiteSpace: 'pre-line' }}>{currentLesson.content}</p>
              )}

              {currentLesson.is_completed ? (
                <span className="badge badge-success icon-text" style={{ marginTop: 16 }}>
                  <CheckIcon width={15} height={15} /> Lección completada
                </span>
              ) : (
                <button className="btn btn-primary btn-block" style={{ marginTop: 16 }} disabled={marking} onClick={handleMarkCompleted}>
                  {marking ? 'Guardando...' : 'Marcar como completada y continuar'}
                </button>
              )}
            </>
          )}
        </div>

        {/* Temario */}
        <div className="glass card">
          <h3 style={{ marginTop: 0 }}>Contenido</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {syllabus.lessons.map((lesson) => (
              <button
                key={lesson.id}
                onClick={() => openLesson(lesson.id)}
                style={{
                  textAlign: 'left', padding: '10px 12px', borderRadius: 10, cursor: 'pointer',
                  border: currentLesson?.id === lesson.id ? '1px solid var(--accent)' : '1px solid var(--surface-border)',
                  background: currentLesson?.id === lesson.id ? 'var(--accent-soft)' : 'var(--surface-2)',
                  color: 'var(--text-primary)', fontSize: 14, fontFamily: 'inherit',
                }}
              >
                <span className="icon-text">
                  {lesson.is_completed
                    ? <CheckCircleIcon width={16} height={16} style={{ color: 'var(--success)' }} />
                    : <CircleIcon width={16} height={16} style={{ color: 'var(--text-muted)' }} />}
                  {lesson.order}. {lesson.title}
                </span>
                <span style={{ display: 'block', fontSize: 12, color: 'var(--text-secondary)' }}>
                  {lesson.duration_minutes} min
                </span>
              </button>
            ))}
          </div>

          {syllabus.is_completed && (
            <p className="badge badge-success" style={{ marginTop: 16, display: 'block', textAlign: 'center' }}>
              Todas las lecciones vistas
            </p>
          )}
        </div>
      </div>

      {/* Las dos actividades evaluadas: sin ellas no hay certificado */}
      <ActividadesCurso
        enrollmentId={enrollmentId}
        courseId={syllabus.course_id}
        actividades={syllabus.activities}
        onCambio={(activities) => setSyllabus((prev) => ({ ...prev, activities }))}
      />
    </div>
  );
}
