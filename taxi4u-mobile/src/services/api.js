// ---------------------------------------------------------------
// IMPORTANT: Replace with your computer's local IP address.
// "localhost" does not work on a physical phone or emulator —
// the device needs to reach your machine over the network.
//
// Find your IP:
//   Windows: run  ipconfig  → look for IPv4 Address
//   Mac/Linux: run  ifconfig  → look for inet
//
// Example: const API_BASE = 'http://192.168.1.42:8001';
// ---------------------------------------------------------------
const API_BASE = 'http://10.0.0.166:8001';
export async function calculateFare(pickup, dropoff) {
  const response = await fetch(`${API_BASE}/fare/calculate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ pickup, dropoff }),
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
