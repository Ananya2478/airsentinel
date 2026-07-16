from mcp.server.fastmcp import FastMCP
import requests

mcp = FastMCP("AirSentinel")
BASE_URL = "https://airsentinel-backend.onrender.com"

@mcp.tool()
def get_aqi(city: str) -> str:
    """Get real-time AQI and pollutant levels for any city worldwide."""
    try:
        r = requests.get(f"{BASE_URL}/api/aqi?city={city}", timeout=10)
        d = r.json()
        return (f"City: {d['city']} ({d.get('country','India')})\nAQI: {d['aqi']} — {d['category']}\nPM2.5: {d['pm25']} µg/m³\nPM10: {d['pm10']} µg/m³\nNO2: {d['no2']} µg/m³\nO3: {d['o3']} µg/m³\nRisk: {d['risk']}\nSource: {d['source']}")
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_forecast(city: str) -> str:
    """Get 7-day AQI forecast for an Indian city using CPCB historical data."""
    try:
        r = requests.get(f"{BASE_URL}/api/forecast?city={city}&days=7", timeout=15)
        d = r.json()
        if "error" in d:
            return f"Forecast unavailable: {d['error']}"
        result = f"7-Day Forecast for {city} (Model: {d.get('model','Statistical')})\nTrend: {d.get('stats',{}).get('trend','N/A')}\n\n"
        for p in d.get("predictions", []):
            result += f"  {p['date']}: AQI {p['aqi']} (range: {p['aqi_low']}–{p['aqi_high']})\n"
        return result
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_weather(city: str) -> str:
    """Get wind speed, direction, temperature and humidity for a city."""
    try:
        r = requests.get(f"{BASE_URL}/api/weather?city={city}", timeout=10)
        d = r.json()
        return (f"Weather for {city}:\nTemp: {d['temp']}°C | Humidity: {d['humidity']}%\nWind: {d['wind_speed']} m/s from {d['wind_direction']} ({d['wind_deg']}°)\nConditions: {d['description']}")
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_fire_hotspots(city: str) -> str:
    """Get NASA FIRMS satellite fire hotspots within 500km of a city."""
    coords = {"Delhi":(28.61,77.21),"Mumbai":(19.08,72.88),"Kolkata":(22.57,88.36),"Chennai":(13.08,80.27),"Bangalore":(12.97,77.59),"Hyderabad":(17.39,78.49),"Jaipur":(26.91,75.79),"Lucknow":(26.85,80.95)}
    lat, lon = coords.get(city, (28.61, 77.21))
    try:
        r = requests.get(f"{BASE_URL}/api/fires?lat={lat}&lon={lon}&radius=500", timeout=10)
        d = r.json()
        count = d.get("count", 0)
        if count == 0:
            return f"No active fire hotspots within 500km of {city} in last 24 hours."
        return f"Fire Hotspots near {city}: {count} active fires detected\nSource: NASA FIRMS VIIRS\nThese may be contributing to elevated AQI depending on wind direction."
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def analyse_pollution_source(city: str) -> str:
    """Autonomously trace pollution sources by combining AQI, wind and NASA fire data."""
    try:
        aqi_d  = requests.get(f"{BASE_URL}/api/aqi?city={city}", timeout=10).json()
        wind_d = requests.get(f"{BASE_URL}/api/weather?city={city}", timeout=10).json()
        coords = {"Delhi":(28.61,77.21),"Mumbai":(19.08,72.88),"Kolkata":(22.57,88.36),"Chennai":(13.08,80.27),"Bangalore":(12.97,77.59)}
        lat, lon = coords.get(city, (28.61, 77.21))
        fire_d = requests.get(f"{BASE_URL}/api/fires?lat={lat}&lon={lon}", timeout=10).json()
        aqi = aqi_d.get("aqi", 0)
        wind_spd = wind_d.get("wind_speed", 0)
        wind_dir = wind_d.get("wind_direction", "Unknown")
        humidity = wind_d.get("humidity", 0)
        fires = fire_d.get("count", 0)
        result = f"=== Pollution Source Analysis: {city} ===\nAQI: {aqi} ({aqi_d.get('category')})\nPM2.5: {aqi_d.get('pm25')} µg/m³\n\nWind: {wind_spd} m/s from {wind_dir}\nHumidity: {humidity}% {'— trapping pollutants' if humidity>70 else ''}\n{'LOW WIND: pollutants stagnant' if wind_spd<3 else ''}\nFire hotspots (500km): {fires}\n\nProbable sources:\n"
        if city in ["Delhi","Kanpur","Lucknow","Patna","Jaipur"]:
            result += "  1. Vehicular emissions\n  2. Industrial/thermal power\n"
            if fires > 5:
                result += "  3. Stubble burning (fires detected upwind)\n"
            result += "  4. Construction dust\n"
        elif city in ["Mumbai","Pune","Surat"]:
            result += "  1. Industrial (petrochemical, textile)\n  2. Vehicular traffic\n  3. Port activity\n"
        else:
            result += "  1. Vehicular emissions\n  2. Construction dust\n"
        return result
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_health_advisory(city: str, group: str = "general") -> str:
    """Get health advisory for a city. group: general, children, elderly, athletes."""
    try:
        d   = requests.get(f"{BASE_URL}/api/aqi?city={city}", timeout=10).json()
        aqi = d.get("aqi", 0)
        cat = d.get("category", "Unknown")
        advisories = {
            "general":  {"Good":"No restrictions.","Satisfactory":"Sensitive people limit outdoor time.","Moderate":"Wear N95 outdoors.","Poor":"Avoid outdoor activity. N95 required.","Very Poor":"Stay indoors. Health alert.","Severe":"EMERGENCY. Do not go outside."},
            "children": {"Good":"Safe for outdoor play.","Satisfactory":"Monitor for symptoms.","Moderate":"Limit outdoor PE classes.","Poor":"Cancel outdoor school events.","Very Poor":"Children must stay indoors.","Severe":"EMERGENCY — children must not go outside."},
            "elderly":  {"Good":"No restrictions.","Satisfactory":"Limit extended outdoor time.","Moderate":"Stay indoors 10am–6pm.","Poor":"Stay indoors. Consult doctor.","Very Poor":"Do not go outdoors.","Severe":"EMERGENCY — seek medical support."},
            "athletes": {"Good":"Safe for all training.","Satisfactory":"Avoid intense outdoor training.","Moderate":"Move training indoors.","Poor":"No outdoor training.","Very Poor":"Cancel all outdoor sports.","Severe":"No exercise. Rest indoors."},
        }
        grp = group.lower() if group.lower() in advisories else "general"
        adv = advisories[grp].get(cat, "Consult local health authorities.")
        return (f"Health Advisory — {city} ({group.title()})\nAQI: {aqi} ({cat})\nRisk: {d.get('risk')}\n\nAdvisory: {adv}\nMask: {'N95 required' if aqi>150 else 'Optional'} | Windows: {'Keep closed' if aqi>200 else 'OK to open'} | Exercise: {'Avoid outdoors' if aqi>150 else 'Safe'}")
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def compare_cities(city1: str, city2: str) -> str:
    """Compare air quality between two cities side by side."""
    try:
        r1 = requests.get(f"{BASE_URL}/api/aqi?city={city1}", timeout=10).json()
        r2 = requests.get(f"{BASE_URL}/api/aqi?city={city2}", timeout=10).json()
        aqi1, aqi2 = r1.get("aqi",0), r2.get("aqi",0)
        safer = city1 if aqi1 < aqi2 else city2
        return (f"AQI Comparison: {city1} vs {city2}\n\n{city1}: AQI {aqi1} ({r1.get('category')}) | PM2.5: {r1.get('pm25')} µg/m³\n{city2}: AQI {aqi2} ({r2.get('category')}) | PM2.5: {r2.get('pm25')} µg/m³\n\nVerdict: {safer} has better air quality by {abs(aqi1-aqi2)} AQI points.")
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_global_stats() -> str:
    """Get global air quality stats — most polluted and cleanest cities from 23,462 cities worldwide."""
    try:
        d = requests.get(f"{BASE_URL}/api/global-stats", timeout=15).json()
        result = f"Global AQI Stats\nCities: {d.get('total_cities')} | Countries: {d.get('total_countries')} | Avg AQI: {d.get('global_avg_aqi')}\n\nMost Polluted:\n"
        for i,c in enumerate(d.get("top_polluted",[])[:5], 1):
            result += f"  {i}. {c['City']}, {c['Country']} — AQI {c['aqi']}\n"
        result += "\nCleanest Cities:\n"
        for i,c in enumerate(d.get("cleanest",[])[:5], 1):
            result += f"  {i}. {c['City']}, {c['Country']} — AQI {c['aqi']}\n"
        return result
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    mcp.run()
