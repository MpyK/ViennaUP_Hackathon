"""
app.py - Digital Product Passport meets ERP
ViennaUP Hackathon 2026 — Europe Tech Hackathon
Competitive Procurement + End of Life Decision Engine
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sqlite3

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DPP-ERP Integration Dashboard",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0D1B3E 0%, #1a3a6e 100%);
        padding: 20px 30px; border-radius: 10px;
        color: white; margin-bottom: 20px;
    }
    .compliant { background:#d4edda; border-left:4px solid #28a745;
        padding:10px 15px; border-radius:8px; color:#155724; font-weight:bold; margin:5px 0; }
    .non-compliant { background:#f8d7da; border-left:4px solid #dc3545;
        padding:10px 15px; border-radius:8px; color:#721c24; font-weight:bold; margin:5px 0; }
    .warning { background:#fff3cd; border-left:4px solid #ffc107;
        padding:10px 15px; border-radius:8px; color:#856404; font-weight:bold; margin:5px 0; }
    .recommend-card { background: linear-gradient(135deg, #0D1B3E, #1a3a6e);
        padding:20px; border-radius:12px; color:white; margin:10px 0; }
    .score-badge { display:inline-block; padding:4px 12px; border-radius:20px;
        font-weight:bold; font-size:0.9em; }
    .section-title { font-size:1.1em; font-weight:bold; color:#0D1B3E;
        border-bottom:2px solid #00B4D8; padding-bottom:5px; margin:15px 0 10px 0; }
</style>
""", unsafe_allow_html=True)

# ── ERP Database ───────────────────────────────────────────────────────────────
def init_erp():
    conn = sqlite3.connect("erp_database.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS purchase_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_date TEXT, battery_id TEXT, manufacturer TEXT,
        quantity INTEGER, unit_price_eur REAL, total_eur REAL,
        recommended_score REAL, reason TEXT, status TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS eol_decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        decision_date TEXT, battery_id TEXT, manufacturer TEXT,
        soh_pct REAL, decision TEXT, estimated_value_eur REAL,
        reason TEXT
    )""")
    conn.commit()
    conn.close()

def save_purchase_order(battery_id, manufacturer, quantity,
                         unit_price, total, score, reason):
    conn = sqlite3.connect("erp_database.db")
    c = conn.cursor()
    c.execute("""INSERT INTO purchase_orders
        (order_date, battery_id, manufacturer, quantity,
         unit_price_eur, total_eur, recommended_score, reason, status)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (datetime.now().strftime("%Y-%m-%d %H:%M"),
         battery_id, manufacturer, quantity,
         unit_price, total, score, reason, "Approved"))
    conn.commit()
    conn.close()

def save_eol_decision(battery_id, manufacturer, soh, decision, value, reason):
    conn = sqlite3.connect("erp_database.db")
    c = conn.cursor()
    c.execute("""INSERT INTO eol_decisions
        (decision_date, battery_id, manufacturer, soh_pct,
         decision, estimated_value_eur, reason)
        VALUES (?,?,?,?,?,?,?)""",
        (datetime.now().strftime("%Y-%m-%d %H:%M"),
         battery_id, manufacturer, soh, decision, value, reason))
    conn.commit()
    conn.close()

def get_purchase_orders():
    conn = sqlite3.connect("erp_database.db")
    df = pd.read_sql_query(
        "SELECT * FROM purchase_orders ORDER BY id DESC", conn)
    conn.close()
    return df

def get_eol_decisions():
    conn = sqlite3.connect("erp_database.db")
    df = pd.read_sql_query(
        "SELECT * FROM eol_decisions ORDER BY id DESC", conn)
    conn.close()
    return df

init_erp()

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_passports():
    with open("passports.json", "r") as f:
        data = json.load(f)
    return {b["id"]: b for b in data["batteries"]}

passports = load_passports()

