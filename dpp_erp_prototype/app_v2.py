"""
app_v2.py - Digital Product Passport meets ERP
ViennaUP Hackathon 2026 — Europe Tech Hackathon
Competitive Procurement + End of Life Decision Engine
+ Mock ERP REST API Integration (localhost:5000)
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sqlite3
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
BASE_DIR = pathlib.Path(__file__).parent

# ERP Connectio
from erp_connector import ERPConnector
from config import GROQ_API_KEY
from ui import (CSS, main_header, section_title, compliant_div, non_compliant_div,
                recommend_card, erp_ref_box, eol_banner, decision_path_row, esg_summary, footer)
erp = ERPConnector()

# Homepage configuration
st.set_page_config(
    page_title="DPP-ERP Integration Dashboard",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown(CSS, unsafe_allow_html=True)

# ERP Database (SQLite fallback)
def init_erp():
    conn = sqlite3.connect(BASE_DIR / "erp_database.db")
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
    conn = sqlite3.connect(BASE_DIR / "erp_database.db")
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
    conn = sqlite3.connect(BASE_DIR / "erp_database.db")
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
    conn = sqlite3.connect(BASE_DIR / "erp_database.db")
    df = pd.read_sql_query(
        "SELECT * FROM purchase_orders ORDER BY id DESC", conn)
    conn.close()
    return df

def get_eol_decisions():
    conn = sqlite3.connect(BASE_DIR / "erp_database.db")
    df = pd.read_sql_query(
        "SELECT * FROM eol_decisions ORDER BY id DESC", conn)
    conn.close()
    return df

init_erp()

# load Data
@st.cache_data
def load_passports():
    with open(BASE_DIR / "passports.json", "r") as f:
        data = json.load(f)
    return {b["id"]: b for b in data["batteries"]}

passports = load_passports()

# Procurement Scoring Engine
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
    soh_pct  = soh["soce_pct"]
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


# EOL Decision
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
            "decision_key": "scrap",
            "color": "#dc3545",
            "value_eur": 0,
            "reason": "Battery is non-compliant with EU regulation. Cannot be remarketed or resold. Escalate to compliance team.",
            "action": "Contact compliance officer immediately"
        }
    elif soh_pct >= 80 and cycle_pct < 60:
        return {
            "decision": "✅ SECOND LIFE",
            "decision_key": "second_life",
            "color": "#28a745",
            "value_eur": second_life_val,
            "reason": f"SoH {soh_pct}% is above 80% threshold and only {cycle_pct:.0f}% of cycle life used. Suitable for stationary energy storage.",
            "action": f"List on secondary market. Estimated value: €{second_life_val:,}"
        }
    elif soh_pct >= 70 and cycle_pct < 80:
        return {
            "decision": "🔧 REPAIR / REFURBISH",
            "decision_key": "repair",
            "color": "#fd7e14",
            "value_eur": second_life_val * 0.7,
            "reason": f"SoH {soh_pct}% borderline. Minor refurbishment could restore value for second-life application.",
            "action": f"Assess repair cost. If repair < €{second_life_val * 0.3:,.0f}, proceed. Expected value post-repair: €{second_life_val * 0.7:,.0f}"
        }
    elif soh_pct >= 60:
        return {
            "decision": "♻️ RECYCLE",
            "decision_key": "recycle",
            "color": "#0D1B3E",
            "value_eur": scrap_val,
            "reason": f"SoH {soh_pct}% below viable second-life threshold. Recycling recovers critical raw materials.",
            "action": f"Send to certified recycler. Estimated material recovery value: €{scrap_val:,}"
        }
    else:
        return {
            "decision": "🗑️ SCRAP",
            "decision_key": "scrap",
            "color": "#6c757d",
            "value_eur": scrap_val * 0.3,
            "reason": f"SoH {soh_pct}% critically degraded. {cycles} cycles used. Beyond economic recovery.",
            "action": "Dispose per ADR transport regulations. Minimal scrap value."
        }


# Sidebar
with st.sidebar:
    st.markdown("## 🔋 DPP-ERP Dashboard")
    st.markdown("**ViennaUP Hackathon 2026**")
    st.markdown("*EU Battery Regulation (2023/1542)*")
    st.divider()

    # ERP API Connection Status
    badge = erp.status_badge()
    if badge["online"]:
        st.success(badge["message"])
    else:
        st.warning(badge["message"])

    st.divider()
    page = st.radio("Navigation", [
        "🏠 Overview",
        "🛒 Procurement Advisor",
        "♻️ End of Life Decisions",
        "🔍 Battery Lookup",
        "📊 Compliance Report",
        "📋 ERP Order History",
        "🤖 AI Procurement Assistant",
        "🌍 ESG Report"
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
    st.markdown(main_header(
        "🔋 DPP-ERP Integration Platform",
        "Competitive Procurement · End of Life Decisions · EU Compliance",
        "EU Battery Regulation (Reg. EU 2023/1542) | Mandatory from 2027"
    ), unsafe_allow_html=True)

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

    # ERP Live Summary
    st.divider()
    summary_result = erp.get_dashboard_summary()
    if summary_result["success"]:
        s = summary_result["data"]
        st.markdown("### 🔗 Live ERP System Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Products Registered", s["products_registered"])
        m2.metric("Purchase Orders", s["purchase_orders"]["total"])
        m3.metric("Total Spend (€)", f"€{s['purchase_orders']['total_spend_eur']:,.0f}")
        m4.metric("EOL Decisions", s["eol_decisions"]["total"])

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
        st.markdown(recommend_card(
            top["manufacturer"], top["model"],
            top["total"], top["price_per_kwh"], top["compliance"]
        ), unsafe_allow_html=True)

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
            with st.expander(f"{'🏆' if r == results[0] else '📋'} {r['manufacturer']} — Score: {r['total']}/100"):
                for criterion, reason in r["reasons"].items():
                    score = r["scores"][criterion]
                    st.markdown(f"**{criterion.title()}** ({score}/100): {reason}")
                    st.progress(score / 100)

        # ── Generate Purchase Order ──────────────────────────────────────────
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
            # ── Save to SQLite (local fallback) ──────────────────────────────
            save_purchase_order(
                top["battery_id"], top["manufacturer"],
                quantity, unit_price, total_value,
                top["total"], reason_text
            )

            # ── POST to Mock ERP REST API ─────────────────────────────────────
            erp_result = erp.create_purchase_order(
                battery_id=top["battery_id"],
                battery_name=f"{top['manufacturer']} {top['model']}",
                supplier=top["manufacturer"],
                quantity=quantity,
                unit_price=round(unit_price, 2),
                score=top["total"],
                notes=reason_text,
            )

            if erp_result["success"]:
                st.success(f"✅ Purchase Order sent to ERP API!")
                st.markdown(erp_ref_box(erp_result["erp_reference"]), unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ ERP API unreachable — order saved locally. ({erp_result.get('error', '')})")

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
    st.markdown(eol_banner(
        decision["color"], decision["decision"], decision["reason"], decision["action"]
    ), unsafe_allow_html=True)

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(section_title("📊 Battery Status"), unsafe_allow_html=True)
        st.metric("State of Health", f"{soh['soce_pct']}%")
        st.metric("Remaining Capacity", f"{soh['remaining_capacity_kwh']} kWh")
        st.metric("Cycles Used", f"{soh['full_equivalent_cycles']}")
        st.metric("Max Cycles", f"{passport['electrical']['expected_cycle_life']}")

    with col2:
        st.markdown(section_title("💶 Value Assessment"), unsafe_allow_html=True)
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
        st.markdown(decision_path_row(label, path, color, active), unsafe_allow_html=True)

    # ── Save EOL Decision to ERP ──────────────────────────────────────────────
    st.divider()
    if st.button("💾 Record EOL Decision in ERP", type="primary"):
        # ── Save to SQLite (local fallback) ──────────────────────────────────
        save_eol_decision(
            selected_id,
            g["manufacturer"],
            soh["soce_pct"],
            decision["decision"],
            decision["value_eur"],
            decision["reason"]
        )

        # ── POST to Mock ERP REST API ─────────────────────────────────────────
        erp_result = erp.create_eol_decision(
            battery_id=selected_id,
            battery_name=f"{g['manufacturer']} {g['model']}",
            decision=decision["decision_key"],
            state_of_health=soh["soce_pct"],
            reason=decision["reason"],
            estimated_value=round(float(decision["value_eur"]), 2),
        )

        if erp_result["success"]:
            st.success("✅ EOL Decision recorded in ERP system!")
            st.markdown(erp_ref_box(erp_result["erp_reference"]), unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ ERP API unreachable — decision saved locally. ({erp_result.get('error', '')})")

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
            st.markdown(compliant_div(f'✅ EU COMPLIANT | QR: {passport["qr_code"]}'), unsafe_allow_html=True)
        else:
            st.markdown(non_compliant_div(f'❌ NON-COMPLIANT | QR: {passport["qr_code"]}'), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(section_title("📦 General"), unsafe_allow_html=True)
            st.write(f"**Manufacturer:** {g['manufacturer']}")
            st.write(f"**Model:** {g['model']}")
            st.write(f"**Chemistry:** {g['chemistry']}")
            st.write(f"**Capacity:** {g['capacity_kwh_gross']} kWh")
            st.write(f"**Price:** €{g.get('price_per_kwh_eur', 'N/A')}/kWh")
            st.write(f"**Cell Production:** {g['place_of_manufacture_cells']}")

        with col2:
            st.markdown(section_title("🌿 Carbon + Ethics"), unsafe_allow_html=True)
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
                st.markdown(compliant_div("✅ FULLY COMPLIANT"), unsafe_allow_html=True)
            else:
                st.markdown(non_compliant_div("❌ NON-COMPLIANT — Cannot be sold in EU"), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ERP ORDER HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 ERP Order History":
    st.markdown("## 📋 ERP Workflow History")
    st.markdown("*All decisions pushed to the ERP REST API and recorded locally*")

    # ── Live ERP API data ─────────────────────────────────────────────────────
    api_online = erp.is_online()

    if api_online:
        summary_result = erp.get_dashboard_summary()
        if summary_result["success"]:
            s = summary_result["data"]
            st.markdown("### 🔗 Live ERP Summary")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Products Registered", s["products_registered"])
            m2.metric("Purchase Orders", s["purchase_orders"]["total"])
            m3.metric("Total Spend (€)", f"€{s['purchase_orders']['total_spend_eur']:,.0f}")
            m4.metric("EOL Decisions", s["eol_decisions"]["total"])
        st.divider()

    tab1, tab2 = st.tabs(["🛒 Purchase Orders", "♻️ EOL Decisions"])

    with tab1:
        if api_online:
            po_result = erp.get_purchase_orders()
            if po_result["success"] and po_result["data"]["purchase_orders"]:
                st.caption("📡 Live from ERP REST API")
                df_po = pd.DataFrame(po_result["data"]["purchase_orders"])
                display_cols = [c for c in ["order_number", "battery_name", "supplier",
                                            "quantity", "unit_price", "total_price",
                                            "score", "status", "created_at"] if c in df_po.columns]
                st.dataframe(df_po[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No purchase orders in ERP yet.")
        else:
            # Fallback to SQLite
            st.caption("💾 From local SQLite (ERP API offline)")
            orders = get_purchase_orders()
            if orders.empty:
                st.info("No purchase orders yet. Go to Procurement Advisor to create one.")
            else:
                st.metric("Total Orders", len(orders))
                st.metric("Total Value", f"€{orders['total_eur'].sum():,.0f}")
                st.dataframe(orders, use_container_width=True, hide_index=True)

    with tab2:
        if api_online:
            eol_result = erp.get_eol_decisions()
            if eol_result["success"] and eol_result["data"]["eol_decisions"]:
                st.caption("📡 Live from ERP REST API")
                df_eol = pd.DataFrame(eol_result["data"]["eol_decisions"])
                display_cols = [c for c in ["decision_number", "battery_name", "decision",
                                            "state_of_health", "estimated_value",
                                            "status", "created_at"] if c in df_eol.columns]
                st.dataframe(df_eol[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No EOL decisions in ERP yet.")
        else:
            # Fallback to SQLite
            st.caption("💾 From local SQLite (ERP API offline)")
            eol_df = get_eol_decisions()
            if eol_df.empty:
                st.info("No EOL decisions yet. Go to EOL Engine to record one.")
            else:
                st.metric("Total EOL Decisions", len(eol_df))
                st.metric("Total Recovered Value", f"€{eol_df['estimated_value_eur'].sum():,.0f}")
                st.dataframe(eol_df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AI PROCUREMENT ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 AI Procurement Assistant":
    st.markdown(main_header(
        "🤖 AI Procurement Assistant",
        "Ask anything about batteries, procurement decisions, EOL strategy, ESG, or geopolitical risk.",
        "Powered by Claude AI · Grounded in real DPP passport data"
    ), unsafe_allow_html=True)

    import requests as _requests

    # ── Build passport context string once ───────────────────────────────────
    def build_passport_context(passports_dict):
        lines = []
        for bid, p in passports_dict.items():
            g    = p["general"]
            cf   = p["carbon_footprint"]
            crm  = p["critical_raw_materials"]
            comp = p["compliance"]
            soh  = p["state_of_health"]
            eol  = p["end_of_life"]
            sup  = p["supplier"]
            elec = p["electrical"]
            lines.append(f"""
