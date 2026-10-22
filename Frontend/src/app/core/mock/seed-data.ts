import { FloodZone, RoadSegment, SystemKPIs, RecentPrediction, PredictionTime } from '../models/flood-risk.model';
import { FloodAlert } from '../models/alert.model';
import { RoutePlanResult, PresetRoute } from '../models/route.model';
import { AnalyticsSummary } from '../models/analytics.model';
import { AdminSystemOverview } from '../models/system-status.model';

export const SEED_SYSTEM_KPIS: SystemKPIs = {
  currentRainfall: 28.4,
  rainfallDelta: '+4.2 mm/hr vs last hour',
  highRiskZones: 12,
  highRiskDelta: '2 more than previous hour',
  unsafeRoads: 3,
  unsafeRoadsStatus: 'Andheri, Khar & Milan Subways Monitored',
  activeAlerts: 3,
  highPriorityAlerts: 2,
  lastUpdated: 'Live BMC IMD AWS Pipeline • Mumbai Baseline',
  isSimulated: true
};

export const SEED_RECENT_PREDICTIONS: RecentPrediction[] = [
  { location: 'Kurla Mithi River Basin', currentRisk: 'HIGH', plus1HourRisk: 'CRITICAL', plus3HoursRisk: 'HIGH', confidence: 94, isSimulated: true },
  { location: 'Hindmata / Parel Bowl', currentRisk: 'HIGH', plus1HourRisk: 'CRITICAL', plus3HoursRisk: 'MEDIUM', confidence: 95, isSimulated: true },
  { location: 'Andheri Subway Corridor', currentRisk: 'HIGH', plus1HourRisk: 'CRITICAL', plus3HoursRisk: 'MEDIUM', confidence: 96, isSimulated: true },
  { location: 'Sion Circle / Gandhi Market', currentRisk: 'MEDIUM', plus1HourRisk: 'HIGH', plus3HoursRisk: 'MEDIUM', confidence: 90, isSimulated: true },
  { location: 'Chembur SCLR Sector', currentRisk: 'MEDIUM', plus1HourRisk: 'HIGH', plus3HoursRisk: 'LOW', confidence: 87, isSimulated: true },
  { location: 'Bandra West / Linking Road', currentRisk: 'LOW', plus1HourRisk: 'LOW', plus3HoursRisk: 'LOW', confidence: 92, isSimulated: true },
  { location: 'Dadar TT Circle', currentRisk: 'LOW', plus1HourRisk: 'MEDIUM', plus3HoursRisk: 'LOW', confidence: 85, isSimulated: true }
];

