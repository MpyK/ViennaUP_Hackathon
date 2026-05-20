"""
pv_app.py - SolarPassport — PV DPP-ERP Platform
ViennaUP Hackathon 2026 — Redesigned with modern app-like UI
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sqlite3
import requests as _requests
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
BASE_DIR = pathlib.Path(__file__).parent

from erp_connector import ERPConnector
from config import GROQ_API_KEY
erp = ERPConnector()

st.set_page_config(page_title="SolarPassport", page_icon="☀️", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"]{font-family:'DM Sans',sans-serif;background:#0a0f1e;color:#e8edf5;}
[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#0a0f1e 0%,#0d1a12 50%,#0a0f1e 100%);}
[data-testid="stSidebar"]{display:none;}
[data-testid="collapsedControl"]{display:none;}
.block-container{padding:0!important;max-width:100%!important;}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu,footer,[data-testid="stToolbar"]{display:none;}

.sp-navbar{display:flex;align-items:center;justify-content:space-between;padding:0 40px;height:64px;
  background:rgba(255,255,255,0.03);border-bottom:1px solid rgba(255,255,255,0.07);backdrop-filter:blur(20px);}
.sp-logo-text{font-size:1.2rem;font-weight:700;letter-spacing:-0.5px;
  background:linear-gradient(135deg,#4ade80,#22d3ee);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.sp-erp-badge{display:flex;align-items:center;gap:8px;padding:10px 20px;border-radius:12px;font-size:0.92rem;font-weight:700;letter-spacing:0.2px;}
.sp-erp-online{background:rgba(74,222,128,0.12);color:#4ade80;border:1px solid rgba(74,222,128,0.35);}
.sp-erp-offline{background:rgba(251,191,36,0.12);color:#fbbf24;border:1px solid rgba(251,191,36,0.35);}
.sp-dot{width:9px;height:9px;border-radius:50%;display:inline-block;}
.sp-dot-green{background:#4ade80;box-shadow:0 0 8px #4ade80;animation:pulse 2s infinite;}
.sp-dot-amber{background:#fbbf24;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}

.sp-page{padding:32px 40px 60px;}
.sp-hero{margin-bottom:36px;}
.sp-hero-title{font-size:2.6rem;font-weight:700;letter-spacing:-1.5px;line-height:1.1;
  background:linear-gradient(135deg,#ffffff 0%,#4ade80 60%,#22d3ee 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px;}
.sp-hero-sub{font-size:0.95rem;color:#64748b;}

.sp-kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px;}
.sp-kpi{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:22px 26px;transition:all 0.2s;}
.sp-kpi:hover{background:rgba(255,255,255,0.07);border-color:rgba(74,222,128,0.3);transform:translateY(-2px);}
.sp-kpi-label{font-size:0.85rem;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;}
.sp-kpi-value{font-size:2.2rem;font-weight:700;color:#ffffff;letter-spacing:-1px;}
.sp-kpi-sub{font-size:0.8rem;color:#4ade80;margin-top:6px;font-weight:500;}

.sp-section-title{font-size:0.9rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;
  margin:28px 0 16px;display:flex;align-items:center;gap:10px;}
.sp-section-title::after{content:'';flex:1;height:1px;background:rgba(255,255,255,0.08);}

.sp-panel-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
  border-radius:16px;padding:22px;transition:all 0.25s;position:relative;overflow:hidden;margin-bottom:4px;}
.sp-panel-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#4ade80,#22d3ee);opacity:0;transition:opacity 0.2s;}
.sp-panel-card:hover{background:rgba(255,255,255,0.07);border-color:rgba(74,222,128,0.3);transform:translateY(-2px);}
.sp-panel-card:hover::before{opacity:1;}
.sp-card-mfr{font-size:1.05rem;font-weight:700;color:#ffffff;}
.sp-card-model{font-size:0.78rem;color:#64748b;margin-top:3px;margin-bottom:16px;}
.sp-card-stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.sp-stat-label{font-size:0.72rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;}
.sp-stat-value{font-size:1.1rem;font-weight:700;color:#ffffff;font-family:'DM Mono',monospace;}
.sp-score-label{display:flex;justify-content:space-between;font-size:0.78rem;color:#94a3b8;font-weight:600;margin-bottom:6px;margin-top:16px;}
.sp-score-bar-bg{height:5px;background:rgba(255,255,255,0.1);border-radius:3px;}
.sp-score-bar-fill{height:5px;border-radius:3px;background:linear-gradient(90deg,#4ade80,#22d3ee);}

.sp-badge{font-size:0.66rem;font-weight:600;padding:3px 10px;border-radius:20px;text-transform:uppercase;letter-spacing:0.5px;white-space:nowrap;}
.sp-badge-green{background:rgba(74,222,128,0.12);color:#4ade80;border:1px solid rgba(74,222,128,0.25);}
.sp-badge-red{background:rgba(248,113,113,0.12);color:#f87171;border:1px solid rgba(248,113,113,0.25);}
.sp-badge-amber{background:rgba(251,191,36,0.12);color:#fbbf24;border:1px solid rgba(251,191,36,0.25);}
.sp-badge-blue{background:rgba(34,211,238,0.12);color:#22d3ee;border:1px solid rgba(34,211,238,0.25);}

.sp-table-wrap{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:16px;overflow:hidden;margin-bottom:28px;}
.sp-table{width:100%;border-collapse:collapse;font-size:0.87rem;}
.sp-table th{padding:13px 18px;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;
  color:#475569;background:rgba(255,255,255,0.02);border-bottom:1px solid rgba(255,255,255,0.07);}
.sp-table td{padding:13px 18px;border-bottom:1px solid rgba(255,255,255,0.04);color:#cbd5e1;}
.sp-table tr:last-child td{border-bottom:none;}
.sp-table tr:hover td{background:rgba(255,255,255,0.025);}
.sp-table tr.top-row td{background:rgba(74,222,128,0.04);}
.sp-score-pill{display:inline-flex;align-items:center;justify-content:center;width:46px;height:22px;
  border-radius:11px;font-size:0.78rem;font-weight:700;font-family:'DM Mono',monospace;}
.sp-score-high{background:rgba(74,222,128,0.2);color:#4ade80;}
.sp-score-mid{background:rgba(251,191,36,0.2);color:#fbbf24;}
.sp-score-low{background:rgba(248,113,113,0.2);color:#f87171;}

.sp-order-panel{background:rgba(255,255,255,0.04);border:1px solid rgba(74,222,128,0.3);border-radius:20px;padding:28px;margin-top:20px;}
.sp-erp-ref{background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.3);border-radius:12px;
  padding:14px 20px;margin-top:14px;font-family:'DM Mono',monospace;font-size:0.95rem;color:#4ade80;}

.stButton>button{background:linear-gradient(135deg,#4ade80,#22d3ee)!important;color:#0a0f1e!important;
  border:none!important;border-radius:10px!important;font-weight:700!important;font-size:1rem!important;
  font-family:'DM Sans',sans-serif!important;transition:all 0.2s!important;padding:12px 28px!important;}
.stButton>button:hover{opacity:0.9!important;transform:translateY(-1px)!important;}
.stTextInput>div>div>input{background:rgba(255,255,255,0.06)!important;border:1px solid rgba(255,255,255,0.15)!important;
  color:#ffffff!important;border-radius:10px!important;font-family:'DM Sans',sans-serif!important;font-size:0.95rem!important;}
.stNumberInput>div>div>input{background:rgba(255,255,255,0.06)!important;border:1px solid rgba(255,255,255,0.15)!important;
  color:#ffffff!important;border-radius:10px!important;font-size:1.1rem!important;font-weight:700!important;}
[data-testid="stMetricValue"]{color:#ffffff!important;font-size:1.6rem!important;font-weight:700!important;}
[data-testid="stMetricLabel"]{color:#94a3b8!important;font-size:0.85rem!important;font-weight:600!important;}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    line-height: 1.7 !important;
}
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    padding: 12px !important;
    margin-bottom: 10px !important;
}
input, textarea, [contenteditable] {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: #4ade80 !important;
}
[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.06) !important;
}
[data-testid="stChatInput"] > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInput"] textarea:active,
[data-testid="stChatInput"] textarea:hover {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: transparent !important;
    caret-color: #4ade80 !important;
    font-size: 1rem !important;
}
.stSlider>div>div>div{background:#4ade80!important;}
.stSlider label p{color:#94a3b8!important;font-weight:600!important;font-size:0.9rem!important;}
</style>
""", unsafe_allow_html=True)

