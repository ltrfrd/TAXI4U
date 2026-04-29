import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { createManualRide } from '../services/api';

export default function DispatcherManualRideScreen() {
  const { token } = useAuth();
  const [pickupText, setPickupText] = useState('');
  const [dropoffText, setDropoffText] = useState('');
  const [fareAmount, setFareAmount] = useState('');
  const [driverEmail, setDriverEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [ride, setRide] = useState(null);

  async function handleSubmit() {
    const pickup_text = pickupText.trim();
    const dropoff_text = dropoffText.trim();
    const fareText = fareAmount.trim();
    const emailText = driverEmail.trim();

    if (!pickup_text || !dropoff_text) {
      setError('Pickup and dropoff are required.');
      return;
    }

    const payload = { pickup_text, dropoff_text };
    if (fareText) {
      const amount = Number(fareText);
      if (!Number.isFinite(amount)) {
        setError('Fare amount must be a number.');
        return;
      }
      payload.fare_amount = amount;
    }
    if (emailText) {
      payload.driver_email = emailText;
    }

    setLoading(true);
    setError('');
    setRide(null);
    try {
      setRide(await createManualRide(token, payload));
    } catch (err) {
      setError(err.message || 'Manual booking failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.heading}>Manual Booking</Text>

        <Text style={styles.label}>Pickup</Text>
        <TextInput
          style={styles.input}
          placeholder="Pickup address or note"
          placeholderTextColor="#888"
          value={pickupText}
          onChangeText={setPickupText}
          autoCorrect={false}
          returnKeyType="next"
        />

        <Text style={styles.label}>Dropoff</Text>
        <TextInput
          style={styles.input}
          placeholder="Dropoff address or note"
          placeholderTextColor="#888"
          value={dropoffText}
          onChangeText={setDropoffText}
          autoCorrect={false}
          returnKeyType="next"
        />

        <Text style={styles.label}>Fare Amount</Text>
        <TextInput
          style={styles.input}
          placeholder="Optional"
          placeholderTextColor="#888"
          value={fareAmount}
          onChangeText={setFareAmount}
          keyboardType="decimal-pad"
          returnKeyType="next"
        />

        <Text style={styles.label}>Driver Email</Text>
        <TextInput
          style={styles.input}
          placeholder="Optional"
          placeholderTextColor="#888"
          value={driverEmail}
          onChangeText={setDriverEmail}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="email-address"
          returnKeyType="done"
          onSubmitEditing={handleSubmit}
        />

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleSubmit}
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color="#1a1a2e" />
          ) : (
            <Text style={styles.buttonText}>Create Manual Ride</Text>
          )}
        </TouchableOpacity>

        {ride ? (
          <View style={styles.result}>
            <Text style={styles.resultTitle}>Ride Created</Text>
            <Row label="Ride ID" value={ride.id} />
            <Row label="Status" value={ride.status?.replace('_', ' ')} />
            {ride.assigned_driver ? (
              <>
                <Row label="Driver" value={ride.assigned_driver.name} />
                <Row label="Email" value={ride.assigned_driver.email} />
              </>
            ) : null}
          </View>
        ) : null}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function Row({ label, value }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value ?? '-'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  heading: {
    color: '#f5f5f5',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 24,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#f5c518',
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  input: {
    backgroundColor: '#16213e',
    color: '#f5f5f5',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    borderWidth: 1,
    borderColor: '#2a2a4a',
    marginBottom: 18,
  },
  error: {
    color: '#ff6b6b',
    fontSize: 14,
    marginBottom: 12,
    textAlign: 'center',
  },
  button: {
    backgroundColor: '#f5c518',
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 4,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#1a1a2e',
    fontSize: 16,
    fontWeight: 'bold',
  },
  result: {
    backgroundColor: '#16213e',
    borderRadius: 12,
    padding: 16,
    marginTop: 20,
    borderWidth: 1,
    borderColor: '#2ecc71',
  },
  resultTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#2ecc71',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 7,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a4a',
  },
  rowLabel: {
    fontSize: 14,
    color: '#aaa',
    flex: 1,
  },
  rowValue: {
    fontSize: 14,
    color: '#f5f5f5',
    fontWeight: '500',
    flexShrink: 1,
    textAlign: 'right',
    marginLeft: 8,
  },
});
