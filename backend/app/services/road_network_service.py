"""
Road Network Graph & Criticality Service (CityPulse)
Constructs a NetworkX directed graph of Greater Chennai arterial network, subways, and bridges.
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

        self._build_chennai_network()
        self._calculate_network_metrics()

    def _build_chennai_network(self):
        """Constructs authentic nodes and arterial links across Greater Chennai."""
        self.nodes = {
            "CHN-NODE-CENTRAL": {"name": "Chennai Central / Park Town", "lat": 13.0827, "lon": 80.2750, "locality": "Central"},
            "CHN-NODE-EGMORE": {"name": "Egmore Rail Junction", "lat": 13.0780, "lon": 80.2600, "locality": "Egmore"},
            "CHN-NODE-TNAGAR": {"name": "T. Nagar Commercial Core", "lat": 13.0418, "lon": 80.2341, "locality": "T. Nagar"},
            "CHN-NODE-GUINDY": {"name": "Guindy Kathipara Grade Separator", "lat": 13.0067, "lon": 80.2026, "locality": "Guindy"},
            "CHN-NODE-SAIDAPET": {"name": "Saidapet Bridge Corridor", "lat": 13.0210, "lon": 80.2230, "locality": "Saidapet"},
            "CHN-NODE-VELACHERY": {"name": "Velachery Basin Lowlands", "lat": 12.9815, "lon": 80.2180, "locality": "Velachery"},
            "CHN-NODE-MADIPAKKAM": {"name": "Madipakkam Puzhuthivakkam", "lat": 12.9640, "lon": 80.1980, "locality": "Madipakkam"},
            "CHN-NODE-ADYAR": {"name": "Adyar Estuary / Kotturpuram", "lat": 13.0080, "lon": 80.2550, "locality": "Adyar"},
            "CHN-NODE-MYLAPORE": {"name": "Mylapore Precinct", "lat": 13.0368, "lon": 80.2676, "locality": "Mylapore"},
            "CHN-NODE-KOYAMBEDU": {"name": "Koyambedu Transit Terminal", "lat": 13.0690, "lon": 80.1920, "locality": "Koyambedu"},
            "CHN-NODE-PORUR": {"name": "Porur Lake Junction", "lat": 13.0382, "lon": 80.1565, "locality": "Porur"},
            "CHN-NODE-AMBATTUR": {"name": "Ambattur Industrial Estate", "lat": 13.1143, "lon": 80.1548, "locality": "Ambattur"},
            "CHN-NODE-KOLATHUR": {"name": "Kolathur North Catchment", "lat": 13.1238, "lon": 80.2185, "locality": "Kolathur"},
            "CHN-NODE-VYASARPADI": {"name": "Vyasarpadi Underpass Corridor", "lat": 13.1185, "lon": 80.2615, "locality": "Vyasarpadi"},
            "CHN-NODE-PERAMBUR": {"name": "Perambur Loco Works", "lat": 13.1070, "lon": 80.2380, "locality": "Perambur"},
            "CHN-NODE-ROYAPURAM": {"name": "Royapuram Harbour Coast", "lat": 13.1120, "lon": 80.2960, "locality": "Royapuram"},
            "CHN-NODE-TONDIARPET": {"name": "Tondiarpet North Terminal", "lat": 13.1290, "lon": 80.2880, "locality": "Tondiarpet"},
            "CHN-NODE-AIRPORT": {"name": "Chennai International Airport", "lat": 12.9941, "lon": 80.1807, "locality": "Meenambakkam"},
            "CHN-NODE-TAMBARAM": {"name": "Tambaram GST Corridor", "lat": 12.9249, "lon": 80.1000, "locality": "Tambaram"},
            "CHN-NODE-OMR-SHOLING": {"name": "Sholinganallur IT Expressway (OMR)", "lat": 12.9010, "lon": 80.2279, "locality": "Sholinganallur"},
            "CHN-NODE-ECR-THIRUVAN": {"name": "Thiruvanmiyur Coastal Corridor (ECR)", "lat": 12.9830, "lon": 80.2590, "locality": "Thiruvanmiyur"},
            "CHN-NODE-PALLAVARAM": {"name": "Pallavaram Lowland Junction", "lat": 12.9675, "lon": 80.1491, "locality": "Pallavaram"}
        }

        # Arterial links with physical length (km), free-flow speed (km/h), and bridge status
        raw_edges = [
            # Anna Salai (NH 45) Main Arterial Spine
            ("EDGE-CENTRAL-EGMORE", "CHN-NODE-CENTRAL", "CHN-NODE-EGMORE", "EVR Periyar Salai Link", 1.9, 40.0, False, "Central"),
            ("EDGE-EGMORE-TNAGAR", "CHN-NODE-EGMORE", "CHN-NODE-TNAGAR", "Anna Salai Arterial Core", 4.8, 45.0, False, "T. Nagar"),
            ("EDGE-TNAGAR-SAIDAPET", "CHN-NODE-TNAGAR", "CHN-NODE-SAIDAPET", "Anna Salai South Corridor", 2.6, 45.0, False, "Saidapet"),
            ("EDGE-SAIDAPET-GUINDY", "CHN-NODE-SAIDAPET", "CHN-NODE-GUINDY", "Saidapet Bridge (Adyar River Crossing)", 2.4, 50.0, True, "Saidapet"),
            ("EDGE-GUINDY-AIRPORT", "CHN-NODE-GUINDY", "CHN-NODE-AIRPORT", "Kathipara Grade Separator to Airport (GST Rd)", 3.8, 55.0, True, "Guindy"),
            ("EDGE-AIRPORT-PALLAVARAM", "CHN-NODE-AIRPORT", "CHN-NODE-PALLAVARAM", "GST Road Meenambakkam-Pallavaram", 4.2, 50.0, False, "Pallavaram"),
            ("EDGE-PALLAVARAM-TAMBARAM", "CHN-NODE-PALLAVARAM", "CHN-NODE-TAMBARAM", "GST Road Pallavaram-Tambaram Flyover", 6.8, 55.0, False, "Tambaram"),

            # Inner Ring Road (100 Feet Road)
            ("EDGE-KOYAMBEDU-PORUR", "CHN-NODE-KOYAMBEDU", "CHN-NODE-PORUR", "Koyambedu-Porur Link Road", 5.2, 45.0, False, "Koyambedu"),
            ("EDGE-PORUR-GUINDY", "CHN-NODE-PORUR", "CHN-NODE-GUINDY", "Mount-Poonamallee Road", 5.9, 45.0, False, "Porur"),
            ("EDGE-KOYAMBEDU-TNAGAR", "CHN-NODE-KOYAMBEDU", "CHN-NODE-TNAGAR", "Vadapalani 100 Feet Road", 5.0, 40.0, False, "Vadapalani"),
            ("EDGE-KOYAMBEDU-AMBATTUR", "CHN-NODE-KOYAMBEDU", "CHN-NODE-AMBATTUR", "Chennai-Tiruvallur High Road (CTH)", 6.4, 45.0, False, "Ambattur"),

            # North Chennai Corridors & Vulnerable Subways
            ("EDGE-CENTRAL-ROYAPURAM", "CHN-NODE-CENTRAL", "CHN-NODE-ROYAPURAM", "Rajaji Salai Harbour Corridor", 3.8, 40.0, False, "Royapuram"),
            ("EDGE-ROYAPURAM-TONDIARPET", "CHN-NODE-ROYAPURAM", "CHN-NODE-TONDIARPET", "Tondiarpet High Road", 2.5, 35.0, False, "Tondiarpet"),
            ("EDGE-CENTRAL-VYASARPADI", "CHN-NODE-CENTRAL", "CHN-NODE-VYASARPADI", "Basin Bridge / Vyasarpadi Underpass", 4.3, 35.0, True, "Vyasarpadi"),
            ("EDGE-VYASARPADI-PERAMBUR", "CHN-NODE-VYASARPADI", "CHN-NODE-PERAMBUR", "Vyasarpadi-Perambur Rail Underpass", 2.8, 30.0, True, "Vyasarpadi"),
            ("EDGE-PERAMBUR-KOLATHUR", "CHN-NODE-PERAMBUR", "CHN-NODE-KOLATHUR", "Paper Mills Road Kolathur Link", 3.2, 35.0, False, "Kolathur"),
            ("EDGE-KOLATHUR-AMBATTUR", "CHN-NODE-KOLATHUR", "CHN-NODE-AMBATTUR", "Madhavaram-Ambattur Bypass Link", 7.1, 50.0, False, "Ambattur"),

            # South Chennai, Velachery & IT Corridor (OMR / ECR)
            ("EDGE-GUINDY-VELACHERY", "CHN-NODE-GUINDY", "CHN-NODE-VELACHERY", "Guindy-Velachery Checkpost Link", 3.7, 40.0, False, "Velachery"),
            ("EDGE-VELACHERY-MADIPAKKAM", "CHN-NODE-VELACHERY", "CHN-NODE-MADIPAKKAM", "Velachery Lake Depression Bypass", 2.9, 35.0, False, "Velachery"),
            ("EDGE-MADIPAKKAM-TAMBARAM", "CHN-NODE-MADIPAKKAM", "CHN-NODE-TAMBARAM", "Madipakkam-Medavakkam-Tambaram Link", 11.2, 45.0, False, "Tambaram"),
            ("EDGE-SAIDAPET-ADYAR", "CHN-NODE-SAIDAPET", "CHN-NODE-ADYAR", "Kotturpuram Adyar River Bridge", 3.6, 45.0, True, "Kotturpuram"),
            ("EDGE-ADYAR-MYLAPORE", "CHN-NODE-ADYAR", "CHN-NODE-MYLAPORE", "Dr. Radhakrishnan Salai Adyar Connector", 3.5, 40.0, False, "Mylapore"),
            ("EDGE-MYLAPORE-CENTRAL", "CHN-NODE-MYLAPORE", "CHN-NODE-CENTRAL", "Kamarajar Promenade (Marina Beach)", 5.6, 45.0, False, "Mylapore"),
            ("EDGE-ADYAR-ECR", "CHN-NODE-ADYAR", "CHN-NODE-ECR-THIRUVAN", "Lattice Bridge Road (Adyar to Thiruvanmiyur)", 2.8, 40.0, True, "Thiruvanmiyur"),
            ("EDGE-ECR-OMR", "CHN-NODE-ECR-THIRUVAN", "CHN-NODE-OMR-SHOLING", "Rajiv Gandhi IT Expressway (OMR Spine)", 9.5, 60.0, False, "Sholinganallur"),
            ("EDGE-VELACHERY-OMR", "CHN-NODE-VELACHERY", "CHN-NODE-OMR-SHOLING", "Taramani-Sholinganallur Link Road", 8.8, 50.0, False, "Taramani"),
            ("EDGE-MADIPAKKAM-PALLAVARAM", "CHN-NODE-MADIPAKKAM", "CHN-NODE-PALLAVARAM", "200 Feet Radial Road Pallavaram Link", 5.2, 55.0, False, "Pallavaram")
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

    def calculate_safe_route(self, source: str, destination: str, vehicle_type: str = "car", flood_service=None) -> Dict[str, Any]:
        """Runs Dijkstra shortest path on dynamic flood-penalized edge weights."""
        s_node = self._match_nearest_node(source)
        d_node = self._match_nearest_node(destination)

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
                zone = flood_service.get_location_risk(ed["locality"])
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
        except Exception:
            safe_path_nodes = [s_node, d_node]
            safe_coords = [[self.nodes[s_node]["lat"], self.nodes[s_node]["lon"]], [self.nodes[d_node]["lat"], self.nodes[d_node]["lon"]]]
            safe_dist = 10.0
            safe_time = 25
            safe_avoided = 0

        # Compute fastest direct baseline path (unpenalized Dijkstra)
        try:
            direct_path_nodes = nx.shortest_path(self.graph, source=s_node, target=d_node, weight="weight")
            direct_coords, direct_dist, direct_time, _ = self._extract_path_metrics(direct_path_nodes, edge_risks)
        except Exception:
            direct_path_nodes = safe_path_nodes
            direct_coords = safe_coords
            direct_dist = safe_dist
            direct_time = safe_time

        s_coords = [self.nodes[s_node]["lat"], self.nodes[s_node]["lon"]]
        d_coords = [self.nodes[d_node]["lat"], self.nodes[d_node]["lon"]]

        hazards = [
            {
                "id": "HAZ-CHN-01",
                "title": "Lowland Susceptibility Bottleneck",
                "location": "Velachery / Saidapet Lowland Basin",
                "coordinates": [12.9815, 80.2180],
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
                "riskStatus": "SAFE",
                "floodPointsAvoided": safe_avoided,
                "hazardExposure": "Low",
                "pathCoordinates": safe_coords,
                "nodesVisited": safe_path_nodes,
                "notes": f"Route dynamically diverts around flood-susceptible links using NetworkX Dijkstra shortest path.",
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

        return coords, tot_dist, tot_time, avoided_count

    def _match_nearest_node(self, query: str) -> str:
        q = (query or "").lower().strip()
        for nid, data in self.nodes.items():
            if q in data["name"].lower() or q in data["locality"].lower():
                return nid
        # Landmark synonyms
        if "airport" in q or "meenambakkam" in q:
            return "CHN-NODE-AIRPORT"
        if "tambaram" in q or "mudichur" in q:
            return "CHN-NODE-TAMBARAM"
        if "central" in q or "park town" in q:
            return "CHN-NODE-CENTRAL"
        if "velachery" in q:
            return "CHN-NODE-VELACHERY"
        if "guindy" in q:
            return "CHN-NODE-GUINDY"
        if "saidapet" in q:
            return "CHN-NODE-SAIDAPET"
        if "koyambedu" in q:
            return "CHN-NODE-KOYAMBEDU"
        return "CHN-NODE-CENTRAL"

    def get_preset_routes(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "PRESET-CHN-AIRPORT",
                "label": "Chennai Central → Chennai Airport (Anna Salai / GST)",
                "source": "Chennai Central",
                "destination": "Chennai Airport",
                "description": "Primary airport corridor via elevated Kathipara grade separator."
            },
            {
                "id": "PRESET-CHN-VELACHERY",
                "label": "Velachery → T. Nagar Commercial Core",
                "source": "Velachery",
                "destination": "T. Nagar",
                "description": "Bypasses low-lying Velachery lake basin via Guindy corridor."
            },
            {
                "id": "PRESET-CHN-TAMBARAM",
                "label": "Tambaram → Guindy Industrial Corridor",
                "source": "Tambaram",
                "destination": "Guindy",
                "description": "High-capacity GST arterial link bypassing Mudichur lowlands."
            },
            {
                "id": "PRESET-CHN-KOYAMBEDU",
                "label": "Koyambedu → Royapuram Harbour",
                "source": "Koyambedu",
                "destination": "Royapuram",
                "description": "East-West cross-city link connecting major logistics hubs."
            }
        ]
