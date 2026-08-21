from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import sklearn

# ------------------------------------------------------------
# Compatibility fix for older/newer scikit-learn model files
# that reference the private "_loss" module directly.
# ------------------------------------------------------------

try:
    import sklearn._loss._loss as sklearn_loss_core
    sys.modules.setdefault("_loss", sklearn_loss_core)
except Exception:
    pass

import joblib


# ============================================================
# Paths / site configuration
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = ROOT / "data" / "Aquacast15Years_Weekly.csv"
MODEL_DIR = ROOT / "models"
MANIFEST_PATH = MODEL_DIR / "model_manifest.json"

SITE_ID = "aquatic_park_san_mateo"
SITE_NAME = "Parkside Aquatic Park, San Mateo"
COUNTY = "San Mateo"

SITE_LAT = 37.5602
SITE_LON = -122.2910

TIMEZONE = "America/Los_Angeles"


# ============================================================
# Bacteria thresholds
# ============================================================

BACTERIA_THRESHOLDS = {
    "E. coli": 235.0,
    "Enterococcus": 130.0,
}


# ============================================================
# Feature definitions
#
# These match the feature engineering used by AquaCast.
# ============================================================

BASE_FEATURES = [
    "rain_1day",
    "rain_3day_sum",
    "rain_1day_lag1",
    "rain_1day_lag2",
    "rain_ratio_1to3",
    "first_flush_index",
    "temp_3day_avg",
    "season_wet",
    "adp_days",
]

EXPANDED_FEATURES = BASE_FEATURES + [
    "rain_7day_sum",
    "rain_14day_sum",

    "rain_3day_max",
    "rain_7day_max",
    "rain_14day_max",

    "rain_3day_avg",
    "rain_7day_avg",
    "rain_14day_avg",

    "rain_3day_rainy_days",
    "rain_7day_rainy_days",
    "rain_14day_rainy_days",

    "rain_intensity_3day",
    "rain_intensity_7day",
    "rain_intensity_14day",

    "temp_7day_avg",
    "temp_14day_avg",

    "temp_3day_min",
    "temp_3day_max",
    "temp_7day_min",
    "temp_7day_max",

    "wet_season_rain_1day",
    "wet_season_rain_3day_sum",
    "wet_season_rain_7day_sum",

    "rain_temp_interaction_1day",
    "rain_temp_interaction_3day",

    "prev_result_value",
    "prev_exceedance",
    "prev_result_to_threshold_ratio",

    "prev3_result_mean",
    "prev5_result_mean",

    "prev3_exceedance_rate",
    "prev5_exceedance_rate",

    "prev3_result_to_threshold_ratio_mean",
    "prev5_result_to_threshold_ratio_mean",

    "days_since_prev_sample",
]


# ============================================================
# Risk categories
# ============================================================

def risk_level(bacteria: str, probability: float) -> str:

    probability = float(probability)

    if bacteria == "E. coli":

        if probability < 0.10:
            return "Safe"

        if probability < 0.50:
            return "Caution"

        return "Unsafe"

    if probability < 0.40:
        return "Safe"

    if probability < 0.85:
        return "Caution"

    return "Unsafe"


def overall_risk(ecoli_risk: str, entero_risk: str) -> str:

    ranking = {
        "Safe": 0,
        "Caution": 1,
        "Unsafe": 2,
    }

    return max(
        [ecoli_risk, entero_risk],
        key=lambda x: ranking[x],
    )


# ============================================================
# Load model manifest
# ============================================================

