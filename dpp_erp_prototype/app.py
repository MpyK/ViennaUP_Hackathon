"""
app.py - Digital Product Passport meets ERP
ViennaUP Hackathon 2026 - Europe Tech Hackathon
Team: Muthukrishnan Jayakumar

Demonstrates integration of EU Battery Passport data (Reg. EU 2023/1542)
with a simulated ERP inventory system.
Real data source: Volvo EX90 Battery Passport
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from erp import init_erp, get_all_batteries, get_battery_erp

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DPP-ERP Integration Dashboard",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0D1B3E 0%, #1a3a6e 100%);
        padding: 20px 30px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #f8f9fa;
        border-left: 4px solid #0D1B3E;
        padding: 15px;
        border-radius: 8px;
        margin: 5px 0;
    }
    .compliant {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 10px 15px;
        border-radius: 8px;
        color: #155724;
        font-weight: bold;
    }
    .non-compliant {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 10px 15px;
        border-radius: 8px;
        color: #721c24;
        font-weight: bold;
    }
    .warning {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px 15px;
        border-radius: 8px;
        color: #856404;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.1em;
        font-weight: bold;
        color: #0D1B3E;
        border-bottom: 2px solid #00B4D8;
        padding-bottom: 5px;
        margin: 15px 0 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Init ERP ──────────────────────────────────────────────────────────────────
init_erp()

# ── Load passport data ────────────────────────────────────────────────────────
@st.cache_data
def load_passports():
    with open("passports.json", "r") as f:
        data = json.load(f)
    return {b["id"]: b for b in data["batteries"]}

passports = load_passports()
erp_data  = get_all_batteries()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔋 DPP-ERP Dashboard")
    st.markdown("**ViennaUP Hackathon 2026**")
    st.markdown("*EU Battery Regulation (2023/1542)*")
    st.divider()

    st.markdown("### Navigation")
    page = st.radio("", [
        "🏠 Overview",
        "🔍 Battery Lookup",
        "📊 Compliance Report",
        "🌍 Supply Chain",
        "⚡ State of Health"
    ])
    st.divider()
    st.markdown("### About")
    st.markdown("""
    This prototype demonstrates how **Digital Product Passport** data
    integrates with **ERP inventory systems** for EU Battery Regulation compliance.

    **Real data:** Volvo EX90 Battery Passport
    **Regulation:** Reg. (EU) 2023/1542
    """)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.markdown("""
    <div class="main-header">
        <h2>🔋 Digital Product Passport ↔ ERP Integration</h2>
        <p>EU Battery Regulation (Reg. EU 2023/1542) | Mandatory from 2027</p>
    </div>
    """, unsafe_allow_html=True)

    # The problem statement
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ❌ The Problem Today")
        st.markdown("""
        Compliance officers managing battery inventories face a critical gap:

        - **ERP systems** track: ID, quantity, price, supplier
        - **Battery Passports** exist: in separate systems, PDFs, or blockchain
        - **Result:** Manual data lookup takes hours per audit
        - **EU Regulation:** Mandatory passport data access from 2027
        - **Penalty:** Products cannot be sold in EU without compliance
        """)

    with col2:
        st.markdown("### ✅ Our Solution")
        st.markdown("""
        One dashboard that bridges both worlds:

        - **Search any battery** by ID — see ERP + Passport data instantly
        - **Compliance check** automated — no manual cross-referencing
        - **Supply chain visibility** — know where every raw material came from
        - **State of Health** monitoring — carbon footprint, recyclability
        - **Audit ready** — generate compliance report in one click
        """)

    st.divider()

    # KPI summary
    st.markdown("### 📦 Current Inventory Summary")

    total_batteries   = sum(b["quantity"] for b in erp_data)
    total_value       = sum(b["total_value_eur"] for b in erp_data)
    compliant_count   = sum(1 for b in erp_data if "Flagged" not in b["status"])
    noncompliant_count = sum(1 for b in erp_data if "Flagged" in b["status"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Battery Units", f"{total_batteries:,}")
    c2.metric("Total Inventory Value", f"€{total_value:,.0f}")
    c3.metric("✅ Compliant Products", f"{compliant_count}")
    c4.metric("⚠️ Flagged Products", f"{noncompliant_count}")

    st.divider()

    # Inventory table
    st.markdown("### 📋 ERP Inventory — All Batteries")
    df = pd.DataFrame(erp_data)
    df = df.rename(columns={
        "battery_id": "Battery ID",
        "product_name": "Product",
        "supplier": "Supplier",
        "quantity": "Qty",
        "unit_price_eur": "Unit Price (€)",
        "total_value_eur": "Total Value (€)",
        "warehouse": "Warehouse",
        "received_date": "Received",
        "status": "Status"
    })
    st.dataframe(df, use_container_width=True)

    # Carbon footprint comparison chart
    st.markdown("### 🌿 Carbon Footprint Comparison")
    co2_data = []
    for bid, passport in passports.items():
        val = passport["carbon_footprint"]["total_kg_co2e"]
        if val:
            co2_data.append({
                "Battery": passport["general"]["model"][:30],
                "CO2 (kg)": val,
                "Class": passport["carbon_footprint"]["performance_class"]
            })

    if co2_data:
        fig = px.bar(
            pd.DataFrame(co2_data),
            x="Battery", y="CO2 (kg)",
            color="Class",
            title="Total Carbon Footprint by Battery (kg CO2e)",
            color_discrete_map={"A": "#28a745", "B": "#ffc107", "C": "#fd7e14",
                                 "Not declared": "#dc3545"}
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — BATTERY LOOKUP
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Battery Lookup":
    st.markdown("## 🔍 Battery Passport Lookup")
    st.markdown("*Search any battery to see ERP inventory data + full Digital Product Passport side by side*")

    battery_ids = list(passports.keys())
    selected_id = st.selectbox("Select Battery ID", battery_ids,
                                format_func=lambda x: f"{x} — {passports[x]['general']['model'][:40]}")

    if selected_id:
        passport = passports[selected_id]
        erp = get_battery_erp(selected_id)

        # Compliance badge
        status = passport["compliance"]["compliance_status"]
        if status == "COMPLIANT":
            st.markdown(f'<div class="compliant">✅ EU COMPLIANT — Reg. (EU) 2023/1542 | QR: {passport["qr_code"]}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="non-compliant">❌ NON-COMPLIANT — Missing mandatory data | QR: {passport["qr_code"]}</div>',
                        unsafe_allow_html=True)

        st.markdown("---")

        # Two columns: ERP left, Passport right
        col_erp, col_dpp = st.columns(2)

        with col_erp:
            st.markdown('<div class="section-header">📦 ERP DATA (Inventory System)</div>',
                        unsafe_allow_html=True)
            if erp:
                st.markdown(f"**Product:** {erp['product_name']}")
                st.markdown(f"**Supplier:** {erp['supplier']}")
                st.markdown(f"**Quantity in Stock:** {erp['quantity']} units")
                st.markdown(f"**Unit Price:** €{erp['unit_price_eur']:,.2f}")
                st.markdown(f"**Total Value:** €{erp['total_value_eur']:,.2f}")
                st.markdown(f"**Warehouse:** {erp['warehouse']}")
                st.markdown(f"**Received:** {erp['received_date']}")
                st.markdown(f"**ERP Status:** {erp['status']}")
            else:
                st.warning("No ERP record found for this battery ID.")

        with col_dpp:
            st.markdown('<div class="section-header">🔋 BATTERY PASSPORT (Digital Product Passport)</div>',
                        unsafe_allow_html=True)
            g = passport["general"]
            st.markdown(f"**Manufacturer:** {g['manufacturer']}")
            st.markdown(f"**Model:** {g['model']}")
            st.markdown(f"**Chemistry:** {g['chemistry']}")
            st.markdown(f"**Capacity:** {g['capacity_kwh_gross']} kWh gross / {g['capacity_kwh_net']} kWh net")
            st.markdown(f"**Weight:** {g['weight_kg']} kg")
            st.markdown(f"**Manufactured:** {g['date_of_manufacture']}")
            st.markdown(f"**Cell Manufacturer:** {g['cell_manufacturer']}")
            st.markdown(f"**Cell Production:** {g['place_of_manufacture_cells']}")
            st.markdown(f"**Pack Assembly:** {g['place_of_manufacture_assembly']}")

        st.divider()

        # Carbon + Recycled content
        col_carbon, col_recycle = st.columns(2)

        with col_carbon:
            st.markdown('<div class="section-header">🌿 Carbon Footprint</div>', unsafe_allow_html=True)
            cf = passport["carbon_footprint"]
            if cf["total_kg_co2e"]:
                st.metric("Total CO2", f"{cf['total_kg_co2e']:,} kg CO2e")
                st.metric("Per kWh", f"{cf['per_kwh_kg_co2e']} kg CO2e/kWh")
                st.metric("Performance Class", cf["performance_class"])
                st.markdown(f"**Renewable energy used:** {'✅ Yes' if cf['renewable_energy_used'] else '❌ No'}")
                if cf["renewable_source"] != "Not declared":
                    st.markdown(f"**Source:** {cf['renewable_source']}")

                # Lifecycle breakdown chart
                breakdown = cf.get("lifecycle_breakdown", {})
                if breakdown:
                    fig = go.Figure(go.Pie(
                        labels=list(breakdown.keys()),
                        values=list(breakdown.values()),
                        hole=0.4,
                        marker_colors=["#E63946", "#457B9D", "#1D3557", "#A8DADC"]
                    ))
                    fig.update_layout(title="CO2 by Life Cycle Phase", height=280,
                                      margin=dict(t=40, b=0, l=0, r=0))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown('<div class="non-compliant">❌ Carbon footprint data MISSING — Non-compliant</div>',
                            unsafe_allow_html=True)

        with col_recycle:
            st.markdown('<div class="section-header">♻️ Recycled Content</div>', unsafe_allow_html=True)
            rc = passport["recycled_content"]
            materials = ["Cobalt", "Lithium", "Nickel", "Lead"]
            values    = [rc["cobalt_pct"], rc["lithium_pct"], rc["nickel_pct"], rc["lead_pct"]]

            valid_vals = [(m, v) for m, v in zip(materials, values) if v is not None]
            if valid_vals:
                fig2 = go.Figure(go.Bar(
                    x=[v[0] for v in valid_vals],
                    y=[v[1] for v in valid_vals],
                    marker_color=["#2196F3", "#4CAF50", "#FF9800", "#9E9E9E"]
                ))
                fig2.update_layout(
                    title="Recycled Content (%)",
                    yaxis_title="Percentage (%)",
                    height=280,
                    margin=dict(t=40, b=0, l=0, r=0)
                )
                st.plotly_chart(fig2, use_container_width=True)
                st.markdown(f"*{rc['note']}*")
            else:
                st.markdown('<div class="non-compliant">❌ Recycled content data MISSING</div>',
                            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — COMPLIANCE REPORT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Compliance Report":
    st.markdown("## 📊 EU Compliance Report")
    st.markdown("*Automated compliance check against Reg. (EU) 2023/1542*")

    for bid, passport in passports.items():
        comp = passport["compliance"]
        g    = passport["general"]

        with st.expander(f"{'✅' if comp['compliance_status'] == 'COMPLIANT' else '❌'} {bid} — {g['model'][:45]}",
                         expanded=(comp['compliance_status'] != 'COMPLIANT')):

            checks = [
                ("CE Marking",          "✅ Present"  if comp["ce_marked"]        else "❌ MISSING"),
                ("Declaration of Conformity", f"✅ {comp['doc_reference']}" if comp["doc_reference"] not in ["MISSING",""] else "❌ MISSING"),
                ("Notified Body",       f"✅ {comp['notified_body']}" if comp["notified_body"] != "None" else "❌ MISSING"),
                ("Carbon Footprint",    "✅ Declared" if passport["carbon_footprint"]["total_kg_co2e"] else "❌ MISSING"),
                ("Supply Chain Due Diligence", "✅ Performed" if comp["due_diligence"] not in ["Not performed",""] else "❌ MISSING"),
                ("Independent Verification", f"✅ {comp['independent_verifier']}" if comp["independent_verifier"] != "None" else "❌ MISSING"),
                ("Standards Applied",   f"✅ {', '.join(comp['standards'])}" if comp["standards"] else "❌ MISSING"),
            ]

            check_df = pd.DataFrame(checks, columns=["Requirement", "Status"])
            st.dataframe(check_df, use_container_width=True, hide_index=True)

            if comp["compliance_status"] == "COMPLIANT":
                st.markdown('<div class="compliant">✅ FULLY COMPLIANT with Reg. (EU) 2023/1542</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<div class="non-compliant">❌ NON-COMPLIANT — Cannot be sold in EU market without correction</div>',
                            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — SUPPLY CHAIN
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌍 Supply Chain":
    st.markdown("## 🌍 Supply Chain Transparency")
    st.markdown("*Origin and due diligence data for critical raw materials*")

    battery_ids = list(passports.keys())
    selected_id = st.selectbox("Select Battery", battery_ids,
                                format_func=lambda x: passports[x]["general"]["model"][:50])

    passport = passports[selected_id]
    crm      = passport["critical_raw_materials"]

    st.markdown("### ⛏️ Critical Raw Materials")

    materials = [
        ("Cobalt",    crm["cobalt_kg"],    crm["cobalt_origin"],    "#E63946"),
        ("Nickel",    crm["nickel_kg"],    crm["nickel_origin"],    "#457B9D"),
        ("Lithium",   crm["lithium_kg"],   crm["lithium_origin"],   "#2A9D8F"),
        ("Graphite",  crm["graphite_kg"],  crm["graphite_origin"],  "#264653"),
    ]

    cols = st.columns(4)
    for i, (name, kg, origin, color) in enumerate(materials):
        with cols[i]:
            if kg:
                st.markdown(f"""
                <div style="background:{color}20; border-left:4px solid {color};
                             padding:12px; border-radius:8px; text-align:center;">
                    <b style="color:{color}; font-size:1.1em;">{name}</b><br>
                    <span style="font-size:1.8em; font-weight:bold;">{kg} kg</span><br>
                    <small>{origin}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:#f8d7da; border-left:4px solid #dc3545;
                             padding:12px; border-radius:8px; text-align:center;">
                    <b style="color:#dc3545;">{name}</b><br>
                    <span style="color:#dc3545;">❌ Data Missing</span>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # Supply chain risk
    st.markdown("### ⚠️ Supply Chain Risk Assessment")
    risk_data = []
    if crm["cobalt_origin"] and "Congo" in crm["cobalt_origin"]:
        risk_data.append({"Material": "Cobalt", "Origin": crm["cobalt_origin"],
                          "Risk Level": "HIGH", "Reason": "DRC — conflict mineral region"})
    if crm["cobalt_origin"] and "Finland" in crm["cobalt_origin"]:
        risk_data.append({"Material": "Cobalt", "Origin": crm["cobalt_origin"],
                          "Risk Level": "LOW", "Reason": "EU-refined — full traceability"})
    if crm["lithium_origin"] and "Chile" in crm["lithium_origin"]:
        risk_data.append({"Material": "Lithium", "Origin": crm["lithium_origin"],
                          "Risk Level": "MEDIUM", "Reason": "Water stress in mining regions"})
    if crm["lithium_origin"] and "Australia" in crm["lithium_origin"]:
        risk_data.append({"Material": "Lithium", "Origin": crm["lithium_origin"],
                          "Risk Level": "LOW", "Reason": "High governance standards"})

    if risk_data:
        risk_df = pd.DataFrame(risk_data)
        st.dataframe(risk_df, use_container_width=True, hide_index=True)
    else:
        st.info("Supply chain origin data not available for risk assessment.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — STATE OF HEALTH
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚡ State of Health":
    st.markdown("## ⚡ Battery State of Health Monitor")
    st.markdown("*Real-time battery performance and degradation data from the Digital Product Passport*")

    battery_ids = list(passports.keys())
    selected_id = st.selectbox("Select Battery", battery_ids,
                                format_func=lambda x: f"{passports[x]['general']['model'][:40]} — SoH: {passports[x]['state_of_health']['soce_pct']}%")

    passport = passports[selected_id]
    soh      = passport["state_of_health"]
    elec     = passport["electrical"]

    # SoH status badge
    soh_pct = soh["soce_pct"]
    if soh_pct >= 90:
        badge_color = "#28a745"
        badge_text  = "✅ EXCELLENT"
    elif soh_pct >= 80:
        badge_color = "#ffc107"
        badge_text  = "⚠️ GOOD"
    elif soh_pct >= 70:
        badge_color = "#fd7e14"
        badge_text  = "⚠️ MODERATE"
    else:
        badge_color = "#dc3545"
        badge_text  = "❌ DEGRADED — Consider replacement"

    st.markdown(f"""
    <div style="background:{badge_color}20; border-left:6px solid {badge_color};
                 padding:15px; border-radius:8px; font-size:1.2em; font-weight:bold;">
        {badge_text} — State of Health: {soh_pct}%
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">📊 Key Performance Metrics</div>',
                    unsafe_allow_html=True)

        metrics = [
            ("State of Certified Energy", f"{soh['soce_kwh']} kWh", f"{soh['soce_pct']}% of rated"),
            ("Remaining Capacity",        f"{soh['remaining_capacity_kwh']} kWh", f"{soh['remaining_capacity_pct']}%"),
            ("Round-trip Efficiency",     f"{soh['round_trip_efficiency_pct']}%", "charge/discharge"),
            ("Self-discharge Rate",       f"{soh['self_discharge_rate_pct_month']}%/month", "lower = better"),
            ("Ohmic Resistance",          f"{soh['ohmic_resistance_mohm']} mΩ", "pack level"),
            ("Full Equivalent Cycles",    str(soh["full_equivalent_cycles"]), f"of {elec['expected_cycle_life']} total"),
            ("Total Charge Cycles",       str(soh["total_charge_cycles"]), "absolute count"),
            ("Deep Discharges",           str(soh["deep_discharges"]), "SoC < 10% events"),
        ]

        for label, value, note in metrics:
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:6px 0;
                         border-bottom:1px solid #eee;">
                <span style="color:#6c757d;">{label}</span>
                <span><b>{value}</b> <small style="color:#aaa;">{note}</small></span>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-header">📈 Health Gauge</div>',
                    unsafe_allow_html=True)

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=soh_pct,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "State of Health (%)"},
            delta={"reference": 100, "suffix": "%"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": badge_color},
                "steps": [
                    {"range": [0, 70],  "color": "#f8d7da"},
                    {"range": [70, 80], "color": "#fff3cd"},
                    {"range": [80, 90], "color": "#d4edda"},
                    {"range": [90, 100],"color": "#cce5ff"},
                ],
                "threshold": {
                    "line": {"color": "#dc3545", "width": 3},
                    "thickness": 0.75,
                    "value": elec["soh_threshold_pct"]
                }
            }
        ))
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"**Current SoC:** {soh['current_soc_pct']}%")
        st.markdown(f"**Warranty:** {elec['warranty_years']} years to ≥{elec['soh_threshold_pct']}% capacity")
        if elec['warranty_km']:
            st.markdown(f"**Or:** {elec['warranty_km']:,} km")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#6c757d; font-size:0.85em;">
    🔋 DPP-ERP Integration Prototype | ViennaUP Europe Tech Hackathon 2026 |
    EU Battery Regulation (Reg. EU 2023/1542) |
    Real data: Volvo EX90 Battery Passport
</div>
""", unsafe_allow_html=True)