export const SEED_FLOOD_ZONES: FloodZone[] = [
  {
    gridId: 'MUM_G101',
    name: 'Kurla Mithi River Catchment Lowlands',
    latitude: 19.0680,
    longitude: 72.8800,
    bounds: [[19.060, 72.870], [19.076, 72.890]],
    riskLevel: 'HIGH',
    riskScore: 96,
    predictionTime: 'NOW',
    rainfall: 58.5,
    elevation: 3.2,
    waterDepth: null,
    runoffCoefficient: 0.94,
    slope: 'Low',
    summary: 'Low-lying Mithi River floodplain depression with severe runoff accumulation and chronic tidal outfall congestion.',
    historicalFlooding: 'Severe',
    drainageStatus: 'Critical',
    builtUpDensity: 94,
    isSimulated: true
  },
  {
    gridId: 'MUM_G102',
    name: 'Hindmata / Parel Bowl Depression',
    latitude: 19.0080,
    longitude: 72.8430,
    bounds: [[19.000, 72.835], [19.016, 72.851]],
    riskLevel: 'HIGH',
    riskScore: 95,
    predictionTime: 'NOW',
    rainfall: 52.0,
    elevation: 2.8,
    waterDepth: null,
    runoffCoefficient: 0.96,
    slope: 'Low',
    summary: 'Saucer-shaped depression bowl on Dr. Ambedkar Road prone to rapid inundation during intense monsoon downpours.',
    historicalFlooding: 'Severe',
    drainageStatus: 'Critical',
    builtUpDensity: 96,
    isSimulated: true
  },
  {
    gridId: 'MUM_G103',
    name: 'Andheri Subway Rail Underpass',
    latitude: 19.1197,
    longitude: 72.8464,
    bounds: [[19.112, 72.839], [19.127, 72.854]],
    riskLevel: 'HIGH',
    riskScore: 94,
    predictionTime: 'NOW',
    rainfall: 54.0,
    elevation: 2.4,
    waterDepth: null,
    runoffCoefficient: 0.95,
    slope: 'Low',
    summary: 'Sub-grade railway underpass connecting East and West Andheri; chronic choke point requiring flood barriers.',
    historicalFlooding: 'Severe',
    drainageStatus: 'Critical',
    builtUpDensity: 95,
    isSimulated: true
  },
  {
    gridId: 'MUM_G104',
    name: 'Sion Circle / Gandhi Market Basin',
    latitude: 19.0400,
    longitude: 72.8620,
    bounds: [[19.032, 72.854], [19.048, 72.870]],
    riskLevel: 'MEDIUM',
    riskScore: 82,
    predictionTime: 'NOW',
    rainfall: 44.0,
    elevation: 4.1,
    waterDepth: null,
    runoffCoefficient: 0.88,
    slope: 'Low',
    summary: 'King Circle / Gandhi Market lowlands on Eastern Express Highway corridor, vulnerable during high tide rainfall.',
    historicalFlooding: 'High',
    drainageStatus: 'Moderate',
    builtUpDensity: 89,
    isSimulated: true
  },
  {
    gridId: 'MUM_G105',
    name: 'Milan Subway Low-Lying Underpass',
    latitude: 19.0880,
    longitude: 72.8420,
    bounds: [[19.080, 72.834], [19.096, 72.850]],
    riskLevel: 'MEDIUM',
    riskScore: 78,
    predictionTime: 'NOW',
    rainfall: 41.5,
    elevation: 3.6,
    waterDepth: null,
    runoffCoefficient: 0.90,
    slope: 'Low',
    summary: 'Santacruz rail underpass depression; dewatering pump stations deployed for arterial relief.',
    historicalFlooding: 'High',
    drainageStatus: 'Moderate',
    builtUpDensity: 91,
    isSimulated: true
  },
  {
    gridId: 'MUM_G106',
    name: 'Bandra West / Linking Road Corridor',
    latitude: 19.0544,
    longitude: 72.8402,
    bounds: [[19.046, 72.832], [19.062, 72.848]],
    riskLevel: 'LOW',
    riskScore: 28,
    predictionTime: 'NOW',
    rainfall: 32.0,
    elevation: 8.5,
    waterDepth: null,
    runoffCoefficient: 0.76,
    slope: 'Moderate',
    summary: 'Coastal western suburban commercial ridge with rapid gravity stormwater discharge to Arabian Sea outfalls.',
    historicalFlooding: 'Low',
    drainageStatus: 'Operational',
    builtUpDensity: 88,
    isSimulated: true
  },
  {
    gridId: 'MUM_G107',
    name: 'Chembur SCLR Commercial Basin',
    latitude: 19.0620,
    longitude: 72.9000,
    bounds: [[19.054, 72.892], [19.070, 72.908]],
    riskLevel: 'LOW',
    riskScore: 24,
    predictionTime: 'NOW',
    rainfall: 31.0,
    elevation: 10.2,
    waterDepth: null,
    runoffCoefficient: 0.74,
    slope: 'Moderate',
    summary: 'Elevated junction on Santacruz-Chembur Link Road with wide culverts and unobstructed storm channels.',
    historicalFlooding: 'Low',
    drainageStatus: 'Operational',
    builtUpDensity: 85,
    isSimulated: true
  },
  {
    gridId: 'MUM_G108',
    name: 'Malad Western Link Road Lowlands',
    latitude: 19.1860,
    longitude: 72.8485,
    bounds: [[19.178, 72.840], [19.194, 72.857]],
    riskLevel: 'LOW',
    riskScore: 30,
    predictionTime: 'NOW',
    rainfall: 35.0,
    elevation: 7.2,
    waterDepth: null,
    runoffCoefficient: 0.78,
    slope: 'Low',
    summary: 'Suburban link road corridor; Malad Creek tidal drainage active.',
    historicalFlooding: 'Low',
    drainageStatus: 'Operational',
    builtUpDensity: 86,
    isSimulated: true
  }
];

