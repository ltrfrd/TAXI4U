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
import { useAuth } from '../context/AuthContext';
import { getDriverProfile, updateDriverLocation } from '../services/api';

export default function DriverProfileScreen() {
  const { token, logout } = useAuth();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [locStatus, setLocStatus] = useState('idle'); // idle | loading | ok | error
  const [locMessage, setLocMessage] = useState('');

  useEffect(() => {
    getDriverProfile(token)
      .then(setProfile)
      .catch(err => setError(err.message || 'Failed to load profile.'))
      .finally(() => setLoading(false));
  }, [token]);

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
            label="Status"
            value={profile?.is_active ? 'Active' : 'Inactive'}
            valueStyle={profile?.is_active ? styles.active : styles.inactive}
          />
          <ProfileRow
            label="Member since"
            value={profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : '—'}
          />
        </View>
      )}

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
