/**
 * FloodWatch AI — EOC deterministic DEMO/SIMULATION dataset (Mumbai, BMC).
 * ==========================================================================
 * ALL values here are illustrative simulation inputs for UI development.
 * They MUST NOT be presented as live measurements. The EOC shell renders a
 * persistent SIMULATION indicator whenever this dataset drives the display.
 * Replace with FastAPI/ML outputs (see eoc-data.service.ts) when available.
 */
import {
  DrainageLink,
  DrainageNode,
  EocIncident,
  FloodZone,
  HealthCheck,
  HorizonKey,
  RainfallSample,
  RouteAdvisory,
  SafeRoutePlan,
  Shelter,
  StormArchiveEntry,
  TelemetrySnapshot,
  VehicleKind,
} from '../models/eoc-models';

export const HORIZONS: HorizonKey[] = ['NOW', 'T+30', 'T+60', 'T+90', 'T+120'];

/** City anchor — Brihanmumbai Municipal Corporation (BMC Headquarters, Fort). */
export const MUMBAI_CENTER = { lat: 19.0760, lng: 72.8777 };

export const SIM_TELEMETRY: TelemetrySnapshot = {
  radarNowcastMmh: 64.2,
  peakNowcastMmh: 92.5,
  drainageLoadPct: 198,
  surchargeNodes: 21,
  totalNodes: 64,
  floodedRoads: 7,
  activeIncidents: 7,
  catchmentRiskIndex: 94,
  catchmentLoadPct: 198,
  soilSaturationPct: 78,
  predictedPeakAt: 'T+01:30',
  generatedAt: new Date().toISOString(),
};

export const SIM_RAINFALL_SERIES: RainfallSample[] = [
  { horizon: 'NOW', observedMmh: 64.2, predictedMmh: 64.2 },
  { horizon: 'T+30', observedMmh: null, predictedMmh: 78.4 },
  { horizon: 'T+60', observedMmh: null, predictedMmh: 92.5 },
  { horizon: 'T+90', observedMmh: null, predictedMmh: 84.1 },
  { horizon: 'T+120', observedMmh: null, predictedMmh: 61.7 },
];

