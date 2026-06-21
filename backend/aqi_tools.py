import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")

# City coordinates for major Indian cities
CITY_COORDS = {
    "Delhi":      (28.6139, 77.2090),
    "Mumbai":     (19.0760, 72.8777),
    "Kolkata":    (22.5726, 88.3639),
    "Chennai":    (13.0827, 80.2707),
    "Bangalore":  (12.9716, 77.5946),
    "Hyderabad":  (17.3850, 78.4867),
    "Pune":       (18.5204, 73.8567),
    "Ahmedabad":  (23.0225, 72.5714),
    "Jaipur":     (26.9124, 75.7873),
    "Lucknow":    (26.8467, 80.9462),
    "Kanpur":     (26.4499, 80.3319),
    "Patna":      (25.5941, 85.1376),
    "Bhopal":     (23.2599, 77.4126),
    "Nagpur":     (21.1458, 79.0882),
    "Surat":      (21.1702, 72.8311),
}

# AQI category labels
def aqi_category(aqi: float) -> dict:
    if aqi <= 50:
        return {"label": "Good",        "color": "#00e400", "risk": "Low"}
    elif aqi <= 100:
        return {"label": "Satisfactory","color": "#ffff00", "risk": "Moderate"}
    elif aqi <= 200:
        return {"label": "Moderate",    "color": "#ff7e00", "risk": "Unhealthy for sensitive groups"}
    elif aqi <= 300:
        return {"label": "Poor",        "color": "#ff0000", "risk": "Unhealthy"}
    elif aqi <= 400:
        return {"label": "Very Poor",   "color": "#8f3f97", "risk": "Very unhealthy"}
    else:
        return {"label": "Severe",      "color": "#7e0023", "risk": "Hazardous"}


def get_aqi_data(city: str) -> dict | None:
    """
    Fetch real-time AQI from OpenAQ API v3.
    Falls back to simulated data if API is unavailable.
    """
    coords = CITY_COORDS.get(city)
    if not coords:
        coords = (28.6139, 77.2090)  # default Delhi

    lat, lon = coords

    try:
        # OpenAQ v3 - free, no key needed for basic usage
        url = "https://api.openaq.org/v3/locations"
        params = {
            "coordinates": f"{lat},{lon}",
            "radius": 25000,
            "limit": 5,
            "order_by": "distance",
        }
        headers = {"Accept": "application/json"}
        r = requests.get(url, params=params, headers=headers, timeout=8)

        if r.status_code == 200:
            data = r.json()
            locations = data.get("results", [])

            if locations:
                loc = locations[0]
                # Get latest measurements for this location
                loc_id = loc.get("id")
                meas_url = f"https://api.openaq.org/v3/locations/{loc_id}/latest"
                mr = requests.get(meas_url, headers=headers, timeout=8)

                pm25 = None
                pm10 = None
                no2  = None
                o3   = None

                if mr.status_code == 200:
                    measurements = mr.json().get("results", [])
                    for m in measurements:
                        param = m.get("parameter", {}).get("name", "")
                        val   = m.get("value", 0)
                        if param == "pm25":  pm25 = round(val, 1)
                        if param == "pm10":  pm10 = round(val, 1)
                        if param == "no2":   no2  = round(val, 1)
                        if param == "o3":    o3   = round(val, 1)

                # Use PM2.5 as primary AQI indicator
                aqi_val = pm25 * 4 if pm25 else _simulated_aqi(city)
                aqi_val = min(aqi_val, 500)
                cat = aqi_category(aqi_val)

                return {
                    "city":     city,
                    "lat":      lat,
                    "lon":      lon,
                    "aqi":      round(aqi_val, 1),
                    "pm25":     pm25,
                    "pm10":     pm10,
                    "no2":      no2,
                    "o3":       o3,
                    "category": cat["label"],
                    "color":    cat["color"],
                    "risk":     cat["risk"],
                    "source":   "OpenAQ",
                    "station":  loc.get("name", "Unknown station"),
                }

    except Exception as e:
        print(f"OpenAQ error for {city}: {e}")

    # Fallback to simulated realistic data
    aqi_val = _simulated_aqi(city)
    cat = aqi_category(aqi_val)
    return {
        "city":     city,
        "lat":      lat,
        "lon":      lon,
        "aqi":      aqi_val,
        "pm25":     round(aqi_val / 4, 1),
        "pm10":     round(aqi_val / 2, 1),
        "no2":      round(aqi_val / 6, 1),
        "o3":       round(aqi_val / 8, 1),
        "category": cat["label"],
        "color":    cat["color"],
        "risk":     cat["risk"],
        "source":   "Simulated (OpenAQ unavailable)",
        "station":  f"{city} Central",
    }


