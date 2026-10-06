# AirSentinel
### Agentic AI System for Global Air Quality Intelligence

An AI-powered platform that investigates air quality like an environmental scientist — tracing pollution to its source, predicting health risks, and generating actionable advisories using real-time data from NASA, OpenAQ and WHO guidelines.

## Features
- Live AQI Map — 60+ cities across 6 continents
- AI Agent — ask "Why is Delhi's AQI high today?"
- RAG Pipeline — searches real WHO Air Quality Guidelines (11,501 chunks in ChromaDB)
- NASA FIRMS — active fire hotspot detection
- Wind and Weather — pollution source tracing
- Analytics — country filter, rankings, category distribution
- Health Advisories — by population group (children, elderly, sensitive)

## Tech Stack
- Frontend: React 18, Vite, Leaflet.js, Recharts
- Backend: FastAPI, Python
- AI Agent: LangChain, Groq (LLaMA 3.3 70B)
- RAG: ChromaDB, sentence-transformers (all-MiniLM-L6-v2)
- Data: OpenAQ API, NASA FIRMS VIIRS, OpenWeatherMap, WHO PDF

## Data Sources
- OpenAQ — real-time AQI station data (openaq.org)
- NASA FIRMS VIIRS — active fire hotspots (firms.modaps.eosdis.nasa.gov)
- WHO Global Air Quality Guidelines 2021 — RAG knowledge base
- OpenWeatherMap — wind and meteorological data

## Setup

### 1. Clone the repo
git clone https://github.com/Ananya2478/airsentinel.git
cd airsentinel

### 2. Backend setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

### 3. Add API key
Create a .env file inside the backend folder and add:
GROQ_API_KEY=your_groq_key_here

Get a free key at console.groq.com

### 4. Load RAG knowledge base
Download the WHO Air Quality Guidelines PDF and place it in backend/data/ then run:
python -c "from rag import load_pdfs; load_pdfs()"

### 5. Start the app
Terminal 1 - backend:
uvicorn main:app --reload --port 8000

Terminal 2 - frontend:
cd frontend
npm install
npm run dev

Open http://localhost:3000

## Project Structure
airsentinel/
  backend/
    main.py         - FastAPI server
    agent.py        - LangChain AI agent with 6 tools
    aqi_tools.py    - OpenAQ + NASA FIRMS + weather data
    rag.py          - RAG pipeline over WHO PDF
    requirements.txt
  frontend/
    src/
      App.jsx       - React app with map, agent chat, analytics
    package.json

## Status
Active development — AQI forecasting model coming next