export const SIM_ZONES: FloodZone[] = [
  {
    id: 'Z-KURLA', zoneName: 'Kurla Mithi River Basin', ward: 'Ward L (Kurla)',
    corridor: 'Mithi River Basin', lat: 19.0680, lng: 72.8800,
    optedInCitizens: 125, notifiedCitizens: 112,
    series: [
      { horizon: 'NOW', rainfallMmh: 58, waterDepthCm: 22, riskScore: 82, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 74, waterDepthCm: 38, riskScore: 90, riskLevel: 'CRITICAL', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 92, waterDepthCm: 55, riskScore: 96, riskLevel: 'CRITICAL', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 84, waterDepthCm: 61, riskScore: 97, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 60, waterDepthCm: 48, riskScore: 91, riskLevel: 'CRITICAL', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-HINDMATA', zoneName: 'Hindmata / Parel Bowl', ward: 'Ward F/South (Parel)',
    corridor: 'Hindmata Lowland Depression', lat: 19.0080, lng: 72.8430,
    optedInCitizens: 94, notifiedCitizens: 89,
    series: [
      { horizon: 'NOW', rainfallMmh: 61, waterDepthCm: 28, riskScore: 86, riskLevel: 'CRITICAL', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 79, waterDepthCm: 44, riskScore: 93, riskLevel: 'CRITICAL', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 95, waterDepthCm: 63, riskScore: 98, riskLevel: 'CRITICAL', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 86, waterDepthCm: 68, riskScore: 98, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 62, waterDepthCm: 52, riskScore: 92, riskLevel: 'CRITICAL', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-ANDHERI', zoneName: 'Andheri Subway Corridor', ward: 'Ward K/East (Andheri)',
    corridor: 'Western Railway Culvert Corridor', lat: 19.1180, lng: 72.8430,
    optedInCitizens: 78, notifiedCitizens: 74,
    series: [
      { horizon: 'NOW', rainfallMmh: 55, waterDepthCm: 24, riskScore: 80, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 71, waterDepthCm: 36, riskScore: 88, riskLevel: 'CRITICAL', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 88, waterDepthCm: 51, riskScore: 94, riskLevel: 'CRITICAL', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 80, waterDepthCm: 54, riskScore: 94, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 58, waterDepthCm: 41, riskScore: 87, riskLevel: 'CRITICAL', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-SION', zoneName: 'Sion Circle / Gandhi Market', ward: 'Ward F/North (Sion)',
    corridor: 'EEH Lowland Sump', lat: 19.0400, lng: 72.8620,
    optedInCitizens: 62, notifiedCitizens: 58,
    series: [
      { horizon: 'NOW', rainfallMmh: 44, waterDepthCm: 15, riskScore: 58, riskLevel: 'CAUTION', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 60, waterDepthCm: 24, riskScore: 71, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 76, waterDepthCm: 35, riskScore: 84, riskLevel: 'HIGH', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 69, waterDepthCm: 38, riskScore: 85, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 50, waterDepthCm: 29, riskScore: 76, riskLevel: 'HIGH', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-MILAN', zoneName: 'Milan Subway Santacruz', ward: 'Ward H/West (Santacruz)',
    corridor: 'Milan Subway Underpass', lat: 19.0830, lng: 72.8420,
    optedInCitizens: 88, notifiedCitizens: 81,
    series: [
      { horizon: 'NOW', rainfallMmh: 52, waterDepthCm: 18, riskScore: 66, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 68, waterDepthCm: 30, riskScore: 79, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 85, waterDepthCm: 44, riskScore: 90, riskLevel: 'CRITICAL', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 78, waterDepthCm: 47, riskScore: 91, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 56, waterDepthCm: 36, riskScore: 83, riskLevel: 'HIGH', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-BANDRA', zoneName: 'Bandra-Kurla Complex (BKC)', ward: 'Ward H/East (Bandra)',
    corridor: 'Mithi Estuary Inflow', lat: 19.0550, lng: 72.8650,
    optedInCitizens: 140, notifiedCitizens: 140,
    series: [
      { horizon: 'NOW', rainfallMmh: 30, waterDepthCm: 4, riskScore: 18, riskLevel: 'SAFE', state: 'CURRENT' },
      { horizon: 'T+30', rainfallMmh: 41, waterDepthCm: 6, riskScore: 24, riskLevel: 'LOW', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 52, waterDepthCm: 9, riskScore: 33, riskLevel: 'MEDIUM', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 47, waterDepthCm: 9, riskScore: 32, riskLevel: 'MEDIUM', state: 'RECEDING' },
      { horizon: 'T+120', rainfallMmh: 35, waterDepthCm: 6, riskScore: 24, riskLevel: 'LOW', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-MALAD', zoneName: 'Malad Subway & Marve Basin', ward: 'Ward P/North (Malad)',
    corridor: 'Poisar River Outfall', lat: 19.1860, lng: 72.8480,
    optedInCitizens: 54, notifiedCitizens: 47,
    series: [
      { horizon: 'NOW', rainfallMmh: 38, waterDepthCm: 11, riskScore: 47, riskLevel: 'MEDIUM', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 52, waterDepthCm: 18, riskScore: 60, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 66, waterDepthCm: 27, riskScore: 74, riskLevel: 'HIGH', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 60, waterDepthCm: 29, riskScore: 75, riskLevel: 'HIGH', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 44, waterDepthCm: 22, riskScore: 64, riskLevel: 'HIGH', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-DADAR', zoneName: 'Dadar TT Circle & Chitra', ward: 'Ward G/North (Dadar)',
    corridor: 'Central Island Basin', lat: 19.0178, lng: 72.8478,
    optedInCitizens: 71, notifiedCitizens: 63,
    series: [
      { horizon: 'NOW', rainfallMmh: 49, waterDepthCm: 20, riskScore: 70, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 66, waterDepthCm: 34, riskScore: 83, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 82, waterDepthCm: 52, riskScore: 93, riskLevel: 'CRITICAL', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 75, waterDepthCm: 68, riskScore: 95, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 54, waterDepthCm: 55, riskScore: 90, riskLevel: 'CRITICAL', state: 'RECEDING' },
    ],
  },
];

export const SIM_DRAINAGE_NODES: DrainageNode[] = [
  {
    id: 'NODE-MITHI-04', name: 'Mithi River Mahim Causeway Outfall', nodeType: 'OUTFALL',
    lat: 19.0425, lng: 72.8415, flowM3s: 41.2, hydraulicLoadPct: 264, waterLevelM: 4.8,
    surchargePct: 264, status: 'CRITICAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 198, status: 'CRITICAL' },
      { horizon: 'T+30', surchargePct: 231, status: 'CRITICAL' },
      { horizon: 'T+60', surchargePct: 264, status: 'CRITICAL' },
      { horizon: 'T+90', surchargePct: 258, status: 'CRITICAL' },
      { horizon: 'T+120', surchargePct: 226, status: 'CRITICAL' },
    ],
  },
  {
    id: 'NODE-BRITANNIA-OUTFALL', name: 'Britannia Pumping Station Outfall', nodeType: 'OUTFALL',
    lat: 18.9720, lng: 72.8520, flowM3s: 38.6, hydraulicLoadPct: 263, waterLevelM: 4.5,
    surchargePct: 263, status: 'CRITICAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 196, status: 'CRITICAL' },
      { horizon: 'T+30', surchargePct: 229, status: 'CRITICAL' },
      { horizon: 'T+60', surchargePct: 263, status: 'CRITICAL' },
      { horizon: 'T+90', surchargePct: 251, status: 'CRITICAL' },
      { horizon: 'T+120', surchargePct: 218, status: 'CRITICAL' },
    ],
  },
  {
    id: 'NODE-LOVEGROVE-OUTFALL', name: 'Lovegrove Worli Tidal Outfall', nodeType: 'OUTFALL',
    lat: 19.0040, lng: 72.8160, flowM3s: 36.1, hydraulicLoadPct: 260, waterLevelM: 4.3,
    surchargePct: 260, status: 'CRITICAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 188, status: 'CRITICAL' },
      { horizon: 'T+30', surchargePct: 224, status: 'CRITICAL' },
      { horizon: 'T+60', surchargePct: 260, status: 'CRITICAL' },
      { horizon: 'T+90', surchargePct: 247, status: 'CRITICAL' },
      { horizon: 'T+120', surchargePct: 210, status: 'CRITICAL' },
    ],
  },
  {
    id: 'NODE-ANDHERI-SUBWAY', name: 'Andheri Subway Low Point Sump', nodeType: 'MANHOLE',
    lat: 19.1180, lng: 72.8430, flowM3s: 12.4, hydraulicLoadPct: 250, waterLevelM: 3.9,
    surchargePct: 250, status: 'CRITICAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 176, status: 'WARNING' },
      { horizon: 'T+30', surchargePct: 214, status: 'CRITICAL' },
      { horizon: 'T+60', surchargePct: 250, status: 'CRITICAL' },
      { horizon: 'T+90', surchargePct: 238, status: 'CRITICAL' },
      { horizon: 'T+120', surchargePct: 199, status: 'CRITICAL' },
    ],
  },
  {
    id: 'NODE-MITHI-03', name: 'Kurla-BKC Siphon Reach', nodeType: 'REGULATOR',
    lat: 19.0680, lng: 72.8750, flowM3s: 22.8, hydraulicLoadPct: 168, waterLevelM: 3.1,
    surchargePct: 168, status: 'WARNING', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 121, status: 'WARNING' },
      { horizon: 'T+30', surchargePct: 144, status: 'WARNING' },
      { horizon: 'T+60', surchargePct: 168, status: 'WARNING' },
      { horizon: 'T+90', surchargePct: 161, status: 'WARNING' },
      { horizon: 'T+120', surchargePct: 138, status: 'WARNING' },
    ],
  },
  {
    id: 'NODE-BRITANNIA-PUMP', name: 'Britannia Storm Water Pumping Station', nodeType: 'PUMP STATION',
    lat: 18.9740, lng: 72.8490, flowM3s: 9.6, hydraulicLoadPct: 92, waterLevelM: 1.8,
    surchargePct: 92, status: 'NOMINAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 74, status: 'NOMINAL' },
      { horizon: 'T+30', surchargePct: 83, status: 'NOMINAL' },
      { horizon: 'T+60', surchargePct: 92, status: 'NOMINAL' },
      { horizon: 'T+90', surchargePct: 88, status: 'NOMINAL' },
      { horizon: 'T+120', surchargePct: 79, status: 'NOMINAL' },
    ],
  },
  {
    id: 'NODE-OSHIWARA-OUTFALL', name: 'Oshiwara River Tidal Outfall', nodeType: 'BARRAGE',
    lat: 19.1480, lng: 72.8190, flowM3s: 15.3, hydraulicLoadPct: 118, waterLevelM: 2.4,
    surchargePct: 118, status: 'WARNING', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 96, status: 'NOMINAL' },
      { horizon: 'T+30', surchargePct: 107, status: 'WARNING' },
      { horizon: 'T+60', surchargePct: 118, status: 'WARNING' },
      { horizon: 'T+90', surchargePct: 114, status: 'WARNING' },
      { horizon: 'T+120', surchargePct: 101, status: 'WARNING' },
    ],
  },
  {
    id: 'NODE-LOVEGROVE-PUMP', name: 'Lovegrove Storm Water Pumping Station', nodeType: 'SLUICE',
    lat: 19.0060, lng: 72.8180, flowM3s: 7.2, hydraulicLoadPct: 64, waterLevelM: 1.2,
    surchargePct: 64, status: 'NOMINAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 52, status: 'NOMINAL' },
      { horizon: 'T+30', surchargePct: 58, status: 'NOMINAL' },
      { horizon: 'T+60', surchargePct: 64, status: 'NOMINAL' },
      { horizon: 'T+90', surchargePct: 61, status: 'NOMINAL' },
      { horizon: 'T+120', surchargePct: 55, status: 'NOMINAL' },
    ],
  },
];

export const SIM_DRAINAGE_LINKS: DrainageLink[] = [
  { from: 'NODE-ANDHERI-SUBWAY', to: 'NODE-OSHIWARA-OUTFALL', path: [{ lat: 19.118, lng: 72.843 }, { lat: 19.135, lng: 72.830 }, { lat: 19.148, lng: 72.819 }] },
  { from: 'NODE-MITHI-03', to: 'NODE-MITHI-04', path: [{ lat: 19.068, lng: 72.875 }, { lat: 19.055, lng: 72.855 }, { lat: 19.0425, lng: 72.8415 }] },
  { from: 'NODE-BRITANNIA-PUMP', to: 'NODE-BRITANNIA-OUTFALL', path: [{ lat: 18.974, lng: 72.849 }, { lat: 18.972, lng: 72.852 }] },
  { from: 'NODE-LOVEGROVE-PUMP', to: 'NODE-LOVEGROVE-OUTFALL', path: [{ lat: 19.006, lng: 72.818 }, { lat: 19.004, lng: 72.816 }] },
];

export const SIM_INCIDENTS: EocIncident[] = [
  {
    id: 'INC-2041', severity: 'CRITICAL', location: 'Mithi River Corridor', ward: 'Ward L (Kurla)',
    description: 'Predicted river overflow approaching critical bank crest near Kurla-BKC border.',
    waterDepthCm: 44, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 12 * 60000).toISOString(),
    status: 'RESPONDING', actionLabel: 'Deploy NDRF inflatable boats',
  },
  {
    id: 'INC-2040', severity: 'CRITICAL', location: 'Kurla Mithi Basin', ward: 'Ward L (Kurla)',
    description: 'Rapid water accumulation and drainage surcharge detected near Kurla Station West.',
    waterDepthCm: 55, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 26 * 60000).toISOString(),
    status: 'RESPONDING', actionLabel: 'Activate dewatering pumps',
  },
  {
    id: 'INC-2039', severity: 'CRITICAL', location: 'Hindmata / Parel Bowl', ward: 'Ward F/South (Parel)',
    description: 'Severe saucer depression waterlogging on Dr. Ambedkar Road; traffic diverted.',
    waterDepthCm: 68, expectedAt: 'T+90', issuedAt: new Date(Date.now() - 34 * 60000).toISOString(),
    status: 'MONITORING', actionLabel: 'Divert to Lalbaug Flyover',
  },
  {
    id: 'INC-2038', severity: 'CRITICAL', location: 'Andheri Subway Corridor', ward: 'Ward K/East (Andheri)',
    description: 'Underpass depression filling faster than 3 submersible pumps discharge capacity.',
    waterDepthCm: 63, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 48 * 60000).toISOString(),
    status: 'RESPONDING', actionLabel: 'Close subway to traffic',
  },
  {
    id: 'INC-2037', severity: 'WARNING', location: 'Sion Circle / Gandhi Market', ward: 'Ward F/North (Sion)',
    description: 'Drainage capacity approaching threshold along Eastern Express Highway reach.',
    waterDepthCm: 35, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 63 * 60000).toISOString(),
    status: 'MONITORING', actionLabel: 'Monitor continuously',
  },
  {
    id: 'INC-2036', severity: 'WARNING', location: 'Milan Subway Santacruz', ward: 'Ward H/West (Santacruz)',
    description: 'Surface runoff accumulating; pumping station operational.',
    waterDepthCm: 27, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 81 * 60000).toISOString(),
    status: 'MONITORING', actionLabel: 'Alert traffic control room',
  },
  {
    id: 'INC-2035', severity: 'CAUTION', location: 'Bandra-Kurla Complex (BKC)', ward: 'Ward H/East (Bandra)',
    description: 'Minor waterlogging reported on BKC Connector ramp; traffic moving slow.',
    waterDepthCm: 9, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 104 * 60000).toISOString(),
    status: 'OPEN', actionLabel: 'Routine patrol',
  },
];

