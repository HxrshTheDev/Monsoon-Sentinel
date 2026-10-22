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

        # Key population origin clusters
        self.origins = [
            {"id": "ORIGIN-VELACHERY", "name": "Velachery Residential Basin", "node": "CHN-NODE-VELACHERY", "lat": 12.9815, "lon": 80.2180},
            {"id": "ORIGIN-TAMBARAM", "name": "Tambaram / Mudichur Lowlands", "node": "CHN-NODE-TAMBARAM", "lat": 12.9249, "lon": 80.1000},
            {"id": "ORIGIN-KOLATHUR", "name": "Kolathur / Madhavaram North", "node": "CHN-NODE-KOLATHUR", "lat": 13.1238, "lon": 80.2185},
            {"id": "ORIGIN-AMBATTUR", "name": "Ambattur Western Sector", "node": "CHN-NODE-AMBATTUR", "lat": 13.1143, "lon": 80.1548},
            {"id": "ORIGIN-PORUR", "name": "Porur Sub-basin", "node": "CHN-NODE-PORUR", "lat": 13.0382, "lon": 80.1565},
            {"id": "ORIGIN-MADIPAKKAM", "name": "Madipakkam Puzhuthivakkam", "node": "CHN-NODE-MADIPAKKAM", "lat": 12.9640, "lon": 80.1980},
            {"id": "ORIGIN-ROYAPURAM", "name": "Royapuram Coastal Enclave", "node": "CHN-NODE-ROYAPURAM", "lat": 13.1120, "lon": 80.2960},
            {"id": "ORIGIN-TNAGAR", "name": "T. Nagar Commercial & Residential Core", "node": "CHN-NODE-TNAGAR", "lat": 13.0418, "lon": 80.2341}
        ]

        # Key destination facilities mapped to nearest network nodes
        self.destination_facilities = [
            {
                "id": "HOSP-RGGGH-01",
                "name": "Rajiv Gandhi Government General Hospital (RGGGH)",
                "facility_type": "hospital",
                "category": "Level 1 Trauma Center",
                "node": "CHN-NODE-CENTRAL",
                "lat": 13.0805, "lon": 80.2785
            },
            {
                "id": "HOSP-APOLLO-02",
                "name": "Apollo Hospitals Greams Road",
                "facility_type": "hospital",
                "category": "Emergency Cardiac & Trauma",
                "node": "CHN-NODE-TNAGAR",
                "lat": 13.0592, "lon": 80.2520
            },
            {
                "id": "HOSP-STANLEY-03",
                "name": "Government Stanley Medical College Hospital",
                "facility_type": "hospital",
                "category": "North Chennai Trauma Center",
                "node": "CHN-NODE-ROYAPURAM",
                "lat": 13.1090, "lon": 80.2865
            },
            {
                "id": "HOSP-FORTIS-04",
                "name": "Fortis Malar Hospital Adyar",
                "facility_type": "hospital",
                "category": "South Chennai Emergency Hub",
                "node": "CHN-NODE-ADYAR",
                "lat": 13.0068, "lon": 80.2570
            },
            {
                "id": "FIRE-CENTRAL-01",
                "name": "Chennai Fire & Rescue Central Station",
                "facility_type": "fire_station",
                "category": "Metropolitan Dispatch",
                "node": "CHN-NODE-EGMORE",
                "lat": 13.0850, "lon": 80.2820
            },
            {
                "id": "FIRE-GUINDY-02",
                "name": "Guindy Fire & Rescue Station",
                "facility_type": "fire_station",
                "category": "Industrial Response",
                "node": "CHN-NODE-GUINDY",
                "lat": 13.0085, "lon": 80.2100
            },
            {
                "id": "FIRE-TAMBARAM-03",
                "name": "Tambaram Fire & Rescue Station",
                "facility_type": "fire_station",
                "category": "South Catchment Response",
                "node": "CHN-NODE-TAMBARAM",
                "lat": 12.9260, "lon": 80.1180
            },
            {
                "id": "POLICE-HQ-01",
                "name": "Greater Chennai Police Headquarters",
                "facility_type": "police",
                "category": "Metropolitan Command",
                "node": "CHN-NODE-MYLAPORE",
                "lat": 13.0450, "lon": 80.2780
            },
            {
                "id": "POLICE-TNAGAR-02",
                "name": "T. Nagar Police Divisional Headquarters",
                "facility_type": "police",
                "category": "Divisional Command",
                "node": "CHN-NODE-TNAGAR",
                "lat": 13.0400, "lon": 80.2330
            }
        ]

    def evaluate_accessibility(self, scenario_threshold: float = 0.40) -> Dict[str, Any]:
        """
        Evaluates baseline vs disrupted travel times across all population origins.
        `scenario_threshold` defines the flood susceptibility above which links experience degradation or disruption.
        """
        # Baseline free-flow graph
        G_base = self.road_service.graph

        # Construct disrupted graph under scenario
        G_disrupted = nx.DiGraph()
        for ed in self.road_service.edge_definitions:
            u, v = ed["u"], ed["v"]
            base_time = ed["free_flow_time_min"]
            risk = 0.15
            zone = self.flood_service.get_location_risk(ed["locality"])
            if zone:
                risk = float(zone.get("probability", 0.15))

            if risk >= 0.70:
                # Impassable / closed link under severe flooding
                continue
            elif risk >= scenario_threshold:
                # Severe delay factor
                impedance = base_time * (2.5 + (risk * 3.0))
            else:
                impedance = base_time * (1.0 + (risk * 0.8))

            G_disrupted.add_edge(u, v, weight=impedance)
            G_disrupted.add_edge(v, u, weight=impedance)

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

        is_accessible = best_disrupt_time < 900.0
        delay_min = (best_disrupt_time - best_base_time) if is_accessible else 999.0
        ratio = (best_disrupt_time / max(1.0, best_base_time)) if is_accessible else 99.0

        if not is_accessible:
            status = "ISOLATED"
        elif delay_min > 15.0:
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
