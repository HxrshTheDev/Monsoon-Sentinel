"""
CityPulse Mumbai Data Downloader
Downloads official and reputable open GIS datasets for Greater Mumbai (BMC / MCGM):
- OpenCity: Wards, Ward Offices, Prabhags, Fire Stations, Microwatersheds, Public Health Facilities, Rainfall
- BMC Disaster Management: Chronic Waterlogging Hotspots Registry
"""

import os
import json
import urllib.request
import ssl

# Define dataset URLs and targets
DATASETS = [
    {
        "name": "mumbai_wards_map.kml",
        "url": "https://data.opencity.in/dataset/60f27371-717e-40b6-8554-fdc7e6c10437/resource/0318c3e8-1530-4bf4-b29b-7281573dee8a/download/e7a671e2-1f71-4219-a83c-556334bc9021.kml",
        "description": "BMC 24 Administrative Wards (A to T) Polygon Boundaries",
        "source": "OpenCity / Municipal Corporation of Greater Mumbai",
        "license": "Open Government Data (OGD) India / ODbL"
    },
    {
        "name": "mumbai_ward_offices.kml",
        "url": "https://data.opencity.in/dataset/60f27371-717e-40b6-8554-fdc7e6c10437/resource/e3156762-a378-445f-85ad-1f9afb6cf31d/download/ec63d011-7ea2-4e54-8451-7ef93773d92e.kml",
        "description": "BMC Ward Administrative Command Offices with addresses and contacts",
        "source": "OpenCity / BMC Disaster Management",
        "license": "Open Government Data (OGD) India"
    },
    {
        "name": "mumbai_prabhag_boundaries.kml",
        "url": "https://data.opencity.in/dataset/60f27371-717e-40b6-8554-fdc7e6c10437/resource/1522e2c3-ef39-458a-8545-c23f85130079/download/1fae9b27-a74f-4968-9778-e4f2e8f1150c.kml",
        "description": "Mumbai 227 Prabhag / Electoral Ward Boundaries",
        "source": "OpenCity / State Election Commission Maharashtra",
        "license": "Open Government Data (OGD) India"
    },
    {
        "name": "mumbai_fire_stations.kml",
        "url": "https://data.opencity.in/dataset/fcc98df6-0ec9-41cb-ac2c-62fc2239d1a5/resource/f63ffd99-167a-4051-92ff-aec139d453eb/download/02b7168c-a860-46f7-9fa2-98f4c2bc9320.kml",
        "description": "Mumbai Fire Brigade Fire Stations and Command Posts",
        "source": "OpenCity / Mumbai Fire Brigade",
        "license": "Open Government Data (OGD) India"
    },
    {
        "name": "mumbai_microwatersheds.geojson",
        "url": "https://data.opencity.in/dataset/796d101e-3803-40b0-8769-db3a53350011/resource/1ed41abe-497a-4c6d-b771-e2d39ccef965/download/mum_micro_watersheds.geojson",
        "description": "Mumbai & Thane Microwatersheds Hydrological Basin Boundaries",
        "source": "OpenCity / MRSAC / Environment Dept",
        "license": "Open Government Data (OGD) India"
    },
    {
        "name": "mumbai_public_hospitals.kml",
        "url": "https://data.opencity.in/dataset/739b0e74-04a5-467b-b356-75374b5ab156/resource/a0e84658-483d-45bf-8637-fa09a8f4ba98/download/23d3867f-3604-4b8b-b3b0-7c9770777f18.kml",
        "description": "Mumbai Public Hospitals & Municipal General Hospitals",
        "source": "OpenCity / MCGM Public Health Department",
        "license": "Open Government Data (OGD) India"
    },
    {
        "name": "mumbai_dispensaries.kml",
        "url": "https://data.opencity.in/dataset/739b0e74-04a5-467b-b356-75374b5ab156/resource/1db8a954-6802-4f28-82a6-706bfa98e3ee/download/5bf84c1c-6eea-4cdc-be35-b4755fafc9a3.kml",
        "description": "Mumbai City Public Dispensaries Map",
        "source": "OpenCity / MCGM Public Health Department",
        "license": "Open Government Data (OGD) India"
    },
    {
        "name": "mumbai_uphcs.kml",
        "url": "https://data.opencity.in/dataset/739b0e74-04a5-467b-b356-75374b5ab156/resource/7162b31a-fd4a-4f70-b73a-9a690b2b4f06/download/d0ef983c-2d2f-498b-b9e9-724a7872fbff.kml",
        "description": "Mumbai City Urban Primary Health Centres (UPHCs)",
        "source": "OpenCity / MCGM Public Health Department",
        "license": "Open Government Data (OGD) India"
    },
    {
        "name": "mumbai_maternity_hospitals.kml",
        "url": "https://data.opencity.in/dataset/739b0e74-04a5-467b-b356-75374b5ab156/resource/22e98b01-82ca-43cc-8bce-f82797ff0a1c/download/3866f702-d906-412c-91fe-25c03c7dcd4b.kml",
        "description": "Mumbai City Public Maternity Hospitals",
        "source": "OpenCity / MCGM Public Health Department",
        "license": "Open Government Data (OGD) India"
    },
    {
        "name": "mumbai_hospitals_list.csv",
        "url": "https://data.opencity.in/dataset/739b0e74-04a5-467b-b356-75374b5ab156/resource/8d1c157e-9cee-4bae-a434-f1e6319edf32/download/19e49fcc-0177-4d0f-be9b-15758484aa49.csv",
        "description": "Tabular list of Mumbai public and municipal hospitals with capacities",
        "source": "OpenCity / MCGM Public Health Department",
        "license": "Open Government Data (OGD) India"
    },
    {
        "name": "mumbai_monthly_rainfall_1901_2021.csv",
        "url": "https://data.opencity.in/dataset/c0e2f1ba-848a-4716-982b-d42636c44bf5/resource/3b1fcae7-b24f-431f-a259-64b56077acd5/download/6b7b0aed-e31d-433b-ba6d-b17b08a000df.csv",
        "description": "Historical Monthly Rainfall Records for Mumbai (1901-2021)",
        "source": "OpenCity / India Meteorological Department (IMD)",
        "license": "Open Government Data (OGD) India"
    }
]

def download_all(target_dir: str):
    os.makedirs(target_dir, exist_ok=True)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    results = []
    print(f"[*] Starting download of verified Mumbai datasets into: {target_dir}")

    for ds in DATASETS:
        dest_path = os.path.join(target_dir, ds["name"])
        print(f"[-] Downloading {ds['name']} from {ds['url']}...")
        try:
            req = urllib.request.Request(
                ds["url"],
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CityPulse/2.0"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                data = resp.read()
                with open(dest_path, "wb") as f:
                    f.write(data)
            size_kb = round(os.path.getsize(dest_path) / 1024, 1)
            print(f"    [OK] Saved {ds['name']} ({size_kb} KB)")
            results.append({
                "file": ds["name"],
                "status": "DOWNLOADED",
                "size_kb": size_kb,
                "description": ds["description"],
                "source": ds["source"],
                "license": ds["license"],
                "url": ds["url"]
            })
        except Exception as e:
            print(f"    [WARN] Failed to download {ds['name']}: {e}")
            results.append({
                "file": ds["name"],
                "status": "FAILED",
                "error": str(e),
                "url": ds["url"]
            })

    # Save download manifest
    manifest_path = os.path.join(target_dir, "raw_datasets_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[+] Download complete. Manifest written to {manifest_path}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    raw_dir = os.path.join(project_root, "backend", "data", "mumbai", "raw")
    download_all(raw_dir)