# ── PDF Generator ──────────────────────────────────────────────────────────────
def generate_order_pdf(panel, quantity, unit_price, total, score, erp_ref, order_num):
    """Generate a professional order confirmation PDF and return as bytes."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        import io

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                                leftMargin=2*cm, rightMargin=2*cm)
        story = []
        styles = getSampleStyleSheet()

        GREEN = colors.HexColor("#1a6e2e")
        DARK  = colors.HexColor("#0a0f1e")
        LIGHT = colors.HexColor("#f8fafc")
        GRAY  = colors.HexColor("#64748b")
        BORDER= colors.HexColor("#e2e8f0")

        g    = panel["general"]
        comp = panel["compliance"]
        cf   = panel["carbon_footprint"]
        crm  = panel["critical_raw_materials"]
        perf = panel["performance"]
        sup  = panel["supplier"]
        eol  = panel["end_of_life"]

        # Header
        story.append(Paragraph("SolarPassport", ParagraphStyle("logo",
            fontSize=22, textColor=GREEN, fontName="Helvetica-Bold", spaceAfter=4)))
        story.append(Paragraph("PV Digital Product Passport · ERP Integration Platform",
            ParagraphStyle("sub", fontSize=10, textColor=GRAY, spaceAfter=2)))
        story.append(Paragraph("ViennaUP Europe Tech Hackathon 2026",
            ParagraphStyle("sub2", fontSize=9, textColor=GRAY, spaceAfter=16)))
        story.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=16))

        # Title
        story.append(Paragraph("ORDER CONFIRMATION", ParagraphStyle("title",
            fontSize=20, textColor=DARK, fontName="Helvetica-Bold", spaceAfter=10)))
        story.append(Paragraph(f"Order Number: <b>{order_num}</b>",
            ParagraphStyle("ordnum", fontSize=12, textColor=GREEN, spaceAfter=4)))
        story.append(Paragraph(f"ERP Reference: {erp_ref}",
            ParagraphStyle("ref", fontSize=10, textColor=GRAY, spaceAfter=4)))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%d %B %Y, %H:%M')}",
            ParagraphStyle("date", fontSize=10, textColor=GRAY, spaceAfter=20)))
        story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=20))

        # Order summary table
        story.append(Paragraph("ORDER SUMMARY", ParagraphStyle("sec",
            fontSize=11, textColor=GREEN, fontName="Helvetica-Bold", spaceAfter=10)))
        summary_data = [
            ["Field", "Details"],
            ["Product", f"{g['manufacturer']} — {g['model']}"],
            ["Technology", g["technology"]],
            ["Panel ID", panel["id"]],
            ["Quantity", f"{quantity:,} panels"],
            ["System Size", f"{quantity * g['power_wp'] / 1000:.1f} kWp"],
            ["Unit Price", f"€{unit_price:,.2f} per panel (€{g['price_per_wp_eur']}/Wp)"],
            ["Total Order Value", f"€{total:,.2f}"],
            ["DPP Procurement Score", f"{score}/100"],
            ["Order Status", "APPROVED"],
        ]
        t = Table(summary_data, colWidths=[5*cm, 12*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), GREEN),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,0), 10),
            ("BACKGROUND", (0,1), (-1,-1), LIGHT),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
            ("FONTSIZE",   (0,1), (-1,-1), 9),
            ("GRID",       (0,0), (-1,-1), 0.5, BORDER),
            ("FONTNAME",   (0,1), (0,-1), "Helvetica-Bold"),
            ("TEXTCOLOR",  (-1,8), (-1,8), GREEN),
            ("FONTNAME",   (-1,8), (-1,8), "Helvetica-Bold"),
            ("PADDING",    (0,0), (-1,-1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # Vendor info
        story.append(Paragraph("VENDOR INFORMATION", ParagraphStyle("sec2",
            fontSize=11, textColor=GREEN, fontName="Helvetica-Bold", spaceAfter=10)))
        vendor_data = [
            ["Field", "Details"],
            ["Supplier Name", sup["name"]],
            ["Country", sup["country"]],
            ["Ethics Score", f"{sup['ethics_score']}/100"],
            ["Third-Party Audited", "Yes" if sup.get("third_party_audited") else "No"],
            ["Audit Standard", sup.get("audit_standard", "N/A")],
            ["Forced Labour Risk", sup.get("forced_labour_risk", "N/A")],
            ["ISO 14001", "Yes" if sup.get("iso_14001") else "No"],
        ]
        t2 = Table(vendor_data, colWidths=[5*cm, 12*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), GREEN),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,0), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
            ("FONTSIZE",   (0,1), (-1,-1), 9),
            ("GRID",       (0,0), (-1,-1), 0.5, BORDER),
            ("FONTNAME",   (0,1), (0,-1), "Helvetica-Bold"),
            ("PADDING",    (0,0), (-1,-1), 8),
        ]))
        story.append(t2)
        story.append(Spacer(1, 20))

        # DPP Compliance data
        story.append(Paragraph("EU COMPLIANCE & DPP DATA", ParagraphStyle("sec3",
            fontSize=11, textColor=GREEN, fontName="Helvetica-Bold", spaceAfter=10)))
        dpp_data = [
            ["Requirement", "Status"],
            ["EU Compliance Status", comp["compliance_status"]],
            ["CE Marking", "✓ Present" if comp["ce_marked"] else "✗ Missing"],
            ["IEC 61215", "✓ Certified" if comp["iec_61215"] else "✗ Missing"],
            ["IEC 61730", "✓ Certified" if comp["iec_61730"] else "✗ Missing"],
            ["EU Ecodesign Regulation", "✓ Compliant" if comp["eu_ecodesign"] else "✗ Missing"],
            ["WEEE Directive", "✓ Registered" if comp["weee_compliant"] else "✗ Missing"],
            ["RoHS", "✓ Compliant" if comp["rohs_compliant"] else "✗ Missing"],
            ["Notified Body", comp["notified_body"]],
            ["Independent Verifier", comp["independent_verifier"]],
            ["Declaration of Conformity", comp["doc_reference"]],
            ["EPD Available", "Yes" if comp["epd_available"] else "No"],
        ]
        t3 = Table(dpp_data, colWidths=[7*cm, 10*cm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), GREEN),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,0), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
            ("FONTSIZE",   (0,1), (-1,-1), 9),
            ("GRID",       (0,0), (-1,-1), 0.5, BORDER),
            ("FONTNAME",   (0,1), (0,-1), "Helvetica-Bold"),
            ("PADDING",    (0,0), (-1,-1), 8),
        ]))
        story.append(t3)
        story.append(Spacer(1, 20))

        # Environmental & Technical
        story.append(Paragraph("ENVIRONMENTAL & TECHNICAL DATA", ParagraphStyle("sec4",
            fontSize=11, textColor=GREEN, fontName="Helvetica-Bold", spaceAfter=10)))
        env_data = [
            ["Parameter", "Value"],
            ["Carbon Footprint", f"{cf.get('per_wp_kg_co2e','N/A')} kg CO2e/Wp"],
            ["Carbon Performance Class", cf.get("performance_class", "N/A")],
            ["Renewable Manufacturing", "Yes — " + cf.get("renewable_source","") if cf.get("renewable_energy_used") else "No"],
            ["Carbon Payback Period", f"{cf.get('carbon_payback_years','N/A')} years"],
            ["Lifetime CO2 (per kWh)", f"{cf.get('per_kwh_lifetime_g_co2e','N/A')} g CO2e/kWh"],
            ["Panel Efficiency", f"{perf['efficiency_pct']}%"],
            ["Annual Degradation", f"{perf['degradation_annual_pct']}%/year"],
            ["Performance at 25 years", f"{perf['performance_at_25yr_pct']}%"],
            ["Performance Warranty", f"{g['warranty_years_performance']} years"],
            ["Product Warranty", f"{g['warranty_years_product']} years"],
            ["Silicon Origin", f"{crm['silicon_origin']} — {crm['silicon_risk']} risk"],
            ["Silver Content", f"{crm.get('silver_content_g_per_panel','N/A')}g per panel"],
            ["Lead Free", "Yes" if crm.get("lead_free") else "No"],
            ["Recyclability", f"{eol.get('recyclability_pct','N/A')}%"],
            ["Take-back Scheme", eol.get("take_back_scheme", "N/A")],
            ["Second Life Eligible", "Yes" if eol.get("second_life_eligible") else "No"],
        ]
        t4 = Table(env_data, colWidths=[7*cm, 10*cm])
        t4.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), GREEN),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,0), 10),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
            ("FONTSIZE",   (0,1), (-1,-1), 9),
            ("GRID",       (0,0), (-1,-1), 0.5, BORDER),
            ("FONTNAME",   (0,1), (0,-1), "Helvetica-Bold"),
            ("PADDING",    (0,0), (-1,-1), 8),
        ]))
        story.append(t4)
        story.append(Spacer(1, 24))

        story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=12))
        story.append(Paragraph(
            "This document was auto-generated by SolarPassport — PV DPP-ERP Platform. "
            "All data sourced from EU Digital Product Passport records. "
            "Compliant with EU Battery Regulation (2023/1542), IEC 61215, IEC 61730, WEEE Directive 2012/19/EU.",
            ParagraphStyle("footer", fontSize=8, textColor=GRAY, spaceAfter=4)))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')} UTC | ViennaUP Hackathon 2026",
            ParagraphStyle("footer2", fontSize=8, textColor=GRAY)))

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        return None

# ── DB ─────────────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(BASE_DIR / "pv_erp_database.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS purchase_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, order_date TEXT, panel_id TEXT,
        manufacturer TEXT, quantity INTEGER, unit_price_eur REAL, total_eur REAL,
        recommended_score REAL, reason TEXT, status TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS eol_decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, decision_date TEXT, panel_id TEXT,
        manufacturer TEXT, current_efficiency_pct REAL, decision TEXT,
        estimated_value_eur REAL, reason TEXT)""")
    conn.commit(); conn.close()

