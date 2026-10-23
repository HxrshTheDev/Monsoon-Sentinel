"""
Road Network Graph & Flood-Aware Routing (CityPulse)

Loads a cached OpenStreetMap drive network for Greater Mumbai and runs
Dijkstra / risk-penalized shortest paths over real road-segment geometry.

Cache: data/processed/roads/mumbai_drive_network.json.gz
Build: python scripts/build_mumbai_road_network.py

API path coordinates remain [lat, lon] (Leaflet order). Stored OSM geometry
uses GeoJSON [lon, lat] and is converted on load.
"""

from __future__ import annotations

import gzip
import json
import logging
import math
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Named landmarks → WGS84 for preset / text queries (snapped onto OSM nodes).
MUMBAI_LANDMARKS: Dict[str, Dict[str, Any]] = {
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

_MAJOR_HIGHWAYS = {
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
}


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _lonlat_to_latlon(coords_lonlat: Sequence[Sequence[float]]) -> List[List[float]]:
    return [[float(c[1]), float(c[0])] for c in coords_lonlat]


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
        self.betweenness_cache: Dict[str, float] = {}
        self.bridges_set: set = set()
        self.network_meta: Dict[str, Any] = {}
        self.network_available: bool = False
        self._network_metrics_calculated = False
        self.geometry_source: str = "missing"
        self._landmark_to_node: Dict[str, str] = {}
        self._node_ids: List[str] = []
        self._node_coords: Optional[np.ndarray] = None  # shape (N, 2) lat, lon

        self._load_network()
        if self.network_available:
            self._index_nodes()
            self._snap_landmarks()

    # ------------------------------------------------------------------
    # Load / index
    # ------------------------------------------------------------------

    def _resolve_network_path(self) -> str:
        configured = settings.ROAD_NETWORK_PATH
        if os.path.isabs(configured):
            return configured
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        return os.path.join(project_root, configured.lstrip("./"))

    def _load_network(self) -> None:
        path = self._resolve_network_path()
        if not os.path.exists(path):
            logger.error(
                "Road network cache missing at %s. Run: python scripts/build_mumbai_road_network.py",
                path,
            )
            self.network_available = False
            self.geometry_source = "missing"
            # Keep landmark stubs so name APIs do not crash; routing will error clearly.
            self.nodes = {k: dict(v) for k, v in MUMBAI_LANDMARKS.items()}
            return

        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as f:
            payload = json.load(f)

        self.network_meta = payload.get("meta") or {}
        raw_nodes = payload.get("nodes") or {}
        raw_edges = payload.get("edges") or []

        for nid, nd in raw_nodes.items():
            self.nodes[nid] = {
                "name": nid,
                "lat": float(nd["lat"]),
                "lon": float(nd["lon"]),
                "locality": "Greater Mumbai",
            }

        for ed in raw_edges:
            u, v = ed["u"], ed["v"]
            if u not in self.nodes or v not in self.nodes:
                continue
            length_km = float(ed.get("length_km") or (float(ed.get("length_m", 0.0)) / 1000.0))
            length_m = float(ed.get("length_m") or length_km * 1000.0)
            if length_m < 0.5:
                continue
            speed = float(ed.get("free_flow_speed_kmh") or 35.0)
            free_time = (length_m / 1000.0 / max(10.0, speed)) * 60.0
            coords_ll = ed.get("coordinates_lonlat") or []
            if len(coords_ll) < 2:
                logger.warning("Skipping OSM edge %s without road geometry.", ed.get("edge_id"))
                continue
            if (
                _haversine_m(
                    self.nodes[u]["lat"], self.nodes[u]["lon"],
                    float(coords_ll[0][1]), float(coords_ll[0][0]),
                ) > 1.0
                or _haversine_m(
                    self.nodes[v]["lat"], self.nodes[v]["lon"],
                    float(coords_ll[-1][1]), float(coords_ll[-1][0]),
                ) > 1.0
            ):
                logger.warning("Skipping OSM edge %s whose geometry does not meet its graph nodes.", ed.get("edge_id"))
                continue
            coords = _lonlat_to_latlon(coords_ll)
            mid = coords[len(coords) // 2]
            locality = f"{mid[0]:.4f}, {mid[1]:.4f}"

            edge_data = {
                "edge_id": ed["edge_id"],
                "u": u,
                "v": v,
                "name": ed.get("name") or ed["edge_id"],
                "highway": ed.get("highway") or "road",
                "length_km": length_km,
                "length_m": length_m,
                "free_flow_speed_kmh": speed,
                "free_flow_time_min": round(free_time, 3),
                "is_bridge": bool(ed.get("is_bridge")),
                "is_tunnel": bool(ed.get("is_tunnel")),
                "oneway": bool(ed.get("oneway")),
                "locality": locality,
                "coordinates": coords,
                "geometrySource": ed.get("geometrySource") or "openstreetmap",
                "osm_way_id": ed.get("osm_way_id"),
                "source": ed.get("source") or "OpenStreetMap",
            }
            self.edge_definitions.append(edge_data)
            existing = self.graph.get_edge_data(u, v)
            if existing is None or length_m < float(existing.get("length_m", float("inf"))):
                self.graph.add_edge(u, v, **edge_data, weight=length_m)

        self.network_available = len(self.edge_definitions) > 0
        self.geometry_source = "openstreetmap_road_network"
        logger.info(
            "Loaded OSM road network: %s nodes, %s directed edges (%s)",
            len(self.nodes),
            len(self.edge_definitions),
            path,
        )

    def _index_nodes(self) -> None:
        self._node_ids = list(self.graph.nodes())
        if not self._node_ids:
            self._node_coords = np.zeros((0, 2))
            return
        self._node_coords = np.array(
            [[self.nodes[n]["lat"], self.nodes[n]["lon"]] for n in self._node_ids],
            dtype=np.float64,
        )

    def _snap_landmarks(self) -> None:
        self._landmark_to_node = {}
        for lid, meta in MUMBAI_LANDMARKS.items():
            node, dist_m = self.get_nearest_node_to_coords(meta["lat"], meta["lon"])
            if dist_m <= settings.ROAD_SNAP_MAX_METERS * 2:
                self._landmark_to_node[lid] = node
                # Alias landmark id onto snapped OSM node metadata for display
                self.nodes[node]["landmark"] = lid
                self.nodes[node]["name"] = meta["name"]
                self.nodes[node]["locality"] = meta["locality"]

    def _calculate_network_metrics(self) -> None:
        """Approximate betweenness on a major-road subgraph (full OSM is too large)."""
        major = nx.Graph()
        for ed in self.edge_definitions:
            if ed.get("highway") not in _MAJOR_HIGHWAYS and not ed.get("is_bridge"):
                continue
            u, v = ed["u"], ed["v"]
            if not major.has_edge(u, v):
                major.add_edge(u, v, weight=ed["length_m"])

        self.betweenness_cache = {}
        if major.number_of_edges() == 0:
            return

        sample_k = min(40, max(8, major.number_of_nodes() // 200))
        try:
            ebb = nx.edge_betweenness_centrality(major, weight="weight", normalized=True, k=sample_k)
            for (u, v), b_val in ebb.items():
                key = f"{min(u, v)}--{max(u, v)}"
                self.betweenness_cache[key] = max(self.betweenness_cache.get(key, 0.0), float(b_val))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Betweenness approximation skipped: %s", exc)

        try:
            raw_bridges = list(nx.bridges(major))
            self.bridges_set = {f"{min(u, v)}--{max(u, v)}" for u, v in raw_bridges}
        except Exception:
            self.bridges_set = set()

        # OSM-tagged bridges always count
        for ed in self.edge_definitions:
            if ed.get("is_bridge"):
                key = f"{min(ed['u'], ed['v'])}--{max(ed['u'], ed['v'])}"
                self.bridges_set.add(key)

    # ------------------------------------------------------------------
    # Snapping / validation
    # ------------------------------------------------------------------

    def _in_bounds(self, lat: float, lon: float) -> bool:
        return (
            settings.BOUNDS_MIN_LAT - 0.02 <= lat <= settings.BOUNDS_MAX_LAT + 0.02
            and settings.BOUNDS_MIN_LON - 0.02 <= lon <= settings.BOUNDS_MAX_LON + 0.02
        )

    def get_nearest_node_to_coords(self, lat: float, lon: float) -> Tuple[str, float]:
        """Nearest graph node; returns (node_id, distance_metres)."""
        if self._node_coords is None or len(self._node_ids) == 0:
            raise ValueError("Road network is not loaded.")
        # Coarse degree distance then haversine on top candidates
        d2 = (self._node_coords[:, 0] - lat) ** 2 + (self._node_coords[:, 1] - lon) ** 2
        top = np.argpartition(d2, min(24, len(d2) - 1))[:24]
        best_i = int(top[0])
        best_m = _haversine_m(lat, lon, float(self._node_coords[best_i, 0]), float(self._node_coords[best_i, 1]))
        for i in top:
            i = int(i)
            m = _haversine_m(lat, lon, float(self._node_coords[i, 0]), float(self._node_coords[i, 1]))
            if m < best_m:
                best_m = m
                best_i = i
        return self._node_ids[best_i], best_m

    def resolve_node(
        self,
        query: Optional[str] = None,
        coords: Optional[Sequence[float]] = None,
        role: str = "endpoint",
    ) -> Tuple[str, List[float], float]:
        """
        Resolve a named landmark or [lat, lon] to a snapped OSM node.
        Returns (node_id, request_coords_[lat,lon], snap_distance_m).
        """
        if not self.network_available:
            raise ValueError(
                "Road network data is missing. Build the OSM cache with "
                "`python scripts/build_mumbai_road_network.py` and restart the API."
            )

        if coords is not None:
            if len(coords) != 2 or not all(math.isfinite(float(value)) for value in coords):
                raise ValueError(f"{role.capitalize()} coordinates must contain finite [latitude, longitude].")
            lat, lon = float(coords[0]), float(coords[1])
            if not self._in_bounds(lat, lon):
                raise ValueError(
                    f"{role.capitalize()} ({lat}, {lon}) is outside the supported Greater Mumbai area."
                )
            node, dist_m = self.get_nearest_node_to_coords(lat, lon)
            if dist_m > settings.ROAD_SNAP_MAX_METERS:
                raise ValueError(
                    f"{role.capitalize()} ({lat}, {lon}) is too far from a mapped road "
                    f"({dist_m:.0f} m; max {settings.ROAD_SNAP_MAX_METERS:.0f} m)."
                )
            return node, [lat, lon], dist_m

        landmark_id = self._match_landmark_id(query or "")
        meta = MUMBAI_LANDMARKS[landmark_id]
        lat, lon = meta["lat"], meta["lon"]
        node = self._landmark_to_node.get(landmark_id)
        if not node:
            node, dist_m = self.get_nearest_node_to_coords(lat, lon)
        else:
            dist_m = _haversine_m(lat, lon, self.nodes[node]["lat"], self.nodes[node]["lon"])
        if dist_m > settings.ROAD_SNAP_MAX_METERS * 2:
            raise ValueError(
                f"{role.capitalize()} '{meta['name']}' could not be snapped to the road network "
                f"({dist_m:.0f} m from nearest node)."
            )
        return node, [lat, lon], dist_m

    # ------------------------------------------------------------------
    # Criticality
    # ------------------------------------------------------------------

    def get_road_criticality_items(self, flood_service=None) -> List[Dict[str, Any]]:
        """Major-road undirected segments with betweenness, bridge status, flood susceptibility."""
        if not self._network_metrics_calculated:
            self._calculate_network_metrics()
            self._network_metrics_calculated = True
        items = []
        seen = set()
        road_edges = [
            ed for ed in self.edge_definitions
            if ed.get("highway") in _MAJOR_HIGHWAYS or ed.get("is_bridge")
        ]
        risk_index = self._build_flood_risk_index(flood_service)
        edge_risks, edge_risk_known = self._sample_edge_flood_risks(road_edges, risk_index)
        for ed in road_edges:
            u, v = ed["u"], ed["v"]
            key = f"{min(u, v)}--{max(u, v)}"
            if key in seen:
                continue
            seen.add(key)

            betweenness = self.betweenness_cache.get(key, 0.02)
            is_cut_edge = key in self.bridges_set or ed["is_bridge"]

            susceptibility = edge_risks[ed["edge_id"]]
            risk_known = edge_risk_known[ed["edge_id"]]

            crit_score = min(
                1.0,
                (betweenness * 3.5)
                + (0.35 if is_cut_edge else 0.0)
                + (ed["length_km"] / 30.0),
            )

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
                "risk_known": risk_known,
                "criticality_score": round(crit_score, 4),
                "coordinates": ed["coordinates"],
                "locality": ed["locality"],
                "status": status,
            })

        return sorted(items, key=lambda x: x["criticality_score"], reverse=True)

    def _build_flood_risk_index(
        self, flood_service
    ) -> Optional[Tuple[cKDTree, np.ndarray]]:
        """KD-tree over flood-zone centroids for O(log n) edge risk lookup."""
        if flood_service is None:
            return None
        try:
            zones = flood_service.get_flood_zones("NOW")
            if not zones:
                return None
            coords = np.array([[z["latitude"], z["longitude"]] for z in zones], dtype=np.float64)
            probs = np.array([float(z.get("probability") or 0.0) for z in zones], dtype=np.float64)
            return cKDTree(coords), probs
        except Exception as exc:  # noqa: BLE001
            logger.warning("Flood risk spatial index unavailable: %s", exc)
            return None

    def _edge_flood_risk(
        self,
        ed: Dict[str, Any],
        risk_index: Optional[Tuple[cKDTree, np.ndarray]] = None,
    ) -> Tuple[float, bool]:
        """Sample susceptibility along the edge; partially unknown edges stay unknown."""
        risks, known = self._sample_edge_flood_risks([ed], risk_index)
        edge_id = ed.get("edge_id") or ""
        return risks[edge_id], known[edge_id]

    def _sample_edge_flood_risks(
        self,
        edges: List[Dict[str, Any]],
        risk_index: Optional[Tuple[cKDTree, np.ndarray]],
    ) -> Tuple[Dict[str, float], Dict[str, bool]]:
        risks: Dict[str, float] = {}
        known_edges: Dict[str, bool] = {}
        if risk_index is None:
            for edge in edges:
                edge_id = edge.get("edge_id") or ""
                risks[edge_id] = settings.UNKNOWN_RISK_DEFAULT
                known_edges[edge_id] = False
            return risks, known_edges

        samples: List[List[float]] = []
        spans: List[Tuple[str, int, int]] = []
        for edge in edges:
            edge_id = edge.get("edge_id") or ""
            start_idx = len(samples)
            coords = edge.get("coordinates") or []
            for start, end in zip(coords, coords[1:]):
                span_m = _haversine_m(float(start[0]), float(start[1]), float(end[0]), float(end[1]))
                steps = max(1, math.ceil(span_m / 250.0))
                for step in range(steps):
                    fraction = step / steps
                    samples.append([
                        float(start[0]) + (float(end[0]) - float(start[0])) * fraction,
                        float(start[1]) + (float(end[1]) - float(start[1])) * fraction,
                    ])
            if len(coords) >= 2:
                samples.append([float(coords[-1][0]), float(coords[-1][1])])
            spans.append((edge_id, start_idx, len(samples)))

        tree, probs = risk_index
        if samples:
            distances, indices = tree.query(np.asarray(samples), distance_upper_bound=0.008)
            sample_known = np.isfinite(distances) & (indices < len(probs))
        else:
            distances = np.array([], dtype=np.float64)
            indices = np.array([], dtype=np.int64)
            sample_known = np.array([], dtype=bool)

        for edge_id, start_idx, end_idx in spans:
            edge_mask = sample_known[start_idx:end_idx]
            values = probs[indices[start_idx:end_idx][edge_mask].astype(int)]
            all_known = len(edge_mask) > 0 and bool(np.all(edge_mask))
            if all_known:
                risks[edge_id] = float(np.mean(values))
                known_edges[edge_id] = True
            else:
                risks[edge_id] = max(
                    float(np.mean(values)) if len(values) else 0.0,
                    settings.UNKNOWN_RISK_DEFAULT,
                )
                known_edges[edge_id] = False
        return risks, known_edges

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _edge_cost_m(self, length_m: float, risk: float, vehicle_type: str) -> float:
        """
        Documented flood-aware cost (metres-equivalent):

            edge_cost = length_m + length_m * RISK_PENALTY_FACTOR * risk ** RISK_PENALTY_EXPONENT

        Critical edges get an extra multiplier for non-rescue vehicles.
        """
        penalty = length_m * settings.RISK_PENALTY_FACTOR * (max(0.0, risk) ** settings.RISK_PENALTY_EXPONENT)
        cost = length_m + penalty
        if risk >= settings.DISRUPTION_THRESHOLD_CRITICAL and vehicle_type != "rescue":
            cost *= 8.0
        return cost

    def _paths_substantially_same(self, a: List[str], b: List[str]) -> bool:
        if a == b:
            return True
        if not a or not b:
            return False
        sa, sb = set(a), set(b)
        if len(sa) <= 2 and sa == sb:
            return True
        overlap = len(sa & sb) / max(len(sa | sb), 1)
        return overlap >= 0.85 and abs(len(a) - len(b)) <= 2

    def _find_disjoint_alternative(
        self,
        graph: nx.DiGraph,
        s_node: str,
        d_node: str,
        primary_path: List[str],
    ) -> Optional[List[str]]:
        if len(primary_path) < 2:
            return None

        g = graph.copy()
        for i in range(len(primary_path) - 1):
            u, v = primary_path[i], primary_path[i + 1]
            if g.has_edge(u, v):
                g.remove_edge(u, v)
        try:
            alt = nx.shortest_path(g, source=s_node, target=d_node, weight="weight")
            if not self._paths_substantially_same(primary_path, alt):
                return alt
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        # Restore a few candidate edges on the single working copy; avoid copying
        # the full city graph for every alternative-path attempt.
        edge_candidates = []
        for i in range(len(primary_path) - 1):
            u, v = primary_path[i], primary_path[i + 1]
            key = f"{min(u, v)}--{max(u, v)}"
            edge_candidates.append((self.betweenness_cache.get(key, 0.0), u, v))
        edge_candidates.sort(reverse=True)

        for _, u, v in edge_candidates[:8]:
            edge_data = graph.get_edge_data(u, v)
            if edge_data and not g.has_edge(u, v):
                g.add_edge(u, v, **edge_data)
            try:
                alt = nx.shortest_path(g, source=s_node, target=d_node, weight="weight")
                if not self._paths_substantially_same(primary_path, alt):
                    return alt
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
        return None

    def _validate_path_geometry(self, coords: List[List[float]]) -> None:
        if not coords or len(coords) < 2:
            raise ValueError("Route geometry is empty or incomplete.")
        for lat, lon in coords:
            if not self._in_bounds(lat, lon):
                raise ValueError("Route geometry leaves the supported Greater Mumbai extent.")

    def calculate_safe_route(
        self,
        source: Optional[str] = None,
        destination: Optional[str] = None,
        vehicle_type: str = "car",
        flood_service=None,
        source_coords: Optional[List[float]] = None,
        dest_coords: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Flood-aware weighted shortest and distance-only routes on the OSM graph.

        Never returns a fabricated straight-line fallback.
        """
        if not self.network_available:
            raise ValueError(
                "Road network data is missing. Build the OSM cache with "
                "`python scripts/build_mumbai_road_network.py` and restart the API."
            )

        s_node, _, s_snap = self.resolve_node(source, source_coords, role="origin")
        d_node, _, d_snap = self.resolve_node(destination, dest_coords, role="destination")
        s_coords = [self.nodes[s_node]["lat"], self.nodes[s_node]["lon"]]
        d_coords = [self.nodes[d_node]["lat"], self.nodes[d_node]["lon"]]
        snap_warnings: List[str] = []
        if s_snap > 1:
            snap_warnings.append(f"Origin snapped {s_snap:.0f} m to nearest road node.")
        if d_snap > 1:
            snap_warnings.append(f"Destination snapped {d_snap:.0f} m to nearest road node.")

        if s_node == d_node:
            raise ValueError(
                "Origin and destination snap to the same mapped road node. Choose distinct locations "
                "to avoid returning an unmapped access connector."
            )

        if not nx.has_path(self.graph, s_node, d_node):
            raise ValueError(
                "No connected road path between the selected origin and destination "
                "on the mapped Mumbai network (disconnected components)."
            )

        v_type = (vehicle_type or "car").lower()
        risk_index = self._build_flood_risk_index(flood_service)

        # Precompute edge risks once (spatial index — do not call get_location_risk per edge)
        edge_risks: Dict[str, float] = {}
        edge_risk_known: Dict[str, bool] = {}
        graph_edges = list(self.graph.edges(data=True))
        edge_risks, edge_risk_known = self._sample_edge_flood_risks(
            [data for _, _, data in graph_edges],
            risk_index,
        )

        for u, v, data in graph_edges:
            eid = data.get("edge_id") or f"{u}->{v}"
            if eid not in edge_risks:
                edge_risks[eid] = settings.UNKNOWN_RISK_DEFAULT
                edge_risk_known[eid] = False

        def safe_edge_cost(u: str, v: str, data: Dict[str, Any]) -> float:
            eid = data.get("edge_id") or f"{u}->{v}"
            length_m = float(data.get("length_m") or data.get("weight") or 1.0)
            return self._edge_cost_m(length_m, edge_risks[eid], v_type)

        try:
            safer_nodes = nx.shortest_path(
                self.graph,
                source=s_node,
                target=d_node,
                weight=safe_edge_cost,
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
            raise ValueError(
                "No viable flood-aware route between the selected points on the road network."
            ) from exc

        try:
            shortest_nodes = nx.shortest_path(self.graph, source=s_node, target=d_node, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            shortest_nodes = list(safer_nodes)

        safer_m = self._extract_path_metrics(safer_nodes, edge_risks, edge_risk_known)
        short_m = self._extract_path_metrics(shortest_nodes, edge_risks, edge_risk_known)

        # Cap extreme detours: if safer is >> shortest, fall back toward shortest for display honesty
        if (
            short_m["distanceKm"] > 0
            and safer_m["distanceKm"] > short_m["distanceKm"] * settings.MAX_SAFE_DETOUR_RATIO
            and short_m["riskExposureScore"] <= safer_m["riskExposureScore"] + 0.05
        ):
            safer_nodes, safer_m = shortest_nodes, short_m

        # Alternative = shortest if distinct, else edge-disjoint attempt
        alt_nodes: Optional[List[str]] = None
        if not self._paths_substantially_same(safer_nodes, shortest_nodes):
            alt_nodes = shortest_nodes
        else:
            alt_nodes = self._find_disjoint_alternative(self.graph, s_node, d_node, safer_nodes)

        higher_m = self._extract_path_metrics(alt_nodes, edge_risks, edge_risk_known) if alt_nodes else None

        # Ensure "safer" label has lower or equal risk exposure
        if higher_m is not None and higher_m["riskExposureScore"] + 1e-6 < safer_m["riskExposureScore"]:
            safer_nodes, alt_nodes = alt_nodes, safer_nodes
            safer_m, higher_m = higher_m, safer_m

        safer_coords = safer_m["coords"]
        self._validate_path_geometry(safer_coords)

        higher_coords = None
        if higher_m is not None and alt_nodes is not None:
            higher_coords = higher_m["coords"]
            self._validate_path_geometry(higher_coords)

        high_on_safer = safer_m["highRiskEdges"]
        high_on_alt = higher_m["highRiskEdges"] if higher_m else 0
        avoided = max(0, high_on_alt - high_on_safer)

        safer_option = self._build_route_option(
            route_id="REC-SAFE-PATH",
            name="Lower-cost flood-aware route",
            route_type="RECOMMENDED_SAFE",
            metrics=safer_m,
            path_coords=safer_coords,
            nodes=safer_nodes,
            flood_points_avoided=avoided,
            notes=(
                f"Minimises edge_cost = length_m + length_m × {settings.RISK_PENALTY_FACTOR} × "
                f"risk^{settings.RISK_PENALTY_EXPONENT} on OSM road segments. "
                f"Unknown risk uses conservative default {settings.UNKNOWN_RISK_DEFAULT} "
                f"(not treated as safe). Length-weighted modeled susceptibility: "
                f"{safer_m['riskExposureScore']:.3f}; risk data is not a live road condition."
            ),
        )

        alternative_option = None
        unavailable_reason = None
        if higher_m is not None and alt_nodes is not None and higher_coords is not None:
            tradeoff = (
                f"Compared with the safer route: "
                f"Δdistance {higher_m['distanceKm'] - safer_m['distanceKm']:+.1f} km, "
                f"Δtime {higher_m['etaMinutes'] - safer_m['etaMinutes']:+.0f} min, "
                f"Δrisk exposure {higher_m['riskExposureScore'] - safer_m['riskExposureScore']:+.3f}."
            )
            alternative_option = self._build_route_option(
                route_id="ALT-SHORTEST",
                name="Shortest road-network route",
                route_type="FASTER_ALTERNATIVE",
                metrics=higher_m,
                path_coords=higher_coords,
                nodes=alt_nodes,
                flood_points_avoided=0,
                notes="Minimum OSM road-network distance (no flood penalty). " + tradeoff,
            )
        else:
            unavailable_reason = (
                "Only one feasible corridor exists between these endpoints on the mapped "
                "road network; a meaningfully different alternative path is not available."
            )

        hazards = self._path_derived_hazards(safer_nodes, alt_nodes, edge_risks, edge_risk_known)

        src_name = self.nodes[s_node].get("name") or source or "Origin"
        dst_name = self.nodes[d_node].get("name") or destination or "Destination"
        if source and not source_coords:
            src_name = MUMBAI_LANDMARKS.get(self._match_landmark_id(source), {}).get("name", src_name)
        if destination and not dest_coords:
            dst_name = MUMBAI_LANDMARKS.get(self._match_landmark_id(destination), {}).get("name", dst_name)

        risk_source = (
            "Mumbai XGBoost scenario susceptibility (not live flood observations)"
            if risk_index is not None
            else "Unavailable; road-edge risk is unknown"
        )
        warnings = list(snap_warnings)
        if risk_index is not None:
            warnings.append(
                "Flood risk is a scenario-based susceptibility estimate, not live water depth, "
                "observed flooding, or current road-closure data."
            )
        else:
            warnings.append(
                "Flood-risk data is unavailable. Unknown road edges are conservatively penalized; "
                "no route is confirmed safe."
            )

        return {
            "source": src_name,
            "destination": dst_name,
            "sourceCoords": s_coords,
            "destCoords": d_coords,
            "recommendedRoute": safer_option,
            "alternativeRoute": alternative_option,
            "alternativeUnavailableReason": unavailable_reason,
            "hazards": hazards,
            "networkProvenance": (
                f"OpenStreetMap drive network ({self.network_meta.get('node_count', len(self.nodes))} nodes, "
                f"{self.network_meta.get('edge_count', len(self.edge_definitions))} directed edges). "
                f"License: {self.network_meta.get('license', 'ODbL')}. "
                "Routes follow mapped highway geometry only — no synthetic bay/sea chords."
            ),
            "riskSource": risk_source,
            "riskIsSimulated": risk_index is not None,
            "isSimulated": False,
            "geometrySource": self.geometry_source,
            "warnings": warnings,
        }

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
        unknown = metrics.get("unknownRiskEdges", 0)
        if high and risk_score >= settings.DISRUPTION_THRESHOLD_CRITICAL:
            status, exposure = "UNSAFE", "High"
        else:
            # Susceptibility estimates and unknown edges do not prove a road is safe.
            status, exposure = "CAUTION", "Medium"

        safety = max(0, min(100, int(round(100 - risk_score * 100))))
        if unknown:
            notes = notes + f" {unknown} edge(s) have unknown flood risk; they are not confirmed safe."

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
            "unknownRiskEdgeCount": unknown,
            "pathCoordinates": path_coords,
            "nodesVisited": nodes,
            "notes": notes,
            "isSimulated": False,
            "geometrySource": self.geometry_source,
        }

    def _path_derived_hazards(
        self,
        safer_nodes: List[str],
        alt_nodes: Optional[List[str]],
        edge_risks: Dict[str, float],
        edge_risk_known: Dict[str, bool],
    ) -> List[Dict[str, Any]]:
        hazards: List[Dict[str, Any]] = []
        seen = set()
        for path in (safer_nodes, alt_nodes or []):
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                data = self.graph.get_edge_data(u, v) or {}
                eid = data.get("edge_id")
                if not eid or eid in seen:
                    continue
                risk = edge_risks.get(eid, 0.0)
                if not edge_risk_known.get(eid, False):
                    continue
                if risk < settings.DISRUPTION_THRESHOLD_HIGH:
                    continue
                seen.add(eid)
                coords = data.get("coordinates") or []
                if len(coords) < 2:
                    continue
                mid = coords[len(coords) // 2]
                hazards.append({
                    "id": f"HAZ-{eid}",
                    "title": f"Elevated susceptibility: {data.get('name', eid)}",
                    "location": data.get("locality", "Greater Mumbai"),
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
        edge_risk_known: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        coords: List[List[float]] = []
        tot_dist = 0.0
        tot_time = 0.0
        high_risk = 0
        unknown_risk = 0
        risk_length = 0.0
        known = edge_risk_known or {}

        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i + 1]
            data = self.graph.get_edge_data(u, v)
            if not data:
                raise ValueError(f"Missing road edge between {u} and {v} — refusing fabricated connector.")
            length_m = float(data.get("length_m") or 0.0)
            speed = max(10.0, float(data.get("free_flow_speed_kmh") or 35.0))
            edge_distance_km = length_m / 1000.0
            tot_dist += edge_distance_km
            tot_time += edge_distance_km / speed * 60.0
            eid = data.get("edge_id") or f"{u}->{v}"
            risk = edge_risks.get(eid, settings.UNKNOWN_RISK_DEFAULT)
            risk_length += risk * edge_distance_km
            if known.get(eid, False) and risk >= settings.DISRUPTION_THRESHOLD_HIGH:
                high_risk += 1
            if not known.get(eid, False):
                unknown_risk += 1
            edge_coords = [list(c) for c in (data.get("coordinates") or [])]
            if len(edge_coords) < 2:
                raise ValueError(f"Missing OSM geometry on road edge {eid}.")
            # Long non-bridge gaps indicate bad geometry
            for j in range(len(edge_coords) - 1):
                gap = _haversine_m(
                    edge_coords[j][0], edge_coords[j][1],
                    edge_coords[j + 1][0], edge_coords[j + 1][1],
                )
                if gap > 2500 and not data.get("is_bridge"):
                    raise ValueError(
                        f"Invalid road geometry on {eid}: {gap:.0f} m span without bridge tag."
                    )
            for c in edge_coords:
                if not coords or coords[-1] != c:
                    coords.append(list(c))

        if len(coords) < 2:
            raise ValueError("Route contains no mapped OSM road geometry.")

        exposure = (risk_length / tot_dist) if tot_dist > 0 else settings.UNKNOWN_RISK_DEFAULT
        return {
            "coords": coords,
            "distanceKm": tot_dist,
            "etaMinutes": tot_time,
            "highRiskEdges": high_risk,
            "unknownRiskEdges": unknown_risk,
            "riskExposureScore": exposure,
        }

    def _match_landmark_id(self, query: str) -> str:
        def normalize(value: str) -> str:
            return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())

        q = normalize(query)
        if q:
            for lid, data in MUMBAI_LANDMARKS.items():
                if q in {
                    normalize(lid.replace("MUM-NODE-", "")),
                    normalize(data["name"]),
                    normalize(data["locality"]),
                }:
                    return lid

        aliases = {
            "airport": "MUM-NODE-AIRPORT",
            "csmia": "MUM-NODE-AIRPORT",
            "cst": "MUM-NODE-CST",
            "csmt": "MUM-NODE-CST",
            "csmt fort": "MUM-NODE-CST",
            "fort": "MUM-NODE-CST",
            "south mumbai": "MUM-NODE-CST",
            "marine drive": "MUM-NODE-CHURCHGATE",
            "dadar": "MUM-NODE-DADAR",
            "dadar tt": "MUM-NODE-DADAR",
            "dadar tt circle": "MUM-NODE-DADAR",
            "bandra west": "MUM-NODE-BANDRA",
            "bandra western spine": "MUM-NODE-BANDRA",
            "linking road": "MUM-NODE-BANDRA",
            "bkc": "MUM-NODE-BKC",
            "bandra kurla": "MUM-NODE-BKC",
            "kurla": "MUM-NODE-KURLA",
            "mithi": "MUM-NODE-KURLA",
            "sion": "MUM-NODE-SION",
            "gandhi market": "MUM-NODE-SION",
            "andheri": "MUM-NODE-ANDHERI",
            "andheri subway": "MUM-NODE-ANDHERI-SUBWAY",
            "khar": "MUM-NODE-KHAR-SUBWAY",
            "santacruz": "MUM-NODE-KHAR-SUBWAY",
            "hindmata": "MUM-NODE-HINDMATA",
            "parel": "MUM-NODE-HINDMATA",
            "worli": "MUM-NODE-SEALINK",
            "sea link": "MUM-NODE-SEALINK",
            "lower parel": "MUM-NODE-LOWERPAREL",
            "wadala": "MUM-NODE-WADALA",
            "byculla": "MUM-NODE-BYCULLA",
            "mahim": "MUM-NODE-MAHIM",
            "powai": "MUM-NODE-POWAI",
            "jvlr": "MUM-NODE-POWAI",
            "ghatkopar": "MUM-NODE-GHATKOPAR",
            "chembur": "MUM-NODE-CHEMBUR",
            "mankhurd": "MUM-NODE-MANKHURD",
            "malad": "MUM-NODE-MALAD",
            "borivali": "MUM-NODE-BORIVALI",
            "mulund": "MUM-NODE-MULUND",
        }
        if q in aliases:
            return aliases[q]
        raise ValueError(
            f"Unsupported Mumbai {query!r} location. Use a supported named landmark "
            "or provide [latitude, longitude] coordinates."
        )

    def get_preset_routes(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "PRESET-MUM-AIRPORT",
                "label": "CSMT Fort → Mumbai Airport CSMIA (OSM road network)",
                "source": "CSMT Fort",
                "destination": "CSMIA International Airport",
                "description": "Road-following route on mapped Mumbai highways between South Mumbai and CSMIA.",
            },
            {
                "id": "PRESET-MUM-BKC",
                "label": "Dadar TT Circle → Bandra-Kurla Complex (BKC)",
                "source": "Dadar TT Circle",
                "destination": "Bandra-Kurla Complex (BKC)",
                "description": "Flood-aware arterial routing avoiding invented Mahim Bay shortcuts.",
            },
            {
                "id": "PRESET-MUM-BORIVALI",
                "label": "Borivali → Bandra West (Western Express Highway Corridor)",
                "source": "Borivali",
                "destination": "Bandra Western Spine",
                "description": "North–south suburban corridor on the mapped WEH / connector network.",
            },
            {
                "id": "PRESET-MUM-KURLA",
                "label": "Sion Circle → Kurla Mithi Basin",
                "source": "Sion Circle",
                "destination": "Kurla Mithi River Corridor",
                "description": "Cross-catchment route on mapped Eastern Express / connector roads.",
            },
            {
                "id": "PRESET-MUM-MAHIM",
                "label": "Dadar → Bandra West (must not cross Mahim Bay as a chord)",
                "source": "Dadar TT Circle",
                "destination": "Bandra Western Spine",
                "description": "Regression preset: geometry must follow causeway / inland roads, not a bay chord.",
            },
        ]
