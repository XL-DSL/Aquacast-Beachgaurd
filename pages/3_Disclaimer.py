import streamlit as st
from utils.styles import apply_styles

st.set_page_config(page_title="Disclaimer · BeachGuard", page_icon="🌊", layout="wide")
apply_styles()

OFFICIAL_URL = "https://www.smchealth.org/beaches"

st.markdown(
    f"""
    <div class="bg-content">
        <h1 style="font-size:2rem;font-weight:800;letter-spacing:-0.02em;margin:0 0 0.25rem 0;">
            Disclaimer &amp; Data Notes
        </h1>
        <p style="color:#6B7280;font-size:0.95rem;margin:0 0 2.5rem 0;">
            Important information before using this forecast
        </p>

        <div class="bg-disclaimer-box">
            <strong>Experimental Forecast</strong><br><br>
            BeachGuard / AquaCast is a research prototype. The risk classifications displayed
            represent model-estimated probabilities and do not constitute an official determination
            that the water is safe or unsafe for swimming. AquaCast does not directly measure
            current water conditions and should never replace official monitoring, laboratory
            results, or public-health advisories issued by San Mateo County.
        </div>

        <a class="bg-advisory-btn" href="{OFFICIAL_URL}" target="_blank">
            Check Official Water-Quality Advisories →
        </a>

        <p class="bg-section-header">Data Notes</p>
        <div class="bg-data-notes">
            Predictions are generated from the AquaCast ML pipeline (Version 12) using historical
            bacterial monitoring data and environmental predictors for Parkside Aquatic Park,
            San Mateo County, California. Data lineage, model selection criteria, and training
            methodology are documented in the project repository. For official current conditions,
            always refer to San Mateo County Environmental Health.
        </div>

        <div class="bg-footer">BeachGuard &nbsp;·&nbsp; Experimental research prototype</div>
    </div>
    """,
    unsafe_allow_html=True,
)
