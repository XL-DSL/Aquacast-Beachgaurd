import pathlib
import streamlit as st
import pandas as pd

_CSS_PATH = pathlib.Path(__file__).parent.parent / "assets" / "styles.css"
_CSV_PATH = pathlib.Path(__file__).parent.parent / "data" / "app_predictions.csv"

_RISK_COLORS = {
    "Safe":    "#2E7D32",
    "Caution": "#F57F17",
    "Unsafe":  "#C62828",
}
_RISK_ICONS = {
    "Safe":    "🟢",
    "Caution": "🟡",
    "Unsafe":  "🔴",
}


def apply_styles() -> None:
    css = _CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_latest() -> pd.Series:
    df = pd.read_csv(_CSV_PATH)
    df["prediction_date"] = pd.to_datetime(df["prediction_date"], errors="coerce")
    df["data_last_updated"] = pd.to_datetime(df["data_last_updated"], errors="coerce")
    df = df.dropna(subset=["prediction_date"])
    return df.sort_values("prediction_date").iloc[-1]


def render_hero(latest: pd.Series) -> None:
    risk = str(latest["overall_risk"]).strip()
    color = _RISK_COLORS.get(risk, "#455A64")
    icon = _RISK_ICONS.get(risk, "⚪")
    site = str(latest["site_name"])
    message = str(latest["safety_message"])
    st.markdown(
        f"""
        <div style="
            background-color: {color};
            width: 100%;
            padding: 2.5rem 2rem;
            margin-bottom: 1.5rem;
            margin-left: -2rem;
            margin-right: -2rem;
            width: calc(100% + 4rem);
            box-sizing: border-box;
        ">
            <p style="color:#FFFFFF;font-size:1.1rem;font-weight:600;margin:0 0 0.25rem 0;opacity:0.9;">
                {site}
            </p>
            <p style="color:#FFFFFF;font-size:4.5rem;font-weight:700;margin:0;line-height:1.05;">
                {icon} {risk.upper()}
            </p>
            <p style="color:#FFFFFF;font-size:1.1rem;margin:0.5rem 0 0 0;opacity:0.85;">
                {message}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
