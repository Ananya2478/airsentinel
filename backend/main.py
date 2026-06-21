import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agent import run_agent
from aqi_tools import get_aqi_data, get_weather, get_fire_hotspots

load_dotenv()

app = FastAPI(title="AirSentinel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request models ────────────────────────────────────────────────
class AgentQuery(BaseModel):
    question: str
    city: str = "Delhi"

# ── Routes ───────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "AirSentinel API is running"}

@app.get("/api/aqi")
def aqi(city: str = "Delhi"):
    """Fetch live AQI data for a city."""
    data = get_aqi_data(city)
    if not data:
        raise HTTPException(status_code=404, detail="No AQI data found for this city")
    return data

@app.get("/api/weather")
def weather(city: str = "Delhi"):
    """Fetch wind and weather data for a city."""
    data = get_weather(city)
    if not data:
        raise HTTPException(status_code=404, detail="Weather data unavailable")
    return data

@app.get("/api/fires")
def fires(lat: float = 28.6, lon: float = 77.2, radius: float = 500):
    """Fetch NASA FIRMS fire hotspots near a location."""
    data = get_fire_hotspots(lat, lon, radius)
    return data

@app.get("/api/india-stations")
def india_stations():
    """Fetch AQI readings from major Indian cities."""
    cities = [
        "Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore",
        "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
        "Kanpur", "Patna", "Bhopal", "Nagpur", "Surat"
    ]
    results = []
    for city in cities:
        data = get_aqi_data(city)
        if data:
            results.append(data)
    return results

@app.post("/api/agent")
def agent_query(body: AgentQuery):
    """Run the AirSentinel agent with a natural language question."""
    try:
        result = run_agent(body.question, body.city)
        return {"answer": result, "city": body.city}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