def save_po(pid,mfr,qty,unit,total,score,reason):
    conn=sqlite3.connect(BASE_DIR / "pv_erp_database.db")
    conn.execute("INSERT INTO purchase_orders (order_date,panel_id,manufacturer,quantity,unit_price_eur,total_eur,recommended_score,reason,status) VALUES (?,?,?,?,?,?,?,?,?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M"),pid,mfr,qty,unit,total,score,reason,"Approved"))
    conn.commit(); conn.close()

def save_eol(pid,mfr,eff,dec,val,reason):
    conn=sqlite3.connect(BASE_DIR / "pv_erp_database.db")
    conn.execute("INSERT INTO eol_decisions (decision_date,panel_id,manufacturer,current_efficiency_pct,decision,estimated_value_eur,reason) VALUES (?,?,?,?,?,?,?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M"),pid,mfr,eff,dec,val,reason))
    conn.commit(); conn.close()

def get_pos():
    conn=sqlite3.connect(BASE_DIR / "pv_erp_database.db")
    df=pd.read_sql_query("SELECT * FROM purchase_orders ORDER BY id DESC",conn); conn.close(); return df

def get_eols():
    conn=sqlite3.connect(BASE_DIR / "pv_erp_database.db")
    df=pd.read_sql_query("SELECT * FROM eol_decisions ORDER BY id DESC",conn); conn.close(); return df

init_db()

@st.cache_data
def load_passports():
    with open(BASE_DIR / "pv_passports.json") as f: data=json.load(f)
    return {p["id"]:p for p in data["panels"]}

passports=load_passports()

def score_panel(p,weights):
    g=p["general"];cf=p["carbon_footprint"];crm=p["critical_raw_materials"]
    comp=p["compliance"];sup=p["supplier"];perf=p["performance"];eol=p["end_of_life"]
    scores={};reasons={}
    if comp["compliance_status"]=="COMPLIANT" and comp["ce_marked"] and comp["iec_61215"] and comp["iec_61730"]:
        scores["compliance"]=100;reasons["compliance"]="Fully EU compliant"
    elif comp["compliance_status"]=="COMPLIANT":
        scores["compliance"]=65;reasons["compliance"]="Partially compliant"
    else:
        scores["compliance"]=0;reasons["compliance"]="NON-COMPLIANT"
    rm={"LOW":100,"NONE":100,"MEDIUM":55,"HIGH":15,"UNKNOWN":0}
    avg_risk=sum(rm.get(r,0) for r in [crm["silicon_risk"],crm["silver_risk"]])/2
    flm={"NONE":100,"LOW":80,"MEDIUM":40,"HIGH":0}
    ethics=(avg_risk*0.5)+(sup["ethics_score"]*0.3)+(flm.get(sup.get("forced_labour_risk","UNKNOWN"),20)*0.2)
    scores["ethics"]=round(ethics,1);reasons["ethics"]=f"Ethics {sup['ethics_score']}/100, Labour: {sup.get('forced_labour_risk','?')}"
    co2=cf.get("per_wp_kg_co2e")
    if co2 is None: scores["sustainability"]=0
    elif co2<=0.5: scores["sustainability"]=100
    elif co2<=0.75: scores["sustainability"]=78
    elif co2<=1.0: scores["sustainability"]=50
    else: scores["sustainability"]=20
    if cf.get("renewable_energy_used"): scores["sustainability"]=min(100,scores["sustainability"]+10)
    reasons["sustainability"]=f"{co2} kg CO2e/Wp" if co2 else "No data"
    eff=perf["efficiency_pct"];deg=perf["degradation_annual_pct"];warr=g["warranty_years_performance"];recycl=eol.get("recyclability_pct",50)
    scores["quality"]=round((min(eff,25)/25*100*0.35)+(max(0,1-deg)*100*0.25)+(min(warr,40)/40*100*0.20)+(recycl*0.20),1)
    reasons["quality"]=f"Eff: {eff}%, Deg: {deg}%/yr, {warr}yr warranty"
    price=g.get("price_per_wp_eur",1.0)
    if price<=0.25: scores["price"]=100
    elif price<=0.35: scores["price"]=80
    elif price<=0.50: scores["price"]=60
    elif price<=0.65: scores["price"]=35
    else: scores["price"]=15
    reasons["price"]=f"€{price}/Wp"
    total=sum(scores[k]*weights[k]/100 for k in scores)
    return {"total":round(total,1),"scores":scores,"reasons":reasons,"panel_id":p["id"],
            "manufacturer":g["manufacturer"],"model":g["model"],"price_per_wp":price,
            "efficiency_pct":eff,"power_wp":g["power_wp"],"compliance":comp["compliance_status"]}

def eol_decision(p):
    soh=p["state_of_health"];eol=p["end_of_life"];comp=p["compliance"];g=p["general"];perf=p["performance"]
    curr=soh["current_efficiency_pct"];orig=perf["efficiency_pct"];deg=soh["degradation_observed_pct"]
    age=soh["age_years"];hot=soh["hotspots_detected"];defects=soh["defects_detected"];ev=eol.get("estimated_eol_value_eur",0)
    if comp["compliance_status"]=="NON-COMPLIANT":
        return {"decision":"⚠️ QUARANTINE","decision_key":"quarantine","color":"#f87171","value_eur":0,
                "reason":"Non-compliant — missing IEC 61215/61730 + CE mark. Cannot be reinstalled in EU.",
                "action":"Contact compliance officer immediately."}
    elif curr>=orig*0.90 and not hot and not defects:
        return {"decision":"✅ CONTINUE","decision_key":"continue","color":"#4ade80","value_eur":ev*3,
                "reason":f"Efficiency {curr}% — {deg}% degradation over {age} years. No defects or hotspots.",
                "action":f"Continue operation. Next inspection 24 months. Residual value: €{ev*3:,.0f}"}
    elif curr>=orig*0.80 and not defects:
        return {"decision":"🔧 REPAIR","decision_key":"repair","color":"#fb923c","value_eur":ev*1.8,
                "reason":f"Efficiency {curr}% with {'hotspots — ' if hot else ''}moderate degradation ({deg}%).",
                "action":f"Inspect junction box. If repair < €{ev*0.6:,.0f}, proceed. Post-repair value: €{ev*1.8:,.0f}"}
    elif curr>=orig*0.70:
        return {"decision":"♻️ SECOND LIFE","decision_key":"second_life","color":"#22d3ee","value_eur":ev*2,
                "reason":f"Efficiency {curr}% — suitable for rural electrification or agriculture.",
                "action":f"List on secondary market. Estimated value: €{ev*2:,.0f}"}
    else:
        return {"decision":"🗑️ RECYCLE","decision_key":"recycle","color":"#64748b","value_eur":ev,
                "reason":f"Efficiency {curr}% critically degraded. Defects: {defects}. Hotspots: {hot}.",
                "action":f"PV Cycle EU. Glass, silicon, silver recovery. Value: €{ev:,.0f}"}

