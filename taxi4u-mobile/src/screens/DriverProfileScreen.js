import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import * as Location from 'expo-location';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../context/AuthContext';
import { getDriverProfile, updateDriverLocation, updateDriverStatus } from '../services/api';

const STATUS_COLOR = {
  available: '#2ecc71',
  busy: '#f39c12',
  offline: '#6c7488',
};

export default function DriverProfileScreen() {
  const { token, logout } = useAuth();
  const navigation = useNavigation();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [locStatus, setLocStatus] = useState('idle'); // idle | loading | ok | error
  const [locMessage, setLocMessage] = useState('');
  const [driverStatus, setDriverStatus] = useState(null); // offline | available | busy
  const [statusUpdating, setStatusUpdating] = useState(false);

  useEffect(() => {
    getDriverProfile(token)
      .then(data => { setProfile(data); setDriverStatus(data.status ?? 'offline'); })
      .catch(err => setError(err.message || 'Failed to load profile.'))
      .finally(() => setLoading(false));
  }, [token]);

  async function changeStatus(newStatus) {
    if (newStatus === driverStatus || statusUpdating) return;
    setStatusUpdating(true);
    try {
      const res = await updateDriverStatus(token, newStatus);
      setDriverStatus(res.status);
    } catch {
      // keep previous status on failure — no crash
    } finally {
      setStatusUpdating(false);
    }
  }

  async function shareLocation() {
    setLocStatus('loading');
    setLocMessage('');
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLocStatus('error');
        setLocMessage('Location permission denied.');
        return;
      }
      const pos = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      const { latitude, longitude } = pos.coords;
      await updateDriverLocation(token, latitude, longitude);
      setLocStatus('ok');
      setLocMessage(`Sent: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}`);
    } catch (err) {
      setLocStatus('error');
      setLocMessage(err.message || 'Failed to send location.');
    }
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#f5c518" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {error ? (
        <Text style={styles.error}>{error}</Text>
      ) : (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Driver Info</Text>
          <ProfileRow label="Name" value={profile?.name} />
          <ProfileRow label="Email" value={profile?.email} />
          <ProfileRow label="Phone" value={profile?.phone ?? '—'} />
          <ProfileRow
            label="Account"
            value={profile?.is_active ? 'Active' : 'Inactive'}
            valueStyle={profile?.is_active ? styles.active : styles.inactive}
          />
          <ProfileRow
            label="Member since"
            value={profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : '—'}
          />
        </View>
      )}

      {driverStatus !== null ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Driver Status</Text>
          <View style={[styles.statusBadge, { backgroundColor: STATUS_COLOR[driverStatus] || '#6c7488' }]}>
            <Text style={styles.statusBadgeText}>
              {driverStatus.charAt(0).toUpperCase() + driverStatus.slice(1)}
            </Text>
          </View>
          <View style={styles.statusRow}>
            {['offline', 'available', 'busy'].map(s => (
              <TouchableOpacity
                key={s}
                style={[styles.statusBtn, driverStatus === s && styles.statusBtnActive]}
                onPress={() => changeStatus(s)}
                disabled={statusUpdating || driverStatus === s}
              >
                <Text style={[styles.statusBtnText, driverStatus === s && styles.statusBtnTextActive]}>
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          {statusUpdating ? <ActivityIndicator size="small" color="#f5c518" style={{ marginTop: 10 }} /> : null}
        </View>
      ) : null}

      <TouchableOpacity
        style={styles.ridesButton}
        onPress={() => navigation.navigate('DriverRides')}
      >
        <Text style={styles.ridesButtonText}>🚕  My Rides</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.locationButton, locStatus === 'loading' && styles.buttonDisabled]}
        onPress={shareLocation}
        disabled={locStatus === 'loading'}
      >
        {locStatus === 'loading' ? (
          <ActivityIndicator color="#1a1a2e" />
        ) : (
          <Text style={styles.locationText}>📍 Share My Location</Text>
        )}
      </TouchableOpacity>

      {locMessage ? (
        <Text style={locStatus === 'ok' ? styles.locOk : styles.locError}>{locMessage}</Text>
      ) : null}

      <TouchableOpacity style={styles.logoutButton} onPress={logout}>
        <Text style={styles.logoutText}>Log Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function ProfileRow({ label, value, valueStyle }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={[styles.rowValue, valueStyle]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  content: {
    padding: 24,
  },
  centered: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    backgroundColor: '#16213e',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2a2a4a',
    padding: 20,
    marginBottom: 24,
  },
  cardTitle: {
    color: '#f5c518',
    fontSize: 16,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    marginBottom: 16,
    letterSpacing: 1,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a4a',
  },
  rowLabel: {
    color: '#aab2cf',
    fontSize: 14,
  },
  rowValue: {
    color: '#f5f5f5',
    fontSize: 14,
    fontWeight: '500',
    maxWidth: '60%',
    textAlign: 'right',
  },
  active: {
    color: '#2ecc71',
  },
  inactive: {
    color: '#ff6b6b',
  },
  error: {
    color: '#ff6b6b',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 24,
  },
  statusRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
  },
  statusBadge: {
    alignSelf: 'flex-start',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  statusBadgeText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  statusBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#f5c518',
    alignItems: 'center',
  },
  statusBtnActive: {
    backgroundColor: '#f5c518',
  },
  statusBtnText: {
    color: '#f5c518',
    fontSize: 13,
    fontWeight: '600',
  },
  statusBtnTextActive: {
    color: '#1a1a2e',
  },
  ridesButton: {
    borderWidth: 1,
    borderColor: '#f5c518',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  ridesButtonText: {
    color: '#f5c518',
    fontSize: 15,
    fontWeight: '600',
  },
  locationButton: {
    backgroundColor: '#f5c518',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  locationText: {
    color: '#1a1a2e',
    fontSize: 15,
    fontWeight: '700',
  },
  locOk: {
    color: '#2ecc71',
    fontSize: 13,
    textAlign: 'center',
    marginBottom: 16,
  },
  locError: {
    color: '#ff6b6b',
    fontSize: 13,
    textAlign: 'center',
    marginBottom: 16,
  },
  logoutButton: {
    borderWidth: 1,
    borderColor: '#ff6b6b',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  logoutText: {
    color: '#ff6b6b',
    fontSize: 16,
    fontWeight: '600',
  },
});
