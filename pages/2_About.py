import streamlit as st
from utils.styles import apply_styles

st.set_page_config(page_title="About · BeachGuard", page_icon="🌊", layout="wide")
apply_styles()

st.markdown(
    """
    <div class="bg-content">
        <h1 style="font-size:2rem;font-weight:800;letter-spacing:-0.02em;margin:0 0 0.25rem 0;">
            About BeachGuard
        </h1>
        <p style="color:#6B7280;font-size:0.95rem;margin:0 0 2.5rem 0;">
            How AquaCast works and what the risk levels mean
        </p>

        <div class="bg-about-section">
            <h2>What AquaCast Predicts</h2>
            <p>
                AquaCast estimates the probability that bacterial levels at Parkside Aquatic Park
                will exceed elevated-risk thresholds for E. coli and Enterococcus.
                It uses historical bacterial monitoring data combined with environmental predictors
                to produce a risk forecast — not a direct water measurement.
            </p>
        </div>

        <div class="bg-about-section">
            <h2>How the Model Works</h2>
            <p>
                The models were developed using chronological training, validation, and test periods
                rather than randomly mixing past and future observations — a method designed to reflect
                real-world forecasting conditions. The pipeline evaluates multiple machine-learning
                configurations and selects the best-performing model for each bacterium.
                Model version and prediction date are shown on the Home page.
            </p>
        </div>

        <div class="bg-about-section">
            <h2>What the Risk Levels Mean</h2>
            <div class="bg-risk-chip-row">
                <div class="bg-risk-chip">
                    <div class="bg-risk-chip-dot" style="background:#2E7D32;"></div>
                    <div class="bg-risk-chip-text">
                        <strong>Safe</strong>
                        <span>Low likelihood of elevated bacterial risk based on current model estimates.</span>
                    </div>
                </div>
                <div class="bg-risk-chip">
                    <div class="bg-risk-chip-dot" style="background:#F57F17;"></div>
                    <div class="bg-risk-chip-text">
                        <strong>Caution</strong>
                        <span>Moderate or uncertain risk. Check official advisories before entering the water.</span>
                    </div>
                </div>
                <div class="bg-risk-chip">
                    <div class="bg-risk-chip-dot" style="background:#C62828;"></div>
                    <div class="bg-risk-chip-text">
                        <strong>Unsafe</strong>
                        <span>Elevated bacterial risk predicted. Avoid water contact and follow official advisories.</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-footer">BeachGuard &nbsp;·&nbsp; Experimental research prototype</div>
    </div>
    """,
    unsafe_allow_html=True,
)
