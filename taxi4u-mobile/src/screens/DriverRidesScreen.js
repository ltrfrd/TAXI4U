import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { useAuth } from '../context/AuthContext';
import { getDriverRides, rideAction } from '../services/api';

const STATUS_COLOR = {
  pending:     '#f5c518',
  assigned:    '#4a90e2',
  accepted:    '#2ecc71',
  in_progress: '#f39c12',
  completed:   '#aab2cf',
  cancelled:   '#ff6b6b',
};

const PRIORITY = { assigned: 0, accepted: 1, in_progress: 2 };

// Buttons to show for each actionable status
const RIDE_ACTIONS = {
  assigned:    [
    { label: 'Accept',   action: 'accept',   variant: 'accept'  },
    { label: 'Decline',  action: 'decline',  variant: 'decline' },
  ],
  accepted:    [{ label: 'Start Trip',    action: 'start',    variant: 'start'    }],
  in_progress: [{ label: 'Complete Trip', action: 'complete', variant: 'complete' }],
};

export default function DriverRidesScreen() {
  const { token } = useAuth();
  const [rides, setRides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actioningId, setActioningId] = useState(null); // ride id currently being actioned
  const [error, setError] = useState('');

  const loadRides = useCallback(async (isRefresh = false) => {
    isRefresh ? setRefreshing(true) : setLoading(true);
    setError('');
    try {
      setRides(await getDriverRides(token));
    } catch (err) {
      setError(err.message || 'Failed to load rides.');
    } finally {
      isRefresh ? setRefreshing(false) : setLoading(false);
    }
  }, [token]);

  useFocusEffect(useCallback(() => { loadRides(); }, [loadRides]));

  async function handleAction(rideId, action) {
    if (actioningId) return; // guard against double-tap
    setActioningId(rideId);
    setError('');
    try {
      await rideAction(token, rideId, action);
      await loadRides(true);
    } catch (err) {
      setError(err.message || `Failed to ${action} ride.`);
    } finally {
      setActioningId(null);
    }
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#f5c518" />
      </View>
    );
  }

  const sorted = [...rides].sort(
    (a, b) => (PRIORITY[a.status] ?? 3) - (PRIORITY[b.status] ?? 3)
  );

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.content}
      data={sorted}
      keyExtractor={item => String(item.id)}
      renderItem={({ item, index }) => (
        <RideCard
          ride={item}
          onAction={handleAction}
          isActioning={actioningId === item.id}
          anyActioning={actioningId !== null}
          isTop={index === 0 && PRIORITY[item.status] !== undefined}
        />
      )}
      refreshing={refreshing}
      onRefresh={() => loadRides(true)}
      ListHeaderComponent={
        <View>
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <TouchableOpacity
            style={[styles.refreshBtn, refreshing && { opacity: 0.5 }]}
            onPress={() => loadRides(true)}
            disabled={refreshing}
            activeOpacity={0.7}
          >
            <Text style={styles.refreshBtnText}>{refreshing ? 'Refreshing…' : '↻ Refresh'}</Text>
          </TouchableOpacity>
        </View>
      }
      ListEmptyComponent={<Text style={styles.empty}>No rides assigned yet.</Text>}
    />
  );
}

function RideCard({ ride, onAction, isActioning, anyActioning, isTop }) {
  const color = STATUS_COLOR[ride.status] ?? '#aab2cf';
  const actions = RIDE_ACTIONS[ride.status] ?? [];

  return (
    <View style={[styles.card, isTop && { borderColor: color, borderWidth: 2 }]}>
      <View style={styles.routeRow}>
        <Text style={styles.routeText} numberOfLines={1}>{ride.pickup_text}</Text>
        <Text style={styles.arrow}>→</Text>
        <Text style={styles.routeText} numberOfLines={1}>{ride.dropoff_text}</Text>
      </View>

      <View style={styles.metaRow}>
        <View style={[styles.badge, { borderColor: color }]}>
          <Text style={[styles.badgeText, { color }]}>
            {ride.status.replace('_', ' ')}
          </Text>
        </View>

        {ride.fare_amount != null ? (
          <Text style={styles.fare}>${ride.fare_amount.toFixed(2)}</Text>
        ) : null}
      </View>

      {ride.assigned_at ? (
        <Text style={styles.time}>
          Assigned {new Date(ride.assigned_at).toLocaleString()}
        </Text>
      ) : null}

      {actions.length > 0 ? (
        <View style={styles.actionRow}>
          {actions.map(({ label, action, variant }) => (
            <TouchableOpacity
              key={action}
              style={[
                styles.actionBtn,
                styles[`btn_${variant}`],
                (anyActioning) && styles.btnDisabled,
              ]}
              onPress={() => onAction(ride.id, action)}
              disabled={anyActioning}
            >
              {isActioning ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={styles.actionBtnText}>{label}</Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      ) : null}
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
  },
  error: {
    color: '#ff6b6b',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 12,
  },
  empty: {
    color: '#aab2cf',
    fontSize: 15,
    textAlign: 'center',
    marginTop: 48,
  },
  card: {
    backgroundColor: '#16213e',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2a2a4a',
    padding: 16,
    marginBottom: 12,
  },
  routeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 10,
  },
  routeText: {
    flex: 1,
    color: '#f5f5f5',
    fontSize: 14,
    fontWeight: '500',
  },
  arrow: {
    color: '#f5c518',
    fontSize: 16,
    fontWeight: 'bold',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  badge: {
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  fare: {
    color: '#f5c518',
    fontSize: 14,
    fontWeight: '700',
  },
  time: {
    color: '#aab2cf',
    fontSize: 12,
    marginTop: 8,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 14,
  },
  actionBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 38,
  },
  actionBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#fff',
  },
  btnDisabled: {
    opacity: 0.5,
  },
  refreshBtn: {
    alignSelf: 'flex-end',
    marginBottom: 8,
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
  btn_accept:   { backgroundColor: '#2ecc71' },
  btn_decline:  { backgroundColor: 'transparent', borderWidth: 1, borderColor: '#ff6b6b' },
  btn_start:    { backgroundColor: '#f5c518' },
  btn_complete: { backgroundColor: '#2ecc71' },
});