def _load_manifest():

    if not MANIFEST_PATH.exists():
        return {}

    try:
        return json.loads(
            MANIFEST_PATH.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return {}


def _manifest_models(manifest):

    if "models" in manifest:
        return manifest["models"]

    return manifest


# ============================================================
# Find model file
# ============================================================

def _find_model_file(bacteria: str, info: dict):

    filename = info.get("model_file")

    if filename:

        path = MODEL_DIR / filename

        if path.exists():
            return path

    if bacteria == "E. coli":

        candidates = [
            MODEL_DIR / "e_coli_current_best_model.joblib",
            MODEL_DIR / "ecoli_current_best_model.joblib",
        ]

        search_terms = [
            "e_coli",
            "ecoli",
        ]

    else:

        candidates = [
            MODEL_DIR / "enterococcus_current_best_model.joblib",
        ]

        search_terms = [
            "enterococcus",
            "entero",
        ]

    for path in candidates:

        if path.exists():
            return path

    for path in MODEL_DIR.glob("*.joblib"):

        name = path.name.lower()

        if "bundle" in name:
            continue

        if any(term in name for term in search_terms):
            return path

    raise FileNotFoundError(
        f"No model file found for {bacteria}"
    )


# ============================================================
# Load models
# ============================================================

@st.cache_resource(show_spinner=False)
def _load_model(path_string: str):

    return joblib.load(path_string)


def _load_model_and_features(bacteria: str):

    manifest = _load_manifest()
    models = _manifest_models(manifest)

    info = models.get(
        bacteria,
        {}
    )

    model_path = _find_model_file(
        bacteria,
        info,
    )

    model = _load_model(
        str(model_path)
    )

    features = info.get(
        "features"
    )

    if not features:

        feature_filename = (
            info.get("feature_file")
            or info.get("features_file")
        )

        if feature_filename:

            path = MODEL_DIR / feature_filename

            if path.exists():

                features = [
                    line.strip()
                    for line in path.read_text(
                        encoding="utf-8"
                    ).splitlines()
                    if line.strip()
                ]

    if not features and hasattr(
        model,
        "feature_names_in_"
    ):

        features = list(
            model.feature_names_in_
        )

    if not features:

        if bacteria == "E. coli":
            features = EXPANDED_FEATURES.copy()

        else:
            features = BASE_FEATURES.copy()

    return model, list(features)


# ============================================================
# Load AquaCast dataset
# ============================================================

@st.cache_data(show_spinner=False)
def _load_dataset():

    df = pd.read_csv(
        DATA_PATH,
        low_memory=False,
    )

    if (
        "sampledate" in df.columns
        and "sample_date" not in df.columns
    ):
        df["sample_date"] = df["sampledate"]

    if (
        "analyte" in df.columns
        and "indicator_clean" not in df.columns
    ):
        df["indicator_clean"] = df["analyte"]

    if (
        "result" in df.columns
        and "result_value" not in df.columns
    ):
        df["result_value"] = df["result"]

    df["sample_date"] = pd.to_datetime(
        df["sample_date"],
        errors="coerce",
    ).dt.normalize()

    df["result_value"] = pd.to_numeric(
        df["result_value"],
        errors="coerce",
    )

    def normalize_indicator(value):

        value = str(value).strip().lower()

        if value in {
            "e. coli",
            "e coli",
            "ecoli",
            "e_coli",
        }:
            return "E. coli"

        if value in {
            "enterococcus",
            "enterococci",
        }:
            return "Enterococcus"

        return value

    df["indicator_clean"] = (
        df["indicator_clean"]
        .apply(normalize_indicator)
    )

    df = df[
        df["indicator_clean"].isin(
            [
                "E. coli",
                "Enterococcus",
            ]
        )
    ].copy()

    return df


# ============================================================
# Weather API
#
# Open-Meteo returns:
# - precipitation_sum in millimeters
# - temperature_2m_mean in Celsius
#
# These match the units used by the AquaCast feature pipeline.
# ============================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def _fetch_weather():

    params = {
        "latitude": SITE_LAT,
        "longitude": SITE_LON,

        "daily": (
            "precipitation_sum,"
            "temperature_2m_mean"
        ),

        # Need enough history for 14-day features.
        "past_days": 20,

        # Today + several future days.
        "forecast_days": 4,

        "timezone": TIMEZONE,
    }

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urllib.parse.urlencode(params)
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "BeachGuard-AquaCast/1.0"
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=12,
    ) as response:

        payload = json.loads(
            response.read().decode("utf-8")
        )

    daily = payload.get(
        "daily",
        {}
    )

    dates = daily.get(
        "time",
        []
    )

    precipitation = daily.get(
        "precipitation_sum",
        []
    )

    temperature = daily.get(
        "temperature_2m_mean",
        []
    )

    if not dates:
        raise RuntimeError(
            "Weather API returned no dates."
        )

    weather = pd.DataFrame(
        {
            "sample_date": pd.to_datetime(
                dates
            ),

            "prcp_mm": pd.to_numeric(
                precipitation,
                errors="coerce",
            ),

            "tavg_c": pd.to_numeric(
                temperature,
                errors="coerce",
            ),
        }
    )

    weather = weather.set_index(
        "sample_date"
    ).sort_index()

    return weather


