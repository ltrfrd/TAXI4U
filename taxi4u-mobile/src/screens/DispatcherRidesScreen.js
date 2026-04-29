import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { assignRide, getAllRides } from '../services/api';

export default function DispatcherRidesScreen() {
  const { token } = useAuth();
  const [rides, setRides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [assigningId, setAssigningId] = useState(null);
  const [assignError, setAssignError] = useState('');

  async function loadRides(showLoading = true) {
    if (showLoading) setLoading(true);
    setError('');
    try {
      setRides(await getAllRides(token));
    } catch (err) {
      setError(err.message || 'Failed to load rides.');
    } finally {
      if (showLoading) setLoading(false);
    }
  }

  useEffect(() => {
    loadRides();
  }, [token]);

  async function handleAssign(rideId, driverEmail) {
    const email = driverEmail.trim();
    if (!email) {
      setAssignError('Enter a driver email.');
      return;
    }

    setAssigningId(rideId);
    setAssignError('');
    try {
      await assignRide(token, rideId, email);
      await loadRides(false);
    } catch (err) {
      setAssignError(err.message || 'Assign failed.');
    } finally {
      setAssigningId(null);
    }
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#f5c518" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.content}
      data={rides}
      keyExtractor={item => String(item.id)}
      ListHeaderComponent={assignError ? <Text style={styles.assignError}>{assignError}</Text> : null}
      ListEmptyComponent={<Text style={styles.empty}>No rides found.</Text>}
      renderItem={({ item }) => (
        <RideRow
          ride={item}
          onAssign={handleAssign}
          assigning={assigningId === item.id}
          disabled={assigningId !== null}
        />
      )}
    />
  );
}

function RideRow({ ride, onAssign, assigning, disabled }) {
  const driver = ride.assigned_driver;
  const [driverEmail, setDriverEmail] = useState(driver?.email || '');

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <Text style={styles.rideId}>Ride #{ride.id}</Text>
        <Text style={styles.status}>{ride.status?.replace('_', ' ')}</Text>
      </View>
      <Text style={styles.label}>Pickup</Text>
      <Text style={styles.value}>{ride.pickup_text}</Text>
      <Text style={styles.label}>Dropoff</Text>
      <Text style={styles.value}>{ride.dropoff_text}</Text>
      <Text style={styles.label}>Driver</Text>
      <Text style={styles.value}>
        {driver ? `${driver.name} (${driver.email})` : 'Unassigned'}
      </Text>
      <View style={styles.assignRow}>
        <TextInput
          style={styles.input}
          placeholder="driver@example.com"
          placeholderTextColor="#888"
          value={driverEmail}
          onChangeText={setDriverEmail}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="email-address"
        />
        <TouchableOpacity
          style={[styles.assignButton, disabled && styles.buttonDisabled]}
          onPress={() => onAssign(ride.id, driverEmail)}
          disabled={disabled}
          activeOpacity={0.8}
        >
          {assigning ? (
            <ActivityIndicator size="small" color="#1a1a2e" />
          ) : (
            <Text style={styles.assignButtonText}>{driver ? 'Reassign' : 'Assign'}</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  centered: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  error: {
    color: '#ff6b6b',
    fontSize: 14,
    textAlign: 'center',
  },
  empty: {
    color: '#aab2cf',
    fontSize: 15,
    textAlign: 'center',
    marginTop: 48,
  },
  assignError: {
    color: '#ff6b6b',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 12,
  },
  card: {
    backgroundColor: '#16213e',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2a2a4a',
    padding: 16,
    marginBottom: 12,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  rideId: {
    color: '#f5f5f5',
    fontSize: 16,
    fontWeight: '700',
  },
  status: {
    color: '#f5c518',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  label: {
    color: '#aab2cf',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    marginTop: 8,
    marginBottom: 3,
  },
  value: {
    color: '#f5f5f5',
    fontSize: 14,
    lineHeight: 20,
  },
  assignRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 14,
  },
  input: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    color: '#f5f5f5',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2a2a4a',
    paddingHorizontal: 12,
    paddingVertical: 9,
    fontSize: 13,
  },
  assignButton: {
    backgroundColor: '#f5c518',
    borderRadius: 8,
    paddingHorizontal: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 82,
  },
  assignButtonText: {
    color: '#1a1a2e',
    fontSize: 13,
    fontWeight: '700',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
});
