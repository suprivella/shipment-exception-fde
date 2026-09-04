"""
Generates synthetic weather data correlated with shipment routes.
Ties into shipments.csv via origin/destination + date, simulating a
weather API feed a real FDE integration would pull from (NOAA, Tomorrow.io, etc).
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

CONDITIONS = ["Clear", "Rain", "Heavy Rain", "Snow", "Ice Storm", "High Wind", "Fog"]
SEVERE_CONDITIONS = {"Heavy Rain", "Snow", "Ice Storm", "High Wind"}

def load_shipments():
    with open("/mnt/user-data/outputs/shipments.csv") as f:
        return list(csv.DictReader(f))

def main():
    shipments = load_shipments()
    rows = []

    for s in shipments:
        # Weather-delayed and exception shipments get severe weather; others mostly clear
        if s["scenario_tag"] == "weather_delay":
            condition = random.choice(["Heavy Rain", "Snow", "Ice Storm", "High Wind"])
            severity_score = round(random.uniform(6.5, 9.5), 1)
        elif s["scenario_tag"] == "exception" and random.random() < 0.3:
            condition = random.choice(["Ice Storm", "High Wind"])
            severity_score = round(random.uniform(7, 9), 1)
        else:
            condition = random.choices(
                ["Clear", "Rain", "Fog"], weights=[0.75, 0.18, 0.07]
            )[0]
            severity_score = round(random.uniform(0.5, 3.5), 1) if condition != "Clear" else 0.0

        rows.append({
            "shipment_id": s["shipment_id"],
            "route": f'{s["origin"]} -> {s["destination"]}',
            "weather_condition": condition,
            "severity_score": severity_score,  # 0-10 scale, mock proprietary index
            "is_severe": condition in SEVERE_CONDITIONS,
            "checked_at": s["last_gps_timestamp"],
        })

    with open("/mnt/user-data/outputs/weather.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated weather records for {len(rows)} shipments.")
    severe = sum(1 for r in rows if r["is_severe"])
    print(f"Severe weather flagged on {severe} shipments.")

if __name__ == "__main__":
    main()
