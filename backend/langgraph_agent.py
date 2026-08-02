"""
AirSentinel LangGraph Agent
Proper agentic AI with state management, planning and multi-step reasoning.
"""

import os
from typing import Annotated, TypedDict, Literal
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from aqi_tools import get_aqi_data, get_weather, get_fire_hotspots, aqi_category

load_dotenv()

# ── State definition ──────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    city: str
    question: str
    tools_used: list[str]
    final_answer: str


# ── Tools ─────────────────────────────────────────────────────────

@tool
def fetch_aqi(city: str) -> str:
    """Fetch real-time AQI and pollutant levels for any city."""
    data = get_aqi_data(city)
    if not data:
        return f"No AQI data for {city}."
    return (
        f"City: {data['city']} ({data.get('country','India')})\n"
        f"AQI: {data['aqi']} ({data['category']})\n"
        f"PM2.5: {data['pm25']} µg/m³ | PM10: {data['pm10']} µg/m³\n"
        f"NO2: {data['no2']} µg/m³ | O3: {data['o3']} µg/m³\n"
        f"Risk: {data['risk']} | Source: {data['source']}"
    )


@tool
def fetch_weather(city: str) -> str:
    """Fetch wind speed, direction, temperature and humidity for a city."""
    data = get_weather(city)
    if not data:
        return f"Weather unavailable for {city}."
    return (
        f"Temp: {data['temp']}°C | Humidity: {data['humidity']}%\n"
        f"Wind: {data['wind_speed']} m/s from {data['wind_direction']}\n"
        f"Conditions: {data['description']}"
    )


@tool
def fetch_fire_hotspots(city: str) -> str:
    """Fetch NASA FIRMS satellite fire hotspots near a city (500km radius)."""
    from aqi_tools import CITY_COORDS, GLOBAL_CITIES
    if city in GLOBAL_CITIES:
        lat, lon, _ = GLOBAL_CITIES[city]
    else:
        coords = CITY_COORDS.get(city, (28.6139, 77.2090))
        lat, lon = coords
    data = get_fire_hotspots(lat, lon, radius_km=500)
    if data["count"] == 0:
        return f"No active fire hotspots within 500km of {city} in last 24 hours."
    return f"Active fires near {city}: {data['count']} hotspots detected (NASA FIRMS VIIRS)"


@tool
def analyse_pollution_source(city: str) -> str:
    """Trace pollution source by combining AQI, wind direction and fire hotspot data."""
    from aqi_tools import CITY_COORDS, GLOBAL_CITIES
    aqi_data  = get_aqi_data(city)
    wind_data = get_weather(city)
    if city in GLOBAL_CITIES:
        lat, lon, _ = GLOBAL_CITIES[city]
    else:
        lat, lon = CITY_COORDS.get(city, (28.6139, 77.2090))
    fires = get_fire_hotspots(lat, lon, 500)

    if not aqi_data:
        return f"Cannot analyse pollution source for {city}."

    result = [f"Pollution Analysis: {city}"]
    result.append(f"AQI: {aqi_data['aqi']} ({aqi_data['category']}) | PM2.5: {aqi_data['pm25']} µg/m³")

    if wind_data:
        result.append(f"Wind: {wind_data['wind_speed']} m/s from {wind_data['wind_direction']}")
        if wind_data['wind_speed'] < 3:
            result.append("⚠ LOW WIND: Pollutants are stagnant and accumulating")
        if wind_data['humidity'] > 70:
            result.append("⚠ HIGH HUMIDITY: Trapping pollutants near ground level")

    result.append(f"Fire hotspots (500km): {fires['count']}")

    result.append("\nProbable sources:")
    if city in ["Delhi", "Kanpur", "Lucknow", "Patna", "Jaipur", "Amritsar"]:
        result.append("  1. Vehicular emissions (major contributor)")
        result.append("  2. Industrial activity and thermal power plants")
        if fires['count'] > 5:
            result.append("  3. ⚠ Stubble burning detected upwind — significant contributor")
        result.append("  4. Construction dust and road dust")
    elif city in ["Mumbai", "Pune", "Surat", "Ahmedabad"]:
        result.append("  1. Industrial emissions (petrochemical, textile)")
        result.append("  2. Vehicular traffic")
        result.append("  3. Port and shipping activity")
    elif city in ["Beijing", "Shanghai", "Wuhan"]:
        result.append("  1. Industrial emissions")
        result.append("  2. Coal burning")
        result.append("  3. Vehicular traffic")
    else:
        result.append("  1. Vehicular emissions")
        result.append("  2. Local industrial activity")

    return "\n".join(result)


