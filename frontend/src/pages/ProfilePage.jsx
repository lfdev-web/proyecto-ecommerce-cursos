import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { CameraIcon, WalletIcon } from '../components/Icons';

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [achievements, setAchievements] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [form, setForm] = useState({ first_name: '', last_name: '', bio: '', phone: '' });
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState('');
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    api.get('/library/achievements/').then(({ data }) => setAchievements(data)).catch(() => {});
    api.get('/auth/wallet/transactions/').then(({ data }) => setTransactions(data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (user) {
      setForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        bio: user.bio || '',
        phone: user.phone || '',
      });
    }
  }, [user]);

  if (!user) return <div className="page">Cargando perfil...</div>;

  const initials = ((user.first_name?.[0] || '') + (user.last_name?.[0] || '')).toUpperCase() || user.email[0].toUpperCase();

  const handleAvatarChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadError('');
    const formData = new FormData();
    formData.append('avatar', file);
    try {
      await api.patch('/auth/profile/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      await refreshUser();
    } catch {
      setUploadError('No se pudo subir la imagen. Usa un archivo JPG o PNG.');
    }
  };

  const handleSave = async (event) => {
    event.preventDefault();
    setSaving(true);
    setSavedMsg('');
    try {
      await api.patch('/auth/profile/', form);
      await refreshUser();
      setSavedMsg('Datos guardados.');
      setTimeout(() => setSavedMsg(''), 2500);
    } catch {
      setSavedMsg('No se pudieron guardar los cambios.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page">
      <h1>Mi perfil</h1>

      {/* Encabezado: avatar + identidad */}
      <div className="glass card profile-header">
        {user.avatar_url
          ? <img src={user.avatar_url} alt="Foto de perfil" className="profile-avatar" />
          : <div className="profile-avatar-placeholder">{initials}</div>}
        <div className="profile-header-info">
          <h2 style={{ margin: 0 }}>{`${user.first_name} ${user.last_name}`.trim() || user.email}</h2>
          <p style={{ margin: '4px 0' }}>{user.email} · {user.role}</p>
          <p className="icon-text" style={{ margin: 0 }}>
            <span>Saldo disponible: <strong>${user.balance}</strong></span>
            <Link to="/recargar" className="btn btn-primary" style={{ padding: '6px 14px', fontSize: 13 }}>
              <WalletIcon width={15} height={15} /> Recargar
            </Link>
          </p>
        </div>
        <div>
          <input ref={fileInputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleAvatarChange} />
          <button className="btn btn-secondary" onClick={() => fileInputRef.current?.click()}>
            <CameraIcon width={16} height={16} /> Cambiar foto
          </button>
          {uploadError && <p style={{ color: 'var(--danger)', fontSize: 13, marginTop: 8 }}>{uploadError}</p>}
        </div>
      </div>

      {/* Medallas */}
      <div className="glass card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>
          Medallas {achievements && <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>({achievements.earned_count} de {achievements.total})</span>}
        </h3>
        {!achievements ? (
          <p>Cargando medallas...</p>
        ) : (
          <div className="medal-grid">
            {achievements.achievements.map((a) => (
              <div
                key={a.code}
                className={`medal ${a.earned ? 'medal-earned' : 'medal-locked'}`}
                title={a.earned ? `${a.description} — ganada el ${new Date(a.earned_at).toLocaleDateString()}` : a.description}
              >
                <div className="medal-icon" aria-hidden="true">{a.icon}</div>
                <strong className="medal-name">{a.name}</strong>
                <span className="medal-hint">{a.earned ? 'Conseguida' : a.description}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Datos personales */}
      <div className="glass card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>Mis datos</h3>
        <form onSubmit={handleSave} className="two-col">
          <div className="field" style={{ marginBottom: 0 }}>
            <label htmlFor="first_name">Nombre</label>
            <input id="first_name" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label htmlFor="last_name">Apellido</label>
            <input id="last_name" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label htmlFor="phone">Teléfono</label>
            <input id="phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </div>
          <div className="field" style={{ marginBottom: 0, gridColumn: '1 / -1' }}>
            <label htmlFor="bio">Sobre mí</label>
            <textarea id="bio" rows={3} value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} />
          </div>
          <div style={{ gridColumn: '1 / -1', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Guardando...' : 'Guardar cambios'}
            </button>
            {savedMsg && <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{savedMsg}</span>}
          </div>
        </form>
      </div>

      {/* Historial del saldo */}
      <div className="glass card">
        <h3 style={{ marginTop: 0 }}>Movimientos de mi saldo</h3>
        {transactions.length === 0 ? (
          <p>Sin movimientos todavía.</p>
        ) : (
          <div className="table-scroll">
            <table className="txn-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Descripción</th>
                  <th className="txn-amount">Monto</th>
                  <th className="txn-amount">Saldo</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((t) => (
                  <tr key={t.id}>
                    <td className="txn-date">{new Date(t.created_at).toLocaleDateString()}</td>
                    <td>{t.type_name}</td>
                    <td>{t.description}</td>
                    <td className={`txn-amount ${Number(t.amount) < 0 ? 'txn-out' : 'txn-in'}`}>
                      {Number(t.amount) > 0 ? '+' : ''}{t.amount}
                    </td>
                    <td className="txn-amount">${t.balance_after}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
