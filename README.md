# Shipment Exception Detection & Rerouting Assistant

**A prototype built to explore how forward-deployed / solutions engineering work could accelerate logistics operations — built as a self-directed case study, not an assigned project.**

<img width="1465" height="797" alt="Screenshot 2026-09-04 at 15 20 36" src="https://github.com/user-attachments/assets/c5c62d71-0e03-4bc0-b924-b8277820bf76" />
<img width="1468" height="795" alt="Screenshot 2026-09-04 at 15 21 04" src="https://github.com/user-attachments/assets/58298613-7e5b-42f7-9f1b-bae9777ac374" />

> 🎯 This project simulates a real pain point in logistics operations: shipments silently going "at risk" (stale GPS, slipping ETAs, severe weather, carrier exceptions) while ops teams find out too late. It ingests messy multi-source data, flags and ranks at-risk shipments by business impact, and (next phase) uses an LLM to generate a recommended action and a customer-facing explanation, the kind of tool a forward-deployed engineer would build embedded inside a logistics customer's operation.

---

## Why I built this

I'm moving toward forward-deployed / solutions engineering work — roles where you sit close to a customer's real operational problems and ship something useful fast, rather than building in the abstract. Instead of just applying, I wanted to show what that looks like: pick a realistic industry problem, build a working (if rough) solution, and document my reasoning along the way.

This isn't tied to any single company's real data — it's synthetic data modeled on how logistics/carrier data actually behaves in the wild (missing pings, conflicting statuses, ETA drift).

## The problem

Logistics ops teams typically monitor shipments reactively — they find out something's wrong when a customer complains or a shipment is already very late. The underlying signals (a GPS feed going quiet, a carrier status stuck on "In Transit" too long, a storm on the route) are usually available *earlier*, but scattered across systems that don't talk to each other.

## What this does

1. **Generates realistic synthetic data** across three linked sources: shipment records, GPS ping history, carrier status events, and a weather feed — deliberately messy (missing pings, delayed status updates, conflicting signals) to mirror real operational data.
2. **Flags at-risk shipments** using rule-based detection across four signals: GPS staleness, ETA slippage, carrier status, and severe weather on the route.
3. **Scores and ranks** flagged shipments by business impact (customer tier × order value × risk severity), so an ops team sees what matters most first, not just what's flagged.
4. *(In progress)* Adds an AI reasoning layer using the Claude API to turn a flagged shipment into a plain-English explanation, a recommended action, and a draft customer-facing message.
5. *(Planned)* A simple dashboard so a non-technical ops user could actually use this.

## How it works (architecture)

```
generate_shipments.py  →  shipments.csv (150 shipments, 6 realistic scenarios)
                        →  gps_pings.csv (900 GPS pings)
                        →  status_events.csv (carrier status history)

generate_weather.py    →  weather.csv (route-level weather, correlated with delay scenarios)

detect_exceptions.py   →  reads shipments.csv + weather.csv
                        →  scores every shipment on 4 risk signals
                        →  flagged_shipments.csv (ranked by business impact)
```

**Detection logic** (see `detect_exceptions.py`): each shipment is scored on:
- GPS staleness (no ping in 12+ hours)
- ETA slippage (8+ hours past original plan)
- Carrier status (Delayed / Exception)
- Severe weather on the route (weighted by a severity index)

The risk score is then multiplied by a business-impact factor combining customer tier (Platinum/Gold/Standard) and order value, so a $20K Platinum shipment stuck in an ice storm ranks above a $300 Standard shipment with a minor delay.

## Sample output

Running the full pipeline on 150 synthetic shipments flags 63 as at-risk. Top result:

```
SHP-10117 | Platinum | impact=165.4 | ETA slipped 45.8 hours from plan;
Carrier status: Exception; Severe weather on route: Ice Storm (severity 8.7)
```

## Tech stack

- **Python** — data generation and detection logic
- **Claude API** — AI reasoning layer (in progress)
- Built iteratively with AI-assisted coding (Claude), with logic, thresholds, and scoring design done by me — I can walk through every design decision in the code.
- **pip3 install streamlit pandas Anthropic**
 
## Getting started

```bash
# clone the repo
git clone https://github.com/YOUR-USERNAME/shipment-exception-fde-prototype.git
cd shipment-exception-fde-prototype

# run the pipeline in order
python3 generate_shipments.py
python3 generate_weather.py
python3 detect_exceptions.py
streamlit run dashboard.py
```

Outputs `shipments.csv`, `gps_pings.csv`, `status_events.csv`, `weather.csv`, and `flagged_shipments.csv`.

## Roadmap

- [x] Synthetic multi-source shipment data generator
- [x] Weather data integration
- [x] Rule-based risk detection and impact scoring
- [x] Claude API reasoning layer (explanation + recommended action + draft customer message)
- [x] Simple dashboard (Streamlit) for a non-technical ops user
- [ ] Demo video walkthrough

## About me

I'm transitioning from a data analytics engineering background into forward-deployed / solutions engineering roles, where the job is being embedded with customers to solve real operational problems fast. This project is part of a series of self-directed case studies — see my [profile](https://github.com/suprivella) for others.

📫 [LinkedIn](https://www.linkedin.com/in/supradeepa-vella/) · [Email](suprivella88@gmail.com)