export const SIM_ROUTES: RouteAdvisory[] = [
  {
    id: 'RD-01', roadName: 'Western Express Highway (WEH)', corridor: 'Bandra → Andheri → Dahisar',
    floodDepthCm: 8, status: 'OPEN', recommendedAction: 'Preferred elevated arterial corridor',
    path: [{ lat: 19.055, lng: 72.840 }, { lat: 19.118, lng: 72.852 }, { lat: 19.220, lng: 72.860 }],
  },
  {
    id: 'RD-02', roadName: 'Eastern Express Highway (EEH)', corridor: 'Sion → Kurla → Mulund',
    floodDepthCm: 12, status: 'OPEN', recommendedAction: 'Elevated segments fully passable',
    path: [{ lat: 19.040, lng: 72.862 }, { lat: 19.070, lng: 72.890 }, { lat: 19.175, lng: 72.955 }],
  },
  {
    id: 'RD-03', roadName: 'Andheri Subway Underpass', corridor: 'Andheri East ↔ Andheri West',
    floodDepthCm: 68, status: 'CLOSED', recommendedAction: 'Closed due to surge. Divert via Gokhale Bridge flyover.',
    path: [{ lat: 19.118, lng: 72.843 }, { lat: 19.119, lng: 72.847 }],
  },
  {
    id: 'RD-04', roadName: 'Milan Subway Santacruz', corridor: 'Santacruz West ↔ WEH East',
    floodDepthCm: 62, status: 'CLOSED', recommendedAction: 'Subway flooded. Use Milan Flyover.',
    path: [{ lat: 19.083, lng: 72.842 }, { lat: 19.085, lng: 72.846 }],
  },
  {
    id: 'RD-05', roadName: 'Bandra-Worli Sea Link (BWSL)', corridor: 'Worli ↔ Bandra Toll Plaza',
    floodDepthCm: 0, status: 'OPEN', recommendedAction: 'Marine viaduct unaffected by surface ponding',
    path: [{ lat: 19.015, lng: 72.815 }, { lat: 19.035, lng: 72.818 }, { lat: 19.052, lng: 72.825 }],
  },
];

