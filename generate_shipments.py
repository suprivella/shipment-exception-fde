"""
Synthetic shipment data generator for the Shipment Exception Detection prototype.

Simulates realistic logistics data messiness:
- Missing/stale GPS pings
- Carrier status delays or conflicts
- ETA slippage
- Varying customer tiers and order values

Outputs:
  shipments.csv        - one row per shipment (core record)
  gps_pings.csv         - multiple GPS pings per shipment (time series)
  status_events.csv     - carrier status update events per shipment
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

NUM_SHIPMENTS = 150
NOW = datetime(2026, 9, 2, 14, 0, 0)

CARRIERS = ["FreightCo", "SwiftHaul", "TransGlobal", "RapidLine", "CargoNet"]
ORIGINS = ["Chicago, IL", "Dallas, TX", "Atlanta, GA", "Los Angeles, CA", "Newark, NJ", "Memphis, TN"]
DESTINATIONS = ["Columbus, OH", "Phoenix, AZ", "Charlotte, NC", "Seattle, WA", "Miami, FL", "Denver, CO"]
CUSTOMER_TIERS = ["Platinum", "Gold", "Standard"]
STATUS_STAGES = ["Picked Up", "In Transit", "At Hub", "Out for Delivery", "Delivered", "Delayed", "Exception"]

def random_timestamp_before(base, max_hours_ago):
    return base - timedelta(hours=random.uniform(0, max_hours_ago))

def generate_shipment(i):
    shipment_id = f"SHP-{10000 + i}"
    carrier = random.choice(CARRIERS)
    origin = random.choice(ORIGINS)
    destination = random.choice(DESTINATIONS)
    customer_tier = random.choices(CUSTOMER_TIERS, weights=[0.15, 0.35, 0.5])[0]
    order_value = round(random.uniform(200, 25000), 2)

    ship_date = NOW - timedelta(days=random.uniform(1, 5))
    transit_days = random.uniform(1.5, 4)
    planned_eta = ship_date + timedelta(days=transit_days)

    # Assign a scenario type to create realistic variety
    scenario = random.choices(
        ["on_time", "minor_delay", "at_risk_no_gps", "at_risk_eta_slip", "weather_delay", "exception"],
        weights=[0.40, 0.20, 0.12, 0.12, 0.08, 0.08]
    )[0]

    last_gps_hours_ago = random.uniform(0.2, 2)  # default: recent ping
    current_status = "In Transit"
    eta_slip_hours = 0
    notes = ""

    if scenario == "on_time":
        current_status = random.choice(["In Transit", "Out for Delivery", "Delivered"])
        last_gps_hours_ago = random.uniform(0.1, 1.5)

    elif scenario == "minor_delay":
        current_status = "In Transit"
        eta_slip_hours = random.uniform(1, 4)
        last_gps_hours_ago = random.uniform(0.5, 3)

    elif scenario == "at_risk_no_gps":
        current_status = "In Transit"
        last_gps_hours_ago = random.uniform(14, 36)  # stale GPS - key risk signal
        notes = "No GPS ping received in over 12 hours"

    elif scenario == "at_risk_eta_slip":
        current_status = "In Transit"
        eta_slip_hours = random.uniform(10, 30)  # significant ETA slippage
        last_gps_hours_ago = random.uniform(1, 6)
        notes = "ETA has slipped significantly from original plan"

    elif scenario == "weather_delay":
        current_status = "Delayed"
        eta_slip_hours = random.uniform(6, 20)
        last_gps_hours_ago = random.uniform(1, 5)
        notes = "Carrier reports weather-related delay on route"

    elif scenario == "exception":
        current_status = "Exception"
        eta_slip_hours = random.uniform(15, 48)
        last_gps_hours_ago = random.uniform(8, 24)
        notes = random.choice([
            "Carrier reports mechanical breakdown",
            "Shipment misrouted to wrong hub",
            "Customs hold at border crossing",
            "Damaged goods reported at last checkpoint"
        ])

    last_gps_timestamp = NOW - timedelta(hours=last_gps_hours_ago)
    current_eta = planned_eta + timedelta(hours=eta_slip_hours)

    return {
        "shipment_id": shipment_id,
        "carrier": carrier,
        "origin": origin,
        "destination": destination,
        "customer_tier": customer_tier,
        "order_value_usd": order_value,
        "ship_date": ship_date.strftime("%Y-%m-%d %H:%M"),
        "planned_eta": planned_eta.strftime("%Y-%m-%d %H:%M"),
        "current_eta": current_eta.strftime("%Y-%m-%d %H:%M"),
        "current_status": current_status,
        "last_gps_timestamp": last_gps_timestamp.strftime("%Y-%m-%d %H:%M"),
        "scenario_tag": scenario,  # kept for validation; not something a real feed would have
        "notes": notes,
    }, ship_date, last_gps_timestamp

def generate_gps_pings(shipment_id, ship_date, last_gps_timestamp, num_pings=6):
    pings = []
    span = (last_gps_timestamp - ship_date).total_seconds()
    if span <= 0:
        span = 3600
    for n in range(num_pings):
        frac = n / max(num_pings - 1, 1)
        ts = ship_date + timedelta(seconds=span * frac)
        pings.append({
            "shipment_id": shipment_id,
            "timestamp": ts.strftime("%Y-%m-%d %H:%M"),
            "lat": round(random.uniform(30.0, 45.0), 4),
            "lon": round(random.uniform(-100.0, -80.0), 4),
        })
    return pings

def generate_status_events(shipment_id, ship_date, current_status, current_eta):
    events = [{"shipment_id": shipment_id, "timestamp": ship_date.strftime("%Y-%m-%d %H:%M"), "status": "Picked Up"}]
    mid = ship_date + (current_eta - ship_date) / 2
    events.append({"shipment_id": shipment_id, "timestamp": mid.strftime("%Y-%m-%d %H:%M"), "status": "In Transit"})
    if current_status not in ("In Transit",):
        events.append({
            "shipment_id": shipment_id,
            "timestamp": (current_eta - timedelta(hours=random.uniform(1, 5))).strftime("%Y-%m-%d %H:%M"),
            "status": current_status
        })
    return events

def main():
    shipments = []
    all_pings = []
    all_events = []

    for i in range(NUM_SHIPMENTS):
        shipment, ship_date, last_gps = generate_shipment(i)
        shipments.append(shipment)
        all_pings.extend(generate_gps_pings(shipment["shipment_id"], ship_date, last_gps))
        all_events.extend(generate_status_events(
            shipment["shipment_id"], ship_date, shipment["current_status"],
            datetime.strptime(shipment["current_eta"], "%Y-%m-%d %H:%M")
        ))

    with open("/mnt/user-data/outputs/shipments.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=shipments[0].keys())
        writer.writeheader()
        writer.writerows(shipments)

    with open("/mnt/user-data/outputs/gps_pings.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_pings[0].keys())
        writer.writeheader()
        writer.writerows(all_pings)

    with open("/mnt/user-data/outputs/status_events.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_events[0].keys())
        writer.writeheader()
        writer.writerows(all_events)

    print(f"Generated {len(shipments)} shipments, {len(all_pings)} GPS pings, {len(all_events)} status events.")
    scenario_counts = {}
    for s in shipments:
        scenario_counts[s["scenario_tag"]] = scenario_counts.get(s["scenario_tag"], 0) + 1
    print("Scenario breakdown:", scenario_counts)

if __name__ == "__main__":
    main()