# ============================================================
# Recreate AquaCast weather features
#
# IMPORTANT:
# Feature calculations intentionally follow the training
# pipeline, including the one-day shift.
# ============================================================

def _engineer_weather_features(
    weather: pd.DataFrame
):

    w = weather.copy().sort_index()

    pr = pd.to_numeric(
        w["prcp_mm"],
        errors="coerce",
    )

    temp = pd.to_numeric(
        w["tavg_c"],
        errors="coerce",
    )

    # Yesterday's rainfall relative to prediction date.
    w["rain_1day"] = pr.shift(1)

    # Older rainfall lags.
    w["rain_1day_lag1"] = pr.shift(2)
    w["rain_1day_lag2"] = pr.shift(3)

    for window in [
        3,
        7,
        14,
    ]:

        w[f"rain_{window}day_sum"] = (
            pr
            .rolling(
                window,
                min_periods=window,
            )
            .sum()
            .shift(1)
        )

        w[f"rain_{window}day_avg"] = (
            pr
            .rolling(
                window,
                min_periods=window,
            )
            .mean()
            .shift(1)
        )

        w[f"rain_{window}day_max"] = (
            pr
            .rolling(
                window,
                min_periods=window,
            )
            .max()
            .shift(1)
        )

        rainy = (
            pr > 0
        ).astype(float)

        w[
            f"rain_{window}day_rainy_days"
        ] = (
            rainy
            .rolling(
                window,
                min_periods=window,
            )
            .sum()
            .shift(1)
        )

        w[
            f"rain_intensity_{window}day"
        ] = (
            w[f"rain_{window}day_sum"]
            /
            (
                w[
                    f"rain_{window}day_rainy_days"
                ]
                + 1e-6
            )
        )

        minimum_periods = max(
            2,
            window // 2,
        )

        w[f"temp_{window}day_avg"] = (
            temp
            .rolling(
                window,
                min_periods=minimum_periods,
            )
            .mean()
            .shift(1)
        )

        w[f"temp_{window}day_min"] = (
            temp
            .rolling(
                window,
                min_periods=minimum_periods,
            )
            .min()
            .shift(1)
        )

        w[f"temp_{window}day_max"] = (
            temp
            .rolling(
                window,
                min_periods=minimum_periods,
            )
            .max()
            .shift(1)
        )

    # Wet season used by AquaCast.
    w["season_wet"] = [
        1
        if date.month in [
            11,
            12,
            1,
            2,
            3,
        ]
        else 0
        for date in w.index
    ]

    # Antecedent dry period.
    adp = []

    count = 0

    for value in pr.values:

        adp.append(count)

        if pd.isna(value):
            count = 0

        elif value > 0:
            count = 0

        else:
            count += 1

    w["adp_days"] = adp

    w["rain_ratio_1to3"] = (
        w["rain_1day"]
        /
        (
            w["rain_3day_sum"]
            + 1e-6
        )
    )

    w["first_flush_index"] = (
        w["rain_1day"]
        * w["adp_days"]
    )

    w["wet_season_rain_1day"] = (
        w["season_wet"]
        * w["rain_1day"]
    )

    w["wet_season_rain_3day_sum"] = (
        w["season_wet"]
        * w["rain_3day_sum"]
    )

    w["wet_season_rain_7day_sum"] = (
        w["season_wet"]
        * w["rain_7day_sum"]
    )

    w["rain_temp_interaction_1day"] = (
        w["rain_1day"]
        * w["temp_3day_avg"]
    )

    w["rain_temp_interaction_3day"] = (
        w["rain_3day_sum"]
        * w["temp_3day_avg"]
    )

    return w