export const SEED_ROAD_SEGMENTS: RoadSegment[] = [
  {
    id: 'RD-MUM-01',
    name: 'Andheri Subway Rail Underpass',
    status: 'BLOCKED',
    riskScore: 96,
    waterDepthCm: null,
    coordinates: [[19.118, 72.845], [19.120, 72.847], [19.122, 72.849]],
    avoidedBySafeRoute: true,
    locality: 'Andheri West'
  },
  {
    id: 'RD-MUM-02',
    name: 'Milan Subway Low-Lying Underpass',
    status: 'UNSAFE',
    riskScore: 92,
    waterDepthCm: null,
    coordinates: [[19.086, 72.840], [19.088, 72.842], [19.090, 72.844]],
    avoidedBySafeRoute: true,
    locality: 'Santacruz'
  },
  {
    id: 'RD-MUM-03',
    name: 'Hindmata Dr. Ambedkar Road Depression',
    status: 'BLOCKED',
    riskScore: 95,
    waterDepthCm: null,
    coordinates: [[19.006, 72.841], [19.008, 72.843], [19.010, 72.845]],
    avoidedBySafeRoute: true,
    locality: 'Parel / Hindmata'
  },
  {
    id: 'RD-MUM-04',
    name: 'Kurla LBS Marg (Mithi River Crossing)',
    status: 'CAUTION',
    riskScore: 78,
    waterDepthCm: null,
    coordinates: [[19.066, 72.878], [19.068, 72.880], [19.070, 72.882]],
    avoidedBySafeRoute: false,
    locality: 'Kurla West'
  },
  {
    id: 'RD-MUM-05',
    name: 'Eastern Freeway South Elevated Corridor',
    status: 'SAFE',
    riskScore: 12,
    waterDepthCm: null,
    coordinates: [[18.940, 72.835], [18.980, 72.855], [19.025, 72.876]],
    avoidedBySafeRoute: false,
    locality: 'Wadala / South Mumbai'
  },
  {
    id: 'RD-MUM-06',
    name: 'Bandra-Worli Sea Link Elevated Viaduct',
    status: 'SAFE',
    riskScore: 10,
    waterDepthCm: null,
    coordinates: [[19.015, 72.815], [19.035, 72.818], [19.054, 72.840]],
    avoidedBySafeRoute: false,
    locality: 'Bandra-Worli Bay'
  }
];

export const SEED_ALERTS: FloodAlert[] = [
  {
    id: 'ALT-MUM-101',
    title: 'Severe Inundation — Andheri Subway Rail Underpass',
    severity: 'HIGH',
    location: 'Andheri Subway, Andheri West',
    coordinates: [19.1197, 72.8464],
    description: 'Depression depth reaches critical threshold due to high rainfall intensity. Brihanmumbai Traffic Police have placed traffic barriers.',
    riskScore: 96,
    predictionHorizon: '+30 Minutes',
    generatedTime: '3 minutes ago',
    timestamp: '2026-09-06T15:30:00Z',
    acknowledged: false,
    aiConfidence: 96,
    recommendedAction: 'Divert all westbound traffic via Gokhale Flyover or Jogeshwari-Vikhroli Link Road (JVLR).',
    isSimulated: true
  },
  {
    id: 'ALT-MUM-102',
    title: 'Extreme Waterlogging Risk — Kurla Mithi Catchment',
    severity: 'HIGH',
    location: 'LBS Marg / Kurla Station Corridor',
    coordinates: [19.0680, 72.8800],
    description: 'Runoff accumulation along low-lying residential sectors. Mithi River water levels rising near bankfull capacity.',
    riskScore: 94,
    predictionHorizon: '+1 Hour',
    generatedTime: '8 minutes ago',
    timestamp: '2026-09-06T15:25:00Z',
    acknowledged: false,
    aiConfidence: 94,
    recommendedAction: 'Caution advised for suburban buses and light vehicles. Utilize elevated SCLR viaducts.',
    isSimulated: true
  },
  {
    id: 'ALT-MUM-103',
    title: 'Lowland Bowl Waterlogging — Hindmata Parel',
    severity: 'HIGH',
    location: 'Hindmata Flyover Service Lanes, Dadar-Parel',
    coordinates: [19.0080, 72.8430],
    description: 'Depression bowl water levels rising. Dewatering high-capacity pump sets activated at Britannia and Lovegrove outfalls.',
    riskScore: 93,
    predictionHorizon: '+30 Minutes',
    generatedTime: '12 minutes ago',
    timestamp: '2026-09-06T15:20:00Z',
    acknowledged: false,
    aiConfidence: 95,
    recommendedAction: 'Surface traffic diverted via Hindmata Flyover upper deck. Avoid lower service lanes.',
    isSimulated: true
  },
  {
    id: 'ALT-MUM-104',
    title: 'Moderate Flow Surge — Sion Circle / Gandhi Market',
    severity: 'MEDIUM',
    location: 'Gandhi Market, King Circle / Sion',
    coordinates: [19.0400, 72.8620],
    description: 'Elevated water stages along Eastern Express Highway low spots. Precautionary flood monitoring active.',
    riskScore: 76,
    predictionHorizon: '+2 Hours',
    generatedTime: '24 minutes ago',
    timestamp: '2026-09-06T15:08:00Z',
    acknowledged: false,
    aiConfidence: 91,
    recommendedAction: 'Maintain reduced speeds along Dr. Ambedkar Road. Utilize Sion Flyover corridor.',
    isSimulated: true
  }
];

