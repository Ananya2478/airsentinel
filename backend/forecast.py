import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ── Data paths ────────────────────────────────────────────────────
INDIA_DATA_PATH  = r"C:\Users\ANANYA\Downloads\city_day.csv\city_day.csv"
GLOBAL_DATA_PATH = r"C:\Users\ANANYA\Downloads\global_aqi\global air pollution dataset.csv"

# ── Load global snapshot data ─────────────────────────────────────
def load_global_data():
    df = pd.read_csv(GLOBAL_DATA_PATH)
    df = df.rename(columns={
        "AQI Value":     "aqi",
        "AQI Category":  "category",
        "PM2.5 AQI Value": "pm25",
        "NO2 AQI Value": "no2",
        "Ozone AQI Value": "o3",
        "CO AQI Value":  "co",
    })
    df = df[df["aqi"] > 0].dropna(subset=["aqi", "City"])
    return df


def load_india_data():
    df = pd.read_csv(INDIA_DATA_PATH, parse_dates=["Date"])
    df = df.dropna(subset=["AQI"])
    df = df[df["AQI"] > 0]
    df["AQI"] = df["AQI"].clip(upper=500)
    return df


# ── Global city stats ─────────────────────────────────────────────
def get_global_aqi_stats() -> dict:
    """
    Return summary stats from global dataset.
    Most polluted countries, cleanest cities, category distribution.
    """
    df = load_global_data()

    # Most polluted cities
    top_polluted = df.nlargest(10, "aqi")[["Country","City","aqi","category"]].to_dict("records")

    # Cleanest cities
    cleanest = df.nsmallest(10, "aqi")[["Country","City","aqi","category"]].to_dict("records")

    # By country average
    country_avg = df.groupby("Country")["aqi"].mean().round(1).sort_values(ascending=False).head(15).to_dict()

    # Category distribution
    cat_dist = df["category"].value_counts().to_dict()

    return {
        "total_cities":   len(df),
        "total_countries": df["Country"].nunique(),
        "global_avg_aqi": round(float(df["aqi"].mean()), 1),
        "top_polluted":   top_polluted,
        "cleanest":       cleanest,
        "by_country":     country_avg,
        "category_dist":  cat_dist,
        "source":         "Kaggle — Global Air Pollution Dataset (hasibalmuzdadid)",
    }


def get_city_global_data(city: str) -> dict | None:
    """Get AQI data for a specific city from global dataset."""
    df = load_global_data()
    match = df[df["City"].str.lower() == city.lower()]
    if match.empty:
        # Try partial match
        match = df[df["City"].str.lower().str.contains(city.lower())]
    if match.empty:
        return None
    row = match.iloc[0]
    return {
        "city":     row["City"],
        "country":  row["Country"],
        "aqi":      int(row["aqi"]),
        "category": row["category"],
        "pm25":     int(row["pm25"]) if pd.notna(row["pm25"]) else None,
        "no2":      int(row["no2"])  if pd.notna(row["no2"])  else None,
        "o3":       int(row["o3"])   if pd.notna(row["o3"])   else None,
    }


# ── Indian city forecasting ───────────────────────────────────────
def get_available_cities():
    """Return list of Indian cities available for forecasting."""
    df = load_india_data()
    return sorted(df["City"].unique().tolist())


def get_historical_aqi(city: str, days: int = 90) -> list:
    """Return last N days of historical AQI for an Indian city."""
    df = load_india_data()
    city_df = df[df["City"] == city].sort_values("Date")
    if city_df.empty:
        return []
    recent = city_df.tail(days)
    return [
        {
            "date": row["Date"].strftime("%Y-%m-%d"),
            "aqi":  round(float(row["AQI"]), 1),
            "pm25": round(float(row["PM2.5"]), 1) if pd.notna(row.get("PM2.5")) else None,
            "pm10": round(float(row["PM10"]),  1) if pd.notna(row.get("PM10"))  else None,
        }
        for _, row in recent.iterrows()
    ]


def forecast_aqi(city: str, days_ahead: int = 7) -> dict:
    """Forecast AQI for next N days using Prophet or statistical fallback."""
    df = load_india_data()
    city_df = df[df["City"] == city][["Date","AQI"]].dropna().sort_values("Date")

    if city_df.empty:
        return {"error": f"No historical data for {city}"}
    if len(city_df) < 30:
        return {"error": f"Insufficient data for {city}"}

    try:
        from prophet import Prophet
        prophet_df = city_df.rename(columns={"Date":"ds","AQI":"y"})
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.1,
        )
        model.fit(prophet_df)
        future   = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        rows     = forecast.tail(days_ahead)

        predictions = [
            {
                "date":     r["ds"].strftime("%Y-%m-%d"),
                "aqi":      max(0, round(r["yhat"], 1)),
                "aqi_low":  max(0, round(r["yhat_lower"], 1)),
                "aqi_high": max(0, round(r["yhat_upper"], 1)),
            }
            for _, r in rows.iterrows()
        ]

        last30  = city_df.tail(30)["AQI"]
        trend   = "improving" if float(last30.iloc[-1]) < float(last30.iloc[0]) else "worsening"

        return {
            "city":        city,
            "model":       "Prophet (Meta)",
            "days_ahead":  days_ahead,
            "predictions": predictions,
            "historical":  get_historical_aqi(city, 30),
            "stats": {
                "avg_aqi_last30": round(float(last30.mean()), 1),
                "trend":          trend,
                "data_points":    len(city_df),
                "date_range":     f"{city_df['Date'].min().strftime('%Y-%m-%d')} to {city_df['Date'].max().strftime('%Y-%m-%d')}",
            }
        }

    except Exception as e:
        print(f"Prophet error: {e}, using fallback")
        return _statistical_forecast(city_df, city, days_ahead)


def _statistical_forecast(city_df, city, days_ahead):
    """Moving average fallback forecaster."""
    vals      = city_df["AQI"].values
    last_date = city_df["Date"].iloc[-1]
    avg = float(np.mean(vals[-30:]))
    std = float(np.std(vals[-30:]))

    predictions = []
    for i in range(1, days_ahead+1):
        pred = max(0, round(avg + np.random.normal(0, std*0.3), 1))
        predictions.append({
            "date":     (last_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "aqi":      pred,
            "aqi_low":  max(0, round(pred - std*0.5, 1)),
            "aqi_high": round(pred + std*0.5, 1),
        })

    return {
        "city":        city,
        "model":       "Statistical (Moving Average)",
        "days_ahead":  days_ahead,
        "predictions": predictions,
        "historical":  get_historical_aqi(city, 30),
        "stats": {
            "avg_aqi_last30": round(avg, 1),
            "trend":          "stable",
            "data_points":    len(city_df),
        }
    }