import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from aqi_tools import get_aqi_data, get_weather, get_fire_hotspots, aqi_category

load_dotenv()

# ── Tools ─────────────────────────────────────────────────────────

@tool
def fetch_aqi(city: str) -> str:
    """Fetch the current real-time AQI and pollutant levels for any city."""
    data = get_aqi_data(city)
    if not data:
        return f"No AQI data available for {city}."
    return (
        f"City: {data['city']} ({data.get('country','India')})\n"
        f"AQI: {data['aqi']} ({data['category']})\n"
        f"PM2.5: {data['pm25']} µg/m³\n"
        f"PM10: {data['pm10']} µg/m³\n"
        f"NO2: {data['no2']} µg/m³\n"
        f"O3: {data['o3']} µg/m³\n"
        f"Risk Level: {data['risk']}\n"
        f"Source: {data['source']}"
    )


@tool
def fetch_weather(city: str) -> str:
    """Fetch current wind speed, wind direction, temperature and humidity for a city."""
    data = get_weather(city)
    if not data:
        return f"Weather data unavailable for {city}."
    return (
        f"City: {data['city']}\n"
        f"Temperature: {data['temp']}°C\n"
        f"Humidity: {data['humidity']}%\n"
        f"Wind Speed: {data['wind_speed']} m/s\n"
        f"Wind Direction: {data['wind_direction']} ({data['wind_deg']}°)\n"
        f"Conditions: {data['description']}\n"
        f"Source: {data['source']}"
    )


@tool
def fetch_fire_hotspots(city: str) -> str:
    """Fetch NASA satellite fire hotspots near a city."""
    from aqi_tools import CITY_COORDS
    coords = CITY_COORDS.get(city, (28.6139, 77.2090))
    lat, lon = coords
    data = get_fire_hotspots(lat, lon, radius_km=500)
    if data["count"] == 0:
        return f"No active fire hotspots detected within 500km of {city} in the last 24 hours."
    return (
        f"Active fire hotspots within 500km of {city}: {data['count']}\n"
        f"Source: {data['source']}\n"
        f"These fires may be contributing to elevated pollution levels."
    )


@tool
def analyse_pollution_source(city: str) -> str:
    """Analyse the probable source of air pollution for a city."""
    from aqi_tools import CITY_COORDS
    aqi  = get_aqi_data(city)
    wind = get_weather(city)
    coords = CITY_COORDS.get(city, (28.6139, 77.2090))
    fires = get_fire_hotspots(coords[0], coords[1], 500)

    if not aqi:
        return f"Unable to analyse pollution source for {city}."

    analysis = [f"=== Pollution Source Analysis for {city} ==="]
    analysis.append(f"Current AQI: {aqi['aqi']} ({aqi['category']})")

    if aqi['aqi'] > 200:
        analysis.append("ALERT: AQI is in the unhealthy range.")

    if wind:
        analysis.append(f"\nMeteorological conditions:")
        analysis.append(f"  Wind: {wind['wind_speed']} m/s from {wind['wind_direction']}")
        analysis.append(f"  Humidity: {wind['humidity']}%")
        if wind['wind_speed'] < 3:
            analysis.append("  LOW WIND SPEED: Pollutants are stagnant.")

    if fires['count'] > 0:
        analysis.append(f"\nFire hotspots detected: {fires['count']} within 500km")
    else:
        analysis.append("\nNo active fire hotspots detected nearby.")

    analysis.append("\nProbable pollution sources:")
    if city in ["Delhi", "Kanpur", "Lucknow", "Patna"]:
        analysis.append("  - Vehicular emissions")
        analysis.append("  - Industrial activity")
        if fires['count'] > 5:
            analysis.append("  - Stubble burning")
        analysis.append("  - Construction dust")
    elif city in ["Mumbai", "Pune", "Surat"]:
        analysis.append("  - Industrial emissions")
        analysis.append("  - Vehicular traffic")
        analysis.append("  - Port activity")
    else:
        analysis.append("  - Vehicular emissions")
        analysis.append("  - Construction activity")

    return "\n".join(analysis)