def _simulated_aqi(city: str) -> float:
    """Realistic AQI values based on known pollution levels."""
    base = {
        "Delhi": 280, "Kanpur": 260, "Patna": 240, "Lucknow": 220,
        "Kolkata": 180, "Mumbai": 150, "Ahmedabad": 160, "Jaipur": 170,
        "Bhopal": 140, "Nagpur": 130, "Hyderabad": 110, "Pune": 120,
        "Surat": 125, "Chennai": 90, "Bangalore": 85,
    }
    import random
    val = base.get(city, 150)
    return round(val + random.uniform(-20, 20), 1)


def get_weather(city: str) -> dict | None:
    """Fetch wind and weather data from OpenWeatherMap."""
    coords = CITY_COORDS.get(city, (28.6139, 77.2090))
    lat, lon = coords

    if not OPENWEATHER_KEY:
        # Return simulated weather data
        import random
        directions = ["N","NE","E","SE","S","SW","W","NW"]
        return {
            "city":           city,
            "lat":            lat,
            "lon":            lon,
            "temp":           round(28 + random.uniform(-5, 10), 1),
            "humidity":       round(55 + random.uniform(-15, 25), 1),
            "wind_speed":     round(random.uniform(2, 15), 1),
            "wind_direction": random.choice(directions),
            "wind_deg":       random.randint(0, 360),
            "description":    "Partly cloudy",
            "source":         "Simulated (add OPENWEATHER_KEY to .env for real data)",
        }

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_KEY, "units": "metric"}
        r = requests.get(url, params=params, timeout=8)
        if r.status_code == 200:
            d = r.json()
            deg = d["wind"].get("deg", 0)
            dirs = ["N","NE","E","SE","S","SW","W","NW"]
            wind_dir = dirs[round(deg / 45) % 8]
            return {
                "city":           city,
                "lat":            lat,
                "lon":            lon,
                "temp":           d["main"]["temp"],
                "humidity":       d["main"]["humidity"],
                "wind_speed":     d["wind"]["speed"],
                "wind_direction": wind_dir,
                "wind_deg":       deg,
                "description":    d["weather"][0]["description"],
                "source":         "OpenWeatherMap",
            }
    except Exception as e:
        print(f"Weather error: {e}")
    return None


def get_fire_hotspots(lat: float, lon: float, radius_km: float = 500) -> dict:
    """
    Fetch fire hotspots from NASA FIRMS.
    Uses the public CSV endpoint — no key needed for basic access.
    """
    try:
        # NASA FIRMS VIIRS 24hr data — public endpoint
        url = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/VIIRS_SNPP_NRT/1"
        # Build bounding box from center + radius (rough approximation)
        deg_offset = radius_km / 111
        bbox = f"{lon-deg_offset},{lat-deg_offset},{lon+deg_offset},{lat+deg_offset}"
        params = {"area": bbox}
        r = requests.get(url, params=params, timeout=10)

        hotspots = []
        if r.status_code == 200 and r.text:
            lines = r.text.strip().split("\n")
            if len(lines) > 1:
                for line in lines[1:51]:  # max 50 hotspots
                    parts = line.split(",")
                    if len(parts) >= 3:
                        try:
                            hotspots.append({
                                "lat":        float(parts[0]),
                                "lon":        float(parts[1]),
                                "brightness": float(parts[2]) if len(parts) > 2 else 300,
                                "type":       "fire",
                            })
                        except:
                            continue

        return {
            "count":     len(hotspots),
            "hotspots":  hotspots,
            "source":    "NASA FIRMS VIIRS",
            "note":      "Active fire detections in the last 24 hours",
        }

    except Exception as e:
        print(f"NASA FIRMS error: {e}")
        return {
            "count":    0,
            "hotspots": [],
            "source":   "NASA FIRMS (unavailable)",
            "note":     str(e),
        }
