import { resolveApiBaseUrl } from '../app/core/utils/api-base-url';

const configuredApiBaseUrl = 'http://localhost:8000';

export const environment = {
  production: false,
  useMockData: false,
  /** Prefer LAN-reachable host when the page is not on localhost. */
  apiBaseUrl: resolveApiBaseUrl(configuredApiBaseUrl),
  appName: 'CityPulse',
  appSubtitle: 'Monsoon Sentinel — Greater Mumbai Flood Decision Support',
  sihProjectCode: 'SIH26085',
  version: '2.1.0-mumbai',
  city: 'Mumbai',
  state: 'Maharashtra',
  jurisdiction: 'BMC / MCGM',
  defaultMapCenter: { lat: 19.0760, lon: 72.8777 },
  mapBounds: { minLat: 18.89, maxLat: 19.30, minLon: 72.75, maxLon: 73.02 }
};
