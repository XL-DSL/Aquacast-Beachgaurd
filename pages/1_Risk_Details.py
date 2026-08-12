import streamlit as st
from utils.styles import apply_styles, load_latest, render_hero, badge

st.set_page_config(page_title="Risk Details · BeachGuard", page_icon="🌊", layout="wide")
apply_styles()

OFFICIAL_URL = "https://www.smchealth.org/beaches"

try:
    latest = load_latest()
except Exception:
    st.markdown(
        '<div class="bg-content"><div class="bg-freshness error">Prediction data unavailable.</div></div>',
        unsafe_allow_html=True,
    )
    st.stop()

render_hero(latest)

ecoli_risk = str(latest["e_coli_risk"]).strip()
ecoli_prob = float(latest["e_coli_probability"])
ecoli_cls = {"Safe": "safe", "Caution": "caution", "Unsafe": "unsafe"}.get(ecoli_risk, "safe")

entero_risk = str(latest["enterococcus_risk"]).strip()
entero_prob = float(latest["enterococcus_probability"])
entero_cls = {"Safe": "safe", "Caution": "caution", "Unsafe": "unsafe"}.get(entero_risk, "safe")

st.markdown(
    f"""
    <div class="bg-content">
        <p class="bg-section-header">Bacteria-Specific Risk</p>

        <div class="bg-detail-card">
            <p class="bg-card-name">E. coli</p>
            {badge(ecoli_risk)}
            <p class="bg-card-prob" style="font-size:3rem;font-weight:800;letter-spacing:-0.03em;
               color:{'#2E7D32' if ecoli_cls=='safe' else '#F57F17' if ecoli_cls=='caution' else '#C62828'};">
               {ecoli_prob:.0%}
            </p>
            <p class="bg-card-sublabel">exceedance probability</p>
            <p><strong>Regulatory threshold:</strong> 235 MPN/100 mL</p>
            <p><strong>Risk thresholds:</strong> Safe &lt;10% &nbsp;·&nbsp; Caution 10–50% &nbsp;·&nbsp; Unsafe ≥50%</p>
            <p>E. coli is an indicator of fecal contamination in recreational water.
            Elevated levels suggest a higher likelihood of illness from water contact.
            This probability reflects the model's estimate that current conditions
            exceed the 235 MPN/100 mL standard.</p>
        </div>

        <div class="bg-detail-card">
            <p class="bg-card-name">Enterococcus</p>
            {badge(entero_risk)}
            <p class="bg-card-prob" style="font-size:3rem;font-weight:800;letter-spacing:-0.03em;
               color:{'#2E7D32' if entero_cls=='safe' else '#F57F17' if entero_cls=='caution' else '#C62828'};">
               {entero_prob:.0%}
            </p>
            <p class="bg-card-sublabel">exceedance probability</p>
            <p><strong>Regulatory threshold:</strong> 130 MPN/100 mL</p>
            <p><strong>Risk thresholds:</strong> Safe &lt;40% &nbsp;·&nbsp; Caution 40–85% &nbsp;·&nbsp; Unsafe ≥85%</p>
            <p>Enterococcus is the primary indicator bacterium for marine and estuarine
            recreational waters. Elevated levels are associated with gastrointestinal
            illness and other health risks from water contact.</p>
        </div>

        <div class="bg-explainer">
            <strong>How are thresholds determined?</strong><br>
            The 235 MPN/100 mL E. coli and 130 MPN/100 mL Enterococcus thresholds are set by
            the U.S. EPA and adopted by California water-quality standards for recreational waters.
            Exceeding these levels is associated with a statistically elevated risk of illness
            among swimmers and other water-contact recreationists.
        </div>

        <div class="bg-footer">
            <a href="{OFFICIAL_URL}" target="_blank" style="color:#6B7280;">
                Official Water-Quality Advisories →
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
