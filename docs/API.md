# CityPulse / Monsoon Sentinel — API Specification (v2.1.0)

## Greater Mumbai (BMC / MCGM) flood susceptibility & decision-support API

FastAPI Gateway Base URL: `http://localhost:8000/api/v1`  
Interactive Swagger Docs: `http://localhost:8000/docs`  
ReDoc Docs: `http://localhost:8000/redoc`

Scores are prototype susceptibility estimates under scenario rainfall — not calibrated flood probabilities. Water depth is always unmeasured (`null`).

---

## 1. System Health & Metadata

### `GET /`
Returns top-level project metadata and endpoints.

### `GET /api/v1/health`
Returns gateway and microservice liveness.

**Response**:
```json
{
  "status": "healthy",
  "service": "CityPulse API Gateway",
  "study_area": "Greater Mumbai (BMC)",
  "model": "XGBoost-v1.1-Mumbai-HotspotProxy",
  "timestamp": "now"
}
```

### `GET /api/v1/health/system-overview`
Returns complete MLOps telemetry, data feeds status, model evaluation card, and hardware loads.

---

## 2. Flood Nowcasting & Geospatial Telemetry

### `GET /api/v1/current-risk/kpis`
Returns live municipal KPIs across Greater Mumbai.

**Response**:
```json
{
  "currentRainfall": 32.2,
  "rainfallDelta": "+6.4 mm/hr vs last hour",
  "highRiskZones": 1584,
  "highRiskDelta": "+3 zones expanding east",
  "unsafeRoads": 3,
  "unsafeRoadsStatus": "Hindmata, Milan & Andheri Subways Blocked",
  "activeAlerts": 4,
  "highPriorityAlerts": 3,
  "lastUpdated": "10:30 UTC • Live BMC AWS Pipeline",
  "isSimulated": false
}
```

### `GET /api/v1/forecast-risk`
Returns high-resolution 500m grid sector predictions for the requested horizon.

**Query Parameters**:
* `horizon` (string, optional, default: `"NOW"`): Temporal nowcasting horizon (`NOW`, `+30M`, `+1H`, `+2H`, `+3H`).

**Response**: `Array<FloodZone>`
```json
[
  {
    "gridId": "MUM_000001",
    "name": "Colaba / Fort",
    "latitude": 18.8977,
    "longitude": 72.7873,
    "bounds": [[18.8955, 72.7851], [18.8999, 72.7895]],
    "riskLevel": "LOW",
    "riskScore": 22,
    "predictionTime": "NOW",
    "rainfall": 30.4,
    "elevation": 14.5,
    "waterDepth": 0.08,
    "runoffCoefficient": 0.72,
    "slope": "Low",
    "summary": "Colaba / Fort sector under LOW flood risk for horizon NOW.",
    "historicalFlooding": "Low",
    "drainageStatus": "Operational",
    "builtUpDensity": 72,
    "isSimulated": false
  }
]
```

### `GET /api/v1/map-data/zones/{grid_id}`
Returns telemetry for a specific 500m sector.

### `GET /api/v1/map-data/roads`
Returns flood status assigned to Mumbai arterial road segments.

---

## 3. Safe Mobility & Graph Dijkstra Routing

Uses the cached OpenStreetMap drive network (`data/processed/roads/mumbai_drive_network.json.gz`).
Routes follow real highway geometry (no synthetic bay chords). Flood-aware weighted route minimizes
`length_m + length_m * RISK_PENALTY_FACTOR * risk^RISK_PENALTY_EXPONENT`; the alternative is shortest distance when distinct.
`pathCoordinates` are `[lat, lon]` (Leaflet). HTTP 422 when snap/path fails; 503 if the road cache is missing.

### `GET /api/v1/safe-route/presets`
Returns predefined Mumbai commute scenarios (e.g., CSMT → CSMIA, Dadar → Bandra).

### `POST /api/v1/safe-route`
Calculates flood-aware vs shortest paths on the OSM road graph.

**Request Body**:
```json
{
  "source": "Sion Circle",
  "destination": "Bandra-Kurla Complex (BKC)",
  "vehicle_type": "rescue"
}
```

The response contains `recommendedRoute` and, when a distinct route exists,
`alternativeRoute`. Each option includes `distanceKm` (sum of mapped edge lengths),
`etaMinutes` (sum of edge free-flow estimates), `pathCoordinates` in Leaflet
`[latitude, longitude]` order, risk metrics, `unknownRiskEdgeCount`, and geometry
provenance. `sourceCoords` and `destCoords` are the snapped OSM road nodes; any
snap offset is included in `warnings`.

`riskSource` identifies the flood-risk data. The current XGBoost input is a
scenario-based susceptibility estimate, not live water depth or road-closure
observations (`riskIsSimulated: true`). Unknown edge risk is penalized and
reported; `safetyScore` is only the inverse modeled susceptibility indicator,
and `riskStatus` never means that a road has been confirmed safe.

---

## 4. Disaster Alerts

### `GET /api/v1/alerts`
Returns active emergency warnings and evacuation alerts.

### `PATCH /api/v1/alerts/{alert_id}/acknowledge`
Acknowledges a specific alert by EOC incident commanders.

---

## 5. Flood Analytics

### `GET /api/v1/analytics/summary`
Returns hourly rainfall curves, sector risk distribution, ranked vulnerable areas, and inundation timelines.
