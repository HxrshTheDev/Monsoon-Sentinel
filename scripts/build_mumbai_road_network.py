#!/usr/bin/env python3
"""
Build a cached Greater Mumbai drive road network from OpenStreetMap (Overpass).

Output (reproducible cache consumed by RoadNetworkService):
  data/processed/roads/mumbai_drive_network.json.gz

Coverage: settings BOUNDS (default 18.89–19.30 N, 72.75–73.02 E).
Highway classes: motorway/trunk/primary/secondary/tertiary (+ links),
unclassified, residential, living_street.

Requires network access on first build. Subsequent routing uses the local cache only.
"""

from __future__ import annotations

import gzip
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Repo root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config import settings  # noqa: E402

OUT_DIR = os.path.join(ROOT, "data", "processed", "roads")
OUT_PATH = os.path.join(OUT_DIR, "mumbai_drive_network.json.gz")
META_PATH = os.path.join(OUT_DIR, "mumbai_drive_network.meta.json")

OVERPASS_URLS = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

_HTTP_HEADERS = {
    "User-Agent": "CityPulse-MonsoonSentinel/1.0 (research; mumbai flood routing)",
    "Accept": "application/json",
}

# Default: arterial + collector network (reliable Overpass size, real OSM geometry).
# Use --full to include residential/unclassified for denser local access.
HIGHWAY_REGEX_ARTERIAL = (
    "motorway|trunk|primary|secondary|tertiary|"
    "motorway_link|trunk_link|primary_link|secondary_link|tertiary_link"
)
HIGHWAY_REGEX_FULL = (
    HIGHWAY_REGEX_ARTERIAL
    + "|unclassified|residential|living_street"
)
HIGHWAY_REGEX = HIGHWAY_REGEX_ARTERIAL

# Approximate metres per degree at Mumbai latitude (for length fallback)
_M_PER_DEG_LAT = 110_540.0
_M_PER_DEG_LON = 102_100.0  # ~cos(19°) * 111320


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _polyline_length_m(coords_lonlat: List[List[float]]) -> float:
    total = 0.0
    for i in range(len(coords_lonlat) - 1):
        lon1, lat1 = coords_lonlat[i]
        lon2, lat2 = coords_lonlat[i + 1]
        total += _haversine_m(lat1, lon1, lat2, lon2)
    return total


def _build_overpass_query(south: float, west: float, north: float, east: float) -> str:
    return f"""
[out:json][timeout:300];
(
  way["highway"~"^({HIGHWAY_REGEX})$"]({south},{west},{north},{east});
);
out body;
>;
out skel qt;
""".strip()


def fetch_overpass(query: str) -> Dict[str, Any]:
    last_err: Optional[Exception] = None
    for url in OVERPASS_URLS:
        for attempt in range(3):
            try:
                print(f"[OVERPASS] POST {url} (attempt {attempt + 1})", flush=True)
                with httpx.Client(
                    timeout=httpx.Timeout(300.0, connect=30.0),
                    headers=_HTTP_HEADERS,
                ) as client:
                    resp = client.post(url, data={"data": query})
                    resp.raise_for_status()
                    payload = resp.json()
                    if "elements" not in payload:
                        raise RuntimeError(f"Unexpected Overpass payload keys: {list(payload.keys())}")
                    print(
                        f"[OVERPASS] Received {len(payload['elements'])} elements from {url}",
                        flush=True,
                    )
                    return payload
            except Exception as exc:  # noqa: BLE001 — retry across mirrors
                last_err = exc
                print(f"[OVERPASS] Failed: {exc}", flush=True)
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"All Overpass mirrors failed. Last error: {last_err}")


def _iter_tiles(
    south: float, west: float, north: float, east: float, rows: int = 2, cols: int = 2
):
    dlat = (north - south) / rows
    dlon = (east - west) / cols
    for r in range(rows):
        for c in range(cols):
            yield (
                south + r * dlat,
                west + c * dlon,
                south + (r + 1) * dlat,
                west + (c + 1) * dlon,
            )


def fetch_overpass_tiled(south: float, west: float, north: float, east: float) -> Dict[str, Any]:
    """Fetch OSM ways in tiles and merge (more reliable than one huge query)."""
    merged: Dict[Tuple[Any, Any], Dict[str, Any]] = {}
    for i, (s, w, n, e) in enumerate(_iter_tiles(south, west, north, east, rows=2, cols=2), start=1):
        print(f"[OVERPASS] Tile {i}/4 bbox=({s:.3f},{w:.3f})–({n:.3f},{e:.3f})", flush=True)
        payload = fetch_overpass(_build_overpass_query(s, w, n, e))
        for el in payload.get("elements", []):
            key = (el.get("type"), el.get("id"))
            merged[key] = el
        time.sleep(1.0)
    return {"elements": list(merged.values())}


