import streamlit as st
import pandas as pd
from datetime import date
from utils.styles import apply_styles, load_latest, render_hero, badge
from utils.live_forecast import load_live_latest

st.set_page_config(
    page_title="BeachGuard",
    page_icon="🌊",
    layout="wide"
)
apply_styles()

OFFICIAL_URL = "https://www.smchealth.org/beaches"
SITE_LAT = 37.5602
SITE_LON = -122.2910

live_prediction = True
live_error = None

try:
    latest = load_live_latest()

except Exception as exc:

    live_prediction = False
    live_error = exc

    try:
        latest = load_latest()

    except Exception:
        st.error(
            "Prediction data unavailable. "
            "Check the official advisory."
        )
        st.stop()

render_hero(latest)

prediction_date = latest["prediction_date"]
updated_date = latest["data_last_updated"]
updated_str = updated_date.strftime("%b %d, %Y") if pd.notna(updated_date) else "Unknown"
model_ver = str(latest["model_version"]).upper()

ecoli_risk = str(latest["e_coli_risk"]).strip()
ecoli_prob = float(latest["e_coli_probability"])
ecoli_cls = {"Safe": "safe", "Caution": "caution", "Unsafe": "unsafe"}.get(ecoli_risk, "safe")

entero_risk = str(latest["enterococcus_risk"]).strip()
entero_prob = float(latest["enterococcus_probability"])
entero_cls = {"Safe": "safe", "Caution": "caution", "Unsafe": "unsafe"}.get(entero_risk, "safe")

freshness_html = ""
if pd.notna(updated_date):
    days_old = (pd.Timestamp(date.today()) - updated_date.normalize()).days
    if 1 < days_old <= 3:
        freshness_html = f'<div class="bg-freshness warn">Data is {days_old} days old — last updated {updated_date.strftime("%b %d, %Y")}.</div>'
    elif days_old > 3:
        freshness_html = f'<div class="bg-freshness error">Outdated data — last updated {updated_date.strftime("%b %d, %Y")}.</div>'

st.html(f"""
<div class="bg-content">
    <div class="bg-stat-row">
        <div class="bg-stat">
            <p class="bg-stat-label">Prediction Date</p>
            <p class="bg-stat-value">{prediction_date.strftime("%b %d, %Y")}</p>
        </div>
        <div class="bg-stat">
            <p class="bg-stat-label">Data Last Updated</p>
            <p class="bg-stat-value">{updated_str}</p>
        </div>
        <div class="bg-stat">
            <p class="bg-stat-label">Model Version</p>
            <p class="bg-stat-value">{model_ver}</p>
        </div>
    </div>
    {freshness_html}
    <p class="bg-section-header">Water Quality Risk</p>
    <div class="bg-card-row">
        <div class="bg-card {ecoli_cls}">
            <p class="bg-card-name">E. coli</p>
            {badge(ecoli_risk)}
            <p class="bg-card-prob">{ecoli_prob:.0%}</p>
            <p class="bg-card-sublabel">exceedance probability</p>
            <p class="bg-card-threshold">
                Threshold: 235 MPN/100 mL<br>
                Safe &lt;10% &nbsp;·&nbsp; Caution 10–50% &nbsp;·&nbsp; Unsafe ≥50%
            </p>
        </div>
        <div class="bg-card {entero_cls}">
            <p class="bg-card-name">Enterococcus</p>
            {badge(entero_risk)}
            <p class="bg-card-prob">{entero_prob:.0%}</p>
            <p class="bg-card-sublabel">exceedance probability</p>
            <p class="bg-card-threshold">
                Threshold: 130 MPN/100 mL<br>
                Safe &lt;40% &nbsp;·&nbsp; Caution 40–85% &nbsp;·&nbsp; Unsafe ≥85%
            </p>
        </div>
    </div>
    <p class="bg-section-header">Pilot Site</p>
</div>
""")

col_l, col_c, col_r = st.columns([1, 10, 1])
with col_c:
    map_data = pd.DataFrame({"lat": [SITE_LAT], "lon": [SITE_LON]})
    st.map(map_data, zoom=13)

st.markdown(f"""
<div class="bg-content">
    <p class="bg-map-label">
        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none"
        stroke="#9CA3AF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
        Parkside Aquatic Park, San Mateo, California
    </p>
    <div class="bg-footer">
        BeachGuard &nbsp;·&nbsp; Experimental research prototype &nbsp;·&nbsp;
        <a href="{OFFICIAL_URL}" target="_blank" style="color:#6B7280;">Official Advisories</a>
    </div>
</div>
""", unsafe_allow_html=True)