--- BATTERY: {bid} ---
Manufacturer: {g['manufacturer']} | Model: {g['model']} | Chemistry: {g['chemistry']}
Capacity: {g['capacity_kwh_gross']} kWh | Price: €{g.get('price_per_kwh_eur','N/A')}/kWh
Cell production: {g['place_of_manufacture_cells']} | Assembly: {g.get('place_of_manufacture_assembly','N/A')}
Compliance: {comp['compliance_status']} | CE marked: {comp['ce_marked']}
Carbon footprint: {cf.get('total_kg_co2e','N/A')} kg CO2e total | {cf.get('per_kwh_kg_co2e','N/A')} kg CO2e/kWh | Class: {cf.get('performance_class','N/A')}
Renewable energy used: {cf.get('renewable_energy_used','N/A')} ({cf.get('renewable_source','N/A')})
Cobalt: {crm['cobalt_origin']} — {crm['cobalt_risk']} risk | Lithium: {crm['lithium_origin']} — {crm['lithium_risk']} risk
Nickel: {crm['nickel_origin']} — {crm['nickel_risk']} risk | Graphite: {crm['graphite_origin']} — {crm['graphite_risk']} risk
State of Health: {soh['soce_pct']}% | Remaining capacity: {soh['remaining_capacity_kwh']} kWh | Cycles used: {soh['full_equivalent_cycles']}
Expected cycle life: {elec['expected_cycle_life']} | Warranty: {elec['warranty_years']} years
Second life eligible: {eol.get('second_life_eligible','N/A')} | Second life value: €{eol.get('second_life_value_eur','N/A')}
Scrap value: €{eol.get('estimated_scrap_value_eur','N/A')} | Recyclability: {eol.get('recyclability_pct','N/A')}%
Supplier ethics score: {sup['ethics_score']}/100 | Audited: {sup.get('third_party_audited','N/A')}
""")
        return "\n".join(lines)

    PASSPORT_CONTEXT = build_passport_context(passports)

    SYSTEM_PROMPT = f"""You are an expert AI Procurement Assistant for a battery supply chain platform that integrates EU Digital Product Passports (DPP) with ERP systems.