def build_context():
    lines=[]
    for pid,p in passports.items():
        g=p["general"];cf=p["carbon_footprint"];crm=p["critical_raw_materials"];comp=p["compliance"];soh=p["state_of_health"];eol=p["end_of_life"];sup=p["supplier"];perf=p["performance"]
        lines.append(f"PANEL {pid}: {g['manufacturer']} {g['model']} | {g['power_wp']}Wp @€{g['price_per_wp_eur']}/Wp | Efficiency: {perf['efficiency_pct']}% | Compliance: {comp['compliance_status']} | Carbon: {cf.get('per_wp_kg_co2e','?')} kg CO2e/Wp | Silicon: {crm['silicon_origin']} ({crm['silicon_risk']} risk) | Ethics: {sup['ethics_score']}/100 | Current efficiency: {soh['current_efficiency_pct']}% | Hotspots: {soh['hotspots_detected']}")
    return "\n".join(lines)

SYSTEM_PROMPT=f"""You are an expert AI procurement assistant for SolarPassport, a PV solar panel DPP-ERP platform used by a European energy company.

STRICT RULES:
- You ONLY answer questions about the 6 panels in this system. If asked about panels or suppliers NOT listed below, say: "That supplier is not in our system. Our database includes: LONGi Solar, Meyer Burger Technology, Jinko Solar, REC Group, SunPower (Maxeon Solar), and SolarMax Generic. Would you like me to compare these?"
- Never invent data. Only use the figures below.
- Be direct, specific, name actual panels, give real numbers. Under 200 words.

PANELS IN SYSTEM:
{build_context()}

GEOPOLITICAL KNOWLEDGE (use this when relevant):
- China controls ~85% of global silicon production and ~75% of solar panel manufacturing. Panels with silicon from China face HIGH supply chain concentration risk in any US-China trade dispute or tariff escalation.
- LONGi Solar (PV-001): Silicon from China, assembled in Austria. MEDIUM silicon risk. Partially exposed to China trade disruptions.
- Jinko Solar (PV-003): Both silicon AND silver from China. MEDIUM risk on both. Most exposed to China trade war of all panels in system.
- SolarMax Generic (PV-006): Unknown silicon origin. UNKNOWN risk. Avoid in any geopolitical uncertainty.
- Meyer Burger (PV-002): Silicon from Germany (Wacker Chemie), silver from EU recycled. LOW risk. Safest choice in a trade war.
- REC Group (PV-004): Silicon from Norway (REC Silicon). LOW risk. Good alternative.
- SunPower/Maxeon (PV-005): Silicon from France/Germany. LOW risk. Premium EU-sourced option.
- Taiwan: None of our 6 panels have primary manufacturing in Taiwan. Taiwan is a major semiconductor hub but not a primary solar panel manufacturer in our portfolio. If asked about Taiwan suppliers, clarify this and note that our EU-manufactured panels (Meyer Burger, Maxeon) are the safest geopolitically.
- Russia/Ukraine war: No direct material exposure in our panel database, but energy price volatility makes solar procurement more attractive.

ANSWER STYLE: Direct, data-driven, name specific panels with actual numbers. For geopolitical questions, clearly rank which panels are most/least at risk and why."""

if "page" not in st.session_state: st.session_state.page="Dashboard"
if "selected_panel" not in st.session_state: st.session_state.selected_panel=None
if "chat_msgs" not in st.session_state: st.session_state.chat_msgs=[]
if "order_panel" not in st.session_state: st.session_state.order_panel=None

def sc(s):
    if s>=75: return "sp-score-high"
    elif s>=50: return "sp-score-mid"
    return "sp-score-low"

def cbadge(status):
    if status=="COMPLIANT": return '<span class="sp-badge sp-badge-green">✓ Compliant</span>'
    return '<span class="sp-badge sp-badge-red">✗ Non-Compliant</span>'

