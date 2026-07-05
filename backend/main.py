import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agent import run_agent
from aqi_tools import get_aqi_data, get_weather, get_fire_hotspots, get_global_stations, get_india_stations
from forecast import forecast_aqi, get_available_cities, get_historical_aqi, get_global_aqi_stats

load_dotenv()

app = FastAPI(title="AirSentinel API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class AgentQuery(BaseModel):
    question: str
    city: str = "Delhi"

@app.get("/")
def root():
    return {"status": "AirSentinel API running"}

@app.get("/api/aqi")
def aqi(city: str = "Delhi"):
    data = get_aqi_data(city)
    if not data:
        raise HTTPException(status_code=404, detail="No AQI data found")
    return data

@app.get("/api/weather")
def weather(city: str = "Delhi"):
    data = get_weather(city)
    if not data:
        raise HTTPException(status_code=404, detail="Weather data unavailable")
    return data

@app.get("/api/fires")
def fires(lat: float = 28.6, lon: float = 77.2, radius: float = 500):
    return get_fire_hotspots(lat, lon, radius)

@app.get("/api/global-stations")
def global_stations():
    return get_global_stations()

@app.get("/api/india-stations")
def india_stations():
    return get_india_stations()

@app.get("/api/forecast")
def forecast(city: str = "Delhi", days: int = 7):
    return forecast_aqi(city, days)

@app.get("/api/forecast/cities")
def forecast_cities():
    return get_available_cities()

@app.get("/api/forecast/history")
def forecast_history(city: str = "Delhi", days: int = 30):
    return get_historical_aqi(city, days)

@app.get("/api/global-stats")
def global_stats():
    return get_global_aqi_stats()

@app.post("/api/agent")
def agent_query(body: AgentQuery):
    try:
        result = run_agent(body.question, body.city)
        return {"answer": result, "city": body.city}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