You have access to real DPP data for 6 batteries in the system. Use this data to give specific, data-driven answers.

BATTERY PASSPORT DATA:
{PASSPORT_CONTEXT}

PLATFORM CAPABILITIES:
- Procurement Advisor: scores batteries on compliance, ethics, sustainability, quality, price with adjustable weights
- EOL Decision Engine: recommends repair / second life / recycle / scrap based on State of Health data
- ERP Integration: purchase orders and EOL decisions are sent via REST API to the ERP system with reference numbers
- Compliance checker: verifies EU Battery Regulation (2023/1542) compliance for all batteries

YOUR ROLE:
- Answer procurement, sustainability, EOL, compliance, ESG, and geopolitical supply chain questions
- Always reference specific battery data when relevant (manufacturer names, exact numbers)
- Give clear business recommendations with reasoning
- Be concise but precise — this is a business tool, not a chatbot
- If asked about geopolitical risk, reason about the origin countries of raw materials (cobalt from DRC, lithium from China, etc.)
- If asked about ESG, compute insights from the carbon, ethics, and recyclability data
- If asked which battery to buy, give a direct recommendation with the key reasons

Always respond in a professional but direct tone. Use bullet points for multi-part answers. Keep responses under 300 words unless a detailed breakdown is explicitly requested."""

    # ── Chat state ────────────────────────────────────────────────────────────
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []

    # ── Suggested questions ───────────────────────────────────────────────────
    if not st.session_state.ai_messages:
        st.markdown("### 💡 Try asking:")
        suggestions = [
            "Which battery should I buy if I prioritise sustainable mining?",
            "There's a trade war affecting China. Which batteries are at risk?",
            "Which batteries are eligible for second life and what are they worth?",
            "Give me an ESG summary of our entire battery portfolio.",
            "Which battery has the best carbon footprint per kWh?",
            "Should I repair or scrap a battery with 74% state of health?",
        ]
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            if cols[i % 2].button(suggestion, key=f"suggestion_{i}"):
                st.session_state.ai_messages.append({"role": "user", "content": suggestion})
                st.rerun()

    # ── Render chat history ───────────────────────────────────────────────────
    for msg in st.session_state.ai_messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # ── Chat input ────────────────────────────────────────────────────────────
    user_input = st.chat_input("Ask about batteries, procurement, EOL, ESG, geopolitical risk...")

    if user_input:
        st.session_state.ai_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analysing DPP data..."):
                try:
                    api_messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.ai_messages
                    ]


                    response = _requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {GROQ_API_KEY}",
                        },
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "max_tokens": 1000,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                *api_messages,
                            ],
                        },
                        timeout=30,
                    )
                    response.raise_for_status()
                    data = response.json()
                    reply = data["choices"][0]["message"]["content"]

                except Exception as e:
                    reply = f"⚠️ AI Assistant unavailable: {str(e)}\n\nPlease check your API connection."

            st.markdown(reply)
            st.session_state.ai_messages.append({"role": "assistant", "content": reply})

    # ── Clear chat button ─────────────────────────────────────────────────────
    if st.session_state.ai_messages:
        st.divider()
        if st.button("🗑️ Clear conversation"):
            st.session_state.ai_messages = []
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ESG REPORT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌍 ESG Report":
    st.markdown(main_header(
        "🌍 ESG Intelligence Report",
        "Environmental · Social · Governance — Auto-generated from Digital Product Passport data",
        "EU Battery Regulation (2023/1542) | Taxonomy Regulation Aligned"
    ), unsafe_allow_html=True)

    # ── Compute ESG metrics from passport data ────────────────────────────────
    compliant_batteries   = [p for p in passports.values() if p["compliance"]["compliance_status"] == "COMPLIANT"]
    all_batteries         = list(passports.values())

    co2_values   = [p["carbon_footprint"]["per_kwh_kg_co2e"] for p in all_batteries if p["carbon_footprint"]["per_kwh_kg_co2e"]]
    total_co2    = [p["carbon_footprint"]["total_kg_co2e"]   for p in all_batteries if p["carbon_footprint"]["total_kg_co2e"]]
    ethics_scores = [p["supplier"]["ethics_score"] for p in all_batteries]
    recyclability = [p["end_of_life"]["recyclability_pct"]   for p in all_batteries if p["end_of_life"].get("recyclability_pct")]
    second_life   = [p for p in all_batteries if p["end_of_life"].get("second_life_eligible")]
    renewable     = [p for p in all_batteries if p["carbon_footprint"].get("renewable_energy_used")]

    risk_map = {"LOW": 0, "NONE": 0, "MEDIUM": 1, "HIGH": 2, "UNKNOWN": 1}
    high_risk_count = sum(
        1 for p in all_batteries
        for risk in [
            p["critical_raw_materials"]["cobalt_risk"],
            p["critical_raw_materials"]["lithium_risk"],
            p["critical_raw_materials"]["graphite_risk"],
        ]
        if risk == "HIGH"
    )

    avg_co2        = sum(co2_values) / len(co2_values) if co2_values else 0
    avg_ethics     = sum(ethics_scores) / len(ethics_scores) if ethics_scores else 0
    avg_recycl     = sum(recyclability) / len(recyclability) if recyclability else 0
    compliance_pct = len(compliant_batteries) / len(all_batteries) * 100

    # ── E / S / G Score computation ───────────────────────────────────────────
    e_score = min(100, round(
        (max(0, 100 - avg_co2) * 0.5) +
        (len(renewable) / len(all_batteries) * 100 * 0.3) +
        (avg_recycl * 0.2), 1
    ))
    s_score = min(100, round(
        (avg_ethics * 0.6) +
        (max(0, 100 - high_risk_count * 10) * 0.4), 1
    ))
    g_score = min(100, round(
        (compliance_pct * 0.6) +
        (sum(1 for p in all_batteries if p["supplier"].get("third_party_audited", False)) / len(all_batteries) * 100 * 0.4), 1
    ))
    esg_total = round((e_score + s_score + g_score) / 3, 1)

    # ── Top ESG KPIs ──────────────────────────────────────────────────────────
    st.markdown("### 📊 Portfolio ESG Score")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall ESG Score", f"{esg_total}/100",
              delta="EU Taxonomy Aligned" if esg_total >= 70 else "Needs Improvement")
    c2.metric("🌿 Environmental", f"{e_score}/100")
    c3.metric("🤝 Social", f"{s_score}/100")
    c4.metric("🏛️ Governance", f"{g_score}/100")

    # ESG gauge chart
    fig_esg = go.Figure()
    fig_esg.add_trace(go.Bar(
        x=["Environmental", "Social", "Governance", "Overall ESG"],
        y=[e_score, s_score, g_score, esg_total],
        marker_color=["#28a745", "#00B4D8", "#0D1B3E", "#fd7e14"],
        text=[f"{v}/100" for v in [e_score, s_score, g_score, esg_total]],
        textposition="outside",
    ))
    fig_esg.update_layout(
        height=350, yaxis_range=[0, 110],
        title="ESG Score Breakdown — Computed from DPP Data",
        showlegend=False
    )
    st.plotly_chart(fig_esg, use_container_width=True)

    st.divider()

    # ── E: Environmental ──────────────────────────────────────────────────────
    st.markdown("## 🌿 E — Environmental")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Avg Carbon Intensity", f"{avg_co2:.1f} kg CO2e/kWh",
              delta="vs EU Class A threshold: 40 kg", delta_color="inverse")
    e2.metric("Renewable Energy Used", f"{len(renewable)}/{len(all_batteries)} batteries")
    e3.metric("Avg Recyclability", f"{avg_recycl:.1f}%")
    e4.metric("Second Life Eligible", f"{len(second_life)}/{len(all_batteries)} batteries")

    # Carbon breakdown per battery
    co2_data = []
    for p in all_batteries:
        val = p["carbon_footprint"]["per_kwh_kg_co2e"]
        if val:
            co2_data.append({
                "Manufacturer": p["general"]["manufacturer"],
                "kg CO2e/kWh": val,
                "Class": p["carbon_footprint"]["performance_class"],
                "Renewable": "✅" if p["carbon_footprint"].get("renewable_energy_used") else "❌",
                "Recyclability %": p["end_of_life"].get("recyclability_pct", "N/A"),
            })
    if co2_data:
        st.markdown("#### Carbon Footprint by Manufacturer")
        df_co2 = pd.DataFrame(co2_data)
        fig_co2 = px.bar(df_co2, x="Manufacturer", y="kg CO2e/kWh",
                         color="Class", text="kg CO2e/kWh",
                         color_discrete_map={"A": "#28a745", "B": "#ffc107", "Not declared": "#dc3545"},
                         title="Carbon Intensity per kWh — EU Performance Classes")
        fig_co2.add_hline(y=40, line_dash="dash", line_color="green",
                          annotation_text="Class A threshold (40 kg CO2e/kWh)")
        fig_co2.add_hline(y=65, line_dash="dash", line_color="orange",
                          annotation_text="Class B threshold (65 kg CO2e/kWh)")
        fig_co2.update_layout(height=380)
        st.plotly_chart(fig_co2, use_container_width=True)
        st.dataframe(df_co2, use_container_width=True, hide_index=True)

    st.divider()

    # ── S: Social ─────────────────────────────────────────────────────────────
    st.markdown("## 🤝 S — Social")
    s1, s2, s3 = st.columns(3)
    s1.metric("Avg Supplier Ethics Score", f"{avg_ethics:.1f}/100")
    s2.metric("High-Risk Material Sources", f"{high_risk_count} flagged",
              delta="conflict mineral risk", delta_color="inverse")
    audited = sum(1 for p in all_batteries if p["supplier"].get("third_party_audited", False))
    s3.metric("Third-Party Audited Suppliers", f"{audited}/{len(all_batteries)}")

    # Raw material risk table
    crm_data = []
    for p in all_batteries:
        crm = p["critical_raw_materials"]
        g   = p["general"]
        crm_data.append({
            "Manufacturer": g["manufacturer"],
            "Cobalt Origin": crm["cobalt_origin"],
            "Cobalt Risk": crm["cobalt_risk"],
            "Lithium Origin": crm["lithium_origin"],
            "Lithium Risk": crm["lithium_risk"],
            "Graphite Origin": crm["graphite_origin"],
            "Graphite Risk": crm["graphite_risk"],
            "Ethics Score": f"{p['supplier']['ethics_score']}/100",
        })
    st.markdown("#### Critical Raw Material Supply Chain Risk")
    st.dataframe(pd.DataFrame(crm_data), use_container_width=True, hide_index=True)

    # Ethics score chart
    ethics_data = [{"Manufacturer": p["general"]["manufacturer"],
                    "Ethics Score": p["supplier"]["ethics_score"]} for p in all_batteries]
    fig_eth = px.bar(pd.DataFrame(ethics_data), x="Manufacturer", y="Ethics Score",
                     text="Ethics Score", color="Ethics Score",
                     color_continuous_scale=["#dc3545", "#ffc107", "#28a745"],
                     range_color=[0, 100],
                     title="Supplier Ethics Score by Manufacturer (0=worst, 100=best)")
    fig_eth.update_layout(height=350)
    st.plotly_chart(fig_eth, use_container_width=True)

    st.divider()

    # ── G: Governance ─────────────────────────────────────────────────────────
    st.markdown("## 🏛️ G — Governance")
    g1, g2, g3 = st.columns(3)
    g1.metric("EU Compliance Rate", f"{compliance_pct:.0f}%",
              delta=f"{len(compliant_batteries)}/{len(all_batteries)} batteries")
    ce_count = sum(1 for p in all_batteries if p["compliance"]["ce_marked"])
    g2.metric("CE Marked", f"{ce_count}/{len(all_batteries)}")
    doc_count = sum(1 for p in all_batteries
                    if p["compliance"]["doc_reference"] not in ["MISSING", "", None])
    g3.metric("Declaration of Conformity", f"{doc_count}/{len(all_batteries)}")

    # Compliance breakdown table
    gov_data = []
    for p in all_batteries:
        comp = p["compliance"]
        gov_data.append({
            "Manufacturer": p["general"]["manufacturer"],
            "Status": comp["compliance_status"],
            "CE Marked": "✅" if comp["ce_marked"] else "❌",
            "DoC": "✅" if comp["doc_reference"] not in ["MISSING", "", None] else "❌",
            "Notified Body": "✅" if comp["notified_body"] != "None" else "❌",
            "Ind. Verifier": "✅" if comp["independent_verifier"] != "None" else "❌",
        })
    st.markdown("#### Governance & Compliance Checklist")
    st.dataframe(pd.DataFrame(gov_data), use_container_width=True, hide_index=True)

    st.divider()

    # ── ESG Summary Box ───────────────────────────────────────────────────────
    st.markdown("### 📋 ESG Executive Summary")
    st.markdown(esg_summary(
        esg_total, e_score, s_score, g_score,
        avg_co2, len(renewable), len(all_batteries), avg_recycl,
        len(second_life), avg_ethics, high_risk_count,
        audited, compliance_pct, ce_count, doc_count
    ), unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(footer(), unsafe_allow_html=True)