@tool
def get_health_advisory(city: str) -> str:
    """Generate a health advisory based on current AQI for a city."""
    data = get_aqi_data(city)
    if not data:
        return f"Unable to get health advisory for {city}."

    aqi_value = data['aqi']
    cat = aqi_category(aqi_value)

    advisories = {
        "Good":         {"general": "Air quality is good. No restrictions needed.", "children": "Safe for outdoor activities.", "elderly": "No special precautions needed."},
        "Satisfactory": {"general": "Acceptable for most people.", "children": "Generally safe.", "elderly": "Consider limiting extended outdoor activities."},
        "Moderate":     {"general": "Sensitive groups may be affected. Wear N95 mask.", "children": "Avoid prolonged outdoor activities.", "elderly": "Stay indoors during peak hours."},
        "Poor":         {"general": "Everyone may experience effects. Wear N95 mask.", "children": "AVOID outdoor activities.", "elderly": "Stay indoors."},
        "Very Poor":    {"general": "Health alert — serious effects possible.", "children": "Do NOT go outside.", "elderly": "Emergency level — remain indoors."},
        "Severe":       {"general": "EMERGENCY CONDITIONS.", "children": "EMERGENCY — do not go outside.", "elderly": "EMERGENCY — seek medical support."},
    }

    label = cat["label"]
    adv = advisories.get(label, advisories["Moderate"])

    return (
        f"=== Health Advisory for {city} ===\n"
        f"AQI: {aqi_value} — {label}\n"
        f"Risk: {cat['risk']}\n\n"
        f"General public: {adv['general']}\n"
        f"Children: {adv['children']}\n"
        f"Elderly: {adv['elderly']}\n\n"
        f"Mask: {'N95 recommended' if aqi_value > 150 else 'Optional'}\n"
        f"Windows: {'Keep closed' if aqi_value > 200 else 'Ventilation acceptable'}\n"
        f"Outdoor exercise: {'Avoid' if aqi_value > 150 else 'Safe'}"
    )


@tool
def search_knowledge_base(query: str) -> str:
    """Search the RAG knowledge base of WHO air quality documents."""
    try:
        from rag import search_documents
        return search_documents(query, n_results=3)
    except Exception as e:
        return f"Knowledge base search unavailable: {e}"


# ── Tool list ─────────────────────────────────────────────────────
tools = [fetch_aqi, fetch_weather, fetch_fire_hotspots,
         analyse_pollution_source, get_health_advisory, search_knowledge_base]


# ── Agent runner ──────────────────────────────────────────────────
def run_agent(question: str, city: str = "Delhi") -> str:
    """Run the AirSentinel agent."""

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
    )

    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content="""You are AirSentinel, a highly intelligent AI assistant with deep expertise in air quality, environment and health. You can answer ANY question — not just about AQI.

For air quality questions: always use your tools to get real data first, then give a detailed answer.
For general knowledge questions: answer directly from your knowledge — no need to use tools.
For creative or fun questions: be engaging, interesting and helpful.
For questions combining AQI with lifestyle (food, sports, travel, relationships, fashion etc.): use your AQI tools AND apply creative, interesting reasoning.

Examples of how to handle questions:
- "How does Delhi AQI affect biryani?" → fetch Delhi AQI, explain how pollution affects outdoor cooking, ingredients, food safety and taste
- "Should I go for a morning run in Mumbai?" → fetch Mumbai AQI, give specific running advice with timing recommendations  
- "What is the capital of France?" → just answer: Paris
- "Tell me a joke about air pollution" → tell a funny, relevant joke
- "How many cigarettes am I smoking by breathing Delhi air?" → fetch Delhi AQI, calculate cigarette equivalent
- "Which city is better to live in — Delhi or Bangalore?" → fetch both AQIs, compare comprehensively

NEVER say you cannot process a question or that it is outside your scope.
ALWAYS give a helpful, interesting, detailed response.
Be conversational, warm, witty and engaging like the best AI assistant.
Use emojis occasionally to make responses more friendly.
Cite your data sources when using real data."""),
        HumanMessage(content=f"City context: {city}. Question: {question}")
    ]

    # Agentic loop
    for _ in range(6):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_map  = {t.name: t for t in tools}

            if tool_name in tool_map:
                try:
                    result = tool_map[tool_name].invoke(tool_args)
                except Exception as e:
                    result = f"Tool error: {e}"
                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                ))

    return response.content
