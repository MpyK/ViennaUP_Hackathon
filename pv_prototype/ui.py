"""
ui.py — HTML templates and CSS for SolarPassport.
All raw HTML lives here. pv_app.py stays logic-only.
"""

# ── Styles ─────────────────────────────────────────────────────────────────────

CSS = """
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
"""

# ── Small helpers ──────────────────────────────────────────────────────────────

def sc(s):
    if s >= 75:
        return "sp-score-high"
    elif s >= 50:
        return "sp-score-mid"
    return "sp-score-low"


def cbadge(status):
    if status == "COMPLIANT":
        return '<span class="sp-badge sp-badge-green">✓ Compliant</span>'
    return '<span class="sp-badge sp-badge-red">✗ Non-Compliant</span>'


# ── Layout components ──────────────────────────────────────────────────────────

def navbar(erp_online: bool) -> str:
    return f"""
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
</div>"""


def hero(title: str, subtitle: str) -> str:
    return f'<div class="sp-hero"><div class="sp-hero-title">{title}</div><div class="sp-hero-sub">{subtitle}</div></div>'


def section_title(text: str) -> str:
    return f'<div class="sp-section-title">{text}</div>'


def kpi_item(label: str, value, sub: str = "", border_color: str = None, value_color: str = None) -> str:
    border_style = f"border-color:{border_color};" if border_color else ""
    value_style = f"color:{value_color};" if value_color else ""
    return (f'<div class="sp-kpi" style="{border_style}">'
            f'<div class="sp-kpi-label">{label}</div>'
            f'<div class="sp-kpi-value" style="{value_style}">{value}</div>'
            f'<div class="sp-kpi-sub">{sub}</div>'
            f'</div>')


def kpi_grid(*items: str) -> str:
    return f'<div class="sp-kpi-grid">{"".join(items)}</div>'


def footer() -> str:
    return """<div style="text-align:center;padding:20px;color:#1e293b;font-size:0.75rem;
  border-top:1px solid rgba(255,255,255,0.04);margin-top:20px">
  ☀️ SolarPassport · ViennaUP Hackathon 2026 · EU Ecodesign · IEC 61215 · IEC 61730 · WEEE
</div>"""


# ── Reusable card primitives ───────────────────────────────────────────────────

def row(label, value, color="#ffffff") -> str:
    return (f'<div style="display:flex;justify-content:space-between;padding:11px 0;'
            f'border-bottom:1px solid rgba(255,255,255,0.06)">'
            f'<span style="color:#94a3b8;font-size:0.9rem">{label}</span>'
            f'<span style="color:{color};font-weight:700;font-family:monospace;font-size:0.9rem">{value}</span>'
            f'</div>')


def card_html(title: str, icon: str, content: str) -> str:
    return (f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);'
            f'border-radius:16px;padding:22px;margin-bottom:16px">'
            f'<div style="font-size:1.05rem;font-weight:700;color:#ffffff;margin-bottom:14px">{icon} {title}</div>'
            f'{content}</div>')


def stat_pill(label: str, value, color: str = "#ffffff", sub: str = None) -> str:
    sub_html = (f'<div style="font-size:0.75rem;color:#64748b;margin-top:2px">{sub}</div>' if sub else "")
    return (f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);'
            f'border-radius:14px;padding:18px 20px;flex:1;min-width:140px">'
            f'<div style="font-size:0.72rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.8px;'
            f'font-weight:600;margin-bottom:8px">{label}</div>'
            f'<div style="font-size:1.6rem;font-weight:800;color:{color};font-family:\'DM Mono\',monospace">{value}</div>'
            f'{sub_html}</div>')


# ── Page-specific components ───────────────────────────────────────────────────

