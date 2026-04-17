import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import MapView, { Marker, Polygon } from 'react-native-maps';
import * as Location from 'expo-location';
import { useFocusEffect } from '@react-navigation/native';
import { DEFAULT_MAP_REGION, fetchZones } from '../data/zones';
import { findZoneForCoordinates } from '../utils/zoneDetection';

export default function MapScreen({ route }) {
  const { result } = route.params;
  const mapRef = useRef(null);
  const [liveLocation, setLiveLocation] = useState(null);
  const [currentZone, setCurrentZone] = useState(null);
  const [previousZone, setPreviousZone] = useState(null);
  const [lastZoneChangeTime, setLastZoneChangeTime] = useState(null);
  const [permissionState, setPermissionState] = useState('pending');
  const [permissionError, setPermissionError] = useState(null);
  const [zones, setZones] = useState([]);
  const [zonesError, setZonesError] = useState(null);

  const pickupCoordinate = toMarkerCoordinate(result?.pickup_coords);
  const dropoffCoordinate = toMarkerCoordinate(result?.dropoff_coords);

  const initialRegion = useMemo(
    () => buildInitialRegion([pickupCoordinate, dropoffCoordinate].filter(Boolean)),
    [pickupCoordinate, dropoffCoordinate]
  );

  useEffect(() => {
    let active = true;

    async function loadZones() {
      try {
        setZonesError(null);
        const nextZones = await fetchZones();

        if (active) {
          setZones(nextZones);
        }
      } catch (error) {
        if (active) {
          setZonesError(error.message || 'Unable to load zones.');
        }
      }
    }

    loadZones();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const coordinates = [pickupCoordinate, dropoffCoordinate].filter(Boolean);

    if (!mapRef.current || !coordinates.length) {
      return;
    }

    mapRef.current.fitToCoordinates(coordinates, {
      animated: true,
      edgePadding: { top: 80, right: 60, bottom: 260, left: 60 },
    });
  }, [pickupCoordinate, dropoffCoordinate]);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      let subscription;

      async function startWatching() {
        try {
          setPermissionError(null);
          const permission = await Location.requestForegroundPermissionsAsync();

          if (!active) {
            return;
          }

          if (permission.status !== 'granted') {
            setPermissionState('denied');
            setPermissionError('Location permission is required for the live driver marker.');
            return;
          }

          setPermissionState('granted');

          const currentPosition = await Location.getCurrentPositionAsync({
            accuracy: Location.Accuracy.Balanced,
          });

          if (active) {
            handleLocationUpdate(currentPosition.coords);
          }

          subscription = await Location.watchPositionAsync(
            {
              accuracy: Location.Accuracy.Balanced,
              distanceInterval: 10,
              timeInterval: 3000,
            },
            (location) => {
              if (active) {
                handleLocationUpdate(location.coords);
              }
            }
          );
        } catch (error) {
          if (active) {
            setPermissionState('error');
            setPermissionError(error.message || 'Unable to start live location updates.');
          }
        }
      }

      function handleLocationUpdate(coords) {
        const nextLocation = {
          latitude: coords.latitude,
          longitude: coords.longitude,
        };
        const nextZone = findZoneForCoordinates(coords.latitude, coords.longitude, zones);

        setLiveLocation(nextLocation);
        setCurrentZone((activeZone) => {
          if (activeZone !== nextZone) {
            if (activeZone) {
              setPreviousZone(activeZone);
            }
            setLastZoneChangeTime(new Date());
          }

          return nextZone;
        });
      }

      startWatching();

      return () => {
        active = false;
        if (subscription) {
          subscription.remove();
        }
      };
    }, [zones])
  );

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        style={styles.map}
        initialRegion={initialRegion}
        showsCompass
        showsScale
      >
        {zones.map((zone) => {
          const isActive = zone.name === currentZone;

          return (
            <Polygon
              key={zone.name}
              coordinates={zone.polygon}
              strokeColor={isActive ? zone.color : `${zone.color}CC`}
              fillColor={isActive ? `${zone.color}66` : `${zone.color}2A`}
              strokeWidth={isActive ? 4 : 2}
            />
          );
        })}

        {pickupCoordinate ? (
          <Marker coordinate={pickupCoordinate} title="Pickup" pinColor="#2ecc71" />
        ) : null}

        {dropoffCoordinate ? (
          <Marker coordinate={dropoffCoordinate} title="Dropoff" pinColor="#e74c3c" />
        ) : null}

        {liveLocation ? (
          <Marker coordinate={liveLocation} title="Driver" pinColor="#f5c518" />
        ) : null}
      </MapView>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>Live Zone Map</Text>
        <InfoRow label="Current Zone" value={currentZone || 'Outside mapped zones'} />
        {previousZone ? <InfoRow label="Previous Zone" value={previousZone} /> : null}
        <InfoRow
          label="Last Zone Change"
          value={lastZoneChangeTime ? formatTimestamp(lastZoneChangeTime) : 'Waiting for zone entry'}
        />
        <InfoRow
          label="Coordinates"
          value={
            liveLocation
              ? `${liveLocation.latitude.toFixed(5)}, ${liveLocation.longitude.toFixed(5)}`
              : 'Waiting for location'
          }
        />
        {permissionState === 'pending' ? (
          <View style={styles.statusRow}>
            <ActivityIndicator size="small" color="#f5c518" />
            <Text style={styles.statusText}>Requesting location permission...</Text>
          </View>
        ) : null}
        {permissionError ? <Text style={styles.errorText}>{permissionError}</Text> : null}
        {zonesError ? <Text style={styles.errorText}>{zonesError}</Text> : null}
      </View>
    </View>
  );
}

function toMarkerCoordinate(coords) {
  if (!coords || typeof coords.lat !== 'number' || typeof coords.lon !== 'number') {
    return null;
  }

  return {
    latitude: coords.lat,
    longitude: coords.lon,
  };
}

function buildInitialRegion(coordinates) {
  if (!coordinates.length) {
    return DEFAULT_MAP_REGION;
  }

  if (coordinates.length === 1) {
    return {
      ...coordinates[0],
      latitudeDelta: 0.04,
      longitudeDelta: 0.04,
    };
  }

  const latitudes = coordinates.map((point) => point.latitude);
  const longitudes = coordinates.map((point) => point.longitude);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  const minLon = Math.min(...longitudes);
  const maxLon = Math.max(...longitudes);

  return {
    latitude: (minLat + maxLat) / 2,
    longitude: (minLon + maxLon) / 2,
    latitudeDelta: Math.max((maxLat - minLat) * 1.8, 0.04),
    longitudeDelta: Math.max((maxLon - minLon) * 1.8, 0.04),
  };
}

function formatTimestamp(date) {
  return date.toLocaleTimeString([], {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  });
}

function InfoRow({ label, value }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  map: {
    flex: 1,
  },
  infoCard: {
    position: 'absolute',
    left: 16,
    right: 16,
    bottom: 20,
    backgroundColor: 'rgba(22, 33, 62, 0.96)',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2a2a4a',
  },
  infoTitle: {
    color: '#f5c518',
    fontSize: 14,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    paddingVertical: 4,
  },
  infoLabel: {
    color: '#aab2cf',
    fontSize: 13,
    flex: 1,
  },
  infoValue: {
    color: '#f5f5f5',
    fontSize: 13,
    fontWeight: '600',
    flex: 1.4,
    textAlign: 'right',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
  },
  statusText: {
    color: '#f5f5f5',
    marginLeft: 8,
    fontSize: 13,
  },
  errorText: {
    color: '#ff7b7b',
    fontSize: 13,
    marginTop: 10,
  },
});
