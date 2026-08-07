# ============================================================
# AquaCast / BeachGuard Streamlit App
# main.py
# ============================================================

import streamlit as st
import pandas as pd
from datetime import date


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="BeachGuard / AquaCast",
    page_icon="🌊",
    layout="wide"
)


# ============================================================
# 2. SETTINGS
# ============================================================

DATA_PATH = "data/app_predictions.csv"

# Pilot-site coordinates
SITE_LAT = 37.5602
SITE_LON = -122.2910

OFFICIAL_ADVISORY_URL = "https://www.smchealth.org/beaches"


# ============================================================
# 3. LOAD DATA
# ============================================================

@st.cache_data(ttl=3600)
def load_predictions():
    df = pd.read_csv(DATA_PATH)

    df["prediction_date"] = pd.to_datetime(
        df["prediction_date"],
        errors="coerce"
    )

    df["data_last_updated"] = pd.to_datetime(
        df["data_last_updated"],
        errors="coerce"
    )

    return df


try:
    df = load_predictions()

except Exception:
    st.error(
        "Prediction currently unavailable. "
        "Please check the official water-quality advisory."
    )

    st.link_button(
        "Check Official Water-Quality Advisories",
        OFFICIAL_ADVISORY_URL
    )

    st.stop()


# ============================================================
# 4. VALIDATE DATA
# ============================================================

required_columns = [
    "site_id",
    "site_name",
    "county",
    "prediction_date",
    "data_last_updated",
    "overall_risk",
    "risk_color",
    "safety_message",
    "model_version",
    "e_coli_probability",
    "e_coli_risk",
    "enterococcus_probability",
    "enterococcus_risk",
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:

    st.error(
        "Prediction currently unavailable because the "
        "prediction file is missing required fields."
    )

    st.write("Missing fields:", ", ".join(missing_columns))

    st.link_button(
        "Check Official Water-Quality Advisories",
        OFFICIAL_ADVISORY_URL
    )

    st.stop()


if df.empty:

    st.error(
        "No valid forecast is currently available. "
        "Please check the official water-quality advisory."
    )

    st.link_button(
        "Check Official Water-Quality Advisories",
        OFFICIAL_ADVISORY_URL
    )

    st.stop()


# ============================================================
# 5. SELECT LATEST VALID FORECAST
# ============================================================

df = df.dropna(subset=["prediction_date"])

if df.empty:

    st.error(
        "No valid forecast is currently available."
    )

    st.stop()


latest = (
    df.sort_values("prediction_date")
    .iloc[-1]
)


# ============================================================
# 6. HELPER FUNCTIONS
# ============================================================

def risk_icon(risk):

    risk = str(risk).strip()

    if risk == "Safe":
        return "🟢"

    if risk == "Caution":
        return "🟡"

    if risk == "Unsafe":
        return "🔴"

    return "⚪"


def display_risk_box(risk):

    icon = risk_icon(risk)

    if risk == "Safe":

        st.success(
            f"{icon} **SAFE** — "
            "The model currently predicts a low likelihood "
            "of elevated bacterial risk."
        )

    elif risk == "Caution":

        st.warning(
            f"{icon} **CAUTION** — "
            "The model predicts moderate or uncertain risk. "
            "Check official advisories before entering the water."
        )

    elif risk == "Unsafe":

        st.error(
            f"{icon} **UNSAFE** — "
            "The model predicts elevated bacterial risk. "
            "Avoid water contact and follow official advisories."
        )

    else:

        st.info(
            "Risk classification unavailable."
        )


# ============================================================
# 7. HEADER
# ============================================================

st.title("🌊 BeachGuard / AquaCast")

st.caption(
    "Experimental water-quality risk forecast for "
    "Parkside Aquatic Park, San Mateo"
)

st.warning(
    "⚠️ AquaCast is an experimental forecasting tool. "
    "It does not replace official laboratory results, "
    "beach closures, or public-health advisories."
)

st.link_button(
    "Check Official Water-Quality Advisories",
    OFFICIAL_ADVISORY_URL
)


st.divider()


# ============================================================
# 8. LOCATION + FORECAST INFORMATION
# ============================================================

st.subheader(latest["site_name"])

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "County",
        latest["county"]
    )


with col2:

    prediction_date = latest["prediction_date"]

    st.metric(
        "Prediction Date",
        prediction_date.strftime("%b %d, %Y")
    )


with col3:

    st.metric(
        "Model Version",
        str(latest["model_version"]).upper()
    )


# ============================================================
# 9. DATA FRESHNESS
# ============================================================

updated_date = latest["data_last_updated"]

if pd.notna(updated_date):

    days_old = (
        pd.Timestamp(date.today())
        - updated_date.normalize()
    ).days

    if days_old <= 1:

        st.success(
            f"✅ Data status: Current — last updated "
            f"{updated_date.strftime('%b %d, %Y')}"
        )

    elif days_old <= 3:

        st.warning(
            f"⚠️ Data status: {days_old} days old — "
            f"last updated {updated_date.strftime('%b %d, %Y')}"
        )

    else:

        st.error(
            f"⚠️ OUTDATED DATA — this forecast was last updated "
            f"{updated_date.strftime('%b %d, %Y')}."
        )


st.divider()


# ============================================================
# 10. OVERALL RISK
# ============================================================

st.subheader("Current Forecast")

overall_risk = str(
    latest["overall_risk"]
).strip()

display_risk_box(overall_risk)


# ============================================================
# 11. BACTERIA-SPECIFIC FORECASTS
# ============================================================