def panel_card(pid: str, g: dict, perf: dict, comp: dict, cf: dict, score: float, rank: str) -> str:
    per_panel_price = g["price_per_wp_eur"] * g["power_wp"]
    if rank == "best":
        border = "rgba(74,222,128,0.5)"
        bg = "rgba(74,222,128,0.05)"
        rank_label = '<span class="sp-badge sp-badge-green" style="margin-bottom:8px">⭐ Best Choice</span>'
    elif rank == "worst":
        border = "rgba(248,113,113,0.4)"
        bg = "rgba(248,113,113,0.04)"
        rank_label = '<span class="sp-badge sp-badge-red" style="margin-bottom:8px">⚠️ Least Optimal</span>'
    else:
        border = "rgba(251,191,36,0.35)"
        bg = "rgba(251,191,36,0.04)"
        rank_label = '<span class="sp-badge sp-badge-amber" style="margin-bottom:8px">✓ Acceptable</span>'

    return (f'<div class="sp-panel-card" style="background:{bg};border-color:{border}">'
            f'<div style="margin-bottom:6px">{rank_label}</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px">'
            f'<div><div class="sp-card-mfr">{g["manufacturer"]}</div>'
            f'<div class="sp-card-model">{g["model"][:42]}</div></div>'
            f'{cbadge(comp["compliance_status"])}</div>'
            f'<div class="sp-card-stats">'
            f'<div><div class="sp-stat-label">Power</div><div class="sp-stat-value">{g["power_wp"]}Wp</div></div>'
            f'<div><div class="sp-stat-label">Efficiency</div><div class="sp-stat-value">{perf["efficiency_pct"]}%</div></div>'
            f'<div><div class="sp-stat-label">Price/Panel</div><div class="sp-stat-value">€{per_panel_price:,.0f}</div></div>'
            f'<div><div class="sp-stat-label">€/Wp</div><div class="sp-stat-value">€{g["price_per_wp_eur"]}</div></div>'
            f'</div>'
            f'<div class="sp-score-label"><span>DPP Score</span>'
            f'<span style="font-family:\'DM Mono\',monospace;font-weight:700;color:#4ade80">{score}/100</span></div>'
            f'<div class="sp-score-bar-bg"><div class="sp-score-bar-fill" style="width:{score}%"></div></div>'
            f'</div>')


def product_header(g: dict, comp: dict, selected_pid: str, unit_price: float) -> str:
    is_compliant = comp["compliance_status"] == "COMPLIANT"
    comp_color = "#4ade80" if is_compliant else "#f87171"
    comp_bg = "rgba(74,222,128,0.1)" if is_compliant else "rgba(248,113,113,0.1)"
    comp_border = "rgba(74,222,128,0.3)" if is_compliant else "rgba(248,113,113,0.3)"
    return f"""
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
</div>"""


def order_header(g: dict, unit_price: float) -> str:
    return f"""
<div style="background:linear-gradient(135deg,rgba(74,222,128,0.08),rgba(34,211,238,0.05));
            border:2px solid rgba(74,222,128,0.35);border-radius:20px;padding:28px;margin-top:8px">
  <div style="font-size:1.3rem;font-weight:800;color:#ffffff;margin-bottom:4px">📦 Place Order</div>
  <div style="font-size:0.9rem;color:#64748b;margin-bottom:0">
    {g['manufacturer']} · {g['model']} · €{unit_price:,.0f}/panel
  </div>
</div>"""


def eol_mini_card(pid: str, g: dict, soh: dict, dec: dict, is_selected: bool) -> str:
    border = "rgba(74,222,128,0.4)" if is_selected else "rgba(255,255,255,0.07)"
    return (f'<div style="background:rgba(255,255,255,0.03);border:1px solid {border};'
            f'border-radius:14px;padding:18px;margin-bottom:8px">'
            f'<div style="font-weight:600;color:#e8edf5;margin-bottom:2px">{g["manufacturer"]}</div>'
            f'<div style="font-size:0.72rem;color:#475569;margin-bottom:12px">{pid}</div>'
            f'<div style="display:flex;justify-content:space-between">'
            f'<div><div style="font-size:0.65rem;color:#475569">Current Eff.</div>'
            f'<div style="font-size:1.3rem;font-weight:700;color:#e8edf5;font-family:\'DM Mono\',monospace">{soh["current_efficiency_pct"]}%</div></div>'
            f'<div style="text-align:right"><div style="font-size:0.65rem;color:#475569">Age</div>'
            f'<div style="font-size:1.3rem;font-weight:700;color:#e8edf5;font-family:\'DM Mono\',monospace">{soh["age_years"]}yr</div></div>'
            f'</div>'
            f'<div style="margin-top:10px;font-size:0.8rem;font-weight:600;color:{dec["color"]}">{dec["decision"]}</div>'
            f'</div>')
