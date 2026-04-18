import { API_BASE } from '../config';

export async function calculateFare(pickup, dropoff, options = {}) {
  const body = { pickup, dropoff };

  if (options.pickupCoords) {
    body.pickup_coords = options.pickupCoords;
  }

  if (options.dropoffCoords) {
    body.dropoff_coords = options.dropoffCoords;
  }

  const response = await fetch(`${API_BASE}/fare/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`Server returned ${response.status}. Check the backend is running.`);
  }

  return response.json();
}

export async function fetchZones() {
  const response = await fetch(`${API_BASE}/zones`);

  if (!response.ok) {
    throw new Error(`Server returned ${response.status}. Check the backend is running.`);
  }

  const payload = await response.json();
  return payload.zones ?? [];
}

// -------------------------------------------------------------------
// Driver auth
// -------------------------------------------------------------------

export async function loginDriver(email, password) {
  const response = await fetch(`${API_BASE}/driver/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Login failed (${response.status})`);
  }
  return response.json(); // { access_token, token_type }
}

export async function getDriverProfile(token) {
  const response = await authFetch(`${API_BASE}/driver/me`, token);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to load profile (${response.status})`);
  }
  return response.json();
}

// Attach Authorization: Bearer <token> to any protected request.
export function authFetch(url, token, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });
}

// -------------------------------------------------------------------
// Driver location
// -------------------------------------------------------------------

export async function updateDriverLocation(token, latitude, longitude) {
  const response = await authFetch(`${API_BASE}/driver/location`, token, {
    method: 'POST',
    body: JSON.stringify({ latitude, longitude }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Location update failed (${response.status})`);
  }
  return response.json(); // { latitude, longitude, updated_at }
}

export async function getMyLocation(token) {
  const response = await authFetch(`${API_BASE}/driver/location/me`, token);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Failed to get location (${response.status})`);
  }
  return response.json();
}

// -------------------------------------------------------------------
// Nominatim address autocomplete — Canada only, no backend needed
// -------------------------------------------------------------------
const NOMINATIM = 'https://nominatim.openstreetmap.org/search';

function _formatLabel(r) {
  const a = r.address || {};
  const street = [a.house_number, a.road].filter(Boolean).join(' ');
  const place = r.name || street || a.suburb || a.neighbourhood || '';
  const city = a.city || a.town || a.village || a.municipality || a.county || '';
  const province = a.state || '';
  return [place, city, province].filter(Boolean).join(', ') || r.display_name;
}

export async function searchAddresses(query, signal) {
  const q = (query || '').trim();
  if (q.length < 2) return [];
  try {
    const params = new URLSearchParams({
      q,
      format: 'json',
      addressdetails: '1',
      limit: '5',
      countrycodes: 'ca',
    });
    const res = await fetch(`${NOMINATIM}?${params}`, {
      headers: { 'User-Agent': 'TAXI4U-MobileApp/1.0' },
      signal,
    });
    if (!res.ok) return [];
    const hits = await res.json();
    return hits.map(r => ({
      label: _formatLabel(r),
      value: r.display_name,
      lat: Number(r.lat),
      lon: Number(r.lon),
      display_name: r.display_name,
    }));
  } catch (err) {
    if (err.name === 'AbortError') return [];
    return [];
  }
}
