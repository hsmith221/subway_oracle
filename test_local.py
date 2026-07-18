"""
Local test — runs on Mac, no Pi hardware needed.
Tests MTA feed, route calculator, and both display renders.
Saves output images to test_output/ for visual inspection.

Usage:
    pip install nyct-gtfs Pillow
    python3 test_local.py
"""

import os
import sys
from datetime import datetime

os.makedirs("test_output", exist_ok=True)

print("=== Subway Oracle — Local Test ===\n")

# --- 1. Stop ID resolution ---
print("[1/4] Resolving missing stop IDs...")
from lookup_stops import resolve_missing_stops
ok = resolve_missing_stops()
if not ok:
    print("      Some stop IDs couldn't be resolved. Feed test may be limited.\n")
else:
    print("      All stop IDs resolved.\n")

# --- 2. MTA feed ---
print("[2/4] Fetching MTA feed data...")
try:
    from mta_feed import get_arrivals
    arrivals_work = get_arrivals("to_work")
    arrivals_home = get_arrivals("to_home")
    print(f"      to_work:  {len(arrivals_work)} stops with data")
    for stop_id, times in arrivals_work.items():
        print(f"        {stop_id}: {[t.strftime('%H:%M') for t in times]}")
    print(f"      to_home:  {len(arrivals_home)} stops with data")
    for stop_id, times in arrivals_home.items():
        print(f"        {stop_id}: {[t.strftime('%H:%M') for t in times]}")
    print()
except Exception as e:
    print(f"      Feed error: {e}\n")
    print("      Continuing with mock data for display tests...\n")
    arrivals_work = {}
    arrivals_home = {}

# --- 3. Route calculator ---
print("[3/4] Calculating routes...")
try:
    from route_calculator import calculate_routes
    routes_to_work = calculate_routes("to_work")
    routes_to_home = calculate_routes("to_home")

    for direction, routes in [("to_work", routes_to_work), ("to_home", routes_to_home)]:
        print(f"      {direction}:")
        for key in ("route_a", "route_b"):
            r = routes[key]
            if r["valid"]:
                print(f"        {r['label']}: {r['total_minutes']} min, "
                      f"departs {r['departs_dt'].strftime('%H:%M')}, "
                      f"arrives {r['arrives_dt'].strftime('%H:%M')}")
            else:
                print(f"        {key}: no valid trains")
        w = routes["winner"]
        s = routes["savings_minutes"]
        print(f"        winner: {w}" + (f" (saves {s} min)" if s else ""))
    print()
except Exception as e:
    print(f"      Route calc error: {e}\n")
    print("      Using dummy route data for display renders.\n")
    from datetime import timedelta
    now = datetime.now()
    _dummy_route = lambda label: {
        "valid": True, "label": label, "total_minutes": 32,
        "departs_dt": now + timedelta(minutes=8),
        "arrives_dt": now + timedelta(minutes=40),
    }
    routes_to_work = {
        "route_a": _dummy_route("Q → R/W"),
        "route_b": _dummy_route("6"),
        "winner": "B", "savings_minutes": 7, "calculated_at": now,
    }
    routes_to_home = {
        "route_a": _dummy_route("R/W → Q"),
        "route_b": _dummy_route("6"),
        "winner": "B", "savings_minutes": 4, "calculated_at": now,
    }

# --- 4. Display renders ---
print("[4/4] Rendering display layouts...")

from assets.generate_bullets import ensure_bullets
ensure_bullets()

now = datetime.now()

try:
    import office_display
    img_office = office_display.render(routes_to_home, now)
    out = "test_output/office_display.png"
    img_office.save(out)
    print(f"      Office display → {out}  ({img_office.size[0]}x{img_office.size[1]}px)")
except Exception as e:
    print(f"      Office render error: {e}")

try:
    import home_display
    img_home = home_display.render(routes_to_work, now)
    out = "test_output/home_display.png"
    img_home.save(out)
    print(f"      Home display   → {out}  ({img_home.size[0]}x{img_home.size[1]}px)")
except Exception as e:
    print(f"      Home render error: {e}")

print("\nDone. Open test_output/ to inspect the layouts.")