export const SEED_PRESET_ROUTES: PresetRoute[] = [
  {
    id: 'PRESET_MUM_CST_AIR',
    label: 'CSMT Fort → Mumbai Airport CSMIA (via Eastern Freeway / WEH)',
    source: 'CSMT Fort',
    destination: 'CSMIA International Airport',
    description: 'Primary metropolitan transit corridor connecting South Mumbai heritage commercial core to international airport terminal.'
  },
  {
    id: 'PRESET_MUM_DAD_BKC',
    label: 'Dadar TT Circle → Bandra-Kurla Complex (BKC)',
    source: 'Dadar TT Circle',
    destination: 'Bandra-Kurla Complex (BKC)',
    description: 'Essential financial corridor bypassing Mahim Bay and Mithi River lowlands.'
  },
  {
    id: 'PRESET_MUM_BOR_BAN',
    label: 'Borivali → Bandra West (Western Express Highway Corridor)',
    source: 'Borivali',
    destination: 'Bandra Western Spine',
    description: 'Major North-South suburban arterial corridor connecting Northern suburbs to coastal bridges.'
  },
  {
    id: 'PRESET_MUM_SIO_KUR',
    label: 'Sion Circle → Kurla Mithi Basin',
    source: 'Sion Circle',
    destination: 'Kurla Mithi River Corridor',
    description: 'Cross-catchment arterial route linking Central Mumbai to Eastern Express Highway.'
  }
];

export const SEED_ROUTE_PLAN: RoutePlanResult = {
  source: 'CSMT Fort',
  destination: 'CSMIA International Airport',
  sourceCoords: [18.9400, 72.8353],
  destCoords: [19.0896, 72.8656],
  recommendedRoute: {
    id: 'ROUTE_SAFE_MUMBAI',
    name: 'High-Ground Arterial Bypass (CSMT -> Eastern Freeway -> SCLR -> Airport)',
    type: 'RECOMMENDED_SAFE',
    distanceKm: 21.4,
    etaMinutes: 38,
    safetyScore: 94,
    riskStatus: 'SAFE',
    floodPointsAvoided: 3,
    hazardExposure: 'Low',
    pathCoordinates: [
      [18.9400, 72.8353],
      [19.0250, 72.8760],
      [19.0620, 72.9000],
      [19.0896, 72.8656]
    ],
    notes: 'Route prioritizes elevated Eastern Freeway viaducts and SCLR, completely avoiding Hindmata and submerged subways.',
    isSimulated: true
  },
  alternativeRoute: {
    id: 'ROUTE_ALT_MUMBAI',
    name: 'Surface Low-Elevation Route (Via Hindmata Bowl & Kurla Mithi Basin)',
    type: 'FASTER_ALTERNATIVE',
    distanceKm: 18.2,
    etaMinutes: 58,
    safetyScore: 38,
    riskStatus: 'UNSAFE',
    floodPointsAvoided: 0,
    hazardExposure: 'High',
    pathCoordinates: [
      [18.9400, 72.8353],
      [19.0080, 72.8430],
      [19.0400, 72.8620],
      [19.0680, 72.8800],
      [19.0896, 72.8656]
    ],
    notes: 'Direct surface path, but encounters severe waterlogging hazards at Hindmata depression and low-lying Kurla Mithi catchment.',
    isSimulated: true
  },
  hazards: [
    {
      id: 'HAZ_MUM_01',
      title: 'Hindmata Lowland Depression',
      location: 'Hindmata Bowl (Parel)',
      coordinates: [19.0080, 72.8430],
      severity: 'UNSAFE',
      waterDepthCm: 65,
      status: 'Depression flooded (-2.5m underpass) • Impassable for light vehicles',
      isSimulated: true
    },
    {
      id: 'HAZ_MUM_02',
      title: 'Andheri Subway Rail Underpass',
      location: 'Andheri Subway Underpass',
      coordinates: [19.1180, 72.8430],
      severity: 'UNSAFE',
      waterDepthCm: 75,
      status: 'Subway waterlogged • Traffic diverted to Gokhale Bridge',
      isSimulated: true
    },
    {
      id: 'HAZ_MUM_03',
      title: 'Kurla Mithi River Overspill',
      location: 'Kurla Mithi River Basin',
      coordinates: [19.0680, 72.8800],
      severity: 'UNSAFE',
      waterDepthCm: 55,
      status: 'Severe waterlogging • Water level exceeding road surface threshold',
      isSimulated: true
    }
  ],
  isSimulated: true
};

