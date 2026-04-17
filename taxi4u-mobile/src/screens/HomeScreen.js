import { useEffect, useRef, useState } from 'react';
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
import { calculateFare, searchAddresses } from '../services/api';

export default function HomeScreen({ navigation }) {
  const [pickup, setPickup] = useState('');
  const [dropoff, setDropoff] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [activeField, setActiveField] = useState(null);
  const debounceRef = useRef(null);

  // Clear pending timer on unmount to avoid setState on dead component
  useEffect(() => () => clearTimeout(debounceRef.current), []);

  function handleTextChange(text, field) {
    if (field === 'pickup') setPickup(text);
    else setDropoff(text);

    setActiveField(field);
    clearTimeout(debounceRef.current);

    if (!text.trim() || text.trim().length < 2) {
      setSuggestions([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      const results = await searchAddresses(text.trim());
      setSuggestions(results);
    }, 400);
  }

  function handleInputFocus(field) {
    if (field !== activeField) {
      setSuggestions([]);
      setActiveField(field);
    }
  }

  function handleSelect(item, field) {
    if (field === 'pickup') setPickup(item.label);
    else setDropoff(item.label);
    setSuggestions([]);
    setActiveField(null);
    clearTimeout(debounceRef.current);
  }

  async function handleCalculate() {
    if (!pickup.trim() || !dropoff.trim()) {
      setError('Please enter both a pickup and dropoff address.');
      return;
    }
    setSuggestions([]);
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

  function renderSuggestions(field) {
    if (activeField !== field || suggestions.length === 0) return null;
    return (
      <View style={styles.dropdown}>
        {suggestions.map((item, idx) => (
          <TouchableOpacity
            key={idx}
            style={[
              styles.dropdownItem,
              idx < suggestions.length - 1 && styles.dropdownSep,
            ]}
            onPress={() => handleSelect(item, field)}
          >
            <Text style={styles.dropdownText} numberOfLines={2}>
              {item.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.inner}>
        <Text style={styles.heading}>Where are you going?</Text>

        <Text style={styles.label}>Pickup Address</Text>
        <View style={[styles.inputWrapper, styles.pickupWrapper]}>
          <TextInput
            style={styles.input}
            placeholder="e.g. 123 Riverview Dr, Cochrane, AB"
            placeholderTextColor="#888"
            value={pickup}
            onChangeText={t => handleTextChange(t, 'pickup')}
            onFocus={() => handleInputFocus('pickup')}
            autoCorrect={false}
            returnKeyType="next"
          />
          {renderSuggestions('pickup')}
        </View>

        <Text style={styles.label}>Dropoff Address</Text>
        <View style={[styles.inputWrapper, styles.dropoffWrapper]}>
          <TextInput
            style={styles.input}
            placeholder="e.g. 456 Fireside Dr, Cochrane, AB"
            placeholderTextColor="#888"
            value={dropoff}
            onChangeText={t => handleTextChange(t, 'dropoff')}
            onFocus={() => handleInputFocus('dropoff')}
            autoCorrect={false}
            returnKeyType="done"
            onSubmitEditing={handleCalculate}
          />
          {renderSuggestions('dropoff')}
        </View>

        <View style={styles.bottomSection}>
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
  // Each input lives in its own wrapper so the dropdown can be
  // absolutely positioned relative to it without shifting other elements.
  inputWrapper: {
    marginBottom: 20,
  },
  pickupWrapper: {
    zIndex: 10,
  },
  dropoffWrapper: {
    zIndex: 9,
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
  },
  // Suggestion dropdown — floats over whatever is below the active input.
  // top:50 matches the TextInput height (paddingVertical:14×2 + ~20px line height).
  dropdown: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    backgroundColor: '#16213e',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#2a2a4a',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.35,
    shadowRadius: 4,
  },
  dropdownItem: {
    paddingHorizontal: 16,
    paddingVertical: 13,
  },
  dropdownSep: {
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a4a',
  },
  dropdownText: {
    color: '#f5f5f5',
    fontSize: 14,
    lineHeight: 20,
  },
  // Explicit zIndex so both input dropdowns overlay the button/error text.
  bottomSection: {
    zIndex: 1,
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
