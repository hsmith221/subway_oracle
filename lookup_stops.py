"""
Downloads MTA static GTFS and resolves stop IDs by station name.
Run manually: python lookup_stops.py
Called automatically by run_office.py / run_home.py on first boot if stop IDs are missing.
"""

import os
import csv
import zipfile
import urllib.request
import io
import config

GTFS_URL = "http://web.mta.info/developers/data/nyct/subway/google_transit.zip"
CACHE_PATH = "/tmp/mta_gtfs_stops.txt"

STOP_TARGETS = [
    ("72nd St Q southbound",  "72 St",  "Q",  "S", "STOP_72ND_Q_SB"),
    ("72nd St Q northbound",  "72 St",  "Q",  "N", "STOP_72ND_Q_NB"),
    ("34th St Q northbound",  "34 St",  "Q",  "N", "STOP_34TH_Q_NB"),
    ("34th St Q southbound",  "34 St",  "Q",  "S", "STOP_34TH_Q_SB"),
    ("34th St R/W southbound","34 St",  "R",  "S", "STOP_34TH_RW_SB"),
    ("34th St R/W northbound","34 St",  "R",  "N", "STOP_34TH_RW_NB"),
    ("23rd St R/W southbound","23 St",  "R",  "S", "STOP_23RD_RW_SB"),
    ("23rd St R/W northbound","23 St",  "R",  "N", "STOP_23RD_RW_NB"),
]


def _fetch_stops_csv():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            return f.read()
    print("Downloading MTA static GTFS...")
    with urllib.request.urlopen(GTFS_URL, timeout=30) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        with z.open("stops.txt") as f:
            content = f.read().decode("utf-8")
    with open(CACHE_PATH, "w") as f:
        f.write(content)
    return content


def search_stops(name_fragment, route_hint=None):
    """Print all stops matching name_fragment, optionally filtered by route_hint in stop_id."""
    content = _fetch_stops_csv()
    reader = csv.DictReader(io.StringIO(content))
    results = []
    for row in reader:
        stop_name = row.get("stop_name", "")
        stop_id = row.get("stop_id", "")
        if name_fragment.lower() in stop_name.lower():
            if route_hint is None or route_hint.upper() in stop_id.upper():
                results.append((stop_id, stop_name))
    return results


def resolve_missing_stops():
    """
    Check config for None stop IDs and resolve them from static GTFS.
    Writes resolved values back to config module at runtime (in-memory only).
    Prints resolved IDs so you can hardcode them in config.py.
    """
    missing = [(label, name, route, direction, attr)
               for label, name, route, direction, attr in STOP_TARGETS
               if getattr(config, attr) is None]

    if not missing:
        return True

    print("Resolving missing stop IDs from MTA static GTFS...")
    content = _fetch_stops_csv()
    reader = list(csv.DictReader(io.StringIO(content)))

    resolved_all = True
    for label, name_frag, route, direction, attr in missing:
        matches = [
            row for row in reader
            if name_frag.lower() in row.get("stop_name", "").lower()
            and row.get("stop_id", "").endswith(direction)
            and route.upper() in row.get("stop_id", "").upper()
        ]
        if matches:
            stop_id = matches[0]["stop_id"]
            setattr(config, attr, stop_id)
            print(f"  {label}: {stop_id}  (add to config.py: {attr} = \"{stop_id}\")")
        else:
            # Broader search ignoring route letter in ID
            matches = [
                row for row in reader
                if name_frag.lower() in row.get("stop_name", "").lower()
                and row.get("stop_id", "").endswith(direction)
            ]
            if matches:
                stop_id = matches[0]["stop_id"]
                setattr(config, attr, stop_id)
                print(f"  {label}: {stop_id} [best guess]  (verify and add to config.py: {attr} = \"{stop_id}\")")
            else:
                print(f"  {label}: NOT FOUND — run: python lookup_stops.py search \"{name_frag}\"")
                resolved_all = False

    return resolved_all


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "search":
        fragment = sys.argv[2]
        route = sys.argv[3] if len(sys.argv) >= 4 else None
        results = search_stops(fragment, route)
        for stop_id, stop_name in results:
            print(f"  {stop_id:12s}  {stop_name}")
    else:
        print("Usage:")
        print("  python lookup_stops.py search \"72 St\"")
        print("  python lookup_stops.py search \"34 St\" R")
        print()
        resolve_missing_stops()
