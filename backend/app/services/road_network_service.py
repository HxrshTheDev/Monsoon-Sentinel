"""
Road Network Graph & Criticality Service (CityPulse)
Constructs a NetworkX directed graph of Greater Mumbai arterial network, subways, and bridges.
Computes link length, travel times, edge betweenness centrality, bridge/cut-edge identification,
and dynamic risk-penalized shortest path routing.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx

from backend.app.core.config import settings
from backend.app.schemas.provenance import ProvenanceStatus


class RoadNetworkService:
    _instance: Optional["RoadNetworkService"] = None

    @classmethod
    def get_instance(cls) -> "RoadNetworkService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edge_definitions: List[Dict[str, Any]] = []
        self.graph: nx.DiGraph = nx.DiGraph()
        self.undirected_graph: nx.Graph = nx.Graph()

        self.betweenness_cache: Dict[str, float] = {}
        self.bridges_set: set = set()

        self._build_mumbai_network()
        self._calculate_network_metrics()

    def _build_mumbai_network(self):
        """Constructs authentic nodes and arterial links across Greater Mumbai (BMC jurisdiction)."""
        self.nodes = {
            "MUM-NODE-CST": {"name": "CSMT Fort / South Mumbai", "lat": 18.9400, "lon": 72.8353, "locality": "Fort / South Mumbai"},
            "MUM-NODE-CHURCHGATE": {"name": "Churchgate / Marine Drive", "lat": 18.9322, "lon": 72.8264, "locality": "Churchgate"},
            "MUM-NODE-BYCULLA": {"name": "Byculla / Nagpada Junction", "lat": 18.9750, "lon": 72.8320, "locality": "Byculla"},
            "MUM-NODE-LOWERPAREL": {"name": "Lower Parel / Worli", "lat": 18.9950, "lon": 72.8250, "locality": "Lower Parel"},
            "MUM-NODE-HINDMATA": {"name": "Hindmata Lowland Bowl", "lat": 19.0080, "lon": 72.8430, "locality": "Hindmata / Parel"},
            "MUM-NODE-DADAR": {"name": "Dadar TT Circle / Central Interchange", "lat": 19.0178, "lon": 72.8478, "locality": "Dadar"},
            "MUM-NODE-WADALA": {"name": "Wadala / Eastern Freeway Portal", "lat": 19.0250, "lon": 72.8760, "locality": "Wadala"},
            "MUM-NODE-SEALINK": {"name": "Bandra-Worli Sea Link South Portal", "lat": 19.0200, "lon": 72.8150, "locality": "Worli Sea Face"},
            "MUM-NODE-MAHIM": {"name": "Mahim Causeway / Bay", "lat": 19.0400, "lon": 72.8410, "locality": "Mahim"},
            "MUM-NODE-SION": {"name": "Sion Circle / Gandhi Market Lowlands", "lat": 19.0400, "lon": 72.8620, "locality": "Sion"},
            "MUM-NODE-BANDRA": {"name": "Bandra Western Spine / Linking Road", "lat": 19.0544, "lon": 72.8402, "locality": "Bandra West"},
            "MUM-NODE-BKC": {"name": "Bandra-Kurla Complex (BKC)", "lat": 19.0650, "lon": 72.8680, "locality": "BKC"},
            "MUM-NODE-KURLA": {"name": "Kurla Mithi River Corridor", "lat": 19.0680, "lon": 72.8800, "locality": "Kurla"},
            "MUM-NODE-KHAR-SUBWAY": {"name": "Khar Subway Lowland Corridor", "lat": 19.0700, "lon": 72.8380, "locality": "Khar"},
            "MUM-NODE-SANTACRUZ": {"name": "Santacruz Milan Subway", "lat": 19.0830, "lon": 72.8420, "locality": "Santacruz"},
            "MUM-NODE-AIRPORT": {"name": "CSMIA International Airport", "lat": 19.0896, "lon": 72.8656, "locality": "Vile Parle / Airport"},
            "MUM-NODE-ANDHERI": {"name": "Andheri WEH Interchange", "lat": 19.1197, "lon": 72.8464, "locality": "Andheri"},
            "MUM-NODE-ANDHERI-SUBWAY": {"name": "Andheri Subway Underpass", "lat": 19.1180, "lon": 72.8430, "locality": "Andheri Subway"},
            "MUM-NODE-POWAI": {"name": "Powai / JVLR Corridor", "lat": 19.1200, "lon": 72.9050, "locality": "Powai"},
            "MUM-NODE-GHATKOPAR": {"name": "Ghatkopar EEH Corridor", "lat": 19.0860, "lon": 72.9080, "locality": "Ghatkopar"},
            "MUM-NODE-CHEMBUR": {"name": "Chembur SCLR Interchange", "lat": 19.0620, "lon": 72.9000, "locality": "Chembur"},
            "MUM-NODE-MANKHURD": {"name": "Mankhurd / Vashi Creek Link", "lat": 19.0550, "lon": 72.9300, "locality": "Mankhurd"},
            "MUM-NODE-MALAD": {"name": "Malad West / Link Road", "lat": 19.1860, "lon": 72.8485, "locality": "Malad"},
            "MUM-NODE-BORIVALI": {"name": "Borivali National Park Gateway", "lat": 19.2300, "lon": 72.8570, "locality": "Borivali"},
            "MUM-NODE-MULUND": {"name": "Mulund EEH Gateway", "lat": 19.1720, "lon": 72.9560, "locality": "Mulund"}
        }

        # Arterial links with physical length (km), free-flow speed (km/h), and bridge status
        raw_edges = [
            # 1. Bandra-Worli Sea Link & Coastal Link (Critical Sea Bridge)
            ("EDGE-BWSL-SEALINK", "MUM-NODE-SEALINK", "MUM-NODE-BANDRA", "Bandra-Worli Sea Link (Mahim Bay Crossing)", 5.6, 70.0, True, "Bandra West"),
            ("EDGE-LOWERPAREL-SEALINK", "MUM-NODE-LOWERPAREL", "MUM-NODE-SEALINK", "Worli Naka to Sea Link South Portal", 2.8, 45.0, False, "Worli Sea Face"),

            # 2. Western Express Highway (WEH) Spine
            ("EDGE-BANDRA-SANTACRUZ", "MUM-NODE-BANDRA", "MUM-NODE-SANTACRUZ", "Western Express Highway Bandra-Santacruz", 3.5, 50.0, False, "Bandra West"),
            ("EDGE-SANTACRUZ-AIRPORT", "MUM-NODE-SANTACRUZ", "MUM-NODE-AIRPORT", "Western Express Highway Santacruz-Airport", 2.2, 55.0, False, "Vile Parle / Airport"),
            ("EDGE-AIRPORT-ANDHERI", "MUM-NODE-AIRPORT", "MUM-NODE-ANDHERI", "Western Express Highway Airport-Andheri Flyover", 3.8, 55.0, False, "Andheri"),
            ("EDGE-ANDHERI-MALAD", "MUM-NODE-ANDHERI", "MUM-NODE-MALAD", "Western Express Highway Andheri-Malad Spine", 7.5, 60.0, False, "Malad"),
            ("EDGE-MALAD-BORIVALI", "MUM-NODE-MALAD", "MUM-NODE-BORIVALI", "Western Express Highway Malad-Borivali", 5.2, 60.0, False, "Borivali"),

            # 3. Eastern Express Highway (EEH) Spine
            ("EDGE-SION-KURLA", "MUM-NODE-SION", "MUM-NODE-KURLA", "Eastern Express Highway Sion-Kurla Link", 3.2, 50.0, False, "Sion"),
            ("EDGE-KURLA-GHATKOPAR", "MUM-NODE-KURLA", "MUM-NODE-GHATKOPAR", "Eastern Express Highway Kurla-Ghatkopar", 3.4, 55.0, False, "Ghatkopar"),
            ("EDGE-GHATKOPAR-MULUND", "MUM-NODE-GHATKOPAR", "MUM-NODE-MULUND", "Eastern Express Highway Ghatkopar-Mulund Expressway", 9.8, 65.0, False, "Mulund"),

            # 4. Eastern Freeway Elevated Viaducts
            ("EDGE-CST-WADALA-FREEWAY", "MUM-NODE-CST", "MUM-NODE-WADALA", "Eastern Freeway South Elevated Corridor", 7.8, 65.0, True, "Wadala"),
            ("EDGE-WADALA-CHEMBUR-FREEWAY", "MUM-NODE-WADALA", "MUM-NODE-CHEMBUR", "Eastern Freeway Anik-Panjarpol Viaduct", 5.4, 65.0, True, "Chembur"),

            # 5. Island City Spine (Dr. Ambedkar Road / Fort Corridors)
            ("EDGE-CHURCHGATE-CST", "MUM-NODE-CHURCHGATE", "MUM-NODE-CST", "DN Road / Fort Heritage Link", 1.8, 40.0, False, "Fort / South Mumbai"),
            ("EDGE-CST-BYCULLA", "MUM-NODE-CST", "MUM-NODE-BYCULLA", "Dr. Ambedkar Road CST-Byculla Spine", 3.8, 40.0, False, "Byculla"),
            ("EDGE-BYCULLA-LOWERPAREL", "MUM-NODE-BYCULLA", "MUM-NODE-LOWERPAREL", "NM Joshi Marg Byculla-Lower Parel", 2.4, 35.0, False, "Lower Parel"),
            ("EDGE-LOWERPAREL-HINDMATA", "MUM-NODE-LOWERPAREL", "MUM-NODE-HINDMATA", "Elphinstone Flyover to Hindmata Bowl", 1.6, 35.0, False, "Hindmata / Parel"),
            ("EDGE-HINDMATA-DADAR", "MUM-NODE-HINDMATA", "MUM-NODE-DADAR", "Dr. Ambedkar Road Hindmata-Dadar TT", 1.4, 35.0, False, "Hindmata / Parel"),
            ("EDGE-DADAR-SION", "MUM-NODE-DADAR", "MUM-NODE-SION", "Dr. Ambedkar Road Dadar-Sion Flyover", 3.0, 45.0, False, "Dadar"),

            # 6. Mahim Causeway & Mithi River Crossings (Bridges)
            ("EDGE-DADAR-MAHIM", "MUM-NODE-DADAR", "MUM-NODE-MAHIM", "Lady Jamshedjee Road Dadar-Mahim", 2.4, 40.0, False, "Mahim"),
            ("EDGE-MAHIM-BANDRA", "MUM-NODE-MAHIM", "MUM-NODE-BANDRA", "Mahim Causeway Bridge (Mithi Outfall Crossing)", 2.1, 45.0, True, "Mahim"),
            ("EDGE-SION-BKC", "MUM-NODE-SION", "MUM-NODE-BKC", "Sion-Bandra Link Road (Mithi River Crossing)", 2.8, 40.0, True, "BKC"),
            ("EDGE-BKC-KURLA", "MUM-NODE-BKC", "MUM-NODE-KURLA", "BKC-Kurla Connector", 2.2, 40.0, False, "Kurla"),
            ("EDGE-BKC-BANDRA", "MUM-NODE-BKC", "MUM-NODE-BANDRA", "Kalanagar Grade Separator to BKC", 3.0, 45.0, False, "BKC"),

            # 7. Cross Connectors & East-West Links
            ("EDGE-KURLA-CHEMBUR-SCLR", "MUM-NODE-KURLA", "MUM-NODE-CHEMBUR", "Santacruz-Chembur Link Road (SCLR Bridge)", 3.6, 50.0, True, "Kurla"),
            ("EDGE-ANDHERI-POWAI-JVLR", "MUM-NODE-ANDHERI", "MUM-NODE-POWAI", "Jogeshwari-Vikhroli Link Road (JVLR West)", 5.8, 50.0, False, "Powai"),
            ("EDGE-POWAI-GHATKOPAR-JVLR", "MUM-NODE-POWAI", "MUM-NODE-GHATKOPAR", "Jogeshwari-Vikhroli Link Road (JVLR East)", 4.5, 50.0, False, "Powai"),
            ("EDGE-CHEMBUR-MANKHURD", "MUM-NODE-CHEMBUR", "MUM-NODE-MANKHURD", "Sion-Panvel Expressway Mankhurd-Vashi Link", 4.2, 55.0, True, "Mankhurd"),

            # 8. Critical Subways & Underpasses (Chronic Flood Vulnerabilities)
            ("EDGE-ANDHERI-SUBWAY", "MUM-NODE-ANDHERI", "MUM-NODE-ANDHERI-SUBWAY", "Andheri Subway Rail Underpass Link", 1.2, 25.0, True, "Andheri Subway"),
            ("EDGE-SANTACRUZ-KHAR-SUBWAY", "MUM-NODE-SANTACRUZ", "MUM-NODE-KHAR-SUBWAY", "Khar-Milan Subway Underpass Link", 1.8, 25.0, True, "Khar")
        ]

        self.edge_definitions = []
        for eid, u, v, name, dist_km, speed_kmh, is_bridge, loc in raw_edges:
            free_time = (dist_km / max(10.0, speed_kmh)) * 60.0
            u_coords = [self.nodes[u]["lat"], self.nodes[u]["lon"]]
            v_coords = [self.nodes[v]["lat"], self.nodes[v]["lon"]]
            coords = [u_coords, [(u_coords[0] + v_coords[0]) * 0.5, (u_coords[1] + v_coords[1]) * 0.5], v_coords]

            edge_data = {
                "edge_id": eid,
                "u": u,
                "v": v,
                "name": name,
                "length_km": dist_km,
                "free_flow_speed_kmh": speed_kmh,
                "free_flow_time_min": round(free_time, 2),
                "is_bridge": is_bridge,
                "locality": loc,
                "coordinates": coords
            }
            self.edge_definitions.append(edge_data)

            # Bidirectional network
            self.graph.add_edge(u, v, **edge_data, weight=free_time)
            self.graph.add_edge(v, u, **edge_data, weight=free_time)

            self.undirected_graph.add_edge(u, v, **edge_data, weight=free_time)

    def _calculate_network_metrics(self):
        """Calculates topological edge betweenness centrality and bridges (cut-edges)."""
        edge_betweenness = nx.edge_betweenness_centrality(self.graph, weight="weight", normalized=True)
        self.betweenness_cache = {}
        for (u, v), b_val in edge_betweenness.items():
            # Edge key as sorted tuple for bidirectional lookup
            key = f"{min(u, v)}--{max(u, v)}"
            self.betweenness_cache[key] = max(self.betweenness_cache.get(key, 0.0), b_val)

        # Detect bridges (cut-edges) in the undirected network
        raw_bridges = list(nx.bridges(self.undirected_graph))
        self.bridges_set = {f"{min(u, v)}--{max(u, v)}" for u, v in raw_bridges}

    def get_road_criticality_items(self, flood_service=None) -> List[Dict[str, Any]]:
        """Returns all road segments with betweenness, bridge status, and flood susceptibility."""
        items = []
        for ed in self.edge_definitions:
            u, v = ed["u"], ed["v"]
            key = f"{min(u, v)}--{max(u, v)}"
            betweenness = self.betweenness_cache.get(key, 0.02)
            is_cut_edge = key in self.bridges_set or ed["is_bridge"]

            # Map flood susceptibility from flood service
            susceptibility = 0.15
            if flood_service:
                mid_lat = (self.nodes[u]["lat"] + self.nodes[v]["lat"]) * 0.5
                mid_lon = (self.nodes[u]["lon"] + self.nodes[v]["lon"]) * 0.5
                zone = flood_service.get_location_risk(ed["locality"])
                if zone:
                    susceptibility = float(zone.get("probability", 0.15))

            # Composite criticality index: betweenness + bridge penalty + length factor
            crit_score = min(1.0, (betweenness * 3.5) + (0.35 if is_cut_edge else 0.0) + (ed["length_km"] / 30.0))

            status = "OPEN"
            if susceptibility >= settings.DISRUPTION_THRESHOLD_CRITICAL:
                status = "CLOSED_SIMULATED"
            elif susceptibility >= settings.DISRUPTION_THRESHOLD_HIGH:
                status = "DEGRADED"

            items.append({
                "edge_id": ed["edge_id"],
                "source_node": u,
                "target_node": v,
                "name": ed["name"],
                "length_km": ed["length_km"],
                "free_flow_speed_kmh": ed["free_flow_speed_kmh"],
                "free_flow_time_min": ed["free_flow_time_min"],
                "betweenness_centrality": round(betweenness, 4),
                "is_bridge_or_cut_edge": is_cut_edge,
                "flood_susceptibility": round(susceptibility, 4),
                "criticality_score": round(crit_score, 4),
                "coordinates": ed["coordinates"],
                "locality": ed["locality"],
                "status": status
            })

        return sorted(items, key=lambda x: x["criticality_score"], reverse=True)

    def get_nearest_node_to_coords(self, lat: float, lon: float) -> str:
        """Finds the geometrically nearest network node to any arbitrary GPS coordinate."""
        best_node = list(self.nodes.keys())[0] if self.nodes else "MUM-NODE-CST"
        best_dist = float("inf")
        for nid, data in self.nodes.items():
            d = math.hypot(lat - data["lat"], lon - data["lon"])
            if d < best_dist:
                best_dist = d
                best_node = nid
        return best_node

    def calculate_safe_route(
        self,
        source: Optional[str] = None,
        destination: Optional[str] = None,
        vehicle_type: str = "car",
        flood_service=None,
        source_coords: Optional[List[float]] = None,
        dest_coords: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Runs Dijkstra shortest path on dynamic flood-penalized edge weights."""
        if source_coords and len(source_coords) >= 2:
            s_node = self.get_nearest_node_to_coords(source_coords[0], source_coords[1])
            s_coords = [source_coords[0], source_coords[1]]
        else:
            s_node = self._match_nearest_node(source or "CSMT Fort")
            s_coords = [self.nodes[s_node]["lat"], self.nodes[s_node]["lon"]]

        if dest_coords and len(dest_coords) >= 2:
            d_node = self.get_nearest_node_to_coords(dest_coords[0], dest_coords[1])
            d_coords = [dest_coords[0], dest_coords[1]]
        else:
            d_node = self._match_nearest_node(destination or "CSMIA International Airport")
            d_coords = [self.nodes[d_node]["lat"], self.nodes[d_node]["lon"]]

        # Handle intra-precinct origin and destination (s_node == d_node)
        if s_node == d_node:
            intra_dist = round(math.hypot(s_coords[0] - d_coords[0], s_coords[1] - d_coords[1]) * 111.0, 2)
            intra_time = max(1, int(round((intra_dist / 25.0) * 60))) if intra_dist > 0 else 1
            path_pts = [s_coords] if s_coords == d_coords else [s_coords, d_coords]
            locality_name = self.nodes[s_node]["locality"]

            return {
                "source": self.nodes[s_node]["name"],
                "destination": self.nodes[d_node]["name"],
                "sourceCoords": s_coords,
                "destCoords": d_coords,
                "recommendedRoute": {
                    "id": "REC-INTRA-PRECINCT",
                    "name": f"Intra-Precinct Local Route within {locality_name} (Recommended)",
                    "type": "RECOMMENDED_SAFE",
                    "distanceKm": max(0.2, intra_dist),
                    "etaMinutes": intra_time,
                    "safetyScore": 95,
                    "riskStatus": "SAFE",
                    "floodPointsAvoided": 0,
                    "hazardExposure": "Low",
                    "pathCoordinates": path_pts,
                    "nodesVisited": [s_node],
                    "notes": f"Origin and destination are within the same arterial precinct ({locality_name}). Local intra-neighborhood traversal applied.",
                    "isSimulated": False
                },
                "alternativeRoute": {
                    "id": "ALT-INTRA-PRECINCT",
                    "name": f"Direct Walk/Access Route within {locality_name}",
                    "type": "FASTER_ALTERNATIVE",
                    "distanceKm": max(0.2, intra_dist),
                    "etaMinutes": intra_time,
                    "safetyScore": 90,
                    "riskStatus": "SAFE",
                    "floodPointsAvoided": 0,
                    "hazardExposure": "Low",
                    "pathCoordinates": path_pts,
                    "nodesVisited": [s_node],
                    "notes": "Direct local access within the same transit node footprint.",
                    "isSimulated": False
                },
                "hazards": [],
                "isSimulated": False
            }

        v_type = (vehicle_type or "car").lower()
        vehicle_speed_factor = 0.85 if v_type in ["suv", "rescue", "truck"] else 1.0

        # Construct dynamic weighted graph
        G_dynamic = nx.DiGraph()
        edge_risks: Dict[str, float] = {}

        for ed in self.edge_definitions:
            u, v = ed["u"], ed["v"]
            base_time = ed["free_flow_time_min"] * vehicle_speed_factor
            risk = 0.15
            if flood_service:
                zone = flood_service.get_location_risk(ed["locality"], fallback_to_first=True)
                if zone:
                    risk = float(zone.get("probability", 0.15))
            edge_risks[ed["edge_id"]] = risk

            # Quadratic flood impedance penalty
            penalty_multiplier = 1.0 + 9.0 * (risk ** 2.0)
            if risk >= settings.DISRUPTION_THRESHOLD_CRITICAL and v_type != "rescue":
                penalty_multiplier *= 10.0  # Heavily divert normal traffic from critical zones

            impedance = base_time * penalty_multiplier

            G_dynamic.add_edge(u, v, weight=impedance, dist=ed["length_km"], base_time=base_time, eid=ed["edge_id"])
            G_dynamic.add_edge(v, u, weight=impedance, dist=ed["length_km"], base_time=base_time, eid=ed["edge_id"])

        # Compute safe path (risk-penalized Dijkstra)
        try:
            safe_path_nodes = nx.shortest_path(G_dynamic, source=s_node, target=d_node, weight="weight")
            safe_coords, safe_dist, safe_time, safe_avoided = self._extract_path_metrics(safe_path_nodes, edge_risks)
            safe_status = "SAFE"
            safe_notes = "Route dynamically diverts around flood-susceptible links using NetworkX Dijkstra shortest path."
        except Exception:
            safe_path_nodes = [s_node, d_node]
            safe_coords = [s_coords, d_coords]
            safe_dist = round(math.hypot(s_coords[0] - d_coords[0], s_coords[1] - d_coords[1]) * 111.0, 1)
            safe_time = int(round((safe_dist / 30.0) * 60))
            safe_avoided = 0
            safe_status = "CAUTION"
            safe_notes = "Severe disruptions encountered on primary corridors; displaying direct contingency trajectory."

        # Compute fastest direct baseline path (unpenalized Dijkstra)
        try:
            direct_path_nodes = nx.shortest_path(self.graph, source=s_node, target=d_node, weight="weight")
            direct_coords, direct_dist, direct_time, _ = self._extract_path_metrics(direct_path_nodes, edge_risks)
        except Exception:
            direct_path_nodes = safe_path_nodes
            direct_coords = safe_coords
            direct_dist = safe_dist
            direct_time = safe_time

        hazards = [
            {
                "id": "HAZ-MUM-01",
                "title": "Mithi River Lowland Bottleneck",
                "location": "Kurla West / LBS Marg Catchment",
                "coordinates": [19.0680, 72.8800],
                "severity": "UNSAFE",
                "waterDepthCm": 0,
                "status": "RISK_BASED_AVOIDANCE",
                "isSimulated": False
            },
            {
                "id": "HAZ-MUM-02",
                "title": "Hindmata Chronic Waterlogging Bowl",
                "location": "Hindmata / Parel Lowland Junction",
                "coordinates": [19.0080, 72.8430],
                "severity": "UNSAFE",
                "waterDepthCm": 0,
                "status": "RISK_BASED_AVOIDANCE",
                "isSimulated": False
            }
        ]

        return {
            "source": self.nodes[s_node]["name"],
            "destination": self.nodes[d_node]["name"],
            "sourceCoords": s_coords,
            "destCoords": d_coords,
            "recommendedRoute": {
                "id": "REC-SAFE-PATH",
                "name": f"Dynamic Safe Route via {len(safe_path_nodes)} Waypoints (Recommended)",
                "type": "RECOMMENDED_SAFE",
                "distanceKm": round(safe_dist, 1),
                "etaMinutes": int(round(safe_time)),
                "safetyScore": max(60, min(98, 100 - int(round(safe_time * 0.4)))),
                "riskStatus": safe_status,
                "floodPointsAvoided": safe_avoided,
                "hazardExposure": "Low",
                "pathCoordinates": safe_coords,
                "nodesVisited": safe_path_nodes,
                "notes": safe_notes,
                "isSimulated": False
            },
            "alternativeRoute": {
                "id": "ALT-DIRECT-PATH",
                "name": f"Direct Shortest Route via {len(direct_path_nodes)} Waypoints",
                "type": "FASTER_ALTERNATIVE",
                "distanceKm": round(direct_dist, 1),
                "etaMinutes": int(round(direct_time)),
                "safetyScore": 45,
                "riskStatus": "UNSAFE" if safe_avoided > 0 else "CAUTION",
                "floodPointsAvoided": 0,
                "hazardExposure": "High" if safe_avoided > 0 else "Medium",
                "pathCoordinates": direct_coords,
                "nodesVisited": direct_path_nodes,
                "notes": "Direct geographical path that crosses susceptible lowlands and depressed subway corridors.",
                "isSimulated": False
            },
            "hazards": hazards,
            "isSimulated": False
        }

    def _extract_path_metrics(self, path_nodes: List[str], edge_risks: Dict[str, float]) -> Tuple[List[List[float]], float, float, int]:
        coords: List[List[float]] = []
        tot_dist = 0.0
        tot_time = 0.0
        avoided_count = 0

        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i + 1]
            ed = next((e for e in self.edge_definitions if (e["u"] == u and e["v"] == v) or (e["u"] == v and e["v"] == u)), None)
            if ed:
                tot_dist += ed["length_km"]
                tot_time += ed["free_flow_time_min"]
                if edge_risks.get(ed["edge_id"], 0.0) >= settings.DISRUPTION_THRESHOLD_HIGH:
                    avoided_count += 1
                for c in ed["coordinates"]:
                    if not coords or coords[-1] != c:
                        coords.append(c)
            else:
                coords.append([self.nodes[u]["lat"], self.nodes[u]["lon"]])
                coords.append([self.nodes[v]["lat"], self.nodes[v]["lon"]])

        if not coords and path_nodes:
            coords = [[self.nodes[path_nodes[0]]["lat"], self.nodes[path_nodes[0]]["lon"]]]

        return coords, tot_dist, tot_time, avoided_count

    def _match_nearest_node(self, query: str) -> str:
        q = (query or "").lower().strip()

        # Check for numeric coordinates in query string e.g. "19.0680, 72.8800"
        cleaned = q.replace(",", " ").replace(";", " ")
        tokens = [t.strip() for t in cleaned.split() if t.strip()]
        if len(tokens) == 2:
            try:
                v1, v2 = float(tokens[0]), float(tokens[1])
                if 18.5 <= v1 <= 19.5 and 72.5 <= v2 <= 73.2:
                    return self.get_nearest_node_to_coords(v1, v2)
                elif 18.5 <= v2 <= 19.5 and 72.5 <= v1 <= 73.2:
                    return self.get_nearest_node_to_coords(v2, v1)
            except ValueError:
                pass

        for nid, data in self.nodes.items():
            if q in data["name"].lower() or q in data["locality"].lower():
                return nid
        # Landmark synonyms
        if "airport" in q or "csmia" in q or "vile parle" in q:
            return "MUM-NODE-AIRPORT"
        if "cst" in q or "csmt" in q or "fort" in q or "south mumbai" in q:
            return "MUM-NODE-CST"
        if "churchgate" in q or "marine drive" in q:
            return "MUM-NODE-CHURCHGATE"
        if "dadar" in q:
            return "MUM-NODE-DADAR"
        if "bandra" in q or "linking road" in q:
            return "MUM-NODE-BANDRA"
        if "bkc" in q or "bandra-kurla" in q:
            return "MUM-NODE-BKC"
        if "kurla" in q or "mithi" in q:
            return "MUM-NODE-KURLA"
        if "sion" in q or "gandhi market" in q or "king's circle" in q:
            return "MUM-NODE-SION"
        if "andheri subway" in q:
            return "MUM-NODE-ANDHERI-SUBWAY"
        if "andheri" in q or "juhu" in q:
            return "MUM-NODE-ANDHERI"
        if "khar" in q or "milan subway" in q or "santacruz" in q:
            return "MUM-NODE-KHAR-SUBWAY"
        if "hindmata" in q or "parel" in q:
            return "MUM-NODE-HINDMATA"
        if "worli" in q or "sea face" in q or "sealink" in q:
            return "MUM-NODE-SEALINK"
        if "lower parel" in q:
            return "MUM-NODE-LOWERPAREL"
        if "wadala" in q:
            return "MUM-NODE-WADALA"
        if "byculla" in q or "nagpada" in q:
            return "MUM-NODE-BYCULLA"
        if "mahim" in q:
            return "MUM-NODE-MAHIM"
        if "powai" in q or "jvlr" in q:
            return "MUM-NODE-POWAI"
        if "ghatkopar" in q:
            return "MUM-NODE-GHATKOPAR"
        if "chembur" in q:
            return "MUM-NODE-CHEMBUR"
        if "mankhurd" in q or "vashi" in q:
            return "MUM-NODE-MANKHURD"
        if "malad" in q or "goregaon" in q:
            return "MUM-NODE-MALAD"
        if "borivali" in q or "kandivali" in q or "dahisar" in q:
            return "MUM-NODE-BORIVALI"
        if "mulund" in q or "bhandup" in q:
            return "MUM-NODE-MULUND"

        return "MUM-NODE-CST"

    def get_preset_routes(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "PRESET-MUM-AIRPORT",
                "label": "CSMT Fort → Mumbai Airport CSMIA (via Eastern Freeway / WEH)",
                "source": "CSMT Fort",
                "destination": "CSMIA International Airport",
                "description": "Primary metropolitan transit corridor connecting South Mumbai heritage commercial core to international airport terminal."
            },
            {
                "id": "PRESET-MUM-BKC",
                "label": "Dadar TT Circle → Bandra-Kurla Complex (BKC)",
                "source": "Dadar TT Circle",
                "destination": "Bandra-Kurla Complex (BKC)",
                "description": "Essential financial corridor bypassing Mahim Bay and Mithi River lowlands."
            },
            {
                "id": "PRESET-MUM-BORIVALI",
                "label": "Borivali → Bandra West (Western Express Highway Corridor)",
                "source": "Borivali",
                "destination": "Bandra Western Spine",
                "description": "Major North-South suburban arterial corridor connecting Northern suburbs to coastal bridges."
            },
            {
                "id": "PRESET-MUM-KURLA",
                "label": "Sion Circle → Kurla Mithi Basin",
                "source": "Sion Circle",
                "destination": "Kurla Mithi River Corridor",
                "description": "Cross-catchment arterial route linking Central Mumbai to Eastern Express Highway."
            }
        ]

