import { fetchZones as fetchZonesFromApi } from '../services/api';

export const DEFAULT_MAP_REGION = {
  latitude: 51.1896,
  longitude: -114.4671,
  latitudeDelta: 0.11,
  longitudeDelta: 0.11,
};

export async function fetchZones() {
  const zones = await fetchZonesFromApi();

  return zones
    .slice()
    .sort((left, right) => left.priority - right.priority)
    .map((zone) => ({
      name: zone.name,
      priority: zone.priority,
      color: zone.color || '#f5c518',
      polygon: zone.polygon,
    }));
}
