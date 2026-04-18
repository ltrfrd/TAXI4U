import { useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { cancelRide, createRide, getRideById } from '../services/api';

export default function ResultScreen({ navigation, route }) {
  const { token } = useAuth();
  const {
    result = null,
    existingRide = null,
    pickup_text = '',
    dropoff_text = '',
    pickup_lat = null,
    pickup_lon = null,
    dropoff_lat = null,
    dropoff_lon = null,
  } = route.params;

  const [booking, setBooking] = useState(false);
  const [bookingError, setBookingError] = useState(null);
  const [bookedRide, setBookedRide] = useState(existingRide);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState(null);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState(null);

  async function handleBook() {
    setBooking(true);
    setBookingError(null);
    try {
      const ride = await createRide(token, {
        pickup_text,
        dropoff_text,
        pickup_lat,
        pickup_lon,
        dropoff_lat,
        dropoff_lon,
        assignment_mode: 'auto',
      });
      setBookedRide(ride);
    } catch (err) {
      setBookingError(err.message || 'Booking failed.');
    } finally {
      setBooking(false);
    }
  }

  async function handleCancel() {
    if (!bookedRide?.id) return;
    setCancelling(true);
    setCancelError(null);
    try {
      const updated = await cancelRide(token, bookedRide.id);
      setBookedRide(updated);
    } catch (err) {
      setCancelError(err.message || 'Cancel failed.');
    } finally {
      setCancelling(false);
    }
  }

  async function handleRefresh() {
    if (!bookedRide?.id) return;
    setRefreshing(true);
    setRefreshError(null);
    try {
      const fresh = await getRideById(token, bookedRide.id);
      setBookedRide(fresh);
    } catch (err) {
      setRefreshError(err.message || 'Refresh failed.');
    } finally {
      setRefreshing(false);
    }
  }

  const showRefresh = bookedRide != null &&
    ['pending', 'assigned', 'accepted', 'in_progress'].includes(bookedRide.status);
  const showCancel = bookedRide?.status === 'pending';

  const fare = result?.fare;
  const isZoneFare = result?.fare_type === 'zone';
  const totalFare = isZoneFare ? fare?.total : fare?.total_fare;
  const distance = result?.route?.distance_km ?? null;
  const duration = result?.route?.duration_minutes ?? null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {result ? (
        <>
          <View style={styles.fareCard}>
            <Text style={styles.fareLabel}>Estimated Fare</Text>
            <Text style={styles.fareAmount}>${totalFare?.toFixed(2)}</Text>
            <Text style={styles.fareType}>
              {isZoneFare ? 'Zone-based pricing' : 'Distance-based pricing'}
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Zones</Text>
            <Row label="Pickup Zone" value={result.pickup_zone} />
            <Row label="Dropoff Zone" value={result.dropoff_zone} />
            <Row
              label="Detection"
              value={`Pickup: ${result.pickup_detection_confidence ?? '-'} | Dropoff: ${result.dropoff_detection_confidence ?? '-'}`}
            />
          </View>

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

          {isZoneFare && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Fare Breakdown</Text>
              <Row label="Base Fare" value={`$${fare.base_fare?.toFixed(2)}`} />
              <Row label="Stop Fee" value={`$${fare.stop_fee?.toFixed(2)}`} />
              <Row label="Wait Fee" value={`$${fare.wait_fee?.toFixed(2)}`} />
            </View>
          )}
        </>
      ) : null}

      {bookedRide ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Ride Status</Text>
          <Row label="Status"  value={bookedRide.status.replace('_', ' ')} />
          <Row label="Pickup"  value={bookedRide.pickup_text} />
          <Row label="Dropoff" value={bookedRide.dropoff_text} />
          {bookedRide.assigned_driver ? (
            <>
              <Row label="Driver" value={bookedRide.assigned_driver.name} />
              {bookedRide.assigned_driver.phone
                ? <Row label="Phone" value={bookedRide.assigned_driver.phone} />
                : null}
            </>
          ) : null}
          {(showRefresh || showCancel) ? (
            <View style={styles.statusActions}>
              {showCancel ? (
                <TouchableOpacity
                  style={[styles.cancelBtn, cancelling && { opacity: 0.5 }]}
                  onPress={handleCancel}
                  disabled={cancelling || refreshing}
                  activeOpacity={0.7}
                >
                  <Text style={styles.cancelBtnText}>{cancelling ? 'Cancelling…' : 'Cancel Ride'}</Text>
                </TouchableOpacity>
              ) : null}
              {showRefresh ? (
                <TouchableOpacity
                  style={[styles.refreshBtn, refreshing && { opacity: 0.5 }]}
                  onPress={handleRefresh}
                  disabled={refreshing || cancelling}
                  activeOpacity={0.7}
                >
                  <Text style={styles.refreshBtnText}>{refreshing ? 'Refreshing…' : 'Refresh Status'}</Text>
                </TouchableOpacity>
              ) : null}
            </View>
          ) : null}
          {(refreshError || cancelError) ? (
            <Text style={styles.refreshError}>{refreshError || cancelError}</Text>
          ) : null}
        </View>
      ) : (
        <>
          {bookingError ? <Text style={styles.bookError}>{bookingError}</Text> : null}
          <TouchableOpacity
            style={[styles.bookButton, booking && { opacity: 0.6 }]}
            onPress={handleBook}
            disabled={booking}
            activeOpacity={0.8}
          >
            <Text style={styles.bookButtonText}>{booking ? 'Booking…' : 'Book Ride'}</Text>
          </TouchableOpacity>
        </>
      )}

      {result ? (
        <TouchableOpacity
          style={styles.mapButton}
          onPress={() => navigation.navigate('Map', { result })}
          activeOpacity={0.8}
        >
          <Text style={styles.mapButtonText}>Open Live Map</Text>
        </TouchableOpacity>
      ) : null}

      <TouchableOpacity
        style={styles.backButton}
        onPress={() => navigation.goBack()}
        activeOpacity={0.8}
      >
        <Text style={styles.backButtonText}>{result ? 'New Fare Estimate' : 'Back'}</Text>
      </TouchableOpacity>
    </ScrollView>
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
  mapButton: {
    backgroundColor: '#f5c518',
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 4,
    marginBottom: 12,
  },
  mapButtonText: {
    color: '#1a1a2e',
    fontSize: 15,
    fontWeight: '700',
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
  bookButton: {
    backgroundColor: '#2ecc71',
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  bookButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
  bookConfirm: {
    backgroundColor: '#1a3a2a',
    borderRadius: 10,
    paddingVertical: 16,
    paddingHorizontal: 16,
    alignItems: 'center',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2ecc71',
  },
  bookConfirmText: {
    color: '#2ecc71',
    fontSize: 15,
    fontWeight: '600',
    textAlign: 'center',
  },
  bookError: {
    color: '#ff6b6b',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 8,
  },
  statusActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 8,
    marginTop: 10,
  },
  cancelBtn: {
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#ff6b6b',
  },
  cancelBtnText: {
    color: '#ff6b6b',
    fontSize: 12,
    fontWeight: '600',
  },
  refreshBtn: {
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#f5c518',
  },
  refreshBtnText: {
    color: '#f5c518',
    fontSize: 12,
    fontWeight: '600',
  },
  refreshError: {
    color: '#ff6b6b',
    fontSize: 12,
    marginTop: 6,
    textAlign: 'right',
  },
});
