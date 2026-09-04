"""
Shipment Exception Dashboard

A simple, clean Streamlit UI over the outputs of the detection pipeline:
flagged_shipments.csv and ai_recommendations.csv

Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Shipment Exception Dashboard",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Shipment Exception Detection & Rerouting Assistant")
st.caption("Prototype dashboard — flags at-risk shipments and surfaces AI-generated recommendations for ops teams.")

# --- Load data ---
if not os.path.exists("flagged_shipments.csv"):
    st.error("flagged_shipments.csv not found. Run generate_shipments.py, generate_weather.py, and detect_exceptions.py first.")
    st.stop()

flagged = pd.read_csv("flagged_shipments.csv")

has_ai = os.path.exists("ai_recommendations.csv")
if has_ai:
    ai_recs = pd.read_csv("ai_recommendations.csv")
    flagged = flagged.merge(ai_recs[["shipment_id", "explanation", "recommended_action", "customer_message"]],
                             on="shipment_id", how="left")

# --- Top-level metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total flagged shipments", len(flagged))
col2.metric("Platinum customers affected", int((flagged["customer_tier"] == "Platinum").sum()))
col3.metric("Total value at risk", f"${flagged['order_value_usd'].sum():,.0f}")
col4.metric("Highest impact score", f"{flagged['impact_score'].max():.1f}")

st.divider()

# --- Filters ---
st.sidebar.header("Filters")
tier_filter = st.sidebar.multiselect(
    "Customer tier",
    options=flagged["customer_tier"].unique(),
    default=list(flagged["customer_tier"].unique())
)
carrier_filter = st.sidebar.multiselect(
    "Carrier",
    options=flagged["carrier"].unique(),
    default=list(flagged["carrier"].unique())
)
min_impact = st.sidebar.slider(
    "Minimum impact score",
    min_value=0.0,
    max_value=float(flagged["impact_score"].max()),
    value=0.0
)

filtered = flagged[
    flagged["customer_tier"].isin(tier_filter) &
    flagged["carrier"].isin(carrier_filter) &
    (flagged["impact_score"] >= min_impact)
].sort_values("impact_score", ascending=False)

st.subheader(f"At-Risk Shipments ({len(filtered)})")

# --- Table ---
display_cols = ["shipment_id", "carrier", "route", "customer_tier", "order_value_usd",
                 "current_status", "impact_score", "reasons"]
st.dataframe(
    filtered[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "order_value_usd": st.column_config.NumberColumn("Order Value", format="$%.2f"),
        "impact_score": st.column_config.ProgressColumn(
            "Impact Score", min_value=0, max_value=float(flagged["impact_score"].max())
        ),
    }
)

st.divider()

# --- Detail view for one shipment ---
st.subheader("Shipment Detail & AI Recommendation")

shipment_ids = filtered["shipment_id"].tolist()
if shipment_ids:
    selected_id = st.selectbox("Select a shipment to inspect", shipment_ids)
    row = filtered[filtered["shipment_id"] == selected_id].iloc[0]

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown(f"**Route:** {row['route']}")
        st.markdown(f"**Carrier:** {row['carrier']}")
        st.markdown(f"**Customer tier:** {row['customer_tier']}")
        st.markdown(f"**Order value:** ${row['order_value_usd']:,.2f}")
        st.markdown(f"**Current status:** {row['current_status']}")
        st.markdown(f"**Impact score:** {row['impact_score']}")
        st.markdown("**Detected risk signals:**")
        st.info(row["reasons"])

    with c2:
        if has_ai and pd.notna(row.get("explanation")):
            st.markdown("**🤖 AI Explanation**")
            st.write(row["explanation"])

            st.markdown("**✅ Recommended Action**")
            st.success(row["recommended_action"])

            st.markdown("**✉️ Draft Customer Message**")
            st.text_area("", row["customer_message"], height=120, label_visibility="collapsed")
        else:
            st.warning("No AI recommendation generated for this shipment yet. "
                       "Run ai_reasoning_layer.py to generate one (currently only processes the top 10 by impact score).")
else:
    st.info("No shipments match the current filters.")

st.divider()
st.caption("Built as a self-directed case study exploring forward-deployed / solutions engineering work in logistics ops. "
           "Data is synthetic. See the project README for architecture and design decisions.")