# ============================================================
# Latest bacteria-history features
#
# For future forecasts we do NOT invent future bacteria
# measurements. We use the newest real observations available.
# ============================================================

def _history_features(
    df: pd.DataFrame,
    bacteria: str,
    target_date: pd.Timestamp,
):

    threshold = (
        BACTERIA_THRESHOLDS[
            bacteria
        ]
    )

    subset = df[
        (
            df["indicator_clean"]
            == bacteria
        )
        &
        (
            df["sample_date"]
            < target_date
        )
    ].copy()

    subset = (
        subset
        .dropna(
            subset=[
                "sample_date",
                "result_value",
            ]
        )
        .sort_values(
            "sample_date"
        )
    )

    if subset.empty:

        raise RuntimeError(
            f"No historical samples for {bacteria}"
        )

    results = (
        subset["result_value"]
        .astype(float)
    )

    exceedance = (
        results >= threshold
    ).astype(float)

    ratios = (
        results / threshold
    )

    latest = subset.iloc[-1]

    last3_results = results.tail(3)
    last5_results = results.tail(5)

    last3_exceed = exceedance.tail(3)
    last5_exceed = exceedance.tail(5)

    last3_ratios = ratios.tail(3)
    last5_ratios = ratios.tail(5)

    return {
        "prev_result_value":
            float(results.iloc[-1]),

        "prev_exceedance":
            float(exceedance.iloc[-1]),

        "prev_result_to_threshold_ratio":
            float(ratios.iloc[-1]),

        "prev3_result_mean":
            float(last3_results.mean()),

        "prev5_result_mean":
            float(last5_results.mean()),

        "prev3_exceedance_rate":
            float(last3_exceed.mean()),

        "prev5_exceedance_rate":
            float(last5_exceed.mean()),

        "prev3_result_to_threshold_ratio_mean":
            float(last3_ratios.mean()),

        "prev5_result_to_threshold_ratio_mean":
            float(last5_ratios.mean()),

        "days_since_prev_sample":
            float(
                (
                    target_date
                    - latest["sample_date"]
                ).days
            ),

        "_latest_lab_date":
            latest["sample_date"],
    }


# ============================================================
# Fallback value for unusual model features
# ============================================================

def _fallback_feature_value(
    df,
    bacteria,
    feature,
):

    subset = df[
        df["indicator_clean"]
        == bacteria
    ]

    if feature in subset.columns:

        values = pd.to_numeric(
            subset[feature],
            errors="coerce",
        )

        median = values.median()

        if pd.notna(median):
            return float(median)

    return 0.0


# ============================================================
# Single bacteria prediction
# ============================================================

def _predict_bacteria(
    bacteria,
    model,
    features,
    target_date,
    weather_features,
    dataset,
):

    if target_date not in weather_features.index:

        raise RuntimeError(
            f"No weather data for {target_date.date()}"
        )

    weather_row = weather_features.loc[
        target_date
    ]

    history = _history_features(
        dataset,
        bacteria,
        target_date,
    )

    values = {}
    estimated = []

    for feature in features:

        if (
            feature in weather_row.index
            and pd.notna(
                weather_row[feature]
            )
        ):

            values[feature] = float(
                weather_row[feature]
            )

        elif feature in history:

            values[feature] = float(
                history[feature]
            )

        else:

            values[feature] = (
                _fallback_feature_value(
                    dataset,
                    bacteria,
                    feature,
                )
            )

            estimated.append(feature)

    X = pd.DataFrame(
        [
            [
                values[feature]
                for feature in features
            ]
        ],
        columns=features,
    )

    probability = float(
        model.predict_proba(X)[0, 1]
    )

    return (
        probability,
        estimated,
        history["_latest_lab_date"],
    )


# ============================================================
# Model version
# ============================================================

def _model_version():

    manifest = _load_manifest()

    pipeline = str(
        manifest.get(
            "pipeline_version",
            "AquaCast",
        )
    )

    match = re.search(
        r"Version[_\s]*(\d+)",
        pipeline,
        flags=re.IGNORECASE,
    )

    if match:
        return f"V{match.group(1)} LIVE"

    return "AquaCast LIVE"


