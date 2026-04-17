import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { calculateFare } from '../services/api';

export default function HomeScreen({ navigation }) {
  const [pickup, setPickup] = useState('');
  const [dropoff, setDropoff] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleCalculate() {
    if (!pickup.trim() || !dropoff.trim()) {
      setError('Please enter both a pickup and dropoff address.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const result = await calculateFare(pickup.trim(), dropoff.trim());
      navigation.navigate('Result', { result });
    } catch (err) {
      setError(err.message || 'Something went wrong. Check your connection.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.inner}>
        <Text style={styles.heading}>Where are you going?</Text>

        <Text style={styles.label}>Pickup Address</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. 123 Riverview Dr, Cochrane, AB"
          placeholderTextColor="#888"
          value={pickup}
          onChangeText={setPickup}
          autoCorrect={false}
          returnKeyType="next"
        />

        <Text style={styles.label}>Dropoff Address</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. 456 Fireside Dr, Cochrane, AB"
          placeholderTextColor="#888"
          value={dropoff}
          onChangeText={setDropoff}
          autoCorrect={false}
          returnKeyType="done"
          onSubmitEditing={handleCalculate}
        />

        {error && <Text style={styles.error}>{error}</Text>}

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleCalculate}
          disabled={loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color="#1a1a2e" />
          ) : (
            <Text style={styles.buttonText}>Calculate Fare</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  inner: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  heading: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#f5f5f5',
    marginBottom: 32,
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
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#2a2a4a',
  },
  error: {
    color: '#ff6b6b',
    fontSize: 14,
    marginBottom: 16,
    textAlign: 'center',
  },
  button: {
    backgroundColor: '#f5c518',
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#1a1a2e',
    fontSize: 16,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
});