export const SEED_ANALYTICS_SUMMARY: AnalyticsSummary = {
  rainfallTrends: [
    { time: '09:00 AM', rainfallMm: 10.5, cumulativeMm: 10.5, isSimulated: true },
    { time: '10:00 AM', rainfallMm: 16.2, cumulativeMm: 26.7, isSimulated: true },
    { time: '11:00 AM', rainfallMm: 24.8, cumulativeMm: 51.5, isSimulated: true },
    { time: '12:00 PM', rainfallMm: 31.0, cumulativeMm: 82.5, isSimulated: true },
    { time: '01:00 PM', rainfallMm: 38.4, cumulativeMm: 120.9, isSimulated: true },
    { time: '02:00 PM', rainfallMm: 35.0, cumulativeMm: 155.9, isSimulated: true },
    { time: '03:00 PM', rainfallMm: 42.1, cumulativeMm: 198.0, isSimulated: true }
  ],
  riskDistribution: {
    noRisk: 1450,
    low: 1820,
    medium: 510,
    high: 165,
    critical: 18
  },
  areaRankings: [
    { rank: 1, area: 'Kurla Mithi River Basin', riskScore: 96, trend: 'INCREASING', rainfall: 64.2, elevation: 4.2 },
    { rank: 2, area: 'Hindmata / Parel Bowl', riskScore: 94, trend: 'INCREASING', rainfall: 58.0, elevation: 3.5 },
    { rank: 3, area: 'Andheri Subway Underpass', riskScore: 92, trend: 'INCREASING', rainfall: 54.5, elevation: 2.8 },
    { rank: 4, area: 'Sion Circle / Gandhi Market', riskScore: 82, trend: 'STABLE', rainfall: 48.0, elevation: 5.1 },
    { rank: 5, area: 'Milan Subway / Santacruz', riskScore: 78, trend: 'STABLE', rainfall: 44.0, elevation: 3.2 },
    { rank: 6, area: 'Malad Subway / SV Road', riskScore: 72, trend: 'DECREASING', rainfall: 40.5, elevation: 4.8 },
    { rank: 7, area: 'Dharavi Transit Lowland', riskScore: 65, trend: 'DECREASING', rainfall: 36.0, elevation: 5.5 }
  ],
  inundationHistory: [
    { hour: '-6h', avgWaterDepthCm: 6.5, affectedRoadsCount: 2 },
    { hour: '-4h', avgWaterDepthCm: 14.0, affectedRoadsCount: 3 },
    { hour: '-2h', avgWaterDepthCm: 28.5, affectedRoadsCount: 7 },
    { hour: 'NOW', avgWaterDepthCm: 44.0, affectedRoadsCount: 12 },
    { hour: '+1h', avgWaterDepthCm: 51.5, affectedRoadsCount: 15 },
    { hour: '+2h', avgWaterDepthCm: 38.0, affectedRoadsCount: 9 }
  ],
  peakRainfallLocality: 'Kurla Mithi River Basin IMD AWS (64.2 mm/hr peak intensity)',
  totalVulnerablePopulation: '2,150,000 across 12 Low-Lying BMC Wards',
  isSimulated: true
};

