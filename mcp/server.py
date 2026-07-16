from mcp.server.fastmcp import FastMCP
import requests
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

mcp = FastMCP("AirSentinel")

@mcp.tool()
def get_aqi(city: str) -> str:
    """Get real-time AQI for any city."""
    try:
        r = requests.get(f"https://airsentinel-backend.onrender.com/api/aqi?city={city}", timeout=10)
        d = r.json()
        return f"{city}: AQI {d['aqi']} ({d['category']}) - PM2.5: {d['pm25']} - Risk: {d['risk']}"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_forecast(city: str) -> str:
    """Get 7-day AQI forecast for an Indian city."""
    try:
        r = requests.get(f"https://airsentinel-backend.onrender.com/api/forecast?city={city}", timeout=10)
        d = r.json()
        preds = d.get('predictions', [])
        result = f"7-day forecast for {city}:\n"
        for p in preds:
            result += f"  {p['date']}: AQI {p['aqi']}\n"
        return result
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_global_stats() -> str:
    """Get global air quality statistics."""
    try:
        r = requests.get("https://airsentinel-backend.onrender.com/api/global-stats", timeout=10)
        d = r.json()
        return f"Global AQI Stats: {d['total_cities']} cities, {d['total_countries']} countries, avg AQI: {d['global_avg_aqi']}"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    mcp.run()