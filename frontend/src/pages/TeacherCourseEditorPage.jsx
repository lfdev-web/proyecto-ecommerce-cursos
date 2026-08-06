import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import api from '../api/client';
import { ArrowLeftIcon } from '../components/Icons';

const LEVELS = [
  { code: 'BASICO', name: 'Básico' },
  { code: 'INTERMEDIO', name: 'Intermedio' },
  { code: 'AVANZADO', name: 'Avanzado' },
];

const EMPTY_COURSE = {
  title: '', description: '', price: '', category: '', level: 'BASICO',
  language: 'Español', cover_image: '', requirements: '', learning_outcomes: '',
};

const EMPTY_LESSON = { title: '', duration_minutes: 10, video_url: '', content: '' };

const STATUS_BADGE = {
  DRAFT: 'badge-accent',
  IN_REVIEW: 'badge-accent',
  PUBLISHED: 'badge-success',
  REJECTED: 'badge-danger',
};

export default function TeacherCourseEditorPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const isNew = !courseId;

  const [course, setCourse] = useState(EMPTY_COURSE);
  const [lessons, setLessons] = useState([]);
  const [categories, setCategories] = useState([]);
  const [lessonForm, setLessonForm] = useState(EMPTY_LESSON);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);

  useEffect(() => {
    api.get('/catalog/categories/').then(({ data }) => setCategories(data)).catch(() => setCategories([]));
    if (!isNew) {
      api.get(`/teacher/courses/${courseId}/`)
        .then(({ data }) => { setCourse(data.course); setLessons(data.lessons); })
        .catch(() => setError('No se pudo cargar el curso.'))
        .finally(() => setLoading(false));
    }
  }, [courseId, isNew]);

  const editable = isNew || course.status === 'DRAFT' || course.status === 'REJECTED';

  const handleSaveCourse = async (e) => {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setSaving(true);
    try {
      const payload = { ...course };
      if (!payload.cover_image) delete payload.cover_image;
      if (isNew) {
        const { data } = await api.post('/teacher/courses/create/', payload);
        navigate(`/panel-docente/curso/${data.id}/editar`, { replace: true });
      } else {
        const { data } = await api.patch(`/teacher/courses/${courseId}/`, payload);
        setCourse(data);
        setNotice('Cambios guardados.');
      }
    } catch (err) {
      const detail = err.response?.data;
      setError(
        detail?.detail
        || (typeof detail === 'object' ? Object.values(detail).flat().join(' ') : null)
        || 'No se pudo guardar el curso.'
      );
    } finally {
      setSaving(false);
    }
  };

  const handleAddLesson = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const { data } = await api.post(`/teacher/courses/${courseId}/lessons/`, lessonForm);
      setLessons([...lessons, data]);
      setLessonForm(EMPTY_LESSON);
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo agregar la lección.');
    }
  };

  const handleDeleteLesson = async (lessonId) => {
    try {
      await api.delete(`/teacher/courses/${courseId}/lessons/${lessonId}/`);
      setLessons(lessons.filter((l) => l.id !== lessonId));
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo eliminar la lección.');
    }
  };

  const handleSubmitForReview = async () => {
    setError(null);
    try {
      await api.post(`/teacher/courses/${courseId}/submit/`);
      const { data } = await api.get(`/teacher/courses/${courseId}/`);
      setCourse(data.course);
      setNotice('Curso enviado a revisión. El administrador lo revisará antes de publicarlo.');
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo enviar a revisión.');
    }
  };

  if (loading) return <div className="page">Cargando curso...</div>;

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
        <h1 style={{ margin: '4px 0 2px' }}>{isNew ? 'Crear curso' : course.title}</h1>
        {!isNew && (
          <span className={`badge ${STATUS_BADGE[course.status] || 'badge-accent'}`}>{course.status_name}</span>
        )}
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      {!isNew && course.status === 'REJECTED' && course.review_notes && (
        <div className="alert alert-danger">
          <strong>Observaciones del administrador:</strong> {course.review_notes}
        </div>
      )}
      {!isNew && course.status === 'IN_REVIEW' && (
        <div className="alert alert-success">
          Tu curso está en revisión. No se puede editar hasta que el administrador responda.
        </div>
      )}

      <div className={`grid${isNew ? '' : ' layout-split'}`} style={{ gap: 24 }}>
        {/* Datos del curso */}
        <form className="glass card" onSubmit={handleSaveCourse}>
          <h3 style={{ marginTop: 0 }}>Información del curso</h3>

          <div className="field">
            <label htmlFor="title">Título</label>
            <input id="title" required maxLength={200} disabled={!editable}
              value={course.title} onChange={(e) => setCourse({ ...course, title: e.target.value })} />
          </div>

          <div className="field">
            <label htmlFor="description">Descripción</label>
            <textarea id="description" required rows={4} disabled={!editable}
              value={course.description} onChange={(e) => setCourse({ ...course, description: e.target.value })} />
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <div className="field" style={{ flex: 1 }}>
              <label htmlFor="price">Precio (USD)</label>
              <input id="price" type="number" step="0.01" min="0" required disabled={!editable}
                value={course.price} onChange={(e) => setCourse({ ...course, price: e.target.value })} />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label htmlFor="category">Categoría</label>
              <select id="category" required disabled={!editable}
                value={course.category || ''} onChange={(e) => setCourse({ ...course, category: e.target.value })}>
                <option value="">Selecciona</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <div className="field" style={{ flex: 1 }}>
              <label htmlFor="level">Nivel</label>
              <select id="level" disabled={!editable}
                value={course.level || 'BASICO'} onChange={(e) => setCourse({ ...course, level: e.target.value })}>
                {LEVELS.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
              </select>
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label htmlFor="language">Idioma</label>
              <input id="language" disabled={!editable}
                value={course.language} onChange={(e) => setCourse({ ...course, language: e.target.value })} />
            </div>
          </div>

          <div className="field">
            <label htmlFor="cover">Imagen de portada (URL)</label>
            <input id="cover" type="url" placeholder="https://..." disabled={!editable}
              value={course.cover_image || ''} onChange={(e) => setCourse({ ...course, cover_image: e.target.value })} />
          </div>

          <div className="field">
            <label htmlFor="outcomes">Lo que aprenderán (una línea por punto)</label>
            <textarea id="outcomes" rows={4} disabled={!editable}
              placeholder={'Crear APIs REST con Django\nAutenticar usuarios con JWT'}
              value={course.learning_outcomes || ''}
              onChange={(e) => setCourse({ ...course, learning_outcomes: e.target.value })} />
          </div>

          <div className="field">
            <label htmlFor="requirements">Requisitos (una línea por punto)</label>
            <textarea id="requirements" rows={3} disabled={!editable}
              placeholder={'Conocimientos básicos de Python\nComputadora con internet'}
              value={course.requirements || ''}
              onChange={(e) => setCourse({ ...course, requirements: e.target.value })} />
          </div>

          {editable && (
            <button className="btn btn-primary btn-block" style={{ background: 'var(--role-docente)' }}
              type="submit" disabled={saving}>
              {saving ? <span className="spinner" /> : (isNew ? 'Crear curso y continuar' : 'Guardar cambios')}
            </button>
          )}
        </form>

        {/* Temario */}
        {!isNew && (
          <div className="glass card">
            <h3 style={{ marginTop: 0 }}>Temario ({lessons.length})</h3>

            {lessons.length === 0 && (
              <p style={{ fontSize: 14 }}>Aún no hay lecciones. Agrega al menos una para poder enviar el curso.</p>
            )}

            {lessons.map((lesson) => (
              <div key={lesson.id} style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0',
                borderBottom: '1px solid var(--surface-border)',
              }}>
                <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>{lesson.order}.</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{lesson.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{lesson.duration_minutes} min</div>
                </div>
                {editable && (
                  <button className="btn btn-secondary" onClick={() => handleDeleteLesson(lesson.id)}>Quitar</button>
                )}
              </div>
            ))}

            {editable && (
              <form onSubmit={handleAddLesson} style={{ marginTop: 16 }}>
                <h4 style={{ margin: '0 0 10px' }}>Agregar lección</h4>
                <div className="field">
                  <label htmlFor="ltitle">Título</label>
                  <input id="ltitle" required value={lessonForm.title}
                    onChange={(e) => setLessonForm({ ...lessonForm, title: e.target.value })} />
                </div>
                <div className="field">
                  <label htmlFor="lduration">Duración (minutos)</label>
                  <input id="lduration" type="number" min="1" required value={lessonForm.duration_minutes}
                    onChange={(e) => setLessonForm({ ...lessonForm, duration_minutes: e.target.value })} />
                </div>
                <div className="field">
                  <label htmlFor="lvideo">Video (URL de YouTube)</label>
                  <input id="lvideo" type="url" placeholder="https://youtube.com/watch?v=..."
                    value={lessonForm.video_url}
                    onChange={(e) => setLessonForm({ ...lessonForm, video_url: e.target.value })} />
                </div>
                <div className="field">
                  <label htmlFor="lcontent">Material de lectura</label>
                  <textarea id="lcontent" rows={3} value={lessonForm.content}
                    onChange={(e) => setLessonForm({ ...lessonForm, content: e.target.value })} />
                </div>
                <button className="btn btn-secondary btn-block" type="submit">Agregar al temario</button>
              </form>
            )}

            {editable && lessons.length > 0 && (
              <button className="btn btn-primary btn-block" style={{ background: 'var(--role-docente)', marginTop: 16 }}
                onClick={handleSubmitForReview}>
                Enviar a revisión
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
