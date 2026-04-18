import { createContext, useContext, useEffect, useState } from 'react';
import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'driver_token';
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    SecureStore.getItemAsync(TOKEN_KEY)
      .then(stored => { if (stored) setToken(stored); })
      .finally(() => setLoading(false));
  }, []);

  async function login(newToken) {
    await SecureStore.setItemAsync(TOKEN_KEY, newToken);
    setToken(newToken);
  }

  async function logout() {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    setToken(null);
  }

  return (
    <AuthContext.Provider value={{ token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
