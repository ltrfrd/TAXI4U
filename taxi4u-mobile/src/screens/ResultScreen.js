import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

export default function ResultScreen({ navigation, route }) {
  const { result } = route.params;

  const fare = result.fare;
  const isZoneFare = result.fare_type === 'zone';
  const totalFare = isZoneFare ? fare.total : fare.total_fare;
  const distance = result.route?.distance_km ?? null;
  const duration = result.route?.duration_minutes ?? null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>

      {/* Fare amount — most important, shown first */}
      <View style={styles.fareCard}>
        <Text style={styles.fareLabel}>Estimated Fare</Text>
        <Text style={styles.fareAmount}>${totalFare?.toFixed(2)}</Text>
        <Text style={styles.fareType}>
          {isZoneFare ? 'Zone-based pricing' : 'Distance-based pricing'}
        </Text>
      </View>

      {/* Zone info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Zones</Text>
        <Row label="Pickup Zone" value={result.pickup_zone} />
        <Row label="Dropoff Zone" value={result.dropoff_zone} />
        <Row label="Detection" value={
          `Pickup: ${result.pickup_detection_confidence ?? '—'}  ·  Dropoff: ${result.dropoff_detection_confidence ?? '—'}`
        } />
      </View>

      {/* Route info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Route</Text>
        <Row
          label="Distance"
          value={distance !== null ? `${distance} km` : 'Unavailable'}
        />
        <Row
          label="Duration"
          value={duration !== null ? `${duration} min` : 'Unavailable'}
        />
      </View>

      {/* Zone fare breakdown when applicable */}
      {isZoneFare && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Fare Breakdown</Text>
          <Row label="Base Fare" value={`$${fare.base_fare?.toFixed(2)}`} />
          <Row label="Stop Fee" value={`$${fare.stop_fee?.toFixed(2)}`} />
          <Row label="Wait Fee" value={`$${fare.wait_fee?.toFixed(2)}`} />
        </View>
      )}

      <TouchableOpacity
        style={styles.backButton}
        onPress={() => navigation.goBack()}
        activeOpacity={0.8}
      >
        <Text style={styles.backButtonText}>New Fare Estimate</Text>
      </TouchableOpacity>

    </ScrollView>
  );
}

function Row({ label, value }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value ?? '—'}</Text>
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
  fareCard: {
    backgroundColor: '#f5c518',
    borderRadius: 16,
    padding: 28,
    alignItems: 'center',
    marginBottom: 24,
  },
  fareLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1a1a2e',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 8,
  },
  fareAmount: {
    fontSize: 52,
    fontWeight: 'bold',
    color: '#1a1a2e',
    lineHeight: 60,
  },
  fareType: {
    fontSize: 13,
    color: '#3a3a1e',
    marginTop: 6,
  },
  section: {
    backgroundColor: '#16213e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#2a2a4a',
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#f5c518',
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
  backButton: {
    backgroundColor: '#16213e',
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#f5c518',
  },
  backButtonText: {
    color: '#f5c518',
    fontSize: 15,
    fontWeight: '600',
  },
});