@tool
def get_health_advisory(city: str) -> str:
    """Generate detailed health advisory for a city based on current AQI."""
    data = get_aqi_data(city)
    if not data:
        return f"Cannot get health advisory for {city}."

    aqi_val = data['aqi']
    cat = aqi_category(aqi_val)
    label = cat["label"]

    advisories = {
        "Good":         ("✅ Air quality is good. Enjoy outdoor activities.", "Safe for all outdoor activities.", "No restrictions needed."),
        "Satisfactory": ("🟡 Acceptable. Sensitive people should limit prolonged outdoor exertion.", "Generally safe. Monitor for symptoms.", "Consider limiting extended outdoor time."),
        "Moderate":     ("🟠 Sensitive groups affected. Wear N95 mask outdoors.", "Limit outdoor PE. Avoid prolonged outdoor play.", "Stay indoors during peak hours 10am-6pm."),
        "Poor":         ("🔴 Everyone may experience effects. Wear N95 mask.", "⚠ AVOID outdoor activities. Cancel school events.", "Stay indoors. Seek medical advice if symptomatic."),
        "Very Poor":    ("🟣 Health alert. Avoid all outdoor activity.", "🚨 Do NOT go outside.", "🚨 Emergency level. Remain indoors."),
        "Severe":       ("⚫ EMERGENCY. Do not go outside under any circumstances.", "🚨 EMERGENCY — children must not go outside.", "🚨 EMERGENCY — seek medical support immediately."),
    }

    gen, child, elder = advisories.get(label, advisories["Moderate"])

    return (
        f"Health Advisory — {city}\n"
        f"AQI: {aqi_val} ({label}) | Risk: {cat['risk']}\n\n"
        f"General public: {gen}\n"
        f"Children: {child}\n"
        f"Elderly: {elder}\n\n"
        f"Mask: {'N95 required 😷' if aqi_val > 150 else 'Optional'}\n"
        f"Windows: {'Keep closed 🪟' if aqi_val > 200 else 'Can ventilate'}\n"
        f"Outdoor exercise: {'❌ Avoid' if aqi_val > 150 else '✅ Safe'}"
    )


@tool
def search_knowledge_base(query: str) -> str:
    """Search WHO Air Quality Guidelines using RAG for research-backed answers."""
    try:
        from rag import search_documents
        return search_documents(query, n_results=3)
    except Exception as e:
        return f"Knowledge base unavailable: {e}"


# ── Tool list ─────────────────────────────────────────────────────
tools = [
    fetch_aqi,
    fetch_weather,
    fetch_fire_hotspots,
    analyse_pollution_source,
    get_health_advisory,
    search_knowledge_base,
]

tool_node = ToolNode(tools)

# ── LLM ──────────────────────────────────────────────────────────
def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
    ).bind_tools(tools)


SYSTEM_PROMPT = """You are AirSentinel, a highly intelligent AI assistant with deep expertise in air quality, environment and health. You can answer ANY question.

For air quality questions: always use your tools to get real data first.
For general questions: answer directly from knowledge.
For creative questions (food, sports, lifestyle + AQI): use tools AND creative reasoning.

Always be:
- Helpful, warm and engaging
- Data-driven when discussing air quality
- Creative and interesting for lifestyle questions
- Never refuse to answer any question

Examples:
- "How does Delhi AQI affect biryani?" → fetch AQI, explain effects creatively
- "How many cigarettes = Delhi air?" → fetch AQI, calculate cigarette equivalent  
- "Tell me a joke" → tell a good joke
- "Capital of France?" → Paris"""


# ── Graph nodes ───────────────────────────────────────────────────

def agent_node(state: AgentState) -> AgentState:
    """Main reasoning node — decides what to do next."""
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)

    # Track which tools were called
    tools_used = state.get("tools_used", [])
    if response.tool_calls:
        for tc in response.tool_calls:
            tools_used.append(tc["name"])

    return {
        "messages": [response],
        "tools_used": tools_used,
    }


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Decide whether to call tools or end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def final_node(state: AgentState) -> AgentState:
    """Extract final answer from state."""
    last_message = state["messages"][-1]
    return {
        "final_answer": last_message.content,
    }


# ── Build graph ───────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("agent",  agent_node)
    graph.add_node("tools",  tool_node)
    graph.add_node("final",  final_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end":   "final",
        }
    )

    graph.add_edge("tools", "agent")
    graph.add_edge("final", END)

    return graph.compile()


# ── Public interface ──────────────────────────────────────────────

_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_langgraph_agent(question: str, city: str = "Delhi") -> dict:
    """
    Run the LangGraph agent and return answer + metadata.
    Returns: {answer, tools_used, city}
    """
    graph = get_graph()

    initial_state = {
        "messages": [HumanMessage(content=f"City context: {city}. Question: {question}")],
        "city":       city,
        "question":   question,
        "tools_used": [],
        "final_answer": "",
    }

    result = graph.invoke(initial_state)

    return {
        "answer":     result.get("final_answer", "Unable to process query."),
        "tools_used": result.get("tools_used", []),
        "city":       city,
    }
