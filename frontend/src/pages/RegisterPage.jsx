import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [form, setForm] = useState({
    email: '', password: '', first_name: '', last_name: '',
    referral_code: searchParams.get('ref') || '',
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(form);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data;
      setError(typeof detail === 'object' ? Object.values(detail).flat().join(' ') : 'No se pudo crear la cuenta.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page container-narrow">
      <div className="glass card">
        <h2 className="text-center">Crear cuenta</h2>
        <p className="text-center">Recibes $500 de saldo simulado para probar la plataforma.</p>
        {error && <div className="alert alert-danger">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="first_name">Nombre</label>
            <input id="first_name" name="first_name" required value={form.first_name} onChange={handleChange} />
          </div>
          <div className="field">
            <label htmlFor="last_name">Apellido</label>
            <input id="last_name" name="last_name" required value={form.last_name} onChange={handleChange} />
          </div>
          <div className="field">
            <label htmlFor="email">Correo</label>
            <input id="email" name="email" type="email" required value={form.email} onChange={handleChange} />
          </div>
          <div className="field">
            <label htmlFor="password">Contraseña</label>
            <input id="password" name="password" type="password" required value={form.password} onChange={handleChange} />
          </div>
          <div className="field">
            <label htmlFor="referral_code">Código de referido (opcional)</label>
            <input id="referral_code" name="referral_code" value={form.referral_code} onChange={handleChange} />
          </div>
          <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Crear cuenta'}
          </button>
        </form>
        <p className="text-center mt-lg">
          ¿Ya tienes cuenta? <Link to="/login">Ingresa</Link>
        </p>
      </div>
    </div>
  );
}