st.subheader("Bacteria-Specific Risk")


ecoli_col, entero_col = st.columns(2)


# ------------------------------------------------------------
# E. COLI
# ------------------------------------------------------------

with ecoli_col:

    st.markdown("### E. coli")

    ecoli_probability = float(
        latest["e_coli_probability"]
    )

    ecoli_risk = str(
        latest["e_coli_risk"]
    ).strip()

    st.metric(
        "Exceedance Probability",
        f"{ecoli_probability:.1%}"
    )

    if ecoli_risk == "Safe":

        st.success(
            f"🟢 {ecoli_risk}"
        )

    elif ecoli_risk == "Caution":

        st.warning(
            f"🟡 {ecoli_risk}"
        )

    elif ecoli_risk == "Unsafe":

        st.error(
            f"🔴 {ecoli_risk}"
        )

    st.caption(
        "Bacterial exceedance threshold: "
        "235 MPN/100 mL"
    )

    st.caption(
        "App risk thresholds: "
        "Safe < 10% • Caution 10–50% • Unsafe ≥ 50%"
    )


# ------------------------------------------------------------
# ENTEROCOCCUS
# ------------------------------------------------------------

with entero_col:

    st.markdown("### Enterococcus")

    entero_probability = float(
        latest["enterococcus_probability"]
    )

    entero_risk = str(
        latest["enterococcus_risk"]
    ).strip()

    st.metric(
        "Exceedance Probability",
        f"{entero_probability:.1%}"
    )

    if entero_risk == "Safe":

        st.success(
            f"🟢 {entero_risk}"
        )

    elif entero_risk == "Caution":

        st.warning(
            f"🟡 {entero_risk}"
        )

    elif entero_risk == "Unsafe":

        st.error(
            f"🔴 {entero_risk}"
        )

    st.caption(
        "Bacterial exceedance threshold: "
        "130 MPN/100 mL"
    )

    st.caption(
        "App risk thresholds: "
        "Safe < 40% • Caution 40–85% • Unsafe ≥ 85%"
    )


st.divider()


# ============================================================
# 12. SITE MAP
# ============================================================

st.subheader("Pilot Site")

map_data = pd.DataFrame(
    {
        "lat": [SITE_LAT],
        "lon": [SITE_LON]
    }
)

st.map(
    map_data,
    zoom=13
)

st.caption(
    "Parkside Aquatic Park, San Mateo, California"
)


# ============================================================
# 13. WHAT THE RISK LEVELS MEAN
# ============================================================

st.divider()

st.subheader("Understanding the Risk Levels")

safe_col, caution_col, unsafe_col = st.columns(3)


with safe_col:

    st.success("🟢 SAFE")

    st.write(
        "The model currently predicts a relatively low "
        "likelihood of elevated bacterial risk."
    )


with caution_col:

    st.warning("🟡 CAUTION")

    st.write(
        "The model predicts moderate or uncertain risk. "
        "Check official advisories before entering the water."
    )


with unsafe_col:

    st.error("🔴 UNSAFE")

    st.write(
        "The model predicts elevated bacterial risk. "
        "Avoid water contact and follow official advisories."
    )


# ============================================================
# 14. MODEL INFORMATION
# ============================================================

st.divider()

with st.expander("About the AquaCast Model"):

    st.markdown(
        """
### What AquaCast predicts

AquaCast estimates the probability that bacterial levels
will exceed elevated-risk thresholds for:

- **E. coli**
- **Enterococcus**

The system uses historical bacterial monitoring data together
with environmental predictors.

### Model development

The models were developed and evaluated using chronological
training, validation, and test periods rather than randomly
mixing past and future observations.

The current model pipeline evaluates multiple machine-learning
models and selects the approved model configuration for each
bacterium.

### Important limitation

AquaCast predicts **risk**, not the exact bacterial
concentration in the water.

It does not directly measure current water conditions and
should never replace official monitoring or laboratory results.
        """
    )


# ============================================================
# 15. PREDICTION DETAILS
# ============================================================

with st.expander("Prediction Details"):

    details = pd.DataFrame(
        {
            "Field": [
                "Site",
                "County",
                "Prediction Date",
                "Data Last Updated",
                "Model Version",
                "Overall Risk",
                "E. coli Probability",
                "E. coli Risk",
                "Enterococcus Probability",
                "Enterococcus Risk",
            ],

            "Value": [
                latest["site_name"],
                latest["county"],
                latest["prediction_date"].strftime(
                    "%Y-%m-%d"
                ),
                (
                    updated_date.strftime("%Y-%m-%d")
                    if pd.notna(updated_date)
                    else "Unknown"
                ),
                latest["model_version"],
                overall_risk,
                f"{ecoli_probability:.1%}",
                ecoli_risk,
                f"{entero_probability:.1%}",
                entero_risk,
            ]
        }
    )

    st.dataframe(
        details,
        hide_index=True,
        use_container_width=True
    )


# ============================================================
# 16. FINAL DISCLAIMER
# ============================================================

st.divider()

st.markdown(
    """
### ⚠️ Experimental Forecast

BeachGuard / AquaCast is a research prototype.

The displayed classifications represent **model-estimated
risk** and do not mean that the water has been officially
determined to be safe or unsafe.

Always follow official San Mateo County water-quality
advisories, beach closures, and laboratory results.
"""
)

st.link_button(
    "Check Official Water-Quality Advisories",
    OFFICIAL_ADVISORY_URL
)


st.caption(
    "BeachGuard / AquaCast • Experimental research prototype"
)
