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

# Lucide SVG icons (circle-check, triangle-alert, x-circle) — white, 52px
_RISK_ICONS = {
    "Safe": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" '
        'fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<polyline points="22 4 12 14.01 9 11.01"/></svg>'
    ),
    "Caution": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" '
        'fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<line x1="12" x2="12" y1="9" y2="13"/>'
        '<line x1="12" x2="12.01" y1="17" y2="17"/></svg>'
    ),
    "Unsafe": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" '
        'fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="15" x2="9" y1="9" y2="15"/>'
        '<line x1="9" x2="15" y1="9" y2="15"/></svg>'
    ),
}

# Small badge icons (14px, white)
_BADGE_ICONS = {
    "Safe": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" '
        'fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<polyline points="22 4 12 14.01 9 11.01"/></svg>'
    ),
    "Caution": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" '
        'fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<line x1="12" x2="12" y1="9" y2="13"/>'
        '<line x1="12" x2="12.01" y1="17" y2="17"/></svg>'
    ),
    "Unsafe": (
        '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" '
        'fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="15" x2="9" y1="9" y2="15"/>'
        '<line x1="9" x2="15" y1="9" y2="15"/></svg>'
    ),
}

_BADGE_CLASS = {"Safe": "safe", "Caution": "caution", "Unsafe": "unsafe"}


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
    icon = _RISK_ICONS.get(risk, "")
    site = str(latest["site_name"])
    message = str(latest["safety_message"])
    pred_date = latest["prediction_date"]
    date_str = pred_date.strftime("Forecast for %B %d, %Y") if pd.notna(pred_date) else ""

    st.markdown(
        f"""
        <div class="bg-hero" style="background-color:{color};">
            <div style="max-width:900px;margin:0 auto;padding:0 2rem;">
                <p class="bg-hero-site">{site}</p>
                <div class="bg-hero-status">
                    {icon}
                    <span class="bg-hero-label">{risk.upper()}</span>
                </div>
                <p class="bg-hero-message">{message}</p>
                <p class="bg-hero-date">{date_str}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge(risk: str) -> str:
    cls = _BADGE_CLASS.get(risk, "safe")
    icon = _BADGE_ICONS.get(risk, "")
    return f'<span class="bg-badge {cls}">{icon}{risk}</span>'


def wrap(html: str) -> None:
    st.markdown(f'<div class="bg-content">{html}</div>', unsafe_allow_html=True)