def parse_osm_to_network(payload: Dict[str, Any]) -> Dict[str, Any]:
    nodes_raw: Dict[int, Tuple[float, float]] = {}
    ways: List[Dict[str, Any]] = []

    for el in payload["elements"]:
        if el.get("type") == "node":
            nodes_raw[int(el["id"])] = (float(el["lat"]), float(el["lon"]))
        elif el.get("type") == "way":
            ways.append(el)

    nodes_out: Dict[str, Dict[str, float]] = {}
    edges_out: List[Dict[str, Any]] = []
    edge_seq = 0

    for way in ways:
        tags = way.get("tags") or {}
        highway = tags.get("highway", "road")
        name = tags.get("name") or tags.get("ref") or f"OSM way {way['id']}"
        oneway_tag = str(tags.get("oneway", "no")).lower()
        oneway = oneway_tag in ("yes", "true", "1", "-1")
        reverse_oneway = oneway_tag == "-1"
        is_bridge = str(tags.get("bridge", "no")).lower() in ("yes", "true", "1", "viaduct", "cantilever", "movable")
        is_tunnel = str(tags.get("tunnel", "no")).lower() in ("yes", "true", "1", "building_passage")
        maxspeed = tags.get("maxspeed")
        try:
            speed_kmh = float(str(maxspeed).split()[0]) if maxspeed else None
        except ValueError:
            speed_kmh = None
        if speed_kmh is None:
            speed_defaults = {
                "motorway": 80.0,
                "trunk": 60.0,
                "primary": 50.0,
                "secondary": 45.0,
                "tertiary": 40.0,
                "residential": 30.0,
                "living_street": 20.0,
                "unclassified": 35.0,
            }
            base = highway.replace("_link", "")
            speed_kmh = speed_defaults.get(base, 35.0)

        nds = [int(n) for n in way.get("nodes") or []]
        if len(nds) < 2:
            continue

        # Split way at each consecutive node pair so graph connectivity matches OSM topology.
        for i in range(len(nds) - 1):
            u_osm, v_osm = nds[i], nds[i + 1]
            if u_osm not in nodes_raw or v_osm not in nodes_raw:
                continue
            u_lat, u_lon = nodes_raw[u_osm]
            v_lat, v_lon = nodes_raw[v_osm]
            u_id, v_id = f"OSM-{u_osm}", f"OSM-{v_osm}"
            nodes_out[u_id] = {"lat": u_lat, "lon": u_lon}
            nodes_out[v_id] = {"lat": v_lat, "lon": v_lon}

            # GeoJSON order [lon, lat] for stored geometry
            geom = [[u_lon, u_lat], [v_lon, v_lat]]
            length_m = _polyline_length_m(geom)
            if length_m < 0.5:
                continue

            edge_seq += 1
            eid = f"OSM-WAY-{way['id']}-{i}"
            edge = {
                "edge_id": eid,
                "osm_way_id": int(way["id"]),
                "u": u_id,
                "v": v_id,
                "name": name,
                "highway": highway,
                "length_m": round(length_m, 2),
                "length_km": round(length_m / 1000.0, 5),
                "free_flow_speed_kmh": float(speed_kmh),
                "oneway": oneway,
                "is_bridge": is_bridge,
                "is_tunnel": is_tunnel,
                "coordinates_lonlat": geom,
                "geometrySource": "openstreetmap_overpass",
                "source": "OpenStreetMap",
            }

            if reverse_oneway:
                edge["u"], edge["v"] = v_id, u_id
                edge["coordinates_lonlat"] = list(reversed(geom))

            edges_out.append(edge)

            # Bidirectional unless oneway
            if not oneway:
                edge_seq += 1
                rev = dict(edge)
                rev["edge_id"] = f"{eid}-REV"
                rev["u"], rev["v"] = edge["v"], edge["u"]
                rev["coordinates_lonlat"] = list(reversed(edge["coordinates_lonlat"]))
                edges_out.append(rev)

    return {
        "meta": {
            "built_at": datetime.now(timezone.utc).isoformat(),
            "source": "OpenStreetMap via Overpass API",
            "license": "ODbL (OpenStreetMap contributors)",
            "bbox": {
                "min_lat": settings.BOUNDS_MIN_LAT,
                "max_lat": settings.BOUNDS_MAX_LAT,
                "min_lon": settings.BOUNDS_MIN_LON,
                "max_lon": settings.BOUNDS_MAX_LON,
            },
            "crs_geographic": "EPSG:4326",
            "crs_projected": settings.CRS_PROJECTED,
            "highway_filter": HIGHWAY_REGEX,
            "node_count": len(nodes_out),
            "edge_count": len(edges_out),
            "coordinate_order_stored": "[lon, lat] GeoJSON",
            "notes": (
                "Edges are consecutive OSM node pairs from tagged highway ways. "
                "No synthetic chord edges are added. Bridges/tunnels follow OSM tags."
            ),
        },
        "nodes": nodes_out,
        "edges": edges_out,
    }


def main() -> int:
    global HIGHWAY_REGEX
    import argparse

    parser = argparse.ArgumentParser(description="Build Mumbai OSM drive network cache")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include residential/unclassified (larger Overpass download)",
    )
    args = parser.parse_args()
    HIGHWAY_REGEX = HIGHWAY_REGEX_FULL if args.full else HIGHWAY_REGEX_ARTERIAL

    south = settings.BOUNDS_MIN_LAT
    west = settings.BOUNDS_MIN_LON
    north = settings.BOUNDS_MAX_LAT
    east = settings.BOUNDS_MAX_LON
    print(f"[BUILD] Mumbai road network bbox: ({south},{west})–({north},{east})", flush=True)
    print(f"[BUILD] Highway filter: {HIGHWAY_REGEX}", flush=True)

    payload = fetch_overpass_tiled(south, west, north, east)
    network = parse_osm_to_network(payload)

    if network["meta"]["edge_count"] < 100:
        print("[ERROR] Too few edges — refusing to write incomplete cache.")
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    with gzip.open(OUT_PATH, "wt", encoding="utf-8") as f:
        json.dump(network, f, separators=(",", ":"))

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(network["meta"], f, indent=2)

    size_mb = os.path.getsize(OUT_PATH) / (1024 * 1024)
    print(f"[SAVE] {OUT_PATH} ({size_mb:.1f} MB)")
    print(f"[SAVE] nodes={network['meta']['node_count']} edges={network['meta']['edge_count']}")
    print(f"[SAVE] meta -> {META_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
