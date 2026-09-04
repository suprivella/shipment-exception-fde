import csv
import json
import os
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from environment automatically

MODEL = "claude-sonnet-4-5"  # fast + strong enough for structured reasoning tasks

SYSTEM_PROMPT = """You are an operations assistant for a logistics company. \
You will be given structured data about a shipment that has been flagged as at-risk \
by an automated detection system. Your job is to:

1. Explain in plain English why this shipment is at risk (1-2 sentences, no jargon)
2. Recommend ONE specific action the ops team should take right now
3. Draft a short, professional customer-facing message (2-3 sentences) that proactively \
   informs the customer, without over-promising or admitting fault unnecessarily

Respond ONLY with valid JSON in this exact format, no markdown fences, no preamble:
{
  "explanation": "...",
  "recommended_action": "...",
  "customer_message": "..."
}"""


def build_user_prompt(shipment):
    return f"""Shipment ID: {shipment['shipment_id']}
Carrier: {shipment['carrier']}
Route: {shipment['route']}
Customer tier: {shipment['customer_tier']}
Order value: ${shipment['order_value_usd']}
Current status: {shipment['current_status']}
Hours since last GPS ping: {shipment['gps_age_hours']}
Hours ETA has slipped: {shipment['eta_slip_hours']}
Risk score: {shipment['risk_score']}
Business impact score: {shipment['impact_score']}
Detected risk signals: {shipment['reasons']}"""


def get_ai_recommendation(shipment):
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(shipment)}]
    )
    raw_text = response.content[0].text.strip()

    # Defensive parsing in case the model wraps output in markdown fences
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "explanation": "AI response could not be parsed.",
            "recommended_action": "Manual review needed.",
            "customer_message": "",
        }


def main():
    with open("flagged_shipments.csv") as f:
        flagged = list(csv.DictReader(f))

    # Process the top 10 highest-impact shipments as a demo
    # (remove this slice to run on all flagged shipments)
    top_shipments = flagged[:10]

    results = []
    for i, shipment in enumerate(top_shipments):
        print(f"Processing {i+1}/{len(top_shipments)}: {shipment['shipment_id']}...")
        ai_output = get_ai_recommendation(shipment)
        results.append({
            "shipment_id": shipment["shipment_id"],
            "impact_score": shipment["impact_score"],
            "reasons": shipment["reasons"],
            "explanation": ai_output["explanation"],
            "recommended_action": ai_output["recommended_action"],
            "customer_message": ai_output["customer_message"],
        })

    with open("ai_recommendations.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. Generated recommendations for {len(results)} shipments.")
    print("See ai_recommendations.csv")

    # Print one example to console
    if results:
        print("\n--- Example output ---")
        print(json.dumps(results[0], indent=2))


if __name__ == "__main__":
    main()
