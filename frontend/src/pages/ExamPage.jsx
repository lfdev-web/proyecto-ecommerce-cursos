import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import {
  CertificateIcon, ChartIcon, CheckIcon, ClipboardIcon, ClockIcon, RefreshIcon, TrophyIcon, XIcon,
} from '../components/Icons';

// Fases de la pantalla: info → en curso → resultado
const PHASE_INFO = 'info';
const PHASE_TAKING = 'taking';
const PHASE_RESULT = 'result';

function formatTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export default function ExamPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();

  const [phase, setPhase] = useState(PHASE_INFO);
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Estado del intento en curso
  const [attempt, setAttempt] = useState(null);
  const [answers, setAnswers] = useState({}); // { [questionId]: optionId }
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  // El deadline se fija UNA vez con el tiempo que dicta el servidor,
  // así el contador no se desincroniza aunque el render se pause.
  const deadlineRef = useRef(null);
  const submittedRef = useRef(false);

  useEffect(() => {
    api.get(`/exams/course/${courseId}/`)
      .then(({ data }) => setInfo(data))
      .catch((err) => setError(err.response?.data?.detail || 'No se pudo cargar el examen.'))
      .finally(() => setLoading(false));
  }, [courseId]);

  // El envío es el mismo lo dispare el alumno o el temporizador: si el tiempo se
  // agota, el servidor cierra el intento con 0 y la respuesta trae expired=true.
  const handleSubmit = useCallback(async () => {
    if (submittedRef.current || !attempt) return;
    submittedRef.current = true;
    setSubmitting(true);
    try {
      const payload = {
        answers: attempt.questions.map((q) => ({
          question: q.id,
          option: answers[q.id] ?? null,
        })),
      };
      const { data } = await api.post(`/exams/attempts/${attempt.attempt_id}/submit/`, payload);
      setResult(data);
      setPhase(PHASE_RESULT);
    } catch (err) {
      // Tiempo agotado en el servidor: el intento se cierra con 0
      const data = err.response?.data;
      if (data && data.score !== undefined) {
        setResult({ ...data, passed: false, expired: true });
        setPhase(PHASE_RESULT);
      } else {
        submittedRef.current = false;
        setError(data?.detail || 'Error al enviar el examen. Intenta de nuevo.');
      }
    } finally {
      setSubmitting(false);
    }
  }, [attempt, answers]);

  // Countdown: recalcula contra el deadline en cada tick y autoenvía al llegar a 0
  useEffect(() => {
    if (phase !== PHASE_TAKING) return undefined;
    const interval = setInterval(() => {
      const remaining = Math.max(Math.round((deadlineRef.current - Date.now()) / 1000), 0);
      setSecondsLeft(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
        handleSubmit();
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [phase, handleSubmit]);

  const handleStart = async () => {
    setError('');
    try {
      const { data } = await api.post(`/exams/course/${courseId}/start/`);
      setAttempt(data);
      setAnswers({});
      submittedRef.current = false;
      deadlineRef.current = Date.now() + data.time_remaining_seconds * 1000;
      setSecondsLeft(data.time_remaining_seconds);
      setPhase(PHASE_TAKING);
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo iniciar el examen.');
    }
  };

  if (loading) return <div className="page">Cargando examen...</div>;

  if (!info?.has_exam) {
    return (
      <div className="page">
        <div className="glass card">
          <h2>Este curso no tiene examen final</h2>
          <p>{error || 'El certificado se emite automáticamente al completar todas las lecciones.'}</p>
          <Link to="/mi-biblioteca" className="btn btn-secondary">Volver a mi biblioteca</Link>
        </div>
      </div>
    );
  }

  // ---------- Pantalla de resultado ----------
  if (phase === PHASE_RESULT && result) {
    const passed = result.passed;
    return (
      <div className="page" style={{ maxWidth: 640, margin: '0 auto' }}>
        <div className="glass card" style={{ textAlign: 'center' }}>
          <div style={{ marginBottom: 4, color: passed ? 'var(--success)' : 'var(--text-muted)' }}>
            {passed
              ? <TrophyIcon width={44} height={44} strokeWidth={1.5} />
              : <ClipboardIcon width={44} height={44} strokeWidth={1.5} />}
          </div>
          <h1>{passed ? '¡Examen aprobado!' : result.expired ? 'Tiempo agotado' : 'Examen no aprobado'}</h1>
          <p style={{ fontSize: 48, fontWeight: 800, margin: '16px 0', color: passed ? 'var(--success)' : 'var(--danger)' }}>
            {Number(result.score).toFixed(0)}%
          </p>
          <p>
            Nota mínima para aprobar: {Number(result.passing_score ?? info.exam.passing_score).toFixed(0)}%
            {result.total_questions !== undefined && (
              <> · {result.correct_answers} de {result.total_questions} correctas</>
            )}
          </p>
          {passed && result.certificate_issued && (
            <p className="badge badge-accent icon-text" style={{ marginTop: 8 }}>
              <CertificateIcon width={15} height={15} /> Tu certificado ya está disponible en tu biblioteca
            </p>
          )}
          {!passed && result.attempts_left !== null && result.attempts_left !== undefined && (
            <p style={{ marginTop: 8 }}>
              {result.attempts_left > 0
                ? `Te quedan ${result.attempts_left} intento(s).`
                : 'Agotaste todos los intentos permitidos.'}
            </p>
          )}
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 24 }}>
            {!passed && (result.attempts_left === null || result.attempts_left > 0) && (
              <button className="btn btn-primary" onClick={() => { setPhase(PHASE_INFO); setResult(null); window.location.reload(); }}>
                Reintentar
              </button>
            )}
            <button className="btn btn-secondary" onClick={() => navigate('/mi-biblioteca')}>
              Ir a mi biblioteca
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ---------- Pantalla del examen en curso ----------
  if (phase === PHASE_TAKING && attempt) {
    const answered = Object.keys(answers).length;
    const lowTime = secondsLeft <= 60;
    return (
      <div className="page" style={{ maxWidth: 760, margin: '0 auto' }}>
        <div
          className="glass card"
          style={{
            position: 'sticky', top: 12, zIndex: 10, display: 'flex',
            justifyContent: 'space-between', alignItems: 'center', marginBottom: 20,
          }}
        >
          <div>
            <strong>{attempt.exam.title}</strong>
            <p style={{ margin: 0, fontSize: 13 }}>Intento #{attempt.attempt_number} · {answered}/{attempt.questions.length} respondidas</p>
          </div>
          <div
            className="icon-text"
            style={{ fontSize: 28, fontWeight: 700, color: lowTime ? 'var(--danger)' : 'var(--text-primary)' }}
          >
            <ClockIcon width={24} height={24} /> {formatTime(secondsLeft)}
          </div>
        </div>

        {attempt.questions.map((question, idx) => (
          <div key={question.id} className="glass card" style={{ marginBottom: 16 }}>
            <h3 style={{ marginTop: 0 }}>
              {idx + 1}. {question.text}
              <span style={{ fontSize: 13, fontWeight: 400, marginLeft: 8, color: 'var(--text-secondary)' }}>
                ({question.points} {question.points === 1 ? 'punto' : 'puntos'})
              </span>
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {question.options.map((option) => (
                <label
                  key={option.id}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
                    borderRadius: 10, cursor: 'pointer',
                    border: answers[question.id] === option.id
                      ? '1px solid var(--accent)'
                      : '1px solid var(--surface-border)',
                    background: answers[question.id] === option.id ? 'var(--accent-soft)' : 'var(--surface-2)',
                  }}
                >
                  <input
                    type="radio"
                    name={`question-${question.id}`}
                    checked={answers[question.id] === option.id}
                    onChange={() => setAnswers((prev) => ({ ...prev, [question.id]: option.id }))}
                  />
                  {option.text}
                </label>
              ))}
            </div>
          </div>
        ))}

        {error && <p style={{ color: 'var(--danger)' }}>{error}</p>}
        <button
          className="btn btn-primary btn-block"
          disabled={submitting}
          onClick={() => {
            const unanswered = attempt.questions.length - answered;
            if (unanswered > 0 && !window.confirm(`Tienes ${unanswered} pregunta(s) sin responder. ¿Enviar de todos modos?`)) return;
            handleSubmit();
          }}
        >
          {submitting ? 'Enviando...' : 'Enviar examen'}
        </button>
      </div>
    );
  }

  // ---------- Pantalla de información previa ----------
  const { exam } = info;
  const noAttemptsLeft = info.attempts_left !== null && info.attempts_left <= 0;
  return (
    <div className="page" style={{ maxWidth: 640, margin: '0 auto' }}>
      <div className="glass card">
        <h1>{exam.title}</h1>
        {exam.instructions && <p>{exam.instructions}</p>}
        <ul style={{ lineHeight: 2, listStyle: 'none', padding: 0 }}>
          <li className="icon-text">
            <ClockIcon width={17} height={17} style={{ color: 'var(--accent)' }} />
            <span>Tiempo límite: <strong>{exam.time_limit_minutes} minutos</strong> (controlado por el servidor)</span>
          </li>
          <li className="icon-text">
            <CheckIcon width={17} height={17} style={{ color: 'var(--accent)' }} />
            <span>Nota mínima para aprobar: <strong>{Number(exam.passing_score).toFixed(0)}%</strong></span>
          </li>
          <li className="icon-text">
            <RefreshIcon width={17} height={17} style={{ color: 'var(--accent)' }} />
            <span>Intentos: <strong>{exam.max_attempts === 0 ? 'ilimitados' : `${info.attempts_used} usados de ${exam.max_attempts}`}</strong></span>
          </li>
          {info.best_score !== null && (
            <li className="icon-text">
              <ChartIcon width={17} height={17} style={{ color: 'var(--accent)' }} />
              <span>Tu mejor puntaje: <strong>{Number(info.best_score).toFixed(0)}%</strong></span>
            </li>
          )}
        </ul>

        {info.attempts.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <h3>Intentos anteriores</h3>
            {info.attempts.map((a) => (
              <p key={a.id} className="icon-text" style={{ margin: '4px 0', fontSize: 14 }}>
                <span>Intento #{a.attempt_number}: {Number(a.score).toFixed(0)}% —</span>
                {a.passed
                  ? <span className="icon-text" style={{ color: 'var(--success)', gap: 4 }}><CheckIcon width={15} height={15} /> Aprobado</span>
                  : <span className="icon-text" style={{ color: 'var(--danger)', gap: 4 }}><XIcon width={15} height={15} /> No aprobado</span>}
              </p>
            ))}
          </div>
        )}

        {error && <p style={{ color: 'var(--danger)' }}>{error}</p>}

        {info.passed ? (
          <>
            <p className="badge badge-accent icon-text">
              <TrophyIcon width={15} height={15} /> Ya aprobaste este examen
            </p>
            <Link to="/mi-biblioteca" className="btn btn-secondary btn-block" style={{ marginTop: 12 }}>
              Descargar mi certificado en la biblioteca
            </Link>
          </>
        ) : noAttemptsLeft ? (
          <p style={{ color: 'var(--danger)' }}>Agotaste todos los intentos permitidos para este examen.</p>
        ) : (
          <>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              Al comenzar, el cronómetro corre aunque cierres la página. Si el tiempo se agota, el intento se califica con 0.
            </p>
            <button className="btn btn-primary btn-block" onClick={handleStart}>
              Comenzar examen
            </button>
          </>
        )}
      </div>
    </div>
  );
}
