import { createContext, useContext, useEffect, useState } from 'react';
import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'driver_token';
const DISPATCHER_DRIVER_ID = '1';
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const isDispatcher = getTokenSubject(token) === DISPATCHER_DRIVER_ID;

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
    <AuthContext.Provider value={{ token, loading, login, logout, isDispatcher }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

function getTokenSubject(token) {
  if (!token) return null;
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    return JSON.parse(decodeBase64Url(payload)).sub;
  } catch {
    return null;
  }
}

function decodeBase64Url(value) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const input = normalized.padEnd(normalized.length + ((4 - normalized.length % 4) % 4), '=');
  let output = '';
  let buffer = 0;
  let bits = 0;

  for (const char of input) {
    if (char === '=') break;
    const index = chars.indexOf(char);
    if (index === -1) continue;
    buffer = (buffer << 6) | index;
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      output += String.fromCharCode((buffer >> bits) & 0xff);
    }
  }

  return output;
}
