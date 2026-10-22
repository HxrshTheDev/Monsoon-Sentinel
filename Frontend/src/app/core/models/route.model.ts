export type RouteType = 'RECOMMENDED_SAFE' | 'FASTER_ALTERNATIVE';
export type RouteRiskStatus = 'SAFE' | 'CAUTION' | 'UNSAFE';

export interface RouteOption {
  id: string;
  name: string;
  type: RouteType;
  distanceKm: number;
  etaMinutes: number;
  safetyScore: number;
  riskStatus: RouteRiskStatus;
  floodPointsAvoided: number;
  hazardExposure: 'Low' | 'Medium' | 'High';
  riskExposureScore?: number;
  highRiskEdgeCount?: number;
  pathCoordinates: [number, number][]; // [lat, lon] Leaflet order
  nodesVisited?: string[];
  notes: string;
  isSimulated: boolean;
  geometrySource?: string;
}

export interface RouteHazard {
  id: string;
  title: string;
  location: string;
  coordinates: [number, number];
  severity: 'CAUTION' | 'UNSAFE';
  waterDepthCm: number;
  status: string;
  isSimulated: boolean;
}

export interface RoutePlanResult {
  source: string;
  destination: string;
  sourceCoords: [number, number];
  destCoords: [number, number];
  recommendedRoute: RouteOption;
  alternativeRoute?: RouteOption | null;
  alternativeUnavailableReason?: string | null;
  hazards: RouteHazard[];
  networkProvenance?: string;
  geometrySource?: string;
  warnings?: string[];
  isSimulated: boolean;
}

export interface PresetRoute {
  id: string;
  label: string;
  source: string;
  destination: string;
  description: string;
}
