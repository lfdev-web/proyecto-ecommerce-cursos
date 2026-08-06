import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import { ArrowLeftIcon } from '../components/Icons';

export default function TeacherCourseStudentsPage() {
  const { courseId } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/teacher/courses/${courseId}/students/`)
      .then(({ data }) => setData(data))
      .catch(() => setError('No se pudo cargar la lista (¿el curso es tuyo?).'));
  }, [courseId]);

  if (error) {
    return (
      <div className="page">
        <div className="glass card">
          <p>{error}</p>
          <Link to="/panel-docente" className="btn btn-secondary">Volver al panel</Link>
        </div>
      </div>
    );
  }
  if (!data) return <div className="page">Cargando alumnos...</div>;

  return (
    <div className="page">
      <Link to="/panel-docente" className="icon-text" style={{ color: 'var(--role-docente-strong)', fontWeight: 600, gap: 6 }}>
        <ArrowLeftIcon width={16} height={16} /> Volver al panel
      </Link>
      <div style={{
        borderLeft: '4px solid var(--role-docente)', background: 'var(--role-docente-soft)',
        borderRadius: 10, padding: '14px 18px', margin: '12px 0 20px',
      }}>
        <h1 style={{ margin: 0 }}>{data.course_title}</h1>
        <p style={{ margin: '2px 0 0', fontSize: 14 }}>
          {data.students.length} {data.students.length === 1 ? 'alumno inscrito' : 'alumnos inscritos'}
        </p>
      </div>

      {data.students.length > 0 && (
        <div className="glass card" style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--surface-border)' }}>
                <th style={{ padding: 10 }}>Alumno</th>
                <th style={{ padding: 10 }}>Inscrito</th>
                <th style={{ padding: 10 }}>Progreso</th>
                <th style={{ padding: 10 }}>Estado</th>
              </tr>
            </thead>
            <tbody>
              {data.students.map((student) => (
                <tr key={student.email} style={{ borderBottom: '1px solid var(--surface-border)' }}>
                  <td style={{ padding: 10 }}>
                    {student.name}
                    <span style={{ display: 'block', fontSize: 12, color: 'var(--text-secondary)' }}>{student.email}</span>
                  </td>
                  <td style={{ padding: 10 }}>{new Date(student.enrolled_at).toLocaleDateString('es-EC')}</td>
                  <td style={{ padding: 10, minWidth: 160 }}>
                    <div style={{ background: 'var(--surface-2)', border: '1px solid var(--surface-border)', borderRadius: 999, height: 8, overflow: 'hidden' }}>
                      <div style={{ width: `${student.progress_percentage}%`, background: 'var(--role-docente)', height: '100%' }} />
                    </div>
                    <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{student.progress_percentage}%</span>
                  </td>
                  <td style={{ padding: 10 }}>
                    {student.is_completed
                      ? <span className="badge badge-success">Completado</span>
                      : <span className="badge badge-accent">En progreso</span>}
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