# ── Procurement Scoring Engine ─────────────────────────────────────────────────
def score_battery(passport, weights):
    """
    Score a battery for procurement based on 5 weighted criteria.
    Returns score 0-100 and detailed breakdown.
    """
    g    = passport["general"]
    cf   = passport["carbon_footprint"]
    crm  = passport["critical_raw_materials"]
    comp = passport["compliance"]
    sup  = passport["supplier"]
    soh  = passport["state_of_health"]

    scores = {}
    reasons = {}

    # 1. COMPLIANCE (0-100)
    if comp["compliance_status"] == "COMPLIANT" and comp["ce_marked"]:
        scores["compliance"] = 100
        reasons["compliance"] = "Fully EU compliant, CE marked"
    elif comp["compliance_status"] == "COMPLIANT":
        scores["compliance"] = 70
        reasons["compliance"] = "Compliant but missing CE mark"
    else:
        scores["compliance"] = 0
        reasons["compliance"] = "NON-COMPLIANT — cannot be sold in EU"

    # 2. ETHICS / SUPPLY CHAIN RISK (0-100)
    risks = [
        crm["cobalt_risk"], crm["nickel_risk"],
        crm["lithium_risk"], crm["graphite_risk"]
    ]
    risk_map = {"LOW": 100, "NONE": 100, "MEDIUM": 60,
                "HIGH": 20, "UNKNOWN": 0}
    avg_risk = sum(risk_map.get(r, 0) for r in risks) / len(risks)
    ethics = (avg_risk * 0.6) + (sup["ethics_score"] * 0.4)
    scores["ethics"] = round(ethics, 1)
    high_risk = [r for r in risks if r == "HIGH"]
    reasons["ethics"] = (
        f"Ethics score {sup['ethics_score']}/100. "
        f"{'⚠️ HIGH RISK materials detected' if high_risk else 'Supply chain risk acceptable'}"
    )

    # 3. SUSTAINABILITY / CARBON (0-100)
    co2 = cf.get("per_kwh_kg_co2e")
    if co2 is None:
        scores["sustainability"] = 0
        reasons["sustainability"] = "Carbon data missing"
    elif co2 <= 40:
        scores["sustainability"] = 100
        reasons["sustainability"] = f"Excellent: {co2} kg CO2e/kWh (Class A)"
    elif co2 <= 65:
        scores["sustainability"] = 70
        reasons["sustainability"] = f"Good: {co2} kg CO2e/kWh (Class B)"
    elif co2 <= 90:
        scores["sustainability"] = 40
        reasons["sustainability"] = f"Average: {co2} kg CO2e/kWh (Class C)"
    else:
        scores["sustainability"] = 10
        reasons["sustainability"] = f"Poor: {co2} kg CO2e/kWh"

    if cf.get("renewable_energy_used"):
        scores["sustainability"] = min(100, scores["sustainability"] + 10)
        reasons["sustainability"] += f" + renewable energy ({cf.get('renewable_source', '')})"

    # 4. QUALITY / PERFORMANCE (0-100)
    soh_pct = soh["soce_pct"]
    cycles   = passport["electrical"]["expected_cycle_life"]
    warranty = passport["electrical"]["warranty_years"]
    quality  = (soh_pct * 0.4) + (min(cycles, 2000) / 2000 * 100 * 0.4) + \
               (min(warranty, 10) / 10 * 100 * 0.2)
    scores["quality"] = round(quality, 1)
    reasons["quality"] = (
        f"SoH: {soh_pct}% | "
        f"Cycle life: {cycles} | "
        f"Warranty: {warranty} years"
    )

    # 5. PRICE (0-100) — lower price = higher score
    price = g.get("price_per_kwh_eur", 200)
    if price <= 100:
        scores["price"] = 100
    elif price <= 150:
        scores["price"] = 80
    elif price <= 180:
        scores["price"] = 60
    elif price <= 220:
        scores["price"] = 40
    else:
        scores["price"] = 20
    reasons["price"] = f"€{price}/kWh"

    # WEIGHTED TOTAL
    total = sum(scores[k] * weights[k] / 100 for k in scores)

    return {
        "total": round(total, 1),
        "scores": scores,
        "reasons": reasons,
        "battery_id": passport["id"],
        "manufacturer": g["manufacturer"],
        "model": g["model"],
        "price_per_kwh": price,
        "compliance": comp["compliance_status"]
    }


