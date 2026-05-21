"""
ui.py — HTML template functions for Battery DPP-ERP app
"""

CSS = """<style>
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
    .erp-ref-box { background:#e8f4fd; border-left:4px solid #00B4D8;
        padding:12px 16px; border-radius:8px; font-family:monospace;
        font-size:1.05em; margin:10px 0; color:#0D1B3E; }
</style>"""


def main_header(title: str, subtitle: str, note: str = "") -> str:
    note_html = f"<p><small>{note}</small></p>" if note else ""
    return f"""<div class="main-header">
    <h2>{title}</h2>
    <p>{subtitle}</p>
    {note_html}</div>"""


def section_title(text: str) -> str:
    return f'<div class="section-title">{text}</div>'


def compliant_div(content: str) -> str:
    return f'<div class="compliant">{content}</div>'


def non_compliant_div(content: str) -> str:
    return f'<div class="non-compliant">{content}</div>'


def recommend_card(manufacturer: str, model: str, score: float, price: float, compliance: str) -> str:
    return f"""<div class="recommend-card">
    <h3>🏆 RECOMMENDED: {manufacturer}</h3>
    <h4>{model}</h4>
    <p><b>Composite Score: {score}/100</b> | Price: €{price}/kWh | Compliance: {compliance}</p>
</div>"""


def erp_ref_box(erp_reference: str) -> str:
    return f'<div class="erp-ref-box">📋 ERP Reference: <b>{erp_reference}</b></div>'


def eol_banner(color: str, decision: str, reason: str, action: str) -> str:
    return (
        f'<div style="background:{color}20; border-left:6px solid {color}; '
        f'padding:20px; border-radius:10px; margin:15px 0;">'
        f'<h2 style="color:{color}; margin:0;">{decision}</h2>'
        f'<p style="margin:8px 0 0 0;">{reason}</p>'
        f'<p style="margin:4px 0 0 0;"><b>Action:</b> {action}</p>'
        f'</div>'
    )


def decision_path_row(label: str, path: str, color: str, active: bool) -> str:
    prefix = "→ " if active else "   "
    if active:
        style = (f"background:{color}20; border-left:3px solid {color}; "
                 f"padding:6px 12px; border-radius:4px; margin:3px 0;")
    else:
        style = "padding:6px 12px; color:#aaa; margin:3px 0;"
    return f'<div style="{style}">{prefix}<b>{label}</b>: {path}</div>'


def esg_summary(esg_total: float, e_score: float, s_score: float, g_score: float,
                avg_co2: float, n_renewable: int, n_batteries: int, avg_recycl: float,
                n_second_life: int, avg_ethics: float, high_risk_count: int,
                audited: int, compliance_pct: float, ce_count: int, doc_count: int) -> str:
    recommendation = (
        "Portfolio meets baseline EU sustainability requirements. Focus on reducing carbon "
        "intensity and eliminating high-risk material sources."
        if esg_total >= 65 else
        "Portfolio requires improvement in compliance and supply chain ethics "
        "before 2027 mandatory DPP enforcement."
    )
    return f"""<div style="background:#f8f9fa; border-left:6px solid #0D1B3E; padding:24px; border-radius:10px; margin:10px 0;">
    <h4 style="color:#0D1B3E; margin:0 0 12px 0;">Portfolio ESG Rating: {esg_total}/100</h4>
    <p><b>🌿 Environmental ({e_score}/100):</b> Portfolio average carbon intensity is {avg_co2:.1f} kg CO2e/kWh.
    {n_renewable} of {n_batteries} batteries use renewable energy in production.
    Average recyclability is {avg_recycl:.1f}%. {n_second_life} batteries are eligible for second life deployment.</p>
    <p><b>🤝 Social ({s_score}/100):</b> Average supplier ethics score is {avg_ethics:.1f}/100.
    {high_risk_count} high-risk raw material sources flagged (conflict mineral exposure).
    {audited} of {n_batteries} suppliers are third-party audited.</p>
    <p><b>🏛️ Governance ({g_score}/100):</b> {compliance_pct:.0f}% of batteries are fully EU compliant
    under Regulation (EU) 2023/1542. {ce_count} carry CE marking. {doc_count} have valid
    Declaration of Conformity on file.</p>
    <p style="margin:0;"><b>Recommendation:</b> {recommendation}</p>
</div>"""


def footer() -> str:
    return (
        '<div style="text-align:center; color:#6c757d; font-size:0.85em;">'
        '🔋 DPP-ERP Integration | ViennaUP Europe Tech Hackathon 2026 | '
        'EU Battery Regulation Reg. (EU) 2023/1542'
        '</div>'
    )
