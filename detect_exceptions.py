"""
Shipment Exception Detection & Scoring Engine

Reads shipments.csv + weather.csv and flags at-risk shipments using
rule-based thresholds, then ranks them by business impact.

This is the "detection layer" — deterministic, explainable rules.
The AI reasoning layer (separate script) sits on top of this to explain
*why* a shipment was flagged and *what to do* about it.
"""

import csv
from datetime import datetime

NOW = datetime(2026, 9, 2, 14, 0, 0)

# --- Thresholds (tune these based on what you'd learn from a real ops team) ---
GPS_STALE_HOURS = 12          # no ping in this long = risk signal
ETA_SLIP_HOURS = 8            # ETA has slipped this much = risk signal
RISK_STATUSES = {"Delayed", "Exception"}
CUSTOMER_TIER_WEIGHT = {"Platinum": 3, "Gold": 2, "Standard": 1}


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def parse_dt(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def evaluate_shipment(shipment, weather_by_id):
    reasons = []
    risk_score = 0

    # Signal 1: stale GPS
    last_gps = parse_dt(shipment["last_gps_timestamp"])
    gps_age_hours = (NOW - last_gps).total_seconds() / 3600
    if gps_age_hours > GPS_STALE_HOURS:
        reasons.append(f"No GPS ping in {gps_age_hours:.1f} hours")
        risk_score += min(gps_age_hours / GPS_STALE_HOURS, 3) * 10

    # Signal 2: ETA slippage
    planned_eta = parse_dt(shipment["planned_eta"])
    current_eta = parse_dt(shipment["current_eta"])
    slip_hours = (current_eta - planned_eta).total_seconds() / 3600
    if slip_hours > ETA_SLIP_HOURS:
        reasons.append(f"ETA slipped {slip_hours:.1f} hours from plan")
        risk_score += min(slip_hours / ETA_SLIP_HOURS, 4) * 10

    # Signal 3: status flags
    if shipment["current_status"] in RISK_STATUSES:
        reasons.append(f"Carrier status: {shipment['current_status']}")
        risk_score += 25

    # Signal 4: severe weather on route
    weather = weather_by_id.get(shipment["shipment_id"])
    if weather and weather["is_severe"] == "True":
        reasons.append(f"Severe weather on route: {weather['weather_condition']} (severity {weather['severity_score']})")
        risk_score += float(weather["severity_score"]) * 3

    # Business impact multiplier
    tier_weight = CUSTOMER_TIER_WEIGHT.get(shipment["customer_tier"], 1)
    order_value = float(shipment["order_value_usd"])
    impact_score = risk_score * (1 + tier_weight * 0.15) * (1 + min(order_value / 25000, 1) * 0.5)

    is_flagged = len(reasons) > 0

    return {
        "shipment_id": shipment["shipment_id"],
        "carrier": shipment["carrier"],
        "route": f'{shipment["origin"]} -> {shipment["destination"]}',
        "customer_tier": shipment["customer_tier"],
        "order_value_usd": order_value,
        "current_status": shipment["current_status"],
        "gps_age_hours": round(gps_age_hours, 1),
        "eta_slip_hours": round(slip_hours, 1),
        "is_flagged": is_flagged,
        "risk_score": round(risk_score, 1),
        "impact_score": round(impact_score, 1),
        "reasons": "; ".join(reasons) if reasons else "No risk signals detected",
    }


def main():
    shipments = load_csv("shipments.csv")
    weather = load_csv("weather.csv")
    weather_by_id = {w["shipment_id"]: w for w in weather}

    results = [evaluate_shipment(s, weather_by_id) for s in shipments]
    flagged = [r for r in results if r["is_flagged"]]
    flagged.sort(key=lambda r: r["impact_score"], reverse=True)

    with open("flagged_shipments.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=flagged[0].keys())
        writer.writeheader()
        writer.writerows(flagged)

    print(f"Evaluated {len(results)} shipments.")
    print(f"Flagged {len(flagged)} as at-risk.")
    print("\nTop 5 highest-impact flagged shipments:")
    for r in flagged[:5]:
        print(f"  {r['shipment_id']} | {r['customer_tier']:9s} | impact={r['impact_score']:7.1f} | {r['reasons']}")


if __name__ == "__main__":
    main()
