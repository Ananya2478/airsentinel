import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")

# ── Indian cities (for deep analysis) ─────────────────────────────
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

# ── Global cities for world map ────────────────────────────────────
GLOBAL_CITIES = {
    # India
    "Delhi":        (28.6139, 77.2090, "India"),
    "Mumbai":       (19.0760, 72.8777, "India"),
    "Kolkata":      (22.5726, 88.3639, "India"),
    "Chennai":      (13.0827, 80.2707, "India"),
    "Bangalore":    (12.9716, 77.5946, "India"),
    "Hyderabad":    (17.3850, 78.4867, "India"),
    "Pune":         (18.5204, 73.8567, "India"),
    "Ahmedabad":    (23.0225, 72.5714, "India"),
    "Jaipur":       (26.9124, 75.7873, "India"),
    "Lucknow":      (26.8467, 80.9462, "India"),
    # Asia
    "Beijing":      (39.9042, 116.4074, "China"),
    "Shanghai":     (31.2304, 121.4737, "China"),
    "Chengdu":      (30.5728, 104.0668, "China"),
    "Guangzhou":    (23.1291, 113.2644, "China"),
    "Wuhan":        (30.5928, 114.3055, "China"),
    "Tokyo":        (35.6762, 139.6503, "Japan"),
    "Seoul":        (37.5665, 126.9780, "South Korea"),
    "Bangkok":      (13.7563, 100.5018, "Thailand"),
    "Jakarta":      (-6.2088, 106.8456, "Indonesia"),
    "Manila":       (14.5995, 120.9842, "Philippines"),
    "Hanoi":        (21.0285, 105.8542, "Vietnam"),
    "Karachi":      (24.8607, 67.0011, "Pakistan"),
    "Lahore":       (31.5204, 74.3587, "Pakistan"),
    "Dhaka":        (23.8103, 90.4125, "Bangladesh"),
    "Kathmandu":    (27.7172, 85.3240, "Nepal"),
    "Colombo":      (6.9271, 79.8612, "Sri Lanka"),
    # Middle East
    "Dubai":        (25.2048, 55.2708, "UAE"),
    "Riyadh":       (24.7136, 46.6753, "Saudi Arabia"),
    "Tehran":       (35.6892, 51.3890, "Iran"),
    "Istanbul":     (41.0082, 28.9784, "Turkey"),
    # Europe
    "London":       (51.5074, -0.1278, "UK"),
    "Paris":        (48.8566, 2.3522, "France"),
    "Berlin":       (52.5200, 13.4050, "Germany"),
    "Madrid":       (40.4168, -3.7038, "Spain"),
    "Rome":         (41.9028, 12.4964, "Italy"),
    "Warsaw":       (52.2297, 21.0122, "Poland"),
    "Kyiv":         (50.4501, 30.5234, "Ukraine"),
    "Moscow":       (55.7558, 37.6173, "Russia"),
    "Amsterdam":    (52.3676, 4.9041, "Netherlands"),
    "Brussels":     (50.8503, 4.3517, "Belgium"),
    # Africa
    "Cairo":        (30.0444, 31.2357, "Egypt"),
    "Lagos":        (6.5244, 3.3792, "Nigeria"),
    "Nairobi":      (-1.2921, 36.8219, "Kenya"),
    "Johannesburg": (-26.2041, 28.0473, "South Africa"),
    "Casablanca":   (33.5731, -7.5898, "Morocco"),
    "Accra":        (5.6037, -0.1870, "Ghana"),
    # Americas
    "New York":     (40.7128, -74.0060, "USA"),
    "Los Angeles":  (34.0522, -118.2437, "USA"),
    "Chicago":      (41.8781, -87.6298, "USA"),
    "Houston":      (29.7604, -95.3698, "USA"),
    "Mexico City":  (19.4326, -99.1332, "Mexico"),
    "Sao Paulo":    (-23.5505, -46.6333, "Brazil"),
    "Buenos Aires": (-34.6037, -58.3816, "Argentina"),
    "Bogota":       (4.7110, -74.0721, "Colombia"),
    "Lima":         (-12.0464, -77.0428, "Peru"),
    "Santiago":     (-33.4489, -70.6693, "Chile"),
    # Oceania
    "Sydney":       (-33.8688, 151.2093, "Australia"),
    "Melbourne":    (-37.8136, 144.9631, "Australia"),
    "Auckland":     (-36.8509, 174.7645, "New Zealand"),
}

