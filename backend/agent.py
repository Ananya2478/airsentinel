import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from aqi_tools import get_aqi_data, get_weather, get_fire_hotspots, aqi_category

load_dotenv()

# ── Tools ─────────────────────────────────────────────────────────

@tool
def fetch_aqi(city: str) -> str:
    """
    Fetch the current real-time AQI and pollutant levels for an Indian city.
    Returns PM2.5, PM10, NO2, O3 values and the overall AQI category.
    Use this to get current air quality data.
    """
    data = get_aqi_data(city)
    if not data:
        return f"No AQI data available for {city}."
    return (
        f"City: {data['city']}\n"
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
    """
    Fetch current wind speed, wind direction, temperature and humidity for a city.
    Use this to understand how pollution is being transported or dispersed.
    Wind direction tells us where pollution is coming FROM.
    """
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
    """
    Fetch NASA satellite fire hotspots near a city.
    Fire hotspots indicate active burning — stubble burning, forest fires, industrial fires.
    Use this to investigate if fires are a contributing source of air pollution.
    """
    from aqi_tools import CITY_COORDS
    coords = CITY_COORDS.get(city, (28.6139, 77.2090))
    lat, lon = coords
    data = get_fire_hotspots(lat, lon, radius_km=500)
    if data["count"] == 0:
        return f"No active fire hotspots detected within 500km of {city} in the last 24 hours."
    return (
        f"Active fire hotspots within 500km of {city}: {data['count']}\n"
        f"Source: {data['source']}\n"
        f"Note: {data['note']}\n"
        f"These fires may be contributing to elevated pollution levels "
        f"depending on wind direction."
    )


@tool
def analyse_pollution_source(city: str) -> str:
    """
    Analyse the probable source of air pollution for a city by combining
    AQI data, wind direction, and fire hotspot information.
    Use this to answer 'why is the air bad' type questions.
    """
    from aqi_tools import CITY_COORDS
    aqi  = get_aqi_data(city)
    wind = get_weather(city)
    coords = CITY_COORDS.get(city, (28.6139, 77.2090))
    fires = get_fire_hotspots(coords[0], coords[1], 500)

    if not aqi:
        return f"Unable to analyse pollution source — no AQI data for {city}."

    analysis = []
    analysis.append(f"=== Pollution Source Analysis for {city} ===")
    analysis.append(f"Current AQI: {aqi['aqi']} ({aqi['category']})")

    if aqi['aqi'] > 200:
        analysis.append("ALERT: AQI is in the unhealthy range.")

    if wind:
        analysis.append(f"\nMeteorological conditions:")
        analysis.append(f"  Wind: {wind['wind_speed']} m/s from {wind['wind_direction']}")
        analysis.append(f"  Humidity: {wind['humidity']}% — {'high humidity traps pollutants' if wind['humidity'] > 70 else 'moderate humidity'}")
        if wind['wind_speed'] < 3:
            analysis.append("  LOW WIND SPEED: Pollutants are stagnant and not dispersing.")

    if fires['count'] > 0:
        analysis.append(f"\nFire hotspots detected: {fires['count']} within 500km")
        if wind:
            analysis.append(f"  Wind is from {wind['wind_direction']} — fires upwind may be contributing to pollution.")
    else:
        analysis.append("\nNo active fire hotspots detected nearby.")

    analysis.append("\nProbable pollution sources:")
    if city in ["Delhi", "Kanpur", "Lucknow", "Patna"]:
        analysis.append("  - Vehicular emissions (high traffic density)")
        analysis.append("  - Industrial activity (thermal power plants)")
        if fires['count'] > 5:
            analysis.append("  - Stubble burning (fire hotspots detected upwind)")
        analysis.append("  - Construction dust")
    elif city in ["Mumbai", "Pune", "Surat"]:
        analysis.append("  - Industrial emissions (petrochemical, textile)")
        analysis.append("  - Vehicular traffic")
        analysis.append("  - Port activity")
    elif city in ["Chennai", "Bangalore", "Hyderabad"]:
        analysis.append("  - Vehicular emissions")
        analysis.append("  - Construction activity")
        analysis.append("  - Relatively lower industrial contribution")

    return "\n".join(analysis)


@tool
def get_health_advisory(city: str) -> str:
    """
    Generate a health advisory based on the current AQI value for a city.
    Provides specific recommendations for different population groups.
    Use this to answer health-related questions about air quality.
    """
    data = get_aqi_data(city)
    if not data:
        return f"Unable to get health advisory — no AQI data for {city}."

    aqi_value = data['aqi']
    cat = aqi_category(aqi_value)

    advisories = {
        "Good": {
            "general":   "Air quality is good. No restrictions needed.",
            "children":  "Safe for outdoor activities.",
            "elderly":   "No special precautions needed.",
            "sensitive": "No special precautions needed.",
        },
        "Satisfactory": {
            "general":   "Air quality is acceptable. Unusually sensitive people should consider reducing prolonged outdoor exertion.",
            "children":  "Generally safe. Monitor for any respiratory symptoms.",
            "elderly":   "Consider limiting extended outdoor activities.",
            "sensitive": "Reduce prolonged outdoor exertion.",
        },
        "Moderate": {
            "general":   "Members of sensitive groups may experience health effects. Wear N95 mask outdoors.",
            "children":  "Avoid prolonged outdoor activities. Keep windows closed.",
            "elderly":   "Stay indoors during peak hours (10am-6pm).",
            "sensitive": "Avoid outdoor activities. Use air purifier indoors.",
        },
        "Poor": {
            "general":   "Everyone may begin to experience health effects. Wear N95 mask at all times outdoors.",
            "children":  "AVOID outdoor activities. Schools should cancel outdoor events.",
            "elderly":   "Stay indoors. Seek medical attention if experiencing symptoms.",
            "sensitive": "Do not go outdoors. Use air purifier indoors.",
        },
        "Very Poor": {
            "general":   "Health alert — everyone may experience serious health effects.",
            "children":  "Do NOT go outside. Schools should be closed.",
            "elderly":   "Emergency level — remain indoors. Consult doctor.",
            "sensitive": "Medical emergency risk. Stay indoors with purifier.",
        },
        "Severe": {
            "general":   "EMERGENCY CONDITIONS. Avoid all outdoor activities.",
            "children":  "EMERGENCY — do not go outside under any circumstances.",
            "elderly":   "EMERGENCY — seek shelter and medical support.",
            "sensitive": "EMERGENCY — avoid all outdoor exposure.",
        },
    }

    label = cat["label"]
    adv   = advisories.get(label, advisories["Moderate"])

    return (
        f"=== Health Advisory for {city} ===\n"
        f"AQI: {aqi_value} — {label}\n"
        f"Risk: {cat['risk']}\n\n"
        f"General public:    {adv['general']}\n"
        f"Children:          {adv['children']}\n"
        f"Elderly:           {adv['elderly']}\n"
        f"Sensitive groups:  {adv['sensitive']}\n\n"
        f"Recommendations:\n"
        f"  • {'Wear N95 mask outdoors' if aqi_value > 150 else 'Mask optional'}\n"
        f"  • {'Keep windows closed' if aqi_value > 200 else 'Ventilation is acceptable'}\n"
        f"  • {'Use air purifier indoors' if aqi_value > 200 else 'Indoor air is generally safe'}\n"
        f"  • {'Avoid outdoor exercise' if aqi_value > 150 else 'Outdoor exercise is safe'}"
    )


@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the RAG knowledge base of WHO and CPCB air quality documents.
    Use this to answer questions about air quality standards, health effects,
    pollution guidelines, historical data, and policy recommendations.
    Always use this tool when asked about standards, guidelines or research.
    """
    from rag import search_documents
    return search_documents(query, n_results=3)


# ── Tool list ─────────────────────────────────────────────────────
tools = [fetch_aqi, fetch_weather, fetch_fire_hotspots, analyse_pollution_source, get_health_advisory, search_knowledge_base]


# ── Agent runner ──────────────────────────────────────────────────
def run_agent(question: str, city: str = "Delhi") -> str:
    """Run the AirSentinel agent using tool calling."""

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2,
    )

    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content="""You are AirSentinel, an expert environmental AI agent specialising in air quality analysis for India.

You have access to real-time AQI data, weather/wind data, NASA fire hotspot data, and pollution source analysis tools.

Your job is to:
1. Answer questions about air quality clearly and accurately
2. Use your tools to fetch real data before answering
3. Explain WHY air quality is bad — trace pollution to its source
4. Give practical, actionable health advice
5. Think like an environmental scientist

Always use tools to get real data. Be specific about pollutants. Cite your sources."""),
        HumanMessage(content=f"City context: {city}. Question: {question}")
    ]

    # Agentic loop — keeps going until no more tool calls
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
                result = tool_map[tool_name].invoke(tool_args)
                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                ))

    return response.content