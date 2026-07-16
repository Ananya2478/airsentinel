# AirSentinel 🌍
### Agentic AI System for Global Air Quality Intelligence

A full-stack agentic AI platform that investigates air quality like an environmental scientist — tracing pollution to its source, forecasting future AQI, and generating health advisories using real-time satellite data and WHO guidelines.

## Live Demo
Frontend: https://airsentinel-five.vercel.app
Backend API: https://airsentinel-backend.onrender.com

---

## Features
- Live AQI Map — 60+ cities across 6 continents with real-time data
- AI Agent — ask anything about air quality in natural language
- RAG Pipeline — searches WHO Air Quality Guidelines (11,501 chunks in ChromaDB)
- NASA FIRMS — active satellite fire hotspot detection
- Pollution Source Tracing — correlates wind direction with fire hotspots
- 7-Day Forecast — statistical model trained on 5 years of CPCB data
- Analytics Dashboard — 23,462 cities across 175 countries

---

## Tech Stack
Frontend: React 18, Vite, Leaflet.js, Recharts
Backend: FastAPI, Python
AI Agent: LangChain, Groq LLaMA 3.3 70B
RAG: ChromaDB, sentence-transformers (all-MiniLM-L6-v2)
Data: OpenAQ API, NASA FIRMS VIIRS, OpenWeatherMap
Deployment: Vercel (frontend), Render (backend)

---

## Data Sources
- OpenAQ API — real-time AQI station data (openaq.org)
- NASA FIRMS VIIRS — active fire hotspots (firms.modaps.eosdis.nasa.gov)
- WHO Global Air Quality Guidelines 2021 — RAG knowledge base
- Kaggle Air Quality Data India (rohanrao) — 5yr CPCB historical data
- Kaggle Global Air Pollution Dataset (hasibalmuzdadid) — 23,462 cities

---

## Architecture
User Query
    ↓
LangChain Agent (Groq LLaMA 3.3)
    ↓
6 Autonomous Tools:
  1. Live AQI Fetcher (OpenAQ API)
  2. NASA Fire Hotspot Detector (FIRMS VIIRS)
  3. Wind Trajectory Analyser (OpenWeatherMap)
  4. Pollution Source Tracer (wind + fire correlation)
  5. WHO Document Search (RAG + ChromaDB)
  6. Health Advisory Generator
    ↓
Structured Response + Map Update

---

## Setup

### 1. Clone
git clone https://github.com/Ananya2478/airsentinel.git
cd airsentinel

### 2. Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

### 3. Environment
Create backend/.env:
GROQ_API_KEY=your_groq_key_here

Get free key at console.groq.com

### 4. RAG Setup
Download WHO Air Quality Guidelines PDF
Place in backend/data/
Run: python -c "from rag import load_pdfs; load_pdfs()"

### 5. Run
Terminal 1 - Backend:
uvicorn main:app --reload --port 8000

Terminal 2 - Frontend:
cd frontend
npm install
npm run dev

Open http://localhost:3000

---

## API Endpoints
GET  /api/aqi?city=Delhi          - Live AQI data
GET  /api/weather?city=Delhi      - Wind and weather
GET  /api/fires?lat=28&lon=77     - NASA fire hotspots
GET  /api/global-stations         - All global cities
GET  /api/forecast?city=Delhi     - 7-day forecast
GET  /api/global-stats            - Global statistics
POST /api/agent                   - AI agent query

---

## Project Structure
airsentinel/
  backend/
    main.py          - FastAPI server with 8 endpoints
    agent.py         - LangChain agent with 6 tools
    aqi_tools.py     - OpenAQ + NASA + weather data
    rag.py           - RAG pipeline over WHO PDF
    forecast.py      - 7-day AQI forecasting model
    requirements.txt
  frontend/
    src/
      App.jsx        - React app (map, agent, analytics, forecast)
    package.json

---

## Deployment
Frontend: Vercel — auto-deploys on every GitHub push
Backend: Render — FastAPI with 8 REST endpoints

---

## Status
Active development
Next: LangGraph agent, real Prophet forecasting, MCP server