export const SEED_ADMIN_SYSTEM_OVERVIEW: AdminSystemOverview = {
  dataFeeds: [
    {
      name: 'IMD Mumbai Doppler Weather Radar (Colaba / Veravali)',
      category: 'RADAR',
      status: 'OPERATIONAL',
      lastUpdate: '2 min ago',
      sampleFrequency: '10 min',
      sourceType: 'S-Band Dual Polarimetric Doppler',
      isSimulated: false
    },
    {
      name: 'BMC & IMD Automatic Weather Stations (AWS)',
      category: 'IOT',
      status: 'OPERATIONAL',
      lastUpdate: 'Just now',
      sampleFrequency: '15 min',
      sourceType: 'Telemetric Rain Gauges (Santacruz, Colaba, BKC, etc.)',
      isSimulated: false
    },
    {
      name: 'Greater Mumbai GIS Cadastral & 500m Grid (EPSG:32643 / WGS84)',
      category: 'GIS',
      status: 'OPERATIONAL',
      lastUpdate: 'Static Master (1,767 Cells)',
      sampleFrequency: 'Permanent',
      sourceType: 'Copernicus 30m DEM & BMC Administrative Boundary',
      isSimulated: false
    },
    {
      name: 'Mumbai Arterial, Sea Link & Subways Road Graph',
      category: 'ROAD_NETWORK',
      status: 'OPERATIONAL',
      lastUpdate: 'Continuous',
      sampleFrequency: 'Event-driven',
      sourceType: 'NetworkX Dynamic Dijkstra Graph',
      isSimulated: false
    },
    {
      name: 'BMC Historical Waterlogging & Chronic Flooding Registry',
      category: 'HISTORICAL',
      status: 'OPERATIONAL',
      lastUpdate: 'Benchmark Registry',
      sampleFrequency: 'Annual',
      sourceType: 'BMC Disaster Management Department & MCGM',
      isSimulated: false
    }
  ],
  modelMetrics: {
    name: 'Mumbai Spatial Flood Susceptibility Baseline (XGBoost)',
    version: 'XGBoost-v1.0-Mumbai',
    status: 'ACTIVE_BASELINE',
    algorithm: 'Gradient Boosted Decision Trees (XGBoostClassifier)',
    prototypeF1Score: 0.9490,
    prototypePrecision: 0.9650,
    prototypeRecall: 0.9340,
    prototypeAccuracy: 0.9720,
    simulatedInferenceLatencyMs: 24.0,
    featureCount: 25,
    lastTrained: 'BMC Chronological Baseline & Hotspot Registry',
    isSimulated: false
  },
  microservices: [
    {
      name: 'FastAPI Core Gateway',
      endpoint: 'http://localhost:8000/api/v1',
      status: 'OPERATIONAL',
      latencyMs: 12.5,
      uptime: '99.98%',
      version: '2.0.0',
      isMock: false
    },
    {
      name: 'XGBoost Baseline Inference Worker',
      endpoint: 'internal://engine.predict_grids',
      status: 'OPERATIONAL',
      latencyMs: 24.0,
      uptime: '100.0%',
      version: 'XGBoost-v1.0-Mumbai',
      isMock: false
    },
    {
      name: 'NetworkX Safe Routing Dijkstra Engine',
      endpoint: 'internal://engine.calculate_safe_route',
      status: 'OPERATIONAL',
      latencyMs: 8.2,
      uptime: '100.0%',
      version: 'v1.2',
      isMock: false
    },
    {
      name: 'BMC IMD Rain Gauge Telemetry Worker',
      endpoint: 'internal://data.pipeline.telemetry',
      status: 'OPERATIONAL',
      latencyMs: 18.0,
      uptime: '99.95%',
      version: 'v1.0',
      isMock: false
    }
  ],
  systemLoad: {
    cpuPercent: 16.2,
    memoryPercent: 38.5,
    activeQueriesPerSec: 22.4
  },
  sihDisclaimer: {
    projectCode: 'SIH26085',
    notice: 'Trained on Greater Mumbai 500m spatial grid (1,767 cells) with 25 topographical, hydrological, and BMC waterlogging features.',
    phase: 'Phase 2 — End-to-End Mumbai Nowcasting + Safe Mobility'
  }
};

export const SEED_ANALYTICS: AnalyticsSummary = SEED_ANALYTICS_SUMMARY;
export const SEED_ADMIN_SYSTEM: AdminSystemOverview = SEED_ADMIN_SYSTEM_OVERVIEW;

export const SEED_ROUTE_PLANS: Record<string, RoutePlanResult> = {
  'Central_Airport': SEED_ROUTE_PLAN,
  'CSMT_Airport': SEED_ROUTE_PLAN,
  'CSMT Fort_CSMIA International Airport': SEED_ROUTE_PLAN,
  'Dadar_BKC': {
    ...SEED_ROUTE_PLAN,
    source: 'Dadar TT Circle',
    destination: 'Bandra-Kurla Complex (BKC)',
    sourceCoords: [19.0178, 72.8478],
    destCoords: [19.0650, 72.8680]
  },
  'Borivali_Bandra': {
    ...SEED_ROUTE_PLAN,
    source: 'Borivali',
    destination: 'Bandra Western Spine',
    sourceCoords: [19.2300, 72.8570],
    destCoords: [19.0544, 72.8402]
  }
};