# NAVBAR
erp_online=erp.is_online()
st.markdown(f"""
<div class="sp-navbar">
  <div style="display:flex;align-items:center;gap:10px">
    <span style="font-size:1.5rem">☀️</span>
    <span class="sp-logo-text">SolarPassport</span>
  </div>
  <div style="display:flex;align-items:center;gap:12px">
    <span style="font-size:0.78rem;color:#334155">ViennaUP Hackathon 2026</span>
    <div class="sp-erp-badge {'sp-erp-online' if erp_online else 'sp-erp-offline'}">
      <span class="sp-dot {'sp-dot-green' if erp_online else 'sp-dot-amber'}"></span>
      {'ERP-API Integrated ✓' if erp_online else 'ERP-API Offline'}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

pages=[("🏠","Dashboard"),("🛒","Procurement"),("♻️","End of Life"),("📊","Compliance"),("🌍","ESG Report"),("🤖","AI Assistant")]
nav_cols=st.columns([1,1,1,1,1,1,3])
for i,(icon,pname) in enumerate(pages):
    with nav_cols[i]:
        btn_type="primary" if st.session_state.page==pname else "secondary"
        if st.button(f"{icon} {pname}",key=f"nav_{pname}",use_container_width=True,type=btn_type):
            st.session_state.page=pname; st.session_state.selected_panel=None; st.rerun()

st.markdown("<div style='height:1px;background:rgba(255,255,255,0.06);margin-bottom:0'></div>", unsafe_allow_html=True)
page=st.session_state.page

# ══════════════════════════════════════════════════════════════════════════════
if page=="Dashboard":
    st.markdown('<div class="sp-page">', unsafe_allow_html=True)
    all_p=list(passports.values())
    compliant_count=sum(1 for p in all_p if p["compliance"]["compliance_status"]=="COMPLIANT")
    avg_eff=sum(p["performance"]["efficiency_pct"] for p in all_p)/len(all_p)
    sl=sum(1 for p in all_p if p["end_of_life"].get("second_life_eligible"))
    co2v=[p["carbon_footprint"]["per_wp_kg_co2e"] for p in all_p if p["carbon_footprint"].get("per_wp_kg_co2e")]
    st.markdown("""<div class="sp-hero"><div class="sp-hero-title">Solar Panel Intelligence</div>
    <div class="sp-hero-sub">EU DPP-ERP Platform · Procurement · End of Life · ESG · Compliance</div></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="sp-kpi-grid">
      <div class="sp-kpi"><div class="sp-kpi-label">Panels in System</div><div class="sp-kpi-value">{len(passports)}</div><div class="sp-kpi-sub">Across 5 manufacturers</div></div>
      <div class="sp-kpi"><div class="sp-kpi-label">EU Compliant</div><div class="sp-kpi-value">{compliant_count}/{len(passports)}</div><div class="sp-kpi-sub">IEC 61215 · IEC 61730 · WEEE</div></div>
      <div class="sp-kpi"><div class="sp-kpi-label">Avg Efficiency</div><div class="sp-kpi-value">{avg_eff:.1f}%</div><div class="sp-kpi-sub">Portfolio average</div></div>
      <div class="sp-kpi"><div class="sp-kpi-label">Second Life Eligible</div><div class="sp-kpi-value">{sl}/{len(passports)}</div><div class="sp-kpi-sub">Circular economy ready</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sp-section-title">All Panels</div>', unsafe_allow_html=True)
    search=st.text_input("","",placeholder="🔍  Search manufacturer, technology, ID...",label_visibility="collapsed")
    filtered={pid:p for pid,p in passports.items() if not search or
              search.lower() in p["general"]["manufacturer"].lower() or
              search.lower() in p["general"]["technology"].lower() or search.lower() in pid.lower()}
    dw={"compliance":25,"ethics":20,"sustainability":25,"quality":20,"price":10}
    # Score all panels and rank them for highlighting
    all_scored = sorted([score_panel(p, dw) for p in filtered.values()], key=lambda x: x["total"], reverse=True)
    rank_map = {}
    for idx, r in enumerate(all_scored):
        if idx == 0: rank_map[r["panel_id"]] = "best"
        elif idx == len(all_scored) - 1: rank_map[r["panel_id"]] = "worst"
        else: rank_map[r["panel_id"]] = "mid"

    cols=st.columns(3)
    for i,(pid,p) in enumerate(filtered.items()):
        g=p["general"];perf=p["performance"];comp=p["compliance"];cf=p["carbon_footprint"]
        scored=score_panel(p,dw);score=scored["total"]
        rank=rank_map.get(pid,"mid")
        per_panel_price = g["price_per_wp_eur"] * g["power_wp"]

        # Border and glow based on rank
        if rank=="best":
            card_border="rgba(74,222,128,0.5)"; card_bg="rgba(74,222,128,0.05)"; rank_label='<span class="sp-badge sp-badge-green" style="margin-bottom:8px">⭐ Best Choice</span>'
        elif rank=="worst":
            card_border="rgba(248,113,113,0.4)"; card_bg="rgba(248,113,113,0.04)"; rank_label='<span class="sp-badge sp-badge-red" style="margin-bottom:8px">⚠️ Least Optimal</span>'
        else:
            card_border="rgba(251,191,36,0.35)"; card_bg="rgba(251,191,36,0.04)"; rank_label='<span class="sp-badge sp-badge-amber" style="margin-bottom:8px">✓ Acceptable</span>'

        with cols[i%3]:
            st.markdown(f"""<div class="sp-panel-card" style="background:{card_bg};border-color:{card_border}">
              <div style="margin-bottom:6px">{rank_label}</div>
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px">
                <div><div class="sp-card-mfr">{g['manufacturer']}</div><div class="sp-card-model">{g['model'][:42]}</div></div>
                {cbadge(comp['compliance_status'])}
              </div>
              <div class="sp-card-stats">
                <div><div class="sp-stat-label">Power</div><div class="sp-stat-value">{g['power_wp']}Wp</div></div>
                <div><div class="sp-stat-label">Efficiency</div><div class="sp-stat-value">{perf['efficiency_pct']}%</div></div>
                <div><div class="sp-stat-label">Price/Panel</div><div class="sp-stat-value">€{per_panel_price:,.0f}</div></div>
                <div><div class="sp-stat-label">€/Wp</div><div class="sp-stat-value">€{g['price_per_wp_eur']}</div></div>
              </div>
              <div class="sp-score-label"><span>DPP Score</span><span style="font-family:'DM Mono',monospace;font-weight:700;color:#4ade80">{score}/100</span></div>
              <div class="sp-score-bar-bg"><div class="sp-score-bar-fill" style="width:{score}%"></div></div>
            </div>""", unsafe_allow_html=True)
            if st.button("View & Order →",key=f"view_{pid}",use_container_width=True):
                st.session_state.order_panel=pid; st.session_state.page="Procurement"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
elif page=="Procurement":
    st.markdown('<div class="sp-page">', unsafe_allow_html=True)
    st.markdown("""<div class="sp-hero"><div class="sp-hero-title">Procurement</div>
    <div class="sp-hero-sub">Select a panel · Review all DPP data · Place order</div></div>""", unsafe_allow_html=True)

    # ── Panel selector as horizontal tabs ──────────────────────────────────────
    panel_list = list(passports.items())
    tab_labels = [f"{p['general']['manufacturer'].split()[0]} ({pid})" for pid, p in panel_list]

    # Use selectbox styled nicely
    selected_pid = st.selectbox(
        "Choose a panel to review:",
        [pid for pid, _ in panel_list],
        format_func=lambda x: f"{passports[x]['general']['manufacturer']} — {passports[x]['general']['model']}",
        index=0 if not st.session_state.order_panel else [pid for pid,_ in panel_list].index(st.session_state.order_panel) if st.session_state.order_panel in [pid for pid,_ in panel_list] else 0
    )

    p = passports[selected_pid]
    g = p["general"]; perf = p["performance"]; comp = p["compliance"]
    cf = p["carbon_footprint"]; crm = p["critical_raw_materials"]
    sup = p["supplier"]; eol = p["end_of_life"]; soh = p["state_of_health"]
    unit_price = g["price_per_wp_eur"] * g["power_wp"]
    is_compliant = comp["compliance_status"] == "COMPLIANT"

    # ── Hero product header ────────────────────────────────────────────────────
    comp_color = "#4ade80" if is_compliant else "#f87171"
    comp_bg = "rgba(74,222,128,0.1)" if is_compliant else "rgba(248,113,113,0.1)"
    comp_border = "rgba(74,222,128,0.3)" if is_compliant else "rgba(248,113,113,0.3)"

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);
                border-radius:20px;padding:28px;margin:20px 0 28px 0">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px">
        <div>
          <div style="font-size:1.8rem;font-weight:800;color:#ffffff;letter-spacing:-0.5px;margin-bottom:4px">
            {g['manufacturer']}
          </div>
          <div style="font-size:1rem;color:#94a3b8;margin-bottom:12px">{g['model']}</div>
          <div style="display:flex;gap:10px;flex-wrap:wrap">
            <span style="background:{comp_bg};border:1px solid {comp_border};color:{comp_color};
                         padding:6px 14px;border-radius:8px;font-size:0.85rem;font-weight:700">
              {'✓ EU COMPLIANT' if is_compliant else '✗ NON-COMPLIANT'}
            </span>
            <span style="background:rgba(34,211,238,0.1);border:1px solid rgba(34,211,238,0.3);color:#22d3ee;
                         padding:6px 14px;border-radius:8px;font-size:0.85rem;font-weight:700">
              {g['technology']}
            </span>
            <span style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);color:#e2e8f0;
                         padding:6px 14px;border-radius:8px;font-size:0.85rem;font-weight:600">
              {selected_pid}
            </span>
          </div>
        </div>
        <div style="text-align:right">
          <div style="font-size:0.8rem;color:#64748b;margin-bottom:4px">PRICE PER PANEL</div>
          <div style="font-size:2.6rem;font-weight:800;color:#ffffff;font-family:'DM Mono',monospace;letter-spacing:-1px">€{unit_price:,.0f}</div>
          <div style="font-size:0.9rem;color:#64748b">€{g['price_per_wp_eur']}/Wp · {g['power_wp']}Wp</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 4 quick stat pills ─────────────────────────────────────────────────────
    def stat_pill(label, value, color="#ffffff", sub=None):
        sub_html = f'<div style="font-size:0.75rem;color:#64748b;margin-top:2px">{sub}</div>' if sub else ""
        return f"""<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
                    border-radius:14px;padding:18px 20px;flex:1;min-width:140px">
          <div style="font-size:0.72rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.8px;font-weight:600;margin-bottom:8px">{label}</div>
          <div style="font-size:1.6rem;font-weight:800;color:{color};font-family:'DM Mono',monospace">{value}</div>
          {sub_html}
        </div>"""

    st.markdown(f"""
    <div style="display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap">
      {stat_pill("Efficiency", f"{perf['efficiency_pct']}%", "#4ade80", f"Best in class: 24.1%")}
      {stat_pill("Carbon Class", cf.get('performance_class','N/A'), "#22d3ee", f"{cf.get('per_wp_kg_co2e','N/A')} kg CO₂e/Wp")}
      {stat_pill("Performance Warranty", f"{g['warranty_years_performance']}yr", "#a78bfa", f"{perf['degradation_annual_pct']}%/yr degradation")}
      {stat_pill("Recyclability", f"{eol.get('recyclability_pct','N/A')}%", "#fb923c", eol.get('take_back_scheme','N/A'))}
      {stat_pill("Ethics Score", f"{sup['ethics_score']}/100", "#f472b6", sup.get('audit_standard','N/A')[:20])}
    </div>
    """, unsafe_allow_html=True)

    # ── DPP DATA SECTIONS ──────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    def row(label, value, color="#ffffff"):
        return f'<div style="display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px solid rgba(255,255,255,0.06)"><span style="color:#94a3b8;font-size:0.9rem">{label}</span><span style="color:{color};font-weight:700;font-family:monospace;font-size:0.9rem">{value}</span></div>'

    def card(title, icon, content):
        st.markdown(f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:22px;margin-bottom:16px"><div style="font-size:1.05rem;font-weight:700;color:#ffffff;margin-bottom:14px">{icon} {title}</div>{content}</div>', unsafe_allow_html=True)

    with col1:
        card("Carbon Footprint", "🌿",
            row("Total Carbon Footprint", f"{cf.get('total_kg_co2e','N/A'):,} kg CO₂e" if cf.get('total_kg_co2e') else "Not declared", "#22d3ee" if cf.get('total_kg_co2e') else "#f87171") +
            row("Per Watt-peak", f"{cf.get('per_wp_kg_co2e','?')} kg CO₂e/Wp", "#4ade80" if cf.get('per_wp_kg_co2e') and cf['per_wp_kg_co2e']<=0.75 else "#fbbf24") +
            row("Lifetime Emissions", f"{cf.get('per_kwh_lifetime_g_co2e','N/A')} g CO₂e/kWh") +
            row("Performance Class", cf.get("performance_class","N/A"), "#4ade80" if cf.get("performance_class") in ["A+","A"] else "#fbbf24") +
            row("Renewable Manufacturing", "✓ Yes — " + cf.get("renewable_source","") if cf.get("renewable_energy_used") else "✗ No", "#4ade80" if cf.get("renewable_energy_used") else "#f87171") +
            row("Carbon Payback Period", f"{cf.get('carbon_payback_years','N/A')} years") +
            row("Manufacturing Share", f"{cf.get('manufacturing_pct','N/A')}% of total footprint")
        )

        card("Raw Materials & Supply Chain", "⛏️",
            row("Silicon Origin", crm['silicon_origin'], "#f87171" if crm['silicon_risk']=="HIGH" else "#fbbf24" if crm['silicon_risk']=="MEDIUM" else "#4ade80") +
            row("Silicon Risk", crm['silicon_risk'], "#f87171" if crm['silicon_risk']=="HIGH" else "#fbbf24" if crm['silicon_risk']=="MEDIUM" else "#4ade80") +
            row("Silver Content", f"{crm.get('silver_content_g_per_panel','N/A')}g per panel") +
            row("Silver Origin", crm['silver_origin'], "#f87171" if crm['silver_risk']=="HIGH" else "#fbbf24" if crm['silver_risk']=="MEDIUM" else "#4ade80") +
            row("Silver Risk", crm['silver_risk'], "#f87171" if crm['silver_risk']=="HIGH" else "#fbbf24" if crm['silver_risk']=="MEDIUM" else "#4ade80") +
            row("Lead Free", "✓ Yes" if crm.get("lead_free") else "✗ No", "#4ade80" if crm.get("lead_free") else "#f87171") +
            row("Conflict Mineral Free", "✓ Yes" if crm.get("conflict_mineral_free") else "✗ No", "#4ade80" if crm.get("conflict_mineral_free") else "#f87171")
        )

        card("Supplier & Ethics", "🤝",
            row("Supplier", sup['name']) +
            row("Country", sup['country']) +
            row("Ethics Score", f"{sup['ethics_score']}/100", "#4ade80" if sup['ethics_score']>=80 else "#fbbf24" if sup['ethics_score']>=60 else "#f87171") +
            row("Forced Labour Risk", sup.get("forced_labour_risk","N/A"), "#4ade80" if sup.get("forced_labour_risk") in ["NONE","LOW"] else "#f87171") +
            row("Third-Party Audit", ("✓ " + sup.get("audit_standard","")) if sup.get("third_party_audited") else "✗ Not audited", "#4ade80" if sup.get("third_party_audited") else "#f87171") +
            row("ISO 14001", "✓ Yes" if sup.get("iso_14001") else "✗ No", "#4ade80" if sup.get("iso_14001") else "#f87171") +
            row("ISO 45001", "✓ Yes" if sup.get("iso_45001") else "✗ No", "#4ade80" if sup.get("iso_45001") else "#f87171")
        )

    with col2:
        card("Technical Performance", "⚡",
            row("Panel Power", f"{g['power_wp']} Wp", "#4ade80") +
            row("Efficiency", f"{perf['efficiency_pct']}%", "#4ade80" if perf['efficiency_pct']>=22 else "#fbbf24") +
            row("Annual Degradation", f"{perf['degradation_annual_pct']}%/year", "#4ade80" if perf['degradation_annual_pct']<=0.4 else "#fbbf24") +
            row("Performance at 25 years", f"{perf['performance_at_25yr_pct']}%") +
            row("Temp. Coefficient", f"{perf['temperature_coefficient_pmax']}%/°C") +
            row("Bifacial", ("✓ Yes — factor " + str(perf.get('bifaciality_factor',''))) if perf.get('bifacial') else "✗ No", "#4ade80" if perf.get("bifacial") else "#94a3b8") +
            row("Product Warranty", f"{g['warranty_years_product']} years") +
            row("Performance Warranty", f"{g['warranty_years_performance']} years", "#4ade80")
        )

        card("EU Compliance & Certification", "📋",
            row("Compliance Status", comp['compliance_status'], "#4ade80" if is_compliant else "#f87171") +
            row("CE Marking", "✓ Present" if comp['ce_marked'] else "✗ Missing", "#4ade80" if comp['ce_marked'] else "#f87171") +
            row("IEC 61215", "✓ Certified" if comp['iec_61215'] else "✗ Missing", "#4ade80" if comp['iec_61215'] else "#f87171") +
            row("IEC 61730", "✓ Certified" if comp['iec_61730'] else "✗ Missing", "#4ade80" if comp['iec_61730'] else "#f87171") +
            row("EU Ecodesign", "✓ Compliant" if comp['eu_ecodesign'] else "✗ Missing", "#4ade80" if comp['eu_ecodesign'] else "#f87171") +
            row("WEEE Directive", "✓ Registered" if comp['weee_compliant'] else "✗ Missing", "#4ade80" if comp['weee_compliant'] else "#f87171") +
            row("RoHS / REACH", "✓ Both compliant" if comp['rohs_compliant'] and comp['reach_compliant'] else "✗ Missing", "#4ade80" if comp['rohs_compliant'] else "#f87171") +
            row("Notified Body", comp['notified_body']) +
            row("Independent Verifier", comp['independent_verifier']) +
            row("EPD Available", "✓ Yes" if comp['epd_available'] else "No", "#4ade80" if comp['epd_available'] else "#94a3b8")
        )

        card("End of Life & Circularity", "♻️",
            row("Recyclability", f"{eol.get('recyclability_pct','N/A')}%", "#4ade80" if eol.get('recyclability_pct',0)>=90 else "#fbbf24") +
            row("Glass Recovery", f"{eol.get('glass_recovery_pct','N/A')}%") +
            row("Silicon Recovery", f"{eol.get('silicon_recovery_pct','N/A')}%") +
            row("Silver Recovery", f"{eol.get('silver_recovery_pct','N/A')}%") +
            row("Aluminium Recovery", f"{eol.get('aluminium_recovery_pct','N/A')}%") +
            row("Take-back Scheme", eol.get("take_back_scheme","N/A")) +
            row("Available In", eol.get("take_back_network","N/A")) +
            row("Second Life", ("✓ " + eol.get("second_life_application","")) if eol.get("second_life_eligible") else "✗ Not eligible", "#4ade80" if eol.get("second_life_eligible") else "#94a3b8") +
            row("Est. EOL Value", f"€{eol.get('estimated_eol_value_eur',0):,.0f}", "#22d3ee") +
            row("WEEE Registration", ("✓ " + eol.get("weee_registration_number","")) if eol.get("weee_registered") else "✗ Not registered", "#4ade80" if eol.get("weee_registered") else "#f87171")
        )

    # ── ORDER FORM ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(74,222,128,0.08),rgba(34,211,238,0.05));
                border:2px solid rgba(74,222,128,0.35);border-radius:20px;padding:28px;margin-top:8px">
      <div style="font-size:1.3rem;font-weight:800;color:#ffffff;margin-bottom:4px">📦 Place Order</div>
      <div style="font-size:0.9rem;color:#64748b;margin-bottom:0">
        {g['manufacturer']} · {g['model']} · €{unit_price:,.0f}/panel
      </div>
    </div>
    """, unsafe_allow_html=True)

    oc1, oc2, oc3, oc4 = st.columns(4)
    with oc1:
        qty = st.number_input("Number of panels", min_value=1, max_value=100000, value=100, step=10)
    with oc2:
        st.metric("Price per panel", f"€{unit_price:,.0f}")
    with oc3:
        kwp = qty * g["power_wp"] / 1000
        st.metric("Total system size", f"{kwp:.1f} kWp")
    with oc4:
        tv = qty * unit_price
        st.metric("Total order value", f"€{tv:,.0f}")

    dw = {"compliance":25,"ethics":20,"sustainability":25,"quality":20,"price":10}
    sel_scored = score_panel(p, dw)
    reason = f"SolarPassport order. Score: {sel_scored['total']}/100. {g['power_wp']}Wp @ {perf['efficiency_pct']}% eff. Carbon: {cf.get('performance_class','N/A')}."

    if st.button("✅ Confirm Order & Generate PDF", type="primary"):
        import uuid
        order_num = f"SP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"
        save_po(selected_pid, g["manufacturer"], qty, unit_price, tv, sel_scored["total"], reason)
        er = erp.create_purchase_order(battery_id=selected_pid,
            battery_name=f"{g['manufacturer']} {g['model']}",
            supplier=g["manufacturer"], quantity=qty,
            unit_price=round(unit_price,2), score=sel_scored["total"], notes=reason)
        erp_ref = er["erp_reference"] if er["success"] else order_num

        st.success(f"✅ Order confirmed — **{order_num}**")
        pdf_bytes = generate_order_pdf(p, qty, unit_price, tv, sel_scored["total"], erp_ref, order_num)
        if pdf_bytes:
            st.download_button(
                label="📄 Download Order Confirmation PDF",
                data=pdf_bytes,
                file_name=f"SolarPassport_Order_{order_num}.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.warning("Install reportlab for PDF: `pip install reportlab`")

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
elif page=="End of Life":
    st.markdown('<div class="sp-page">', unsafe_allow_html=True)
    st.markdown("""<div class="sp-hero"><div class="sp-hero-title">End of Life Engine</div>
    <div class="sp-hero-sub">Data-driven · continue · repair · second life · recycle</div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="sp-section-title">Select Panel to Assess</div>', unsafe_allow_html=True)
    cols=st.columns(3)
    for i,(pid,p) in enumerate(passports.items()):
        soh=p["state_of_health"];g=p["general"];perf=p["performance"]
        dec=eol_decision(p)
        with cols[i%3]:
            is_sel=st.session_state.selected_panel==pid
            border="rgba(74,222,128,0.4)" if is_sel else "rgba(255,255,255,0.07)"
            st.markdown(f"""<div style="background:rgba(255,255,255,0.03);border:1px solid {border};border-radius:14px;padding:18px;margin-bottom:8px">
              <div style="font-weight:600;color:#e8edf5;margin-bottom:2px">{g['manufacturer']}</div>
              <div style="font-size:0.72rem;color:#475569;margin-bottom:12px">{pid}</div>
              <div style="display:flex;justify-content:space-between">
                <div><div style="font-size:0.65rem;color:#475569">Current Eff.</div>
                <div style="font-size:1.3rem;font-weight:700;color:#e8edf5;font-family:'DM Mono',monospace">{soh['current_efficiency_pct']}%</div></div>
                <div style="text-align:right"><div style="font-size:0.65rem;color:#475569">Age</div>
                <div style="font-size:1.3rem;font-weight:700;color:#e8edf5;font-family:'DM Mono',monospace">{soh['age_years']}yr</div></div>
              </div>
              <div style="margin-top:10px;font-size:0.8rem;font-weight:600;color:{dec['color']}">{dec['decision']}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Assess →",key=f"eol_{pid}",use_container_width=True):
                st.session_state.selected_panel=pid; st.rerun()

    if st.session_state.selected_panel:
        pid=st.session_state.selected_panel; p=passports[pid]
        soh=p["state_of_health"];eol=p["end_of_life"];g=p["general"];perf=p["performance"]
        dec=eol_decision(p)
        st.markdown(f"""<div style="background:{dec['color']}12;border:1px solid {dec['color']}40;border-radius:16px;padding:24px;margin:20px 0">
          <div style="font-size:1.5rem;font-weight:700;color:{dec['color']};margin-bottom:8px">{dec['decision']}</div>
          <div style="color:#cbd5e1;margin-bottom:6px">{dec['reason']}</div>
          <div style="color:#94a3b8;font-size:0.87rem"><b>Action:</b> {dec['action']}</div>
        </div>""", unsafe_allow_html=True)
        dc1,dc2,dc3,dc4=st.columns(4)
        dc1.metric("Original Efficiency",f"{perf['efficiency_pct']}%")
        dc2.metric("Current Efficiency",f"{soh['current_efficiency_pct']}%",delta=f"-{soh['degradation_observed_pct']}%")
        dc3.metric("Hotspots","⚠️ Yes" if soh["hotspots_detected"] else "✅ None")
        dc4.metric("Est. Value",f"€{dec['value_eur']:,.0f}")
        fig=go.Figure(go.Indicator(mode="gauge+number",value=soh["current_efficiency_pct"],
            title={"text":"Current Efficiency (%)","font":{"color":"#94a3b8","family":"DM Sans"}},
            number={"font":{"color":"#e8edf5","family":"DM Mono"},"suffix":"%"},
            gauge={"axis":{"range":[0,26],"tickcolor":"#475569"},"bar":{"color":dec["color"]},
                   "bgcolor":"rgba(0,0,0,0)","bordercolor":"rgba(255,255,255,0.1)",
                   "steps":[{"range":[0,perf["efficiency_pct"]*0.7],"color":"rgba(248,113,113,0.12)"},
                             {"range":[perf["efficiency_pct"]*0.7,perf["efficiency_pct"]*0.80],"color":"rgba(251,191,36,0.12)"},
                             {"range":[perf["efficiency_pct"]*0.80,26],"color":"rgba(74,222,128,0.08)"}],
                   "threshold":{"line":{"color":"#f87171","width":2},"thickness":0.75,"value":perf["efficiency_pct"]*0.80}}))
        fig.update_layout(height=250,paper_bgcolor="rgba(0,0,0,0)",font=dict(color="#94a3b8"),margin=dict(t=30,b=10,l=20,r=20))
        st.plotly_chart(fig,use_container_width=True)
        if st.button("💾 Record EOL Decision in ERP",type="primary"):
            save_eol(pid,g["manufacturer"],soh["current_efficiency_pct"],dec["decision"],dec["value_eur"],dec["reason"])
            er=erp.create_eol_decision(battery_id=pid,battery_name=f"{g['manufacturer']} {g['model']}",
                decision=dec["decision_key"],state_of_health=soh["current_efficiency_pct"],
                reason=dec["reason"],estimated_value=round(float(dec["value_eur"]),2))
            if er["success"]:
                st.success("✅ EOL Decision recorded!")
                st.markdown(f'<div class="sp-erp-ref">📋 ERP Reference: {er["erp_reference"]}</div>',unsafe_allow_html=True)
            else:
                st.success("✅ Saved locally")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
elif page=="Compliance":
    st.markdown('<div class="sp-page">', unsafe_allow_html=True)
    st.markdown("""<div class="sp-hero"><div class="sp-hero-title">Compliance Report</div>
    <div class="sp-hero-sub">IEC 61215 · IEC 61730 · EU Ecodesign · WEEE · RoHS · REACH</div></div>""", unsafe_allow_html=True)
    for pid,p in passports.items():
        comp=p["compliance"];g=p["general"];is_ok=comp["compliance_status"]=="COMPLIANT"
        border="rgba(74,222,128,0.25)" if is_ok else "rgba(248,113,113,0.25)"
        checks=[("CE",comp["ce_marked"]),("IEC 61215",comp["iec_61215"]),("IEC 61730",comp["iec_61730"]),
                ("Ecodesign",comp["eu_ecodesign"]),("WEEE",comp["weee_compliant"]),("RoHS",comp["rohs_compliant"]),("REACH",comp["reach_compliant"])]
        ch="".join([f'<span class="sp-badge {"sp-badge-green" if v else "sp-badge-red"}" style="margin:3px">{"✓" if v else "✗"} {k}</span>' for k,v in checks])
        with st.expander(f"{'✅' if is_ok else '❌'} {g['manufacturer']} — {pid}",expanded=not is_ok):
            st.markdown(f"""<div style="border:1px solid {border};border-radius:12px;padding:20px;background:rgba(255,255,255,0.02)">
              <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px">{ch}</div>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;font-size:0.84rem;color:#94a3b8">
                <div><span style="color:#475569">Notified Body: </span>{comp['notified_body']}</div>
                <div><span style="color:#475569">Verifier: </span>{comp['independent_verifier']}</div>
                <div><span style="color:#475569">EPD: </span>{'✅' if comp['epd_available'] else '⚠️ No'}</div>
              </div>
            </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
elif page=="ESG Report":
    st.markdown('<div class="sp-page">', unsafe_allow_html=True)
    st.markdown("""<div class="sp-hero"><div class="sp-hero-title">ESG Intelligence</div>
    <div class="sp-hero-sub">Auto-generated from Digital Product Passport data · Board-ready</div></div>""", unsafe_allow_html=True)
    all_p=list(passports.values())
    co2v=[p["carbon_footprint"]["per_wp_kg_co2e"] for p in all_p if p["carbon_footprint"].get("per_wp_kg_co2e")]
    eth=[p["supplier"]["ethics_score"] for p in all_p]
    rec=[p["end_of_life"]["recyclability_pct"] for p in all_p if p["end_of_life"].get("recyclability_pct")]
    ren=[p for p in all_p if p["carbon_footprint"].get("renewable_energy_used")]
    sl=[p for p in all_p if p["end_of_life"].get("second_life_eligible")]
    fl=sum(1 for p in all_p if p["supplier"].get("forced_labour_risk") in ["HIGH","MEDIUM"])
    aud=sum(1 for p in all_p if p["supplier"].get("third_party_audited"))
    comp_ok=sum(1 for p in all_p if p["compliance"]["compliance_status"]=="COMPLIANT")
    avg_co2=sum(co2v)/len(co2v) if co2v else 0
    avg_eth=sum(eth)/len(eth); avg_rec=sum(rec)/len(rec) if rec else 0; cp=comp_ok/len(all_p)*100
    e=min(100,round((max(0,100-avg_co2*80)*0.4)+(len(ren)/len(all_p)*100*0.35)+(avg_rec*0.25),1))
    s=min(100,round((avg_eth*0.5)+(max(0,100-fl*15)*0.3)+(aud/len(all_p)*100*0.2),1))
    gv=min(100,round((cp*0.7)+(aud/len(all_p)*100*0.3),1))
    tot=round((e+s+gv)/3,1)
    st.markdown(f"""<div class="sp-kpi-grid">
      <div class="sp-kpi" style="border-color:rgba(74,222,128,0.3)"><div class="sp-kpi-label">Overall ESG</div><div class="sp-kpi-value" style="color:#4ade80">{tot}</div><div class="sp-kpi-sub">out of 100</div></div>
      <div class="sp-kpi"><div class="sp-kpi-label">🌿 Environmental</div><div class="sp-kpi-value">{e}</div><div class="sp-kpi-sub">Carbon · Renewables · Recycling</div></div>
      <div class="sp-kpi"><div class="sp-kpi-label">🤝 Social</div><div class="sp-kpi-value">{s}</div><div class="sp-kpi-sub">Ethics · Labour · Audits</div></div>
      <div class="sp-kpi"><div class="sp-kpi-label">🏛️ Governance</div><div class="sp-kpi-value">{gv}</div><div class="sp-kpi-sub">Compliance · Certification</div></div>
    </div>""", unsafe_allow_html=True)
    c1,c2=st.columns([1,2])
    with c1:
        fig=go.Figure();fig.add_trace(go.Scatterpolar(r=[e,s,gv,e],theta=["Environmental","Social","Governance","Environmental"],
            fill="toself",fillcolor="rgba(74,222,128,0.1)",line=dict(color="#4ade80",width=2)))
        fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True,range=[0,100],gridcolor="rgba(255,255,255,0.08)",tickfont=dict(color="#475569")),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)",tickfont=dict(color="#94a3b8",size=12))),
            showlegend=False,paper_bgcolor="rgba(0,0,0,0)",height=300,margin=dict(t=20,b=20))
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        cd=[{"Manufacturer":p["general"]["manufacturer"],"kg CO2e/Wp":p["carbon_footprint"].get("per_wp_kg_co2e"),"Class":p["carbon_footprint"]["performance_class"]} for p in all_p if p["carbon_footprint"].get("per_wp_kg_co2e")]
        fig2=px.bar(pd.DataFrame(cd),x="Manufacturer",y="kg CO2e/Wp",color="Class",text="kg CO2e/Wp",
            color_discrete_map={"A+":"#4ade80","A":"#22d3ee","B":"#fbbf24","Not declared":"#f87171"})
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#94a3b8"),
            height=300,margin=dict(t=10,b=10,l=10,r=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
        st.plotly_chart(fig2,use_container_width=True)
    st.markdown(f"""<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:24px;margin-top:8px">
      <div style="font-size:0.95rem;font-weight:600;color:#4ade80;margin-bottom:14px">📋 Executive Summary</div>
      <p style="color:#94a3b8;line-height:1.7;margin-bottom:10px"><b style="color:#e8edf5">🌿 Environmental ({e}/100):</b> Avg {avg_co2:.2f} kg CO2e/Wp. {len(ren)}/{len(all_p)} use renewable manufacturing. Avg recyclability {avg_rec:.1f}%. {len(sl)} panels second-life eligible.</p>
      <p style="color:#94a3b8;line-height:1.7;margin-bottom:10px"><b style="color:#e8edf5">🤝 Social ({s}/100):</b> Avg ethics {avg_eth:.1f}/100. {fl} suppliers flagged for labour risk — silicon supply concentration in China is key exposure. {aud}/{len(all_p)} independently audited.</p>
      <p style="color:#94a3b8;line-height:1.7;margin-bottom:0"><b style="color:#e8edf5">🏛️ Governance ({gv}/100):</b> {cp:.0f}% EU compliance rate — IEC 61215, IEC 61730, WEEE verified. Recommend prioritising EU-manufactured panels (Meyer Burger, Maxeon) to achieve A+ carbon class.</p>
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
elif page=="AI Assistant":
    st.markdown('<div class="sp-page">', unsafe_allow_html=True)
    st.markdown("""<div class="sp-hero"><div class="sp-hero-title">AI Assistant</div>
    <div class="sp-hero-sub">Ask anything — procurement, ESG, supply chain risk, EOL decisions</div></div>""", unsafe_allow_html=True)
    if not st.session_state.chat_msgs:
        st.markdown("### 💡 Try asking:")
        suggestions=[
            "There is a trade war between the US and China. Which of our panels are at risk?",
            "Taiwan is in conflict. Are any of our panels affected?",
            "Which panel should I buy if I care about ethics and sustainability?",
            "Give me a full ESG summary of our portfolio.",
            "Which panel has the lowest carbon footprint per Wp?",
            "Which panels can be sold in the second-hand market after use?",
            "Compare Meyer Burger vs LONGi Solar on sustainability.",
            "Should I repair a panel with 14.8% efficiency and hotspots detected?",
        ]
        cols=st.columns(2)
        for i,s in enumerate(suggestions):
            with cols[i%2]:
                if st.button(s,key=f"sug_{i}",use_container_width=True):
                    st.session_state.chat_msgs.append({"role":"user","content":s}); st.rerun()
    for msg in st.session_state.chat_msgs:
        with st.chat_message(msg["role"],avatar="🤖" if msg["role"]=="assistant" else "👤"):
            st.markdown(msg["content"])
    user_input=st.chat_input("Ask about panels, procurement, EOL, ESG, geopolitical risk...")
    if user_input:
        st.session_state.chat_msgs.append({"role":"user","content":user_input})
        with st.chat_message("user",avatar="👤"): st.markdown(user_input)
        with st.chat_message("assistant",avatar="🤖"):
            with st.spinner("Thinking..."):
                try:

                    msgs=[{"role":m["role"],"content":m["content"]} for m in st.session_state.chat_msgs]
                    r=_requests.post("https://api.groq.com/openai/v1/chat/completions",
                        headers={"Content-Type":"application/json","Authorization":f"Bearer {GROQ_API_KEY}"},
                        json={"model":"llama-3.3-70b-versatile","max_tokens":1000,
                              "messages":[{"role":"system","content":SYSTEM_PROMPT},*msgs]},timeout=30)
                    r.raise_for_status(); reply=r.json()["choices"][0]["message"]["content"]
                except Exception as ex: reply=f"⚠️ AI unavailable: {str(ex)}"
            st.markdown(reply)
            st.session_state.chat_msgs.append({"role":"assistant","content":reply})
    if st.session_state.chat_msgs:
        if st.button("🗑️ Clear chat"): st.session_state.chat_msgs=[]; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""<div style="text-align:center;padding:20px;color:#1e293b;font-size:0.75rem;
  border-top:1px solid rgba(255,255,255,0.04);margin-top:20px">
  ☀️ SolarPassport · ViennaUP Hackathon 2026 · EU Ecodesign · IEC 61215 · IEC 61730 · WEEE
</div>""", unsafe_allow_html=True)