# ============================================================
# Generate live outlook
# ============================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def load_live_outlook(
    days: int = 3
):

    dataset = _load_dataset()

    raw_weather = _fetch_weather()

    weather = (
        _engineer_weather_features(
            raw_weather
        )
    )

    ecoli_model, ecoli_features = (
        _load_model_and_features(
            "E. coli"
        )
    )

    entero_model, entero_features = (
        _load_model_and_features(
            "Enterococcus"
        )
    )

    today = (
        pd.Timestamp.now(
            tz=TIMEZONE
        )
        .tz_localize(None)
        .normalize()
    )

    rows = []

    for offset in range(days):

        target_date = (
            today
            + pd.Timedelta(
                days=offset
            )
        )

        ecoli_prob, ecoli_estimated, ecoli_lab = (
            _predict_bacteria(
                "E. coli",
                ecoli_model,
                ecoli_features,
                target_date,
                weather,
                dataset,
            )
        )

        entero_prob, entero_estimated, entero_lab = (
            _predict_bacteria(
                "Enterococcus",
                entero_model,
                entero_features,
                target_date,
                weather,
                dataset,
            )
        )

        ecoli_risk = risk_level(
            "E. coli",
            ecoli_prob,
        )

        entero_risk = risk_level(
            "Enterococcus",
            entero_prob,
        )

        overall = overall_risk(
            ecoli_risk,
            entero_risk,
        )

        rows.append(
            {
                "prediction_date":
                    target_date,

                "e_coli_probability":
                    ecoli_prob,

                "e_coli_risk":
                    ecoli_risk,

                "enterococcus_probability":
                    entero_prob,

                "enterococcus_risk":
                    entero_risk,

                "overall_risk":
                    overall,

                "e_coli_latest_lab_date":
                    ecoli_lab,

                "enterococcus_latest_lab_date":
                    entero_lab,

                "estimated_features":
                    sorted(
                        set(
                            ecoli_estimated
                            + entero_estimated
                        )
                    ),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# Return a Series compatible with the CURRENT main.py
# ============================================================

def load_live_latest():

    outlook = load_live_outlook(
        days=3
    )

    if outlook.empty:

        raise RuntimeError(
            "No live predictions generated."
        )

    row = outlook.iloc[0]

    overall = row["overall_risk"]

    messages = {
        "Safe":
            (
                "Low bacterial risk predicted. "
                "Always check official advisories "
                "before entering the water."
            ),

        "Caution":
            (
                "Elevated or uncertain bacterial "
                "risk predicted. Check official "
                "advisories before entering the water."
            ),

        "Unsafe":
            (
                "High bacterial risk predicted. "
                "Avoid water contact and follow "
                "official advisories."
            ),
    }

    colors = {
        "Safe": "#2E7D32",
        "Caution": "#F57F17",
        "Unsafe": "#C62828",
    }

    now = (
        pd.Timestamp.now(
            tz=TIMEZONE
        )
        .tz_localize(None)
    )

    return pd.Series(
        {
            "site_id":
                SITE_ID,

            "site_name":
                SITE_NAME,

            "county":
                COUNTY,

            "prediction_date":
                row["prediction_date"],

            "data_last_updated":
                now,

            "overall_risk":
                overall,

            "risk_color":
                colors[overall],

            "safety_message":
                messages[overall],

            "model_version":
                _model_version(),

            "e_coli_probability":
                float(
                    row[
                        "e_coli_probability"
                    ]
                ),

            "e_coli_risk":
                row["e_coli_risk"],

            "enterococcus_probability":
                float(
                    row[
                        "enterococcus_probability"
                    ]
                ),

            "enterococcus_risk":
                row[
                    "enterococcus_risk"
                ],

            "weather_source":
                "Open-Meteo",

            "live_prediction":
                True,

            "e_coli_latest_lab_date":
                row[
                    "e_coli_latest_lab_date"
                ],

            "enterococcus_latest_lab_date":
                row[
                    "enterococcus_latest_lab_date"
                ],

            "estimated_features":
                row[
                    "estimated_features"
                ],
        }
    )
