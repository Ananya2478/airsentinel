# AirSentinel
### Agentic AI System for Global Air Quality Intelligence

A full-stack agentic AI platform that investigates air quality like an environmental scientist — tracing pollution sources, forecasting future AQI and generating health advisories using real-time satellite data, WHO guidelines and trained ML models.

## Live Demo
Frontend: https://airsentinel-five.vercel.app
Backend API: https://airsentinel-backend.onrender.com

---

## Features
- Live AQI Map — 60+ cities across 6 continents with real-time data
- LangGraph AI Agent — autonomous tool selection with state management
- RAG Pipeline — WHO Air Quality Guidelines (11,501 chunks in ChromaDB)
- Prophet ML Forecasting — trained on 5 years of CPCB historical data
- NASA FIRMS — active satellite fire hotspot detection
- Pollution Source Tracing — wind direction and fire hotspot correlation
- Analytics Dashboard — 23,462 cities across 175 countries
- REST API — 8 endpoints deployed on Render

---

## Model Performance (Prophet ML)
City               | MAE   | RMSE
-------------------|-------|------
Mumbai             | 8.59  | 9.72
Kolkata            | 8.70  | 10.64
Shillong           | 7.59  | 9.63
Bangalore          | 12.41 | 15.01
Hyderabad          | 15.38 | 19.79
Delhi              | 30.19 | 47.69
Jaipur             | 20.82 | 28.02

---

## System Architecture

Data Ingestion:
  OpenAQ API        - real-time AQI (60+ cities globally)
  NASA FIRMS VIIRS  - satellite fire hotspot detection
  OpenWeatherMap    - wind speed, direction, meteorology
  Kaggle CPCB       - 5yr daily historical data (26 Indian cities)
  Kaggle Global AQI - snapshot data for 23,462 cities, 175 countries

Processing Layer:
  LangGraph agent   - state management and autonomous tool orchestration
  Prophet ML        - time series forecasting with confidence intervals
  ChromaDB          - vector search over WHO guidelines (11,501 chunks)
  sentence-transformers - all-MiniLM-L6-v2 embeddings
  FastAPI           - 8 REST endpoints with CORS

Presentation Layer:
  React 18 + Leaflet.js - interactive world map
  Recharts          - analytics charts with country filtering
  Vercel            - frontend with CI/CD auto-deploy on GitHub push

---

## Tech Stack
Frontend:    React 18, Vite, Leaflet.js, Recharts
Backend:     FastAPI, Python
AI Agent:    LangGraph, LangChain, Groq LLaMA 3.3 70B
RAG:         ChromaDB, sentence-transformers
Forecasting: Prophet (Meta), scikit-learn, Pandas, NumPy
APIs:        OpenAQ, NASA FIRMS, OpenWeatherMap
Deployment:  Vercel (frontend), Render (backend)

---

## Data Sources
- OpenAQ API - real-time AQI station data (openaq.org)
- NASA FIRMS VIIRS - active fire hotspots (firms.modaps.eosdis.nasa.gov)
- WHO Global Air Quality Guidelines 2021 - RAG knowledge base
- Kaggle: Air Quality Data India (rohanrao) - 5yr CPCB historical data
- Kaggle: Global Air Pollution Dataset (hasibalmuzdadid) - 23,462 cities

---

## API Endpoints
GET  /api/aqi?city=Delhi           - Live AQI data
GET  /api/weather?city=Delhi       - Wind and weather
GET  /api/fires?lat=28&lon=77      - NASA fire hotspots
GET  /api/global-stations          - All global cities
GET  /api/forecast?city=Delhi      - 7-day Prophet forecast
GET  /api/global-stats             - Global statistics
POST /api/agent                    - LangChain agent query
POST /api/agent/langgraph          - LangGraph agent with tool tracking

---

## Setup

1. Clone
git clone https://github.com/Ananya2478/airsentinel.git
cd airsentinel

2. Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

3. Environment - create backend/.env
GROQ_API_KEY=" "
Get free key at console.groq.com

4. RAG Setup
Download WHO Air Quality Guidelines PDF and place in backend/data/
python -c "from rag import load_pdfs; load_pdfs()"

5. Run
Terminal 1: uvicorn main:app --reload --port 8000
Terminal 2: cd frontend && npm install && npm run dev
Open http://localhost:3000

---

## Project Structure
airsentinel/
  backend/
    main.py              - FastAPI server (8 endpoints)
    agent.py             - LangChain agent
    langgraph_agent.py   - LangGraph agent with state management
    aqi_tools.py         - OpenAQ + NASA + weather data fetchers
    rag.py               - RAG pipeline over WHO PDF
    forecast.py          - Prophet forecasting model loader
    models/              - Trained Prophet models + metrics.json
    requirements.txt
  frontend/
    src/App.jsx          - React app (map, agent, analytics, forecast)
  mcp/
    server.py            - MCP server (in development)

---

## Deployment
Frontend: Vercel - auto-deploys on every GitHub push
Backend:  Render - FastAPI serving 8 REST endpoints

---

## Status
Active development - June 2026 to present

Completed:
- LangGraph agent with state management and tool tracking
- Prophet ML forecasting (26 cities, best MAE=7.59 for Shillong)
- Global AQI monitoring across 60+ cities in 6 continents
- RAG pipeline over WHO Air Quality Guidelines (11,501 chunks)
- Full stack deployment on Vercel and Render with CI/CD

In Progress:
- MCP server integration with Claude Desktop
- RAG deployment on cloud vector database
- Extended global city coverage for forecasting
- Real-time alert notification system
