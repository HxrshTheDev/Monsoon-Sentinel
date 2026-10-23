# API reference

FastAPI REST API for the Greater Mumbai susceptibility and disruption
decision-support prototype.

- Base URL: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

All forecast and route-risk results are scenario/model outputs. They are not
calibrated flood probabilities, live rainfall observations, road-closure
confirmations, or emergency instructions. Continuous water depth is returned
as `null`.

## Health and metadata

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | Project metadata and API location (outside `/api/v1`). |
| GET | `/health` | Gateway and service health. |
| GET | `/health/system-overview` | Data, model, road-cache, and evaluation diagnostics. |

## Flood susceptibility

| Method | Path | Query/body | Description |
| --- | --- | --- | --- |
| GET | `/current-risk/kpis` | — | Current scenario KPI summary. |
| GET | `/forecast-risk` | `horizon`: `NOW`, `+30M`, `+1H`, `+2H`, or `+3H` | Scores the 500 m Mumbai grid. |
| GET | `/forecast-risk/recent` | — | Recent prediction records. |
| GET | `/hotspots` | `limit` from 1 to 100 | Ranks the highest model scores. |
| GET | `/flood/hotspots` | `limit` from 1 to 100 | Compatibility alias for `/hotspots`. |
| GET | `/depth` | `location` | Depth response; depth is unavailable in this prototype. |
| GET | `/flood/depth` | `location` | Compatibility alias for `/depth`. |
| GET | `/map-data/zones/{grid_id}` | — | Returns one grid-cell result. |
| GET | `/location-risk` | `location` | Looks up a named locality. |
| GET | `/predict-eta` | `rainfall_rate_mm_h`, `accumulated_rainfall_mm` | Scenario inundation ETA estimate. |
| GET | `/rainfall/telemetry-details` | — | Deterministic scenario payload labelled `SCENARIO_DEMO`. |

`forecast-risk` returns `Array<FloodZone>`. A zone includes `gridId`,
coordinates, `riskLevel`, `riskScore`, `predictionTime`, scenario rainfall,
`waterDepth: null`, `isSimulated: true`, and provenance fields. Consult the
OpenAPI schema at `/openapi.json` for the authoritative field types.

## Safe mobility and network analysis

| Method | Path | Description |
| --- | --- | --- |
| GET | `/safe-route/presets` | Predefined Mumbai route inputs. |
| POST | `/safe-route` | Compares a risk-penalized route with a shortest route when distinct. |
| GET | `/criticality/roads` | Road-edge betweenness and bridge indicators. |
| GET | `/criticality/network-overview` | Network node, edge, and critical-bridge summary. |

Example request:

```json
{
  "source": "CSMT Fort",
  "destination": "CSMIA International Airport",
  "vehicle_type": "car"
}
```

The route cache is
`data/processed/roads/mumbai_drive_network.json.gz`. Route coordinates use
Leaflet order `[latitude, longitude]`; stored cache geometry uses GeoJSON
`[longitude, latitude]`. The risk penalty is
`length_m + length_m * RISK_PENALTY_FACTOR * risk^RISK_PENALTY_EXPONENT`.
Missing cache errors are reported as HTTP 503 and invalid snapping/path input
as HTTP 422.

## Accessibility and prioritization

| Method | Path | Description |
| --- | --- | --- |
| GET | `/accessibility/analysis` | Compares baseline and disrupted access to facilities; accepts `scenario_threshold`. |
| GET | `/accessibility/facilities` | Lists facilities; accepts `facility_type` (`all`, `hospital`, `fire_station`, or `police`). |
| GET | `/accessibility/emergency/facilities` | Emergency-facility compatibility route. |
| POST | `/prioritization/rank` | Ranks inspection candidates using supplied weights. |
| POST | `/prioritization/compare` | Compares hazard-only and network-aware strategies; accepts `budget_k`. |

## Analytics and decision reports

| Method | Path | Description |
| --- | --- | --- |
| GET | `/analytics/summary` | Scenario rainfall trends, risk distribution, rankings, and depth-unavailable history. |
| GET | `/analytics/decision-report` | Combines KPIs, network overview, budget comparison, and inspection priorities. |

See [architecture.md](architecture.md) for the request flow and
[data_sources.md](data_sources.md) for provenance and limitations.