# ── AQI category ──────────────────────────────────────────────────
def aqi_category(aqi: float) -> dict:
    if aqi <= 50:
        return {"label": "Good",         "color": "#00c853", "risk": "Low — air quality is satisfactory"}
    elif aqi <= 100:
        return {"label": "Satisfactory", "color": "#ffd600", "risk": "Moderate — acceptable for most people"}
    elif aqi <= 200:
        return {"label": "Moderate",     "color": "#ff6d00", "risk": "Unhealthy for sensitive groups"}
    elif aqi <= 300:
        return {"label": "Poor",         "color": "#d50000", "risk": "Unhealthy — everyone may be affected"}
    elif aqi <= 400:
        return {"label": "Very Poor",    "color": "#6a1b9a", "risk": "Very unhealthy — health alert"}
    else:
        return {"label": "Severe",       "color": "#37474f", "risk": "Hazardous — emergency conditions"}

# ── Simulated realistic AQI values ────────────────────────────────
SIMULATED_AQI = {
    "Delhi": 280, "Kanpur": 260, "Patna": 240, "Lucknow": 220,
    "Kolkata": 180, "Mumbai": 150, "Ahmedabad": 160, "Jaipur": 170,
    "Bhopal": 140, "Nagpur": 130, "Hyderabad": 110, "Pune": 120,
    "Surat": 125, "Chennai": 90, "Bangalore": 85,
    "Beijing": 160, "Shanghai": 110, "Chengdu": 140, "Guangzhou": 100,
    "Wuhan": 130, "Tokyo": 45, "Seoul": 80, "Bangkok": 95,
    "Jakarta": 110, "Manila": 90, "Hanoi": 120, "Karachi": 180,
    "Lahore": 200, "Dhaka": 170, "Kathmandu": 130, "Colombo": 60,
    "Dubai": 85, "Riyadh": 100, "Tehran": 140, "Istanbul": 75,
    "London": 40, "Paris": 45, "Berlin": 38, "Madrid": 42,
    "Rome": 50, "Warsaw": 65, "Kyiv": 70, "Moscow": 80,
    "Amsterdam": 35, "Brussels": 42,
    "Cairo": 130, "Lagos": 120, "Nairobi": 55, "Johannesburg": 70,
    "Casablanca": 60, "Accra": 85,
    "New York": 48, "Los Angeles": 65, "Chicago": 52, "Houston": 58,
    "Mexico City": 110, "Sao Paulo": 85, "Buenos Aires": 60,
    "Bogota": 70, "Lima": 90, "Santiago": 75,
    "Sydney": 30, "Melbourne": 28, "Auckland": 22,
}

def _simulated_aqi(city: str) -> float:
    import random
    base = SIMULATED_AQI.get(city, 80)
    return round(base + random.uniform(-15, 15), 1)

def get_aqi_data(city: str) -> dict | None:
    """Fetch real-time AQI for a city. Falls back to simulation if API unavailable."""
    if city in GLOBAL_CITIES:
        lat, lon, country = GLOBAL_CITIES[city]
    elif city in CITY_COORDS:
        lat, lon = CITY_COORDS[city]
        country = "India"
    else:
        lat, lon, country = 28.6139, 77.2090, "India"

    try:
        headers = {"Accept": "application/json"}
        r = requests.get(
            "https://api.openaq.org/v3/locations",
            params={"coordinates": f"{lat},{lon}", "radius": 25000, "limit": 5, "order_by": "distance"},
            headers=headers, timeout=8
        )
        if r.status_code == 200:
            locations = r.json().get("results", [])
            if locations:
                loc    = locations[0]
                loc_id = loc.get("id")
                mr = requests.get(
                    f"https://api.openaq.org/v3/locations/{loc_id}/latest",
                    headers=headers, timeout=8
                )
                pm25 = pm10 = no2 = o3 = None
                if mr.status_code == 200:
                    for m in mr.json().get("results", []):
                        param = m.get("parameter", {}).get("name", "")
                        val   = m.get("value", 0)
                        if param == "pm25": pm25 = round(val, 1)
                        if param == "pm10": pm10 = round(val, 1)
                        if param == "no2":  no2  = round(val, 1)
                        if param == "o3":   o3   = round(val, 1)

                aqi_val = min(pm25 * 4, 500) if pm25 else _simulated_aqi(city)
                cat     = aqi_category(aqi_val)
                return {
                    "city": city, "country": country,
                    "lat": lat, "lon": lon,
                    "aqi": round(aqi_val, 1),
                    "pm25": pm25, "pm10": pm10, "no2": no2, "o3": o3,
                    "category": cat["label"], "color": cat["color"],
                    "risk": cat["risk"], "source": "OpenAQ",
                    "station": loc.get("name", "Unknown station"),
                }
    except Exception as e:
        print(f"OpenAQ error for {city}: {e}")

    aqi_val = _simulated_aqi(city)
    cat     = aqi_category(aqi_val)
    return {
        "city": city, "country": country if city in GLOBAL_CITIES else "India",
        "lat": lat, "lon": lon,
        "aqi": aqi_val,
        "pm25": round(aqi_val / 4, 1),
        "pm10": round(aqi_val / 2, 1),
        "no2":  round(aqi_val / 6, 1),
        "o3":   round(aqi_val / 8, 1),
        "category": cat["label"], "color": cat["color"],
        "risk": cat["risk"], "source": "Simulated (OpenAQ unavailable)",
        "station": f"{city} Central",
    }