const RESCUE_PATH = [
  { lat: 19.040, lng: 72.862 }, { lat: 19.060, lng: 72.870 },
  { lat: 19.068, lng: 72.880 }, { lat: 19.076, lng: 72.8777 },
];

export function planSafeRoute(vehicle: VehicleKind): SafeRoutePlan {
  const base = {
    CAR: { name: 'EEH → BKC Connector → Kurla Relief Corridor', distanceKm: 8.6, etaMin: 22, maxDepthCm: 10 },
    SUV: { name: 'WEH → Kalina University Flyover → Kurla West', distanceKm: 7.4, etaMin: 18, maxDepthCm: 18 },
    TRUCK: { name: 'Eastern Freeway → SCLR Elevated Bypass', distanceKm: 11.2, etaMin: 28, maxDepthCm: 15 },
    RESCUE: { name: 'Emergency priority corridor (Elevated viaducts, min risk)', distanceKm: 6.8, etaMin: 14, maxDepthCm: 5 },
  }[vehicle];
  return { vehicle, path: RESCUE_PATH, ...base };
}

export const SIM_SHELTERS: Shelter[] = [
  { id: 'SH-01', name: 'Kurla Municipal Secondary School Relief Camp', lat: 19.0710, lng: 72.8820, capacity: 850, occupied: 340 },
  { id: 'SH-02', name: 'K. B. Bhabha Hospital Ground Hall', lat: 19.0650, lng: 72.8780, capacity: 600, occupied: 195 },
  { id: 'SH-03', name: 'Parel Shirodkar High School Shelter', lat: 19.0110, lng: 72.8420, capacity: 700, occupied: 420 },
];

