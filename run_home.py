#!/usr/bin/env python3
import time
from datetime import datetime
import config
from lookup_stops import resolve_missing_stops
from route_calculator import calculate_routes
import home_display

def main():
    if not resolve_missing_stops():
        print("WARNING: Some stop IDs could not be resolved. Route data may be incomplete.")
        print("Run: python lookup_stops.py search \"<station name>\" to find IDs manually.")

    print("Subway Oracle — Home Display (→ work)")
    while True:
        try:
            routes = calculate_routes("to_work")
            updated_at = datetime.now()
            home_display.show(routes, updated_at)
            winner = routes["winner"]
            savings = routes["savings_minutes"]
            if winner:
                label = routes[f"route_{winner.lower()}"]["label"]
                print(f"[{updated_at.strftime('%H:%M')}] Winner: {label}" +
                      (f" (saves {savings} min)" if savings else ""))
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(config.REFRESH_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
