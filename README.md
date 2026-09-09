# AirSentinel

**Agentic AI system for global air quality intelligence** — an LLM agent that autonomously chooses tools (live AQI, weather, satellite fire data, RAG search, health advisories) to investigate air pollution like an environmental analyst, plus a 7-day AQI forecast for Indian cities built on historical CPCB data.

**Live demo:** [airsentinel-five.vercel.app](https://airsentinel-five.vercel.app) · **API:** [airsentinel-backend.onrender.com](https://airsentinel-backend.onrender.com) · **API docs:** `/docs` (FastAPI/Swagger)

---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Forecasting](#forecasting)
- [API Endpoints](#api-endpoints)
- [Data Sources](#data-sources)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)

---

## Overview

AirSentinel combines a tool-calling LLM agent, a RAG pipeline over the WHO Air Quality Guidelines, and a time-series forecasting module behind a FastAPI backend, with a React + Leaflet frontend for exploring live air quality on a world map. Ask it a question — "should I run outdoors in Mumbai today?", "what's causing Delhi's smog?", "how does AQI affect biryani?" — and the agent decides which of its tools to call, pulls real data, and answers in plain language, citing sources where relevant.

## Features

- **Live AQI map** — 59 cities across 6 continents, updated on each request
- **LangGraph agent** — autonomous tool selection with typed state and multi-step tool chaining
- **RAG over WHO guidelines** — 11,501 chunks embedded with `sentence-transformers` in ChromaDB, for grounded, citable health guidance
- **7-day AQI forecasting** — seasonal + trend modeling per city, trained against 5 years of CPCB historical data (26 Indian cities)
- **Pollution source tracing** — correlates AQI with wind direction and NASA FIRMS active-fire detections
- **Health advisories** — tailored guidance by AQI band and audience (general public, children, elderly)
- **Graceful data fallback** — every response is source-labeled (`OpenAQ` / `OpenWeatherMap` / `Simulated`) so the frontend never silently shows fabricated data as real
- **MCP server** *(in development)* — exposes the same tools to Claude Desktop and other MCP clients

## Architecture

```
Data Ingestion                Processing                    Presentation
───────────────               ───────────────                ───────────────
OpenAQ API          ──┐
OpenWeatherMap       ──┤       LangGraph agent                React 18 + Vite
NASA FIRMS VIIRS     ──┼──►    (Groq · Llama 3.3 70B)   ──►    Leaflet map
CPCB (Kaggle, 5yr)   ──┤       ChromaDB + MiniLM RAG           Recharts
WHO AQ Guidelines    ──┘       Seasonal/trend forecast         Vercel
                               FastAPI · 11 REST routes
                               Render
```

Request flow for the agent: the frontend POSTs `{question, city}` to `/api/agent/langgraph` → FastAPI calls into a LangGraph state machine → the `agent` node asks Llama 3.3 70B (via Groq) which of six bound tools to call, if any → a `ToolNode` executes the chosen tool(s) and the result loops back to the `agent` node → once the model stops requesting tools, a `final` node extracts the answer → the API returns `{answer, tools_used, city}`, and the frontend shows which tools fired.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Leaflet.js, Recharts |
| Backend | FastAPI, Python, Uvicorn |
| Agent | LangGraph, LangChain, Groq (Llama 3.3 70B) |
| RAG | ChromaDB, sentence-transformers (`all-MiniLM-L6-v2`) |
| Forecasting | Pandas, NumPy, scikit-learn |
| External APIs | OpenAQ, NASA FIRMS, OpenWeatherMap |
| Deployment | Vercel (frontend), Render (backend) — auto-deploy on push to `main` |

## Forecasting

The forecast endpoint models each Indian city's AQI as a **seasonal + trend decomposition**: a fixed per-city baseline level, an annual seasonal cycle, and a trend term (worsening / stable / improving) derived from 5 years of CPCB daily readings (2015–2020, 26 cities), with confidence bands scaled to each city's historical volatility.

Representative evaluation results (MAE / RMSE, AQI points):

| City | MAE | RMSE |
|---|---|---|
| Shillong | 7.59 | 9.63 |
| Mumbai | 8.59 | 9.72 |
| Kolkata | 8.70 | 10.64 |
| Bangalore | 12.41 | 15.01 |
| Hyderabad | 15.38 | 19.79 |
| Jaipur | 20.82 | 28.02 |
| Delhi | 30.19 | 47.69 |

Delhi and other high-variance cities score worse because their AQI is driven by irregular events (stubble-burning season, winter inversion layers, festival spikes) that a smooth seasonal model underfits — cities with steadier, more seasonal pollution (Shillong, Mumbai) forecast far more accurately.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/aqi?city=` | Live AQI + pollutant levels |
| GET | `/api/weather?city=` | Wind, temperature, humidity |
| GET | `/api/fires?lat=&lon=&radius=` | NASA FIRMS fire hotspots |
| GET | `/api/global-stations` | AQI for all tracked cities |
| GET | `/api/india-stations` | AQI for Indian cities only |
| GET | `/api/forecast?city=&days=` | N-day AQI forecast |
| GET | `/api/forecast/cities` | Cities available for forecasting |
| GET | `/api/forecast/history?city=&days=` | Historical AQI series |
| GET | `/api/global-stats` | Aggregate global statistics |
| POST | `/api/agent` | LangChain agent query |
| POST | `/api/agent/langgraph` | LangGraph agent query, with tool-call tracking |

## Data Sources

- [OpenAQ API](https://openaq.org) — real-time station AQI data
- [NASA FIRMS VIIRS](https://firms.modaps.eosdis.nasa.gov) — active fire hotspot detection
- [WHO Global Air Quality Guidelines (2021)](https://www.who.int) — RAG knowledge base
- [Kaggle: Air Quality Data in India](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india) — 5-year CPCB historical data

## Project Structure

```
airsentinel/
├─ backend/
│  ├─ main.py              FastAPI app (11 routes)
│  ├─ agent.py              LangChain agent (single-loop implementation)
│  ├─ langgraph_agent.py    LangGraph agent (deployed) — state graph, tool tracking
│  ├─ aqi_tools.py          OpenAQ / NASA / OpenWeatherMap fetchers + fallback logic
│  ├─ rag.py                PDF ingestion + ChromaDB RAG pipeline
│  ├─ forecast.py           Seasonal/trend AQI forecasting
│  ├─ data/                 WHO PDF + CPCB CSV (not committed — see Setup)
│  ├─ chroma_db/            Persisted vector store (generated, not committed)
│  └─ requirements.txt
├─ frontend/
│  └─ src/App.jsx           React app — map, agent chat, analytics, forecast
├─ mcp/
│  └─ server.py             MCP server exposing the same tools (in development)
└─ README.md
```

## Setup

**1. Clone**
```bash
git clone https://github.com/Ananya2478/airsentinel.git
cd airsentinel
```

**2. Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Environment** — create `backend/.env`:
```
GROQ_API_KEY=your_key_here          # console.groq.com
OPENWEATHER_KEY=your_key_here       # optional — falls back to simulated weather if unset
```

**4. Load the RAG knowledge base** — place the WHO Air Quality Guidelines PDF in `backend/data/`, then:
```bash
python -c "from rag import load_pdfs; load_pdfs()"
```

**5. Run**
```bash
# Terminal 1
uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend && npm install && npm run dev
```
Frontend runs at airsentinel-five.vercel.app

## Known Limitations

- No authentication or rate limiting on any endpoint; CORS currently allows all origins.
- No automated test suite yet.
- OpenAQ/OpenWeatherMap calls silently fall back to labeled simulated data when the upstream API is unavailable or unauthenticated — check the `source` field in any response to see which is active.
- `/api/global-stats` currently returns fixed placeholder figures rather than being computed from an ingested global dataset.
- Forecast confidence bands are a fixed proportion of historical volatility, not a statistically fitted prediction interval.

## Roadmap

- MCP server integration with Claude Desktop
- Authentication + rate limiting on public endpoints
- Retrieval evaluation harness for the RAG pipeline (precision@k on a labeled query set)
- Ingest the full global AQI dataset to back `/api/global-stats` with real numbers
- Real-time alert notifications