# ── End of Life Decision Engine ───────────────────────────────────────────────
def eol_decision(passport):
    """Decide: repair, second life, recycle, or scrap."""
    soh  = passport["state_of_health"]
    eol  = passport["end_of_life"]
    comp = passport["compliance"]
    g    = passport["general"]

    soh_pct    = soh["soce_pct"]
    cycles     = soh["full_equivalent_cycles"]
    max_cycles = passport["electrical"]["expected_cycle_life"]
    cycle_pct  = (cycles / max_cycles * 100) if max_cycles else 100

    second_life_val = eol.get("second_life_value_eur", 0)
    scrap_val       = eol.get("estimated_scrap_value_eur", 0)

    if comp["compliance_status"] == "NON-COMPLIANT":
        return {
            "decision": "⚠️ QUARANTINE",
            "color": "#dc3545",
            "value_eur": 0,
            "reason": "Battery is non-compliant with EU regulation. Cannot be remarketed or resold. Escalate to compliance team.",
            "action": "Contact compliance officer immediately"
        }
    elif soh_pct >= 80 and cycle_pct < 60:
        return {
            "decision": "✅ SECOND LIFE",
            "color": "#28a745",
            "value_eur": second_life_val,
            "reason": f"SoH {soh_pct}% is above 80% threshold and only {cycle_pct:.0f}% of cycle life used. Suitable for stationary energy storage.",
            "action": f"List on secondary market. Estimated value: €{second_life_val:,}"
        }
    elif soh_pct >= 70 and cycle_pct < 80:
        return {
            "decision": "🔧 REPAIR / REFURBISH",
            "color": "#fd7e14",
            "value_eur": second_life_val * 0.7,
            "reason": f"SoH {soh_pct}% borderline. Minor refurbishment could restore value for second-life application.",
            "action": f"Assess repair cost. If repair < €{second_life_val * 0.3:,.0f}, proceed. Expected value post-repair: €{second_life_val * 0.7:,.0f}"
        }
    elif soh_pct >= 60:
        return {
            "decision": "♻️ RECYCLE",
            "color": "#0D1B3E",
            "value_eur": scrap_val,
            "reason": f"SoH {soh_pct}% below viable second-life threshold. Recycling recovers critical raw materials.",
            "action": f"Send to certified recycler. Estimated material recovery value: €{scrap_val:,}"
        }
    else:
        return {
            "decision": "🗑️ SCRAP",
            "color": "#6c757d",
            "value_eur": scrap_val * 0.3,
            "reason": f"SoH {soh_pct}% critically degraded. {cycles} cycles used. Beyond economic recovery.",
            "action": "Dispose per ADR transport regulations. Minimal scrap value."
        }


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔋 DPP-ERP Dashboard")
    st.markdown("**ViennaUP Hackathon 2026**")
    st.markdown("*EU Battery Regulation (2023/1542)*")
    st.divider()
    page = st.radio("Navigation", [
        "🏠 Overview",
        "🛒 Procurement Advisor",
        "♻️ End of Life Decisions",
        "🔍 Battery Lookup",
        "📊 Compliance Report",
        "📋 ERP Order History"
    ])
    st.divider()
    st.markdown(f"**Batteries in system:** {len(passports)}")
    compliant = sum(1 for b in passports.values()
                    if b["compliance"]["compliance_status"] == "COMPLIANT")
    st.markdown(f"**EU Compliant:** {compliant}/{len(passports)}")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.markdown("""
    <div class="main-header">
        <h2>🔋 DPP-ERP Integration Platform</h2>
        <p>Competitive Procurement · End of Life Decisions · EU Compliance</p>
        <p><small>EU Battery Regulation (Reg. EU 2023/1542) | Mandatory from 2027</small></p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ❌ The Problem")
        st.markdown("""
- Procurement teams buy batteries **without sustainability data**
- End-of-life decisions made **manually with no data support**
- Compliance audits take **hours of manual cross-referencing**
- EU Battery Regulation mandates passport data access **from 2027**
        """)
    with col2:
        st.markdown("### ✅ Our Solution")
        st.markdown("""
- **Procurement Advisor** — score and recommend batteries on ethics, sustainability, quality, price
- **End of Life Engine** — data-driven repair vs recycle vs scrap decisions
- **ERP Workflow** — decisions create purchase orders and EOL records automatically
- **Full compliance** audit trail in one dashboard
        """)

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Batteries in System", len(passports))
    c2.metric("EU Compliant", f"{compliant}/{len(passports)}")
    avg_co2 = [b["carbon_footprint"]["per_kwh_kg_co2e"]
               for b in passports.values()
               if b["carbon_footprint"]["per_kwh_kg_co2e"]]
    c3.metric("Avg Carbon", f"{sum(avg_co2)/len(avg_co2):.1f} kg CO2e/kWh")
    c4.metric("Second Life Eligible",
              sum(1 for b in passports.values()
                  if b["end_of_life"]["second_life_eligible"]))

    st.divider()
    st.markdown("### 🌿 Carbon Footprint Comparison")
    co2_data = []
    for bid, p in passports.items():
        val = p["carbon_footprint"]["per_kwh_kg_co2e"]
        if val:
            co2_data.append({
                "Battery": p["general"]["manufacturer"],
                "CO2/kWh": val,
                "Class": p["carbon_footprint"]["performance_class"],
                "ID": bid
            })
    if co2_data:
        fig = px.bar(pd.DataFrame(co2_data), x="Battery", y="CO2/kWh",
                     color="Class", text="CO2/kWh",
                     color_discrete_map={"A": "#28a745", "B": "#ffc107",
                                         "Not declared": "#dc3545"},
                     title="Carbon Footprint per kWh by Manufacturer")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PROCUREMENT ADVISOR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🛒 Procurement Advisor":
    st.markdown("## 🛒 Competitive Procurement Advisor")
    st.markdown("*Score and rank batteries based on your procurement priorities. Generate ERP purchase order.*")

    st.markdown("### ⚖️ Set Your Procurement Priorities")
    st.markdown("Adjust the weights to match your company's values. Total must equal 100%.")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        w_compliance = st.slider("✅ Compliance", 0, 100, 25, 5)
    with col2:
        w_ethics = st.slider("🤝 Ethics", 0, 100, 25, 5)
    with col3:
        w_sustainability = st.slider("🌿 Sustainability", 0, 100, 20, 5)
    with col4:
        w_quality = st.slider("⚡ Quality", 0, 100, 20, 5)
    with col5:
        w_price = st.slider("💶 Price", 0, 100, 10, 5)

    total_weight = w_compliance + w_ethics + w_sustainability + w_quality + w_price

    if total_weight != 100:
        st.warning(f"⚠️ Weights sum to {total_weight}%. Adjust to exactly 100% for accurate scoring.")
    else:
        weights = {
            "compliance":    w_compliance,
            "ethics":        w_ethics,
            "sustainability": w_sustainability,
            "quality":       w_quality,
            "price":         w_price
        }

        # Score all batteries
        results = []
        for bid, passport in passports.items():
            result = score_battery(passport, weights)
            results.append(result)

        results.sort(key=lambda x: x["total"], reverse=True)

        st.divider()
        st.markdown("### 🏆 Procurement Ranking")

        # Top recommendation
        top = results[0]
        st.markdown(f"""
        <div class="recommend-card">
            <h3>🏆 RECOMMENDED: {top['manufacturer']}</h3>
            <h4>{top['model']}</h4>
            <p><b>Composite Score: {top['total']}/100</b> | 
               Price: €{top['price_per_kwh']}/kWh | 
               Compliance: {top['compliance']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Full Ranking")

        # Ranking table
        rank_data = []
        for i, r in enumerate(results):
            rank_data.append({
                "Rank": f"#{i+1}",
                "Manufacturer": r["manufacturer"],
                "Total Score": f"{r['total']}/100",
                "Compliance": r["scores"]["compliance"],
                "Ethics": r["scores"]["ethics"],
                "Sustainability": r["scores"]["sustainability"],
                "Quality": r["scores"]["quality"],
                "Price Score": r["scores"]["price"],
                "€/kWh": r["price_per_kwh"],
                "Status": r["compliance"]
            })

        rank_df = pd.DataFrame(rank_data)
        st.dataframe(rank_df, use_container_width=True, hide_index=True)

        # Score breakdown chart
        fig = go.Figure()
        categories = ["Compliance", "Ethics", "Sustainability", "Quality", "Price"]
        colors = ["#0D1B3E", "#00B4D8", "#06D6A0", "#FFD166", "#E63946"]

        for i, r in enumerate(results[:4]):
            fig.add_trace(go.Bar(
                name=r["manufacturer"],
                x=categories,
                y=[r["scores"]["compliance"],
                   r["scores"]["ethics"],
                   r["scores"]["sustainability"],
                   r["scores"]["quality"],
                   r["scores"]["price"]],
                text=[f"{v}" for v in [
                    r["scores"]["compliance"],
                    r["scores"]["ethics"],
                    r["scores"]["sustainability"],
                    r["scores"]["quality"],
                    r["scores"]["price"]]],
                textposition="outside"
            ))

        fig.update_layout(barmode="group", height=400,
                          title="Score Breakdown by Category (Top 4 Batteries)")
        st.plotly_chart(fig, use_container_width=True)

        # Detailed reasoning
        st.markdown("### 🔍 Scoring Rationale")
        for r in results:
            color = "#28a745" if r["total"] >= 70 else "#ffc107" if r["total"] >= 50 else "#dc3545"
            with st.expander(f"{'🏆' if r == results[0] else '📋'} {r['manufacturer']} — Score: {r['total']}/100"):
                for criterion, reason in r["reasons"].items():
                    score = r["scores"][criterion]
                    bar_color = "#28a745" if score >= 70 else "#ffc107" if score >= 50 else "#dc3545"
                    st.markdown(f"**{criterion.title()}** ({score}/100): {reason}")
                    st.progress(score / 100)

        # Generate Purchase Order
        st.divider()
        st.markdown("### 📋 Generate ERP Purchase Order")
        st.markdown(f"*Creating order for recommended battery: **{top['manufacturer']}***")

        col_q, col_p = st.columns(2)
        with col_q:
            quantity = st.number_input("Quantity (units)", min_value=1, max_value=1000, value=10)
        with col_p:
            cap = passports[top["battery_id"]]["general"]["capacity_kwh_gross"]
            unit_price = top["price_per_kwh"] * cap
            st.metric("Unit Price", f"€{unit_price:,.0f}")

        total_value = quantity * unit_price

        st.metric("Total Order Value", f"€{total_value:,.0f}")

        reason_text = (
            f"Recommended by DPP Procurement Advisor. "
            f"Score: {top['total']}/100. "
            f"Ethics: {top['scores']['ethics']}/100. "
            f"Sustainability: {top['scores']['sustainability']}/100."
        )

        if st.button("✅ Approve & Create Purchase Order in ERP", type="primary"):
            save_purchase_order(
                top["battery_id"], top["manufacturer"],
                quantity, unit_price, total_value,
                top["total"], reason_text
            )
            st.success(f"✅ Purchase Order created in ERP!")
            st.markdown(f"""
            **Order Summary:**
            - Battery: {top['model']}
            - Manufacturer: {top['manufacturer']}
            - Quantity: {quantity} units
            - Total: €{total_value:,.0f}
            - DPP Score: {top['total']}/100
            - Status: Approved
            """)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: END OF LIFE DECISIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "♻️ End of Life Decisions":
    st.markdown("## ♻️ End of Life Decision Engine")
    st.markdown("*Data-driven decisions: repair, second life, recycle, or scrap. Powered by DPP data.*")

    battery_ids = list(passports.keys())
    selected_id = st.selectbox(
        "Select Battery for EOL Assessment",
        battery_ids,
        format_func=lambda x: f"{passports[x]['general']['manufacturer']} — {x} (SoH: {passports[x]['state_of_health']['soce_pct']}%)"
    )

    passport = passports[selected_id]
    soh      = passport["state_of_health"]
    eol      = passport["end_of_life"]
    g        = passport["general"]

    decision = eol_decision(passport)

    # Decision banner
    st.markdown(f"""
    <div style="background:{decision['color']}20; border-left:6px solid {decision['color']};
                 padding:20px; border-radius:10px; margin:15px 0;">
        <h2 style="color:{decision['color']}; margin:0;">{decision['decision']}</h2>
        <p style="margin:8px 0 0 0;">{decision['reason']}</p>
        <p style="margin:4px 0 0 0;"><b>Action:</b> {decision['action']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="section-title">📊 Battery Status</div>', unsafe_allow_html=True)
        st.metric("State of Health", f"{soh['soce_pct']}%")
        st.metric("Remaining Capacity", f"{soh['remaining_capacity_kwh']} kWh")
        st.metric("Cycles Used", f"{soh['full_equivalent_cycles']}")
        st.metric("Max Cycles", f"{passport['electrical']['expected_cycle_life']}")

    with col2:
        st.markdown('<div class="section-title">💶 Value Assessment</div>', unsafe_allow_html=True)
        st.metric("Second Life Value", f"€{eol.get('second_life_value_eur', 0):,}")
        st.metric("Scrap/Recycle Value", f"€{eol.get('estimated_scrap_value_eur', 0):,}")
        st.metric("Recyclability", f"{eol.get('recyclability_pct', 'N/A')}%")
        st.metric("Take-back Network", eol.get("take_back_network", "N/A")[:25])

    with col3:
        # SoH gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=soh["soce_pct"],
            title={"text": "State of Health (%)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": decision["color"]},
                "steps": [
                    {"range": [0, 60],  "color": "#f8d7da"},
                    {"range": [60, 70], "color": "#fff3cd"},
                    {"range": [70, 80], "color": "#d4edda"},
                    {"range": [80, 100], "color": "#cce5ff"},
                ],
                "threshold": {"line": {"color": "red", "width": 3},
                              "thickness": 0.75, "value": 70}
            }
        ))
        fig.update_layout(height=280, margin=dict(t=40, b=0, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

    # Decision path explanation
    st.markdown("### 📋 Decision Logic")
    decision_paths = [
        ("SoH ≥ 80% + < 60% cycles used", "Second Life", "#28a745",
         soh["soce_pct"] >= 80 and soh["full_equivalent_cycles"] < passport["electrical"]["expected_cycle_life"] * 0.6),
        ("SoH 70-80% + < 80% cycles used", "Repair/Refurbish", "#fd7e14",
         70 <= soh["soce_pct"] < 80),
        ("SoH 60-70%", "Recycle", "#0D1B3E",
         60 <= soh["soce_pct"] < 70),
        ("SoH < 60%", "Scrap", "#6c757d",
         soh["soce_pct"] < 60),
        ("Non-compliant", "Quarantine", "#dc3545",
         passport["compliance"]["compliance_status"] == "NON-COMPLIANT"),
    ]

    for path, label, color, active in decision_paths:
        prefix = "→ " if active else "   "
        style = f"background:{color}20; border-left:3px solid {color}; padding:6px 12px; border-radius:4px; margin:3px 0;" if active else "padding:6px 12px; color:#aaa; margin:3px 0;"
        st.markdown(f'<div style="{style}">{prefix}<b>{label}</b>: {path}</div>',
                    unsafe_allow_html=True)

    # Save EOL Decision to ERP
    st.divider()
    if st.button("💾 Record EOL Decision in ERP", type="primary"):
        save_eol_decision(
            selected_id,
            g["manufacturer"],
            soh["soce_pct"],
            decision["decision"],
            decision["value_eur"],
            decision["reason"]
        )
        st.success("✅ EOL Decision recorded in ERP system!")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: BATTERY LOOKUP
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Battery Lookup":
    st.markdown("## 🔍 Battery Passport Lookup")

    battery_ids = list(passports.keys())
    selected_id = st.selectbox("Select Battery ID", battery_ids,
                                format_func=lambda x: f"{x} — {passports[x]['general']['manufacturer']}")

    if selected_id:
        passport = passports[selected_id]
        comp = passport["compliance"]
        g    = passport["general"]
        cf   = passport["carbon_footprint"]
        crm  = passport["critical_raw_materials"]

        status = comp["compliance_status"]
        if status == "COMPLIANT":
            st.markdown(f'<div class="compliant">✅ EU COMPLIANT | QR: {passport["qr_code"]}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="non-compliant">❌ NON-COMPLIANT | QR: {passport["qr_code"]}</div>',
                        unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">📦 General</div>', unsafe_allow_html=True)
            st.write(f"**Manufacturer:** {g['manufacturer']}")
            st.write(f"**Model:** {g['model']}")
            st.write(f"**Chemistry:** {g['chemistry']}")
            st.write(f"**Capacity:** {g['capacity_kwh_gross']} kWh")
            st.write(f"**Price:** €{g.get('price_per_kwh_eur', 'N/A')}/kWh")
            st.write(f"**Cell Production:** {g['place_of_manufacture_cells']}")

        with col2:
            st.markdown('<div class="section-title">🌿 Carbon + Ethics</div>', unsafe_allow_html=True)
            if cf["total_kg_co2e"]:
                st.write(f"**Total CO2:** {cf['total_kg_co2e']:,} kg CO2e")
                st.write(f"**Per kWh:** {cf['per_kwh_kg_co2e']} kg CO2e/kWh")
                st.write(f"**Class:** {cf['performance_class']}")
                st.write(f"**Renewable:** {'✅' if cf['renewable_energy_used'] else '❌'} {cf.get('renewable_source','')}")
            st.write(f"**Cobalt origin:** {crm['cobalt_origin']} — {crm['cobalt_risk']} risk")
            st.write(f"**Lithium origin:** {crm['lithium_origin']} — {crm['lithium_risk']} risk")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: COMPLIANCE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Compliance Report":
    st.markdown("## 📊 EU Compliance Report")

    for bid, passport in passports.items():
        comp = passport["compliance"]
        g    = passport["general"]
        icon = "✅" if comp["compliance_status"] == "COMPLIANT" else "❌"

        with st.expander(f"{icon} {g['manufacturer']} — {bid}",
                         expanded=(comp["compliance_status"] != "COMPLIANT")):
            checks = [
                ("CE Marking",           "✅ Present"    if comp["ce_marked"]               else "❌ MISSING"),
                ("Declaration of Conformity", f"✅ {comp['doc_reference']}" if comp["doc_reference"] not in ["MISSING",""] else "❌ MISSING"),
                ("Notified Body",        f"✅ {comp['notified_body']}" if comp["notified_body"] != "None" else "❌ MISSING"),
                ("Carbon Footprint",     "✅ Declared"   if passport["carbon_footprint"]["total_kg_co2e"] else "❌ MISSING"),
                ("Independent Verifier", f"✅ {comp['independent_verifier']}" if comp["independent_verifier"] != "None" else "❌ MISSING"),
                ("Standards",            f"✅ {', '.join(comp.get('standards',[]))}" if comp.get("standards") else "❌ MISSING"),
            ]
            st.dataframe(pd.DataFrame(checks, columns=["Requirement", "Status"]),
                         use_container_width=True, hide_index=True)

            if comp["compliance_status"] == "COMPLIANT":
                st.markdown('<div class="compliant">✅ FULLY COMPLIANT</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="non-compliant">❌ NON-COMPLIANT — Cannot be sold in EU</div>',
                            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ERP ORDER HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 ERP Order History":
    st.markdown("## 📋 ERP Workflow History")
    st.markdown("*All decisions recorded in the ERP system*")

    tab1, tab2 = st.tabs(["🛒 Purchase Orders", "♻️ EOL Decisions"])

    with tab1:
        orders = get_purchase_orders()
        if orders.empty:
            st.info("No purchase orders yet. Go to Procurement Advisor to create one.")
        else:
            st.metric("Total Orders", len(orders))
            st.metric("Total Value", f"€{orders['total_eur'].sum():,.0f}")
            st.dataframe(orders, use_container_width=True, hide_index=True)

    with tab2:
        eol_df = get_eol_decisions()
        if eol_df.empty:
            st.info("No EOL decisions yet. Go to End of Life Decisions to create one.")
        else:
            st.metric("Total EOL Decisions", len(eol_df))
            st.metric("Total Recovered Value", f"€{eol_df['estimated_value_eur'].sum():,.0f}")
            st.dataframe(eol_df, use_container_width=True, hide_index=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#6c757d; font-size:0.85em;">
    🔋 DPP-ERP Integration | ViennaUP Europe Tech Hackathon 2026 |
    EU Battery Regulation Reg. (EU) 2023/1542
</div>
""", unsafe_allow_html=True)
