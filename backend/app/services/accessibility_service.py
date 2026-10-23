"""
Essential-Service Accessibility Service (CityPulse)
Evaluates emergency transit times from population clusters to hospitals,
fire stations, and police headquarters under baseline and flood-disrupted scenarios.
"""

from typing import Dict, Any, List, Optional
import networkx as nx

from backend.app.core.config import settings
from backend.app.services.data_loader_service import DataLoaderService
from backend.app.services.road_network_service import RoadNetworkService
from backend.app.services.flood_service import FloodService
from backend.app.schemas.provenance import ProvenanceStatus


class AccessibilityService:
    _instance: Optional["AccessibilityService"] = None

    @classmethod
    def get_instance(cls) -> "AccessibilityService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.loader = DataLoaderService.get_instance()
        self.road_service = RoadNetworkService.get_instance()
        self.flood_service = FloodService.get_instance()

        # Key population origin clusters across Greater Mumbai (nodes snapped to OSM)
        raw_origins = [
            {"id": "ORIGIN-KURLA", "name": "Kurla Mithi Catchment Lowlands", "lat": 19.0680, "lon": 72.8800},
            {"id": "ORIGIN-SION", "name": "Sion Circle / Gandhi Market Lowlands", "lat": 19.0400, "lon": 72.8620},
            {"id": "ORIGIN-HINDMATA", "name": "Hindmata / Parel Lowland Bowl", "lat": 19.0080, "lon": 72.8430},
            {"id": "ORIGIN-ANDHERI", "name": "Andheri West / SV Road Catchment", "lat": 19.1197, "lon": 72.8464},
            {"id": "ORIGIN-BANDRA", "name": "Bandra West / Khar Sector", "lat": 19.0544, "lon": 72.8402},
            {"id": "ORIGIN-CHEMBUR", "name": "Chembur / Trombay Sector", "lat": 19.0620, "lon": 72.9000},
            {"id": "ORIGIN-MALAD", "name": "Malad Western Lowlands", "lat": 19.1860, "lon": 72.8485},
            {"id": "ORIGIN-BORIVALI", "name": "Borivali / Dahisar Gateway", "lat": 19.2300, "lon": 72.8570},
        ]
        self.origins = []
        for o in raw_origins:
            node = self._snap_node(o["lat"], o["lon"])
            self.origins.append({**o, "node": node})

        # Key destination facilities — snap lat/lon onto the OSM road graph
        raw_facilities = [
            {"id": "HOSP-KEM-01", "name": "King Edward Memorial Hospital (KEM Hospital)", "facility_type": "hospital", "category": "Level 1 Trauma Center", "lat": 19.0028, "lon": 72.8431},
            {"id": "HOSP-SION-02", "name": "Lokmanya Tilak Municipal General Hospital (Sion Hospital)", "facility_type": "hospital", "category": "Metropolitan Disaster Trauma Center", "lat": 19.0378, "lon": 72.8606},
            {"id": "HOSP-LILAVATI-03", "name": "Lilavati Hospital & Research Centre", "facility_type": "hospital", "category": "Emergency Cardiac & Trauma", "lat": 19.0514, "lon": 72.8295},
            {"id": "HOSP-KDAH-04", "name": "Kokilaben Dhirubhai Ambani Hospital", "facility_type": "hospital", "category": "Western Suburbs Trauma Center", "lat": 19.1312, "lon": 72.8252},
            {"id": "HOSP-BHABHA-05", "name": "K. B. Bhabha Municipal General Hospital Kurla", "facility_type": "hospital", "category": "Suburban Municipal Trauma Center", "lat": 19.0650, "lon": 72.8790},
            {"id": "FIRE-BYCULLA-01", "name": "Mumbai Fire Brigade Headquarters", "facility_type": "fire_station", "category": "Metropolitan Dispatch", "lat": 18.9780, "lon": 72.8310},
            {"id": "FIRE-ANDHERI-02", "name": "Andheri Fire & Rescue Station", "facility_type": "fire_station", "category": "Mid-Suburbs Heavy Rescue Hub", "lat": 19.1180, "lon": 72.8490},
            {"id": "FIRE-KURLA-03", "name": "Kurla Fire & Rescue Station", "facility_type": "fire_station", "category": "Mithi Catchment Flood Dispatch", "lat": 19.0680, "lon": 72.8780},
            {"id": "POLICE-HQ-01", "name": "Mumbai Police Commissionerate Headquarters", "facility_type": "police", "category": "Metropolitan Command", "lat": 18.9440, "lon": 72.8340},
            {"id": "POLICE-BANDRA-02", "name": "Bandra Police Divisional Headquarters", "facility_type": "police", "category": "Divisional Command", "lat": 19.0550, "lon": 72.8350},
            {"id": "POLICE-KURLA-03", "name": "Kurla Police Station Hub", "facility_type": "police", "category": "Divisional Command", "lat": 19.0670, "lon": 72.8795},
        ]
        self.destination_facilities = []
        for fac in raw_facilities:
            self.destination_facilities.append({**fac, "node": self._snap_node(fac["lat"], fac["lon"])})

    def _snap_node(self, lat: float, lon: float) -> str:
        """Snap a facility/origin coordinate to the nearest OSM road node."""
        if not self.road_service.network_available:
            return f"UNSNAPPED-{lat:.4f}-{lon:.4f}"
        node, _dist = self.road_service.get_nearest_node_to_coords(lat, lon)
        return node

    def evaluate_accessibility(self, scenario_threshold: float = 0.40) -> Dict[str, Any]:
        """
        Evaluates baseline vs disrupted travel times across all population origins.
        `scenario_threshold` defines the flood susceptibility above which links experience degradation or disruption.
        """
        # Baseline free-flow graph
        G_base = self.road_service.graph

        # Construct disrupted graph under scenario (honour directed / one-way OSM edges)
        G_disrupted = nx.DiGraph()
        G_disrupted.add_nodes_from(G_base.nodes)
        for ed in self.road_service.edge_definitions:
            u, v = ed["u"], ed["v"]
            base_time = ed["free_flow_time_min"]
            is_bridge = ed.get("is_bridge", False)
            risk = settings.UNKNOWN_RISK_DEFAULT
            zone = self.flood_service.get_location_risk(ed["locality"])
            if zone and zone.get("probability") is not None:
                risk = float(zone["probability"])

            name_l = (ed.get("name") or "").lower()
            is_subway = "subway" in name_l or "underpass" in name_l or ed.get("is_tunnel")
            if is_subway and risk >= 0.70:
                continue

            if is_bridge:
                if risk >= scenario_threshold:
                    impedance = base_time * (2.2 + (risk * 2.8))
                else:
                    impedance = base_time * (1.0 + (risk * 0.5))
            else:
                if risk >= 0.85:
                    continue
                elif risk >= scenario_threshold:
                    impedance = base_time * (3.0 + (risk * 4.0))
                else:
                    impedance = base_time * (1.0 + (risk * 0.8))

            G_disrupted.add_edge(u, v, weight=impedance)

        results = []
        isolated_count = 0
        severely_delayed_count = 0
        total_delay_sum = 0.0

        for orig in self.origins:
            o_node = orig["node"]

            # Compute access to nearest hospital, fire station, and police
            hosp_access = self._find_nearest_facility(G_base, G_disrupted, o_node, "hospital")
            fire_access = self._find_nearest_facility(G_base, G_disrupted, o_node, "fire_station")
            pol_access = self._find_nearest_facility(G_base, G_disrupted, o_node, "police")

            delays = [hosp_access["delay_min"], fire_access["delay_min"], pol_access["delay_min"]]
            avg_delay = sum(delays) / len(delays)
            total_delay_sum += avg_delay

            is_isolated = not (hosp_access["is_accessible"] and fire_access["is_accessible"] and pol_access["is_accessible"])
            if is_isolated:
                isolated_count += 1
                disruption_level = "ISOLATED"
            elif avg_delay > 15.0:
                severely_delayed_count += 1
                disruption_level = "SEVERE"
            elif avg_delay > 5.0:
                disruption_level = "MODERATE"
            else:
                disruption_level = "LOW"

            results.append({
                "origin_id": orig["id"],
                "origin_name": orig["name"],
                "lat": orig["lat"],
                "lon": orig["lon"],
                "nearest_hospital": hosp_access,
                "nearest_fire_station": fire_access,
                "nearest_police": pol_access,
                "average_delay_min": round(avg_delay, 1),
                "is_isolated": is_isolated,
                "disruption_level": disruption_level
            })

        avg_net_delay = round(total_delay_sum / len(self.origins), 1) if self.origins else 0.0

        return {
            "scenario_name": f"Monsoon Flood Disruption Scenario (Threshold tau={scenario_threshold})",
            "disruption_description": (
                f"Evaluates travel times from 8 urban population centers to nearest emergency facilities. "
                f"Links with flood susceptibility >= {scenario_threshold} suffer severe traffic impedance or closure."
            ),
            "total_origins_evaluated": len(self.origins),
            "isolated_origins_count": isolated_count,
            "severely_delayed_count": severely_delayed_count,
            "average_network_delay_min": avg_net_delay,
            "results": results,
            "provenance_status": ProvenanceStatus.DERIVED,
            "notes": "Calculated via NetworkX Dijkstra shortest paths on free-flow vs impedance-penalized edge weights."
        }

    def _find_nearest_facility(self, G_base: nx.DiGraph, G_disrupted: nx.DiGraph, origin_node: str, fac_type: str) -> Dict[str, Any]:
        candidates = [f for f in self.destination_facilities if f["facility_type"] == fac_type]
        best_fac = candidates[0]
        best_base_time = float("inf")
        best_disrupt_time = float("inf")

        for fac in candidates:
            dst_node = fac["node"]
            # Baseline travel time
            if origin_node == dst_node:
                base_time = 0.0
                disrupt_time = 0.0
            else:
                try:
                    base_time = nx.shortest_path_length(G_base, source=origin_node, target=dst_node, weight="weight")
                except Exception:
                    base_time = 999.0

                # Disrupted travel time
                try:
                    disrupt_time = nx.shortest_path_length(G_disrupted, source=origin_node, target=dst_node, weight="weight")
                except Exception:
                    disrupt_time = 999.0

            if base_time < best_base_time:
                best_base_time = base_time
                best_disrupt_time = disrupt_time
                best_fac = fac

        # If primary baseline facility is cut off under disruption, check if an accessible alternative facility exists
        if best_disrupt_time >= 900.0:
            alt_best_disrupt = float("inf")
            alt_best_fac = None
            alt_base = float("inf")
            for fac in candidates:
                dst_node = fac["node"]
                if origin_node == dst_node:
                    d_time = 0.0
                    b_time = 0.0
                else:
                    try:
                        d_time = nx.shortest_path_length(G_disrupted, source=origin_node, target=dst_node, weight="weight")
                    except Exception:
                        d_time = 999.0
                    try:
                        b_time = nx.shortest_path_length(G_base, source=origin_node, target=dst_node, weight="weight")
                    except Exception:
                        b_time = 999.0

                if d_time < alt_best_disrupt:
                    alt_best_disrupt = d_time
                    alt_best_fac = fac
                    alt_base = b_time
            if alt_best_fac and alt_best_disrupt < 900.0:
                best_fac = alt_best_fac
                best_disrupt_time = alt_best_disrupt
                best_base_time = alt_base

        is_accessible = best_disrupt_time < 900.0
        delay_min = max(0.0, best_disrupt_time - best_base_time) if is_accessible else 999.0

        if not is_accessible:
            ratio = 99.0
            status = "ISOLATED"
        elif abs(best_disrupt_time - best_base_time) < 1e-4 or best_base_time <= 0.0:
            ratio = 1.0
            status = "NORMAL"
        else:
            ratio = best_disrupt_time / max(1.0, best_base_time)
            if delay_min > 15.0:
                status = "SEVERELY_DELAYED"
            elif delay_min > 4.0:
                status = "DELAYED"
            else:
                status = "NORMAL"

        return {
            "facility_id": best_fac["id"],
            "name": best_fac["name"],
            "facility_type": best_fac["facility_type"],
            "category": best_fac.get("category"),
            "lat": best_fac["lat"],
            "lon": best_fac["lon"],
            "baseline_time_min": round(best_base_time, 1),
            "disrupted_time_min": round(best_disrupt_time, 1) if is_accessible else 999.0,
            "delay_min": round(delay_min, 1),
            "delay_ratio": round(ratio, 2),
            "is_accessible": is_accessible,
            "status": status
        }