def get_global_stations() -> list:
    """Fetch AQI for all global cities."""
    results = []
    for city in GLOBAL_CITIES:
        data = get_aqi_data(city)
        if data:
            results.append(data)
    return results

def get_india_stations() -> list:
    """Fetch AQI for Indian cities only."""
    india_cities = [c for c, v in GLOBAL_CITIES.items() if v[2] == "India"]
    results = []
    for city in india_cities:
        data = get_aqi_data(city)
        if data:
            results.append(data)
    return results

def get_weather(city: str) -> dict | None:
    """Fetch wind and weather data."""
    if city in GLOBAL_CITIES:
        lat, lon, _ = GLOBAL_CITIES[city]
    elif city in CITY_COORDS:
        lat, lon = CITY_COORDS[city]
    else:
        lat, lon = 28.6139, 77.2090

    if not OPENWEATHER_KEY:
        import random
        dirs = ["N","NE","E","SE","S","SW","W","NW"]
        return {
            "city": city, "lat": lat, "lon": lon,
            "temp":           round(22 + random.uniform(-8, 15), 1),
            "humidity":       round(55 + random.uniform(-20, 30), 1),
            "wind_speed":     round(random.uniform(1, 12), 1),
            "wind_direction": random.choice(dirs),
            "wind_deg":       random.randint(0, 360),
            "description":    "Partly cloudy",
            "source":         "Simulated (add OPENWEATHER_KEY to .env for real data)",
        }

    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": lat, "lon": lon, "appid": OPENWEATHER_KEY, "units": "metric"},
            timeout=8
        )
        if r.status_code == 200:
            d   = r.json()
            deg = d["wind"].get("deg", 0)
            dirs = ["N","NE","E","SE","S","SW","W","NW"]
            return {
                "city": city, "lat": lat, "lon": lon,
                "temp":           d["main"]["temp"],
                "humidity":       d["main"]["humidity"],
                "wind_speed":     d["wind"]["speed"],
                "wind_direction": dirs[round(deg/45) % 8],
                "wind_deg":       deg,
                "description":    d["weather"][0]["description"],
                "source":         "OpenWeatherMap",
            }
    except Exception as e:
        print(f"Weather error: {e}")
    return None

def get_fire_hotspots(lat: float, lon: float, radius_km: float = 500) -> dict:
    """Fetch NASA FIRMS fire hotspots near a location."""
    try:
        deg_offset = radius_km / 111
        bbox = f"{lon-deg_offset},{lat-deg_offset},{lon+deg_offset},{lat+deg_offset}"
        r = requests.get(
            "https://firms.modaps.eosdis.nasa.gov/api/area/csv/VIIRS_SNPP_NRT/1",
            params={"area": bbox}, timeout=10
        )
        hotspots = []
        if r.status_code == 200 and r.text:
            for line in r.text.strip().split("\n")[1:51]:
                parts = line.split(",")
                if len(parts) >= 2:
                    try:
                        hotspots.append({
                            "lat": float(parts[0]),
                            "lon": float(parts[1]),
                            "brightness": float(parts[2]) if len(parts) > 2 else 300,
                        })
                    except:
                        continue
        return {
            "count": len(hotspots), "hotspots": hotspots,
            "source": "NASA FIRMS VIIRS",
            "note": "Active fire detections in last 24 hours",
        }
    except Exception as e:
        return {"count": 0, "hotspots": [], "source": "NASA FIRMS (unavailable)", "note": str(e)}