export const SIM_ARCHIVE: StormArchiveEntry[] = [
  { id: 'ST-06', eventName: 'Mumbai Cloudburst & Mithi Inundation', eventDate: '2025-07-26', peakRainfallMmh: 94.4, maxDepthCm: 72, affectedZones: ['Kurla Mithi River Basin', 'Hindmata / Parel Bowl'], leadTimeMin: 48, isDemo: true },
  { id: 'ST-05', eventName: 'August 29 Flash Monsoon Surge', eventDate: '2025-08-29', peakRainfallMmh: 78.5, maxDepthCm: 56, affectedZones: ['Andheri Subway Corridor', 'Milan Subway Santacruz'], leadTimeMin: 42, isDemo: true },
  { id: 'ST-04', eventName: 'Sept High Tide + Downpour Event', eventDate: '2025-09-23', peakRainfallMmh: 86.2, maxDepthCm: 64, affectedZones: ['Sion Circle / Gandhi Market', 'Kurla Mithi River Basin'], leadTimeMin: 55, isDemo: true },
  { id: 'ST-03', eventName: 'Suburban Convective Trough', eventDate: '2025-09-14', peakRainfallMmh: 58.0, maxDepthCm: 32, affectedZones: ['Malad Subway & Marve Basin'], leadTimeMin: 35, isDemo: true },
  { id: 'ST-02', eventName: 'Monsoon Depression Wave II', eventDate: '2025-08-04', peakRainfallMmh: 52.4, maxDepthCm: 26, affectedZones: ['Dadar TT Circle & Chitra'], leadTimeMin: 38, isDemo: true },
  { id: 'ST-01', eventName: 'Pre-Monsoon Line Squall', eventDate: '2025-06-12', peakRainfallMmh: 42.1, maxDepthCm: 15, affectedZones: ['Bandra-Kurla Complex (BKC)'], leadTimeMin: 25, isDemo: true },
];

export const SIM_HEALTH: HealthCheck[] = [
  { id: 'radar', label: 'Doppler Weather Radar', status: 'ONLINE', detail: 'IMD Colaba & Veravali radar · sweep 4 min ago' },
  { id: 'rain', label: 'Rainfall Telemetry', status: 'ONLINE', detail: 'BMC Automatic Weather Station (AWS) network · 60 stations reporting' },
  { id: 'floodmodel', label: 'Flood Model', status: 'ONLINE', detail: 'Calibrated Mumbai XGBoost · inference 16 ms' },
  { id: 'drainmodel', label: 'Drainage Model', status: 'DEGRADED', detail: 'Mithi outfall sensor telemetry stale > 10 min' },
  { id: 'db', label: 'Database', status: 'ONLINE', detail: 'Primary reachable · replication lag 1.2 s' },
  { id: 'api', label: 'FastAPI Backend', status: 'ONLINE', detail: 'EOC feed connected to localhost:8000' },
];
