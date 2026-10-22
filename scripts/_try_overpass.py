#!/usr/bin/env python3
"""Quick Overpass probe for Mumbai arterial highways."""
from urllib.parse import quote

import httpx

q = """[out:json][timeout:180];
(
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"](19.00,72.80,19.10,72.90);
);
out body;
>;
out skel qt;
"""
urls = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
headers = {
    "User-Agent": "CityPulse-MonsoonSentinel/1.0 (research; mumbai flood routing)",
    "Accept": "application/json",
}
for url in urls:
    try:
        print("TRY form", url, flush=True)
        with httpx.Client(timeout=httpx.Timeout(200.0, connect=25.0), headers=headers) as client:
            r = client.post(url, data={"data": q})
            print("STATUS", r.status_code, "BYTES", len(r.content), flush=True)
            if r.status_code == 200:
                j = r.json()
                print("ELEMENTS", len(j.get("elements", [])), flush=True)
                break
            print("BODY", r.text[:200], flush=True)
    except Exception as e:
        print("ERR", type(e).__name__, e, flush=True)

    try:
        print("TRY raw", url, flush=True)
        with httpx.Client(timeout=httpx.Timeout(200.0, connect=25.0), headers=headers) as client:
            r = client.post(
                url,
                content=f"data={quote(q)}".encode("utf-8"),
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
            )
            print("STATUS", r.status_code, "BYTES", len(r.content), flush=True)
            if r.status_code == 200:
                j = r.json()
                print("ELEMENTS", len(j.get("elements", [])), flush=True)
                break
    except Exception as e:
        print("ERR", type(e).__name__, e, flush=True)
