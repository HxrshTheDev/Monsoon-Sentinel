export type RiskLevel = 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type PredictionTime = 'NOW' | '+30M' | '+1H' | '+2H' | '+3H';

export interface FloodZone {
  gridId: string;
  name: string;
  latitude: number;
  longitude: number;
  bounds: [[number, number], [number, number]]; // Leaflet LatLngBoundsExpression
  riskLevel: RiskLevel;
  riskScore: number; // 0 - 100
  predictionTime: PredictionTime;
  rainfall: number; // mm (scenario baseline unless live feed connected)
  elevation: number; // meters
  /** Continuous depth is unmeasured — always null from the Mumbai backend. */
  waterDepth: number | null;
  runoffCoefficient: number; // 0.0 - 1.0
  slope: string;
  summary: string;
  historicalFlooding: string;
  drainageStatus: string;
  builtUpDensity: number; // percentage e.g. 82%
  isSimulated: boolean;
  probability?: number;
  provenanceStatus?: string;
}

export interface RoadSegment {
  id: string;
  name: string;
  status: 'SAFE' | 'CAUTION' | 'UNSAFE' | 'BLOCKED';
  riskScore: number;
  /** Unmeasured unless a depth model exists — null in Mumbai prototype. */
  waterDepthCm: number | null;
  coordinates: [number, number][];
  avoidedBySafeRoute: boolean;
  locality: string;
}

export interface SystemKPIs {
  currentRainfall: number;
  rainfallDelta: string;
  highRiskZones: number;
  highRiskDelta: string;
  unsafeRoads: number;
  unsafeRoadsStatus: string;
  activeAlerts: number;
  highPriorityAlerts: number;
  lastUpdated: string;
  isSimulated: boolean;
}

export interface RecentPrediction {
  location: string;
  currentRisk: RiskLevel;
  plus1HourRisk: RiskLevel;
  plus3HoursRisk: RiskLevel;
  confidence: number;
  isSimulated: boolean;
}
