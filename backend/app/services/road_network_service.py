"""
Road Network Graph & Criticality Service (CityPulse)

Prototype NetworkX digraph of curated Greater Mumbai arterial corridors
(WEH, EEH, Sea Link, subways, causeways). This is NOT a complete OSM road
network and must not be presented as live traffic or official closures.

Path geometry follows reconstructed arterial edge polylines (node sequences
with densified intermediate vertices). Coordinates are [lat, lon] for Leaflet.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import networkx as nx

from backend.app.core.config import settings


# Max snap distance (~degrees) before an endpoint is rejected as off-network.
# ~0.08 deg ≈ 9 km — generous for named landmarks mapped to nearest arterial node.
_MAX_SNAP_DEG = 0.08


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

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _densify_segment(
        a: Sequence[float],
        b: Sequence[float],
        steps: int = 6,
        bends: Optional[List[Sequence[float]]] = None,
    ) -> List[List[float]]:
        """Build a continuous [lat, lon] polyline from a→(optional bends)→b."""
        control: List[Sequence[float]] = [a]
        if bends:
            control.extend(bends)
        control.append(b)
        out: List[List[float]] = []
        for i in range(len(control) - 1):
            p0, p1 = control[i], control[i + 1]
            n = max(2, steps)
            for t in range(n):
                frac = t / (n - 1)
                pt = [p0[0] + (p1[0] - p0[0]) * frac, p0[1] + (p1[1] - p0[1]) * frac]
                if not out or out[-1] != pt:
                    out.append(pt)
        return out

    def _corridor_bends(self, edge_id: str, u: str, v: str) -> List[List[float]]:
        """Approximate arterial curvature with curated bend points (lat, lon)."""
        # Keyed by undirected edge identity so both directions share bends.
        bends_by_pair = {
            frozenset({"MUM-NODE-CST", "MUM-NODE-WADALA"}): [
                [18.9600, 72.8450],
                [18.9900, 72.8600],
                [19.0100, 72.8700],
            ],
            frozenset({"MUM-NODE-WADALA", "MUM-NODE-CHEMBUR"}): [
                [19.0350, 72.8850],
                [19.0500, 72.8950],
            ],
            frozenset({"MUM-NODE-BANDRA", "MUM-NODE-SANTACRUZ"}): [
                [19.0620, 72.8410],
                [19.0750, 72.8415],
            ],
            frozenset({"MUM-NODE-SANTACRUZ", "MUM-NODE-AIRPORT"}): [
                [19.0860, 72.8500],
            ],
            frozenset({"MUM-NODE-AIRPORT", "MUM-NODE-ANDHERI"}): [
                [19.1050, 72.8550],
            ],
            frozenset({"MUM-NODE-ANDHERI", "MUM-NODE-MALAD"}): [
                [19.1400, 72.8470],
                [19.1650, 72.8480],
            ],
            frozenset({"MUM-NODE-MALAD", "MUM-NODE-BORIVALI"}): [
                [19.2100, 72.8520],
            ],
            frozenset({"MUM-NODE-SION", "MUM-NODE-KURLA"}): [
                [19.0500, 72.8700],
                [19.0600, 72.8750],
            ],
            frozenset({"MUM-NODE-KURLA", "MUM-NODE-GHATKOPAR"}): [
                [19.0750, 72.8900],
            ],
            frozenset({"MUM-NODE-GHATKOPAR", "MUM-NODE-MULUND"}): [
                [19.1100, 72.9200],
                [19.1400, 72.9400],
            ],
            frozenset({"MUM-NODE-SEALINK", "MUM-NODE-BANDRA"}): [
                [19.0300, 72.8200],
                [19.0400, 72.8300],
            ],
            frozenset({"MUM-NODE-CST", "MUM-NODE-BYCULLA"}): [
                [18.9550, 72.8335],
            ],
            frozenset({"MUM-NODE-DADAR", "MUM-NODE-SION"}): [
                [19.0280, 72.8550],
            ],
            frozenset({"MUM-NODE-MAHIM", "MUM-NODE-BANDRA"}): [
                [19.0470, 72.8405],
            ],
            frozenset({"MUM-NODE-KURLA", "MUM-NODE-CHEMBUR"}): [
                [19.0650, 72.8900],
            ],
            frozenset({"MUM-NODE-ANDHERI", "MUM-NODE-POWAI"}): [
                [19.1220, 72.8700],
                [19.1210, 72.8900],
            ],
            frozenset({"MUM-NODE-POWAI", "MUM-NODE-GHATKOPAR"}): [
                [19.1150, 72.9100],
            ],
            frozenset({"MUM-NODE-LOWERPAREL", "MUM-NODE-SEALINK"}): [
                [19.0050, 72.8200],
            ],
        }
        pair = frozenset({u, v})
        bends = bends_by_pair.get(pair)
        if not bends:
            return []
        # Reverse bend order when traversing opposite direction
        if edge_id and u > v:
            return list(reversed(bends))
        # Prefer geographic order: start from endpoint nearer first bend
        u_lat, u_lon = self.nodes[u]["lat"], self.nodes[u]["lon"]
        first, last = bends[0], bends[-1]
        d_first = math.hypot(u_lat - first[0], u_lon - first[1])
        d_last = math.hypot(u_lat - last[0], u_lon - last[1])
        return bends if d_first <= d_last else list(reversed(bends))

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
            "MUM-NODE-MULUND": {"name": "Mulund EEH Gateway", "lat": 19.1720, "lon": 72.9560, "locality": "Mulund"},
        }

        raw_edges = [
            ("EDGE-BWSL-SEALINK", "MUM-NODE-SEALINK", "MUM-NODE-BANDRA", "Bandra-Worli Sea Link (Mahim Bay Crossing)", 5.6, 70.0, True, "Bandra West"),
            ("EDGE-LOWERPAREL-SEALINK", "MUM-NODE-LOWERPAREL", "MUM-NODE-SEALINK", "Worli Naka to Sea Link South Portal", 2.8, 45.0, False, "Worli Sea Face"),
            ("EDGE-BANDRA-SANTACRUZ", "MUM-NODE-BANDRA", "MUM-NODE-SANTACRUZ", "Western Express Highway Bandra-Santacruz", 3.5, 50.0, False, "Bandra West"),
            ("EDGE-SANTACRUZ-AIRPORT", "MUM-NODE-SANTACRUZ", "MUM-NODE-AIRPORT", "Western Express Highway Santacruz-Airport", 2.2, 55.0, False, "Vile Parle / Airport"),
            ("EDGE-AIRPORT-ANDHERI", "MUM-NODE-AIRPORT", "MUM-NODE-ANDHERI", "Western Express Highway Airport-Andheri Flyover", 3.8, 55.0, False, "Andheri"),
            ("EDGE-ANDHERI-MALAD", "MUM-NODE-ANDHERI", "MUM-NODE-MALAD", "Western Express Highway Andheri-Malad Spine", 7.5, 60.0, False, "Malad"),
            ("EDGE-MALAD-BORIVALI", "MUM-NODE-MALAD", "MUM-NODE-BORIVALI", "Western Express Highway Malad-Borivali", 5.2, 60.0, False, "Borivali"),
            ("EDGE-SION-KURLA", "MUM-NODE-SION", "MUM-NODE-KURLA", "Eastern Express Highway Sion-Kurla Link", 3.2, 50.0, False, "Sion"),
            ("EDGE-KURLA-GHATKOPAR", "MUM-NODE-KURLA", "MUM-NODE-GHATKOPAR", "Eastern Express Highway Kurla-Ghatkopar", 3.4, 55.0, False, "Ghatkopar"),
            ("EDGE-GHATKOPAR-MULUND", "MUM-NODE-GHATKOPAR", "MUM-NODE-MULUND", "Eastern Express Highway Ghatkopar-Mulund Expressway", 9.8, 65.0, False, "Mulund"),
            ("EDGE-CST-WADALA-FREEWAY", "MUM-NODE-CST", "MUM-NODE-WADALA", "Eastern Freeway South Elevated Corridor", 7.8, 65.0, True, "Wadala"),
            ("EDGE-WADALA-CHEMBUR-FREEWAY", "MUM-NODE-WADALA", "MUM-NODE-CHEMBUR", "Eastern Freeway Anik-Panjarpol Viaduct", 5.4, 65.0, True, "Chembur"),
            ("EDGE-CHURCHGATE-CST", "MUM-NODE-CHURCHGATE", "MUM-NODE-CST", "DN Road / Fort Heritage Link", 1.8, 40.0, False, "Fort / South Mumbai"),
            ("EDGE-CST-BYCULLA", "MUM-NODE-CST", "MUM-NODE-BYCULLA", "Dr. Ambedkar Road CST-Byculla Spine", 3.8, 40.0, False, "Byculla"),
            ("EDGE-BYCULLA-LOWERPAREL", "MUM-NODE-BYCULLA", "MUM-NODE-LOWERPAREL", "NM Joshi Marg Byculla-Lower Parel", 2.4, 35.0, False, "Lower Parel"),
            ("EDGE-LOWERPAREL-HINDMATA", "MUM-NODE-LOWERPAREL", "MUM-NODE-HINDMATA", "Elphinstone Flyover to Hindmata Bowl", 1.6, 35.0, False, "Hindmata / Parel"),
            ("EDGE-HINDMATA-DADAR", "MUM-NODE-HINDMATA", "MUM-NODE-DADAR", "Dr. Ambedkar Road Hindmata-Dadar TT", 1.4, 35.0, False, "Hindmata / Parel"),
            ("EDGE-DADAR-SION", "MUM-NODE-DADAR", "MUM-NODE-SION", "Dr. Ambedkar Road Dadar-Sion Flyover", 3.0, 45.0, False, "Dadar"),
            ("EDGE-DADAR-MAHIM", "MUM-NODE-DADAR", "MUM-NODE-MAHIM", "Lady Jamshedjee Road Dadar-Mahim", 2.4, 40.0, False, "Mahim"),
            ("EDGE-MAHIM-BANDRA", "MUM-NODE-MAHIM", "MUM-NODE-BANDRA", "Mahim Causeway Bridge (Mithi Outfall Crossing)", 2.1, 45.0, True, "Mahim"),
            ("EDGE-SION-BKC", "MUM-NODE-SION", "MUM-NODE-BKC", "Sion-Bandra Link Road (Mithi River Crossing)", 2.8, 40.0, True, "BKC"),
            ("EDGE-BKC-KURLA", "MUM-NODE-BKC", "MUM-NODE-KURLA", "BKC-Kurla Connector", 2.2, 40.0, False, "Kurla"),
            ("EDGE-BKC-BANDRA", "MUM-NODE-BKC", "MUM-NODE-BANDRA", "Kalanagar Grade Separator to BKC", 3.0, 45.0, False, "BKC"),
            ("EDGE-KURLA-CHEMBUR-SCLR", "MUM-NODE-KURLA", "MUM-NODE-CHEMBUR", "Santacruz-Chembur Link Road (SCLR Bridge)", 3.6, 50.0, True, "Kurla"),
            ("EDGE-ANDHERI-POWAI-JVLR", "MUM-NODE-ANDHERI", "MUM-NODE-POWAI", "Jogeshwari-Vikhroli Link Road (JVLR West)", 5.8, 50.0, False, "Powai"),
            ("EDGE-POWAI-GHATKOPAR-JVLR", "MUM-NODE-POWAI", "MUM-NODE-GHATKOPAR", "Jogeshwari-Vikhroli Link Road (JVLR East)", 4.5, 50.0, False, "Powai"),
            ("EDGE-CHEMBUR-MANKHURD", "MUM-NODE-CHEMBUR", "MUM-NODE-MANKHURD", "Sion-Panvel Expressway Mankhurd-Vashi Link", 4.2, 55.0, True, "Mankhurd"),
            ("EDGE-ANDHERI-SUBWAY", "MUM-NODE-ANDHERI", "MUM-NODE-ANDHERI-SUBWAY", "Andheri Subway Rail Underpass Link", 1.2, 25.0, True, "Andheri Subway"),
            ("EDGE-SANTACRUZ-KHAR-SUBWAY", "MUM-NODE-SANTACRUZ", "MUM-NODE-KHAR-SUBWAY", "Khar-Milan Subway Underpass Link", 1.8, 25.0, True, "Khar"),
            # Cross-links that create genuine alternative corridors (west vs east spines)
            ("EDGE-CHEMBUR-AIRPORT", "MUM-NODE-CHEMBUR", "MUM-NODE-AIRPORT", "Chembur-Airport Connector via Marol", 6.5, 45.0, False, "Vile Parle / Airport"),
            ("EDGE-WADALA-SION", "MUM-NODE-WADALA", "MUM-NODE-SION", "Wadala-Sion Link Road", 2.6, 40.0, False, "Sion"),
            ("EDGE-DADAR-BANDRA", "MUM-NODE-DADAR", "MUM-NODE-BANDRA", "Tilak Bridge / Western Coastal Approach", 4.8, 40.0, False, "Mahim"),
        ]

        self.edge_definitions = []
        for eid, u, v, name, dist_km, speed_kmh, is_bridge, loc in raw_edges:
            free_time = (dist_km / max(10.0, speed_kmh)) * 60.0
            u_coords = [self.nodes[u]["lat"], self.nodes[u]["lon"]]
            v_coords = [self.nodes[v]["lat"], self.nodes[v]["lon"]]
            bends = self._corridor_bends(eid, u, v)
            coords = self._densify_segment(u_coords, v_coords, steps=8, bends=bends)

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
                "coordinates": coords,
                "geometrySource": "curated_arterial_polyline",
            }
            self.edge_definitions.append(edge_data)

            self.graph.add_edge(u, v, **edge_data, weight=free_time)
            self.graph.add_edge(v, u, **edge_data, weight=free_time)
            self.undirected_graph.add_edge(u, v, **edge_data, weight=free_time)

    def _calculate_network_metrics(self):
        """Calculates topological edge betweenness centrality and bridges (cut-edges)."""
        edge_betweenness = nx.edge_betweenness_centrality(self.graph, weight="weight", normalized=True)
        self.betweenness_cache = {}
        for (u, v), b_val in edge_betweenness.items():
            key = f"{min(u, v)}--{max(u, v)}"
            self.betweenness_cache[key] = max(self.betweenness_cache.get(key, 0.0), b_val)

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

            susceptibility = 0.15
            if flood_service:
                zone = flood_service.get_location_risk(ed["locality"])
                if zone:
                    susceptibility = float(zone.get("probability", 0.15))

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
                "status": status,
            })

        return sorted(items, key=lambda x: x["criticality_score"], reverse=True)

    def get_nearest_node_to_coords(self, lat: float, lon: float) -> Tuple[str, float]:
        """Nearest network node and Euclidean degree distance."""
        best_node = next(iter(self.nodes.keys()))
        best_dist = float("inf")
        for nid, data in self.nodes.items():
            d = math.hypot(lat - data["lat"], lon - data["lon"])
            if d < best_dist:
                best_dist = d
                best_node = nid
        return best_node, best_dist

    def _paths_substantially_same(self, a: List[str], b: List[str]) -> bool:
        if a == b:
            return True
        if not a or not b:
            return False
        sa, sb = set(a), set(b)
        if len(sa) <= 2 and sa == sb:
            return True
        overlap = len(sa & sb) / max(len(sa | sb), 1)
        return overlap >= 0.85 and abs(len(a) - len(b)) <= 1

    def _find_disjoint_alternative(
        self,
        graph: nx.DiGraph,
        s_node: str,
        d_node: str,
        primary_path: List[str],
    ) -> Optional[List[str]]:
        """Find a loopless path that differs from primary by removing primary edges."""
        if len(primary_path) < 2:
            return None

        # Attempt 1: remove all primary edges at once
        g = graph.copy()
        for i in range(len(primary_path) - 1):
            u, v = primary_path[i], primary_path[i + 1]
            if g.has_edge(u, v):
                g.remove_edge(u, v)
            if g.has_edge(v, u):
                g.remove_edge(v, u)
        try:
            alt = nx.shortest_path(g, source=s_node, target=d_node, weight="weight")
            if not self._paths_substantially_same(primary_path, alt):
                return alt
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        # Attempt 2: remove one primary edge at a time (prefer high-betweenness)
        edge_candidates = []
        for i in range(len(primary_path) - 1):
            u, v = primary_path[i], primary_path[i + 1]
            key = f"{min(u, v)}--{max(u, v)}"
            edge_candidates.append((self.betweenness_cache.get(key, 0.0), u, v))
        edge_candidates.sort(reverse=True)

        for _, u, v in edge_candidates:
            g2 = graph.copy()
            if g2.has_edge(u, v):
                g2.remove_edge(u, v)
            if g2.has_edge(v, u):
                g2.remove_edge(v, u)
            try:
                alt = nx.shortest_path(g2, source=s_node, target=d_node, weight="weight")
                if not self._paths_substantially_same(primary_path, alt):
                    return alt
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
        return None

    def calculate_safe_route(
        self,
        source: Optional[str] = None,
        destination: Optional[str] = None,
        vehicle_type: str = "car",
        flood_service=None,
        source_coords: Optional[List[float]] = None,
        dest_coords: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Risk-aware Dijkstra on arterial graph + distinct alternative when feasible."""
        snap_warnings: List[str] = []

        if source_coords and len(source_coords) >= 2:
            s_node, s_snap = self.get_nearest_node_to_coords(source_coords[0], source_coords[1])
            if s_snap > _MAX_SNAP_DEG:
                raise ValueError(
                    f"Origin ({source_coords[0]}, {source_coords[1]}) is too far from the "
                    f"prototype arterial network (nearest node {s_snap:.3f}° away)."
                )
            s_coords = [float(source_coords[0]), float(source_coords[1])]
        else:
            s_node = self._match_nearest_node(source or "CSMT Fort")
            s_coords = [self.nodes[s_node]["lat"], self.nodes[s_node]["lon"]]

        if dest_coords and len(dest_coords) >= 2:
            d_node, d_snap = self.get_nearest_node_to_coords(dest_coords[0], dest_coords[1])
            if d_snap > _MAX_SNAP_DEG:
                raise ValueError(
                    f"Destination ({dest_coords[0]}, {dest_coords[1]}) is too far from the "
                    f"prototype arterial network (nearest node {d_snap:.3f}° away)."
                )
            d_coords = [float(dest_coords[0]), float(dest_coords[1])]
        else:
            d_node = self._match_nearest_node(destination or "CSMIA International Airport")
            d_coords = [self.nodes[d_node]["lat"], self.nodes[d_node]["lon"]]

        if s_node == d_node:
            return self._intra_precinct_result(s_node, d_node, s_coords, d_coords)

        v_type = (vehicle_type or "car").lower()
        vehicle_speed_factor = 0.85 if v_type in ["suv", "rescue", "truck"] else 1.0

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

            penalty_multiplier = 1.0 + 9.0 * (risk ** 2.0)
            if risk >= settings.DISRUPTION_THRESHOLD_CRITICAL and v_type != "rescue":
                penalty_multiplier *= 10.0

            impedance = base_time * penalty_multiplier
            G_dynamic.add_edge(u, v, weight=impedance, dist=ed["length_km"], base_time=base_time, eid=ed["edge_id"])
            G_dynamic.add_edge(v, u, weight=impedance, dist=ed["length_km"], base_time=base_time, eid=ed["edge_id"])

        try:
            risk_aware_nodes = nx.shortest_path(G_dynamic, source=s_node, target=d_node, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
            raise ValueError(
                f"No connected arterial path between '{self.nodes[s_node]['name']}' and "
                f"'{self.nodes[d_node]['name']}' on the prototype network."
            ) from exc

        # Free-flow baseline (often shorter/faster, may traverse higher-risk edges)
        try:
            free_flow_nodes = nx.shortest_path(self.graph, source=s_node, target=d_node, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            free_flow_nodes = list(risk_aware_nodes)

        # Prefer a geometrically distinct alternative; fall back to free-flow if different
        alt_nodes: Optional[List[str]] = None
        if not self._paths_substantially_same(risk_aware_nodes, free_flow_nodes):
            alt_nodes = free_flow_nodes
        else:
            alt_nodes = self._find_disjoint_alternative(self.graph, s_node, d_node, risk_aware_nodes)

        safe_metrics = self._extract_path_metrics(risk_aware_nodes, edge_risks)
        alt_metrics = self._extract_path_metrics(alt_nodes, edge_risks) if alt_nodes else None

        # Ensure the route labelled "safer" has lower (or equal) length-weighted risk
        safer_nodes = risk_aware_nodes
        safer_m = safe_metrics
        higher_nodes = alt_nodes
        higher_m = alt_metrics

        if higher_m is not None and higher_m["riskExposureScore"] + 1e-6 < safer_m["riskExposureScore"]:
            # Free-flow / alt actually safer under scoring — swap labels honestly
            safer_nodes, higher_nodes = higher_nodes, safer_nodes
            safer_m, higher_m = higher_m, safer_m

        # Prepend/append request endpoints when they differ from snapped nodes
        safer_coords = self._attach_endpoints(s_coords, safer_m["coords"], d_coords, safer_nodes, s_node, d_node)
        higher_coords = None
        if higher_m is not None and higher_nodes is not None:
            higher_coords = self._attach_endpoints(s_coords, higher_m["coords"], d_coords, higher_nodes, s_node, d_node)

        high_on_safer = safer_m["highRiskEdges"]
        high_on_alt = higher_m["highRiskEdges"] if higher_m else 0
        avoided = max(0, high_on_alt - high_on_safer)

        safer_option = self._build_route_option(
            route_id="REC-SAFE-PATH",
            name=f"Lower-Risk Arterial Route via {len(safer_nodes)} Nodes",
            route_type="RECOMMENDED_SAFE",
            metrics=safer_m,
            path_coords=safer_coords,
            nodes=safer_nodes,
            flood_points_avoided=avoided,
            notes=(
                "Minimises travel time with quadratic flood-susceptibility penalties on arterial edges. "
                "Geometry follows the curated Greater Mumbai arterial graph (not a full OSM network). "
                f"Length-weighted risk exposure: {safer_m['riskExposureScore']:.3f}."
            ),
        )

        alternative_option = None
        unavailable_reason = None
        if higher_m is not None and higher_nodes is not None and higher_coords is not None:
            tradeoff = (
                f"Compared with the safer route: "
                f"Δdistance {higher_m['distanceKm'] - safer_m['distanceKm']:+.1f} km, "
                f"Δtime {higher_m['etaMinutes'] - safer_m['etaMinutes']:+.0f} min, "
                f"Δrisk exposure {higher_m['riskExposureScore'] - safer_m['riskExposureScore']:+.3f}."
            )
            alternative_option = self._build_route_option(
                route_id="ALT-HIGHER-RISK",
                name=f"Alternative Arterial Route via {len(higher_nodes)} Nodes",
                route_type="FASTER_ALTERNATIVE",
                metrics=higher_m,
                path_coords=higher_coords,
                nodes=higher_nodes,
                flood_points_avoided=0,
                notes=(
                    "Distinct feasible corridor on the same arterial graph. "
                    + tradeoff
                ),
            )
        else:
            unavailable_reason = (
                "Only one feasible corridor exists between these endpoints on the prototype "
                "arterial network; a meaningfully different alternative path is not available."
            )

        hazards = self._path_derived_hazards(safer_nodes, higher_nodes, edge_risks)

        return {
            "source": self.nodes[s_node]["name"],
            "destination": self.nodes[d_node]["name"],
            "sourceCoords": s_coords,
            "destCoords": d_coords,
            "recommendedRoute": safer_option,
            "alternativeRoute": alternative_option,
            "alternativeUnavailableReason": unavailable_reason,
            "hazards": hazards,
            "networkProvenance": (
                "Curated BMC arterial prototype graph with densified edge polylines. "
                "Not complete OpenStreetMap coverage. Flood penalties use locality susceptibility proxies."
            ),
            "isSimulated": True,
            "geometrySource": "arterial_graph_reconstruction",
            "warnings": snap_warnings,
        }

    def _intra_precinct_result(
        self,
        s_node: str,
        d_node: str,
        s_coords: List[float],
        d_coords: List[float],
    ) -> Dict[str, Any]:
        locality_name = self.nodes[s_node]["locality"]
        node_pt = [self.nodes[s_node]["lat"], self.nodes[s_node]["lon"]]
        # Honest: same arterial node — no fabricated second corridor
        path_pts = [s_coords]
        if s_coords != node_pt:
            path_pts.append(node_pt)
        if d_coords != path_pts[-1]:
            path_pts.append(d_coords)
        intra_dist = round(
            sum(
                math.hypot(path_pts[i][0] - path_pts[i + 1][0], path_pts[i][1] - path_pts[i + 1][1]) * 111.0
                for i in range(len(path_pts) - 1)
            ),
            2,
        )
        intra_time = max(1, int(round((max(intra_dist, 0.2) / 25.0) * 60)))
        option = {
            "id": "REC-INTRA-PRECINCT",
            "name": f"Intra-Precinct Access within {locality_name}",
            "type": "RECOMMENDED_SAFE",
            "distanceKm": max(0.2, intra_dist),
            "etaMinutes": intra_time,
            "safetyScore": 90,
            "riskStatus": "SAFE",
            "floodPointsAvoided": 0,
            "hazardExposure": "Low",
            "riskExposureScore": 0.1,
            "highRiskEdgeCount": 0,
            "pathCoordinates": path_pts,
            "nodesVisited": [s_node],
            "notes": (
                f"Origin and destination snap to the same arterial node ({locality_name}). "
                "No distinct higher-risk alternative corridor exists at this scale."
            ),
            "isSimulated": True,
            "geometrySource": "arterial_node_snap",
        }
        return {
            "source": self.nodes[s_node]["name"],
            "destination": self.nodes[d_node]["name"],
            "sourceCoords": s_coords,
            "destCoords": d_coords,
            "recommendedRoute": option,
            "alternativeRoute": None,
            "alternativeUnavailableReason": (
                "Origin and destination share the same arterial precinct; "
                "a second network path is not available."
            ),
            "hazards": [],
            "networkProvenance": "Curated BMC arterial prototype graph.",
            "isSimulated": True,
            "geometrySource": "arterial_node_snap",
            "warnings": [],
        }

    def _attach_endpoints(
        self,
        s_coords: List[float],
        path_coords: List[List[float]],
        d_coords: List[float],
        nodes: List[str],
        s_node: str,
        d_node: str,
    ) -> List[List[float]]:
        coords = [list(c) for c in path_coords]
        if not coords:
            coords = [
                [self.nodes[nodes[0]]["lat"], self.nodes[nodes[0]]["lon"]],
                [self.nodes[nodes[-1]]["lat"], self.nodes[nodes[-1]]["lon"]],
            ]
        if s_coords != coords[0]:
            coords.insert(0, list(s_coords))
        if d_coords != coords[-1]:
            coords.append(list(d_coords))
        return coords

    def _build_route_option(
        self,
        route_id: str,
        name: str,
        route_type: str,
        metrics: Dict[str, Any],
        path_coords: List[List[float]],
        nodes: List[str],
        flood_points_avoided: int,
        notes: str,
    ) -> Dict[str, Any]:
        risk_score = metrics["riskExposureScore"]
        high = metrics["highRiskEdges"]
        if risk_score < 0.25 and high == 0:
            status, exposure = "SAFE", "Low"
        elif risk_score < 0.45:
            status, exposure = "CAUTION", "Medium"
        else:
            status, exposure = "UNSAFE", "High"

        safety = max(15, min(98, int(round(100 - risk_score * 100 - high * 8))))

        return {
            "id": route_id,
            "name": name,
            "type": route_type,
            "distanceKm": round(metrics["distanceKm"], 1),
            "etaMinutes": int(round(metrics["etaMinutes"])),
            "safetyScore": safety,
            "riskStatus": status,
            "floodPointsAvoided": flood_points_avoided,
            "hazardExposure": exposure,
            "riskExposureScore": round(risk_score, 4),
            "highRiskEdgeCount": high,
            "pathCoordinates": path_coords,
            "nodesVisited": nodes,
            "notes": notes,
            "isSimulated": True,
            "geometrySource": "arterial_graph_reconstruction",
        }

    def _path_derived_hazards(
        self,
        safer_nodes: List[str],
        alt_nodes: Optional[List[str]],
        edge_risks: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """Hazards from high-risk edges actually traversed by either candidate."""
        hazards: List[Dict[str, Any]] = []
        seen = set()
        for path in (safer_nodes, alt_nodes or []):
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                ed = next(
                    (e for e in self.edge_definitions if (e["u"] == u and e["v"] == v) or (e["u"] == v and e["v"] == u)),
                    None,
                )
                if not ed:
                    continue
                risk = edge_risks.get(ed["edge_id"], 0.0)
                if risk < settings.DISRUPTION_THRESHOLD_HIGH:
                    continue
                if ed["edge_id"] in seen:
                    continue
                seen.add(ed["edge_id"])
                mid = ed["coordinates"][len(ed["coordinates"]) // 2]
                hazards.append({
                    "id": f"HAZ-{ed['edge_id']}",
                    "title": f"Elevated susceptibility: {ed['name']}",
                    "location": ed["locality"],
                    "coordinates": [mid[0], mid[1]],
                    "severity": "UNSAFE" if risk >= settings.DISRUPTION_THRESHOLD_CRITICAL else "CAUTION",
                    "waterDepthCm": 0,
                    "status": "PROXY_SUSCEPTIBILITY",
                    "isSimulated": True,
                })
        return hazards

    def _extract_path_metrics(
        self,
        path_nodes: List[str],
        edge_risks: Dict[str, float],
    ) -> Dict[str, Any]:
        coords: List[List[float]] = []
        tot_dist = 0.0
        tot_time = 0.0
        high_risk = 0
        risk_length = 0.0

        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i + 1]
            ed = next(
                (e for e in self.edge_definitions if (e["u"] == u and e["v"] == v) or (e["u"] == v and e["v"] == u)),
                None,
            )
            if ed:
                tot_dist += ed["length_km"]
                tot_time += ed["free_flow_time_min"]
                risk = edge_risks.get(ed["edge_id"], 0.0)
                risk_length += risk * ed["length_km"]
                if risk >= settings.DISRUPTION_THRESHOLD_HIGH:
                    high_risk += 1
                if ed["u"] == u and ed["v"] == v:
                    edge_coords = list(ed["coordinates"])
                else:
                    edge_coords = list(reversed(ed["coordinates"]))
                for c in edge_coords:
                    if not coords or coords[-1] != c:
                        coords.append(list(c))
            else:
                for nid in (u, v):
                    pt = [self.nodes[nid]["lat"], self.nodes[nid]["lon"]]
                    if not coords or coords[-1] != pt:
                        coords.append(pt)

        if not coords and path_nodes:
            coords = [[self.nodes[path_nodes[0]]["lat"], self.nodes[path_nodes[0]]["lon"]]]

        exposure = (risk_length / tot_dist) if tot_dist > 0 else 0.15
        return {
            "coords": coords,
            "distanceKm": tot_dist,
            "etaMinutes": tot_time,
            "highRiskEdges": high_risk,
            "riskExposureScore": exposure,
        }

    def _match_nearest_node(self, query: str) -> str:
        q = (query or "").lower().strip()

        cleaned = q.replace(",", " ").replace(";", " ")
        tokens = [t.strip() for t in cleaned.split() if t.strip()]
        if len(tokens) == 2:
            try:
                v1, v2 = float(tokens[0]), float(tokens[1])
                if 18.5 <= v1 <= 19.5 and 72.5 <= v2 <= 73.2:
                    return self.get_nearest_node_to_coords(v1, v2)[0]
                elif 18.5 <= v2 <= 19.5 and 72.5 <= v1 <= 73.2:
                    return self.get_nearest_node_to_coords(v2, v1)[0]
            except ValueError:
                pass

        for nid, data in self.nodes.items():
            if q in data["name"].lower() or q in data["locality"].lower():
                return nid

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
        if "kem" in q or "edward memorial" in q:
            return "MUM-NODE-HINDMATA"
        if "lokmanya" in q or "sion hospital" in q:
            return "MUM-NODE-SION"
        if "lilavati" in q:
            return "MUM-NODE-BANDRA"
        if "kokilaben" in q:
            return "MUM-NODE-ANDHERI"
        if "fire" in q and "byculla" in q:
            return "MUM-NODE-BYCULLA"

        return "MUM-NODE-CST"

    def get_preset_routes(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "PRESET-MUM-AIRPORT",
                "label": "CSMT Fort → Mumbai Airport CSMIA (via Eastern Freeway / WEH)",
                "source": "CSMT Fort",
                "destination": "CSMIA International Airport",
                "description": "Primary metropolitan transit corridor connecting South Mumbai heritage commercial core to international airport terminal.",
            },
            {
                "id": "PRESET-MUM-BKC",
                "label": "Dadar TT Circle → Bandra-Kurla Complex (BKC)",
                "source": "Dadar TT Circle",
                "destination": "Bandra-Kurla Complex (BKC)",
                "description": "Essential financial corridor bypassing Mahim Bay and Mithi River lowlands.",
            },
            {
                "id": "PRESET-MUM-BORIVALI",
                "label": "Borivali → Bandra West (Western Express Highway Corridor)",
                "source": "Borivali",
                "destination": "Bandra Western Spine",
                "description": "Major North-South suburban arterial corridor connecting Northern suburbs to coastal bridges.",
            },
            {
                "id": "PRESET-MUM-KURLA",
                "label": "Sion Circle → Kurla Mithi Basin",
                "source": "Sion Circle",
                "destination": "Kurla Mithi River Corridor",
                "description": "Cross-catchment arterial route linking Central Mumbai to Eastern Express Highway.",
            },
        ]
