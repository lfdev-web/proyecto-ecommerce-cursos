import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import api, { tokenStorage } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadProfile = useCallback(async () => {
    if (!tokenStorage.getAccess()) {
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get('/auth/profile/');
      setUser(data);
      return data;
    } catch {
      tokenStorage.clear();
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadProfile(); }, [loadProfile]);

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login/', { email, password });
    tokenStorage.set(data.access, data.refresh);
    // Devuelve el perfil para que la pantalla de login redirija según el rol
    return loadProfile();
  };

  const register = async (payload) => {
    const { data } = await api.post('/auth/register/', payload);
    tokenStorage.set(data.access, data.refresh);
    setUser(data.user);
  };

  const logout = async () => {
    const refresh = tokenStorage.getRefresh();
    try {
      if (refresh) await api.post('/auth/logout/', { refresh });
    } catch {
      // Si falla el logout en el backend (token ya vencido, etc.), igual limpiamos localmente.
    }
    tokenStorage.clear();
    setUser(null);
  };

  const refreshUser = () => loadProfile();

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>');
  return ctx;
}
