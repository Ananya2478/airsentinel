import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const API = "http://localhost:8000";

const AQI_COLORS = {
  "Good":         "#00c853",
  "Satisfactory": "#ffd600",
  "Moderate":     "#ff6d00",
  "Poor":         "#d50000",
  "Very Poor":    "#6a1b9a",
  "Severe":       "#37474f",
};

export default function App() {
  const [page,       setPage]       = useState("map");
  const [stations,   setStations]   = useState([]);
  const [selected,   setSelected]   = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [agentCity,  setAgentCity]  = useState("Delhi");
  const [agentQ,     setAgentQ]     = useState("");
  const [agentMsgs,  setAgentMsgs]  = useState([
    { role:"assistant", text:"Hello! I'm AirSentinel. Ask me anything about air quality in India — 'Why is Delhi's AQI high today?', 'Is it safe to jog in Mumbai?', 'What is causing pollution in Kolkata?'" }
  ]);
  const [agentBusy,  setAgentBusy]  = useState(false);
  const chatRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/api/india-stations`)
      .then(r => r.json())
      .then(d => { setStations(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [agentMsgs]);

  async function askAgent() {
    if (!agentQ.trim() || agentBusy) return;
    const q = agentQ.trim();
    setAgentQ("");
    setAgentMsgs(prev => [...prev, { role:"user", text:q }]);
    setAgentBusy(true);
    try {
      const r = await fetch(`${API}/api/agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, city: agentCity }),
      });
      const d = await r.json();
      setAgentMsgs(prev => [...prev, { role:"assistant", text: d.answer || "Sorry, I couldn't process that." }]);
    } catch {
      setAgentMsgs(prev => [...prev, { role:"assistant", text:"Backend unavailable. Make sure the FastAPI server is running on port 8000." }]);
    }
    setAgentBusy(false);
  }

  const avgAqi = stations.length > 0 ? Math.round(stations.reduce((s,c) => s+c.aqi, 0) / stations.length) : 0;
  const worst  = stations.length > 0 ? stations.reduce((a,b) => a.aqi>b.aqi?a:b, stations[0]) : null;
  const best   = stations.length > 0 ? stations.reduce((a,b) => a.aqi<b.aqi?a:b, stations[0]) : null;

  return (
    <div style={{ minHeight:"100vh", background:"#f8fafc", fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif", color:"#111827" }}>
      <style>{`
        .btn { border:none; border-radius:7px; padding:8px 16px; font-size:13px; font-weight:500; cursor:pointer; transition:opacity .15s; font-family:inherit; }
        .btn:hover { opacity:.85; }
        .card { background:#fff; border:1px solid #e5e7eb; border-radius:10px; }
        input, select, textarea { font-family:inherit; font-size:13px; outline:none; }
        ::-webkit-scrollbar { width:4px; }
        ::-webkit-scrollbar-thumb { background:#d1d5db; border-radius:4px; }
      `}</style>

      {/* Header */}
      <header style={{ background:"#fff", borderBottom:"1px solid #e5e7eb", padding:"0 28px", display:"flex", alignItems:"center", justifyContent:"space-between", height:54 }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{ width:30, height:30, background:"#1d4ed8", borderRadius:7, display:"flex", alignItems:"center", justifyContent:"center", color:"#fff", fontWeight:700, fontSize:14 }}>A</div>
          <span style={{ fontWeight:700, fontSize:16, color:"#111827" }}>AirSentinel</span>
          <span style={{ fontSize:12, color:"#9ca3af", marginLeft:4 }}>India Air Quality Intelligence</span>
        </div>
        <nav style={{ display:"flex", gap:4 }}>
          {[["map","Live Map"],["agent","AI Agent"],["analytics","Analytics"]].map(([id,label]) => (
            <button key={id} className="btn" onClick={() => setPage(id)}
              style={{ background:page===id?"#eff6ff":"transparent", color:page===id?"#1d4ed8":"#6b7280", fontWeight:page===id?600:400 }}>
              {label}
            </button>
          ))}
        </nav>
      </header>

      {/* Stats bar */}
      {stations.length > 0 && (
        <div style={{ background:"#fff", borderBottom:"1px solid #e5e7eb", padding:"10px 28px", display:"flex", gap:32, alignItems:"center" }}>
          <div style={{ fontSize:12, color:"#6b7280" }}>
            <span style={{ fontWeight:600, color:"#111827", fontSize:14 }}>{stations.length}</span> cities monitored
          </div>
          <div style={{ fontSize:12, color:"#6b7280" }}>
            National avg AQI: <span style={{ fontWeight:600, color: avgAqi>200?"#dc2626":avgAqi>100?"#d97706":"#059669", fontSize:14 }}>{avgAqi}</span>
          </div>
          {worst && <div style={{ fontSize:12, color:"#6b7280" }}>
            Most polluted: <span style={{ fontWeight:600, color:"#dc2626" }}>{worst.city} ({worst.aqi})</span>
          </div>}
          {best && <div style={{ fontSize:12, color:"#6b7280" }}>
            Cleanest: <span style={{ fontWeight:600, color:"#059669" }}>{best.city} ({best.aqi})</span>
          </div>}
          <div style={{ marginLeft:"auto", fontSize:11, color:"#9ca3af" }}>
            Source: OpenAQ · NASA FIRMS · Updated live
          </div>
        </div>
      )}

      {/* Pages */}
      {page === "map"       && <MapPage stations={stations} loading={loading} selected={selected} setSelected={setSelected} />}
      {page === "agent"     && <AgentPage agentCity={agentCity} setAgentCity={setAgentCity} agentQ={agentQ} setAgentQ={setAgentQ} agentMsgs={agentMsgs} agentBusy={agentBusy} askAgent={askAgent} chatRef={chatRef} />}
      {page === "analytics" && <AnalyticsPage stations={stations} />}
    </div>
  );
}

// ─────────────────────────────────────────────
// Map Page
// ─────────────────────────────────────────────
function MapPage({ stations, loading, selected, setSelected }) {
  if (loading) return (
    <div style={{ display:"flex", alignItems:"center", justifyContent:"center", height:"calc(100vh - 100px)", color:"#6b7280", fontSize:14 }}>
      Loading live AQI data…
    </div>
  );

  return (
    <div style={{ display:"flex", height:"calc(100vh - 100px)" }}>
      {/* Map */}
      <div style={{ flex:1, position:"relative" }}>
        <MapContainer center={[20.5937, 78.9629]} zoom={5} style={{ height:"100%", width:"100%" }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />
          {stations.map(s => (
            <CircleMarker
              key={s.city}
              center={[s.lat, s.lon]}
              radius={Math.max(14, s.aqi / 18)}
              pathOptions={{ fillColor:s.color, color:"#fff", weight:1.5, fillOpacity:0.85 }}
              eventHandlers={{ click: () => setSelected(s) }}
            >
              <Popup>
                <div style={{ fontFamily:"system-ui", minWidth:160 }}>
                  <div style={{ fontWeight:700, fontSize:15, marginBottom:4 }}>{s.city}</div>
                  <div style={{ fontSize:22, fontWeight:700, color:s.color }}>{s.aqi}</div>
                  <div style={{ fontSize:12, color:"#6b7280", marginBottom:6 }}>AQI — {s.category}</div>
                  <div style={{ fontSize:12 }}>PM2.5: {s.pm25} µg/m³</div>
                  <div style={{ fontSize:12 }}>PM10: {s.pm10} µg/m³</div>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>

        {/* Legend */}
        <div style={{ position:"absolute", bottom:20, left:12, zIndex:1000, background:"rgba(255,255,255,0.95)", border:"1px solid #e5e7eb", borderRadius:9, padding:"12px 16px", fontSize:12 }}>
          <div style={{ fontWeight:600, marginBottom:8, color:"#111827" }}>AQI Scale</div>
          {[["Good","#00c853","0–50"],["Satisfactory","#ffd600","51–100"],["Moderate","#ff6d00","101–200"],["Poor","#d50000","201–300"],["Very Poor","#6a1b9a","301–400"],["Severe","#37474f","400+"]].map(([l,c,r]) => (
            <div key={l} style={{ display:"flex", alignItems:"center", gap:8, marginBottom:4 }}>
              <div style={{ width:12, height:12, borderRadius:"50%", background:c }} />
              <span style={{ color:"#374151" }}>{l}</span>
              <span style={{ color:"#9ca3af", marginLeft:"auto" }}>{r}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Sidebar */}
      <div style={{ width:300, background:"#fff", borderLeft:"1px solid #e5e7eb", overflowY:"auto", padding:16 }}>
        {selected ? (
          <CityDetail city={selected} onClose={() => setSelected(null)} />
        ) : (
          <>
            <div style={{ fontWeight:600, fontSize:14, marginBottom:14, color:"#111827" }}>All Cities</div>
            {[...stations].sort((a,b) => b.aqi - a.aqi).map(s => (
              <div key={s.city} onClick={() => setSelected(s)} style={{ display:"flex", alignItems:"center", gap:10, padding:"9px 0", borderBottom:"1px solid #f3f4f6", cursor:"pointer" }}
                onMouseEnter={e => e.currentTarget.style.background="#fafafa"}
                onMouseLeave={e => e.currentTarget.style.background="transparent"}>
                <div style={{ width:10, height:10, borderRadius:"50%", background:s.color, flexShrink:0 }} />
                <span style={{ flex:1, fontSize:13, fontWeight:500 }}>{s.city}</span>
                <span style={{ fontSize:14, fontWeight:700, color:s.color }}>{s.aqi}</span>
                <span style={{ fontSize:11, color:"#9ca3af" }}>{s.category}</span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function CityDetail({ city, onClose }) {
  const [weather, setWeather] = useState(null);
  const [fires,   setFires]   = useState(null);

  useEffect(() => {
    fetch(`${API}/api/weather?city=${city.city}`).then(r=>r.json()).then(setWeather).catch(()=>{});
    fetch(`${API}/api/fires?lat=${city.lat}&lon=${city.lon}`).then(r=>r.json()).then(setFires).catch(()=>{});
  }, [city.city]);

  const pollutants = [
    { name:"PM2.5", val:city.pm25, unit:"µg/m³", safe:60  },
    { name:"PM10",  val:city.pm10, unit:"µg/m³", safe:100 },
    { name:"NO2",   val:city.no2,  unit:"µg/m³", safe:80  },
    { name:"O3",    val:city.o3,   unit:"µg/m³", safe:100 },
  ].filter(p => p.val !== null);

  return (
    <div>
      <button onClick={onClose} style={{ background:"none", border:"none", color:"#6b7280", cursor:"pointer", fontSize:13, marginBottom:12, padding:0 }}>
        ← All cities
      </button>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:14 }}>
        <div>
          <div style={{ fontWeight:700, fontSize:18 }}>{city.city}</div>
          <div style={{ fontSize:12, color:"#6b7280", marginTop:2 }}>{city.station}</div>
        </div>
        <div style={{ textAlign:"right" }}>
          <div style={{ fontSize:32, fontWeight:700, color:city.color, lineHeight:1 }}>{city.aqi}</div>
          <div style={{ fontSize:12, color:city.color, fontWeight:500 }}>{city.category}</div>
        </div>
      </div>

      <div style={{ background: city.color + "18", border:`1px solid ${city.color}44`, borderRadius:8, padding:"10px 12px", marginBottom:14, fontSize:13, color:"#374151" }}>
        {city.risk}
      </div>

      <div style={{ fontWeight:600, fontSize:12, color:"#6b7280", textTransform:"uppercase", letterSpacing:".05em", marginBottom:8 }}>Pollutants</div>
      {pollutants.map(p => (
        <div key={p.name} style={{ marginBottom:10 }}>
          <div style={{ display:"flex", justifyContent:"space-between", fontSize:12, marginBottom:3 }}>
            <span style={{ color:"#374151" }}>{p.name}</span>
            <span style={{ fontWeight:600 }}>{p.val} {p.unit}</span>
          </div>
          <div style={{ background:"#f3f4f6", borderRadius:4, height:6 }}>
            <div style={{ width:`${Math.min((p.val/p.safe)*100,100)}%`, height:"100%", background: p.val>p.safe?"#dc2626":"#059669", borderRadius:4 }} />
          </div>
        </div>
      ))}

      {weather && (
        <>
          <div style={{ fontWeight:600, fontSize:12, color:"#6b7280", textTransform:"uppercase", letterSpacing:".05em", margin:"14px 0 8px" }}>Wind & Weather</div>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8 }}>
            {[["Wind",`${weather.wind_speed} m/s ${weather.wind_direction}`],["Temp",`${weather.temp}°C`],["Humidity",`${weather.humidity}%`],["Conditions",weather.description]].map(([k,v]) => (
              <div key={k} style={{ background:"#f9fafb", borderRadius:7, padding:"8px 10px" }}>
                <div style={{ fontSize:11, color:"#9ca3af" }}>{k}</div>
                <div style={{ fontSize:13, fontWeight:500, marginTop:2 }}>{v}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {fires && (
        <>
          <div style={{ fontWeight:600, fontSize:12, color:"#6b7280", textTransform:"uppercase", letterSpacing:".05em", margin:"14px 0 8px" }}>Fire Hotspots (500km)</div>
          <div style={{ background: fires.count>0?"#fef2f2":"#f0fdf4", border:`1px solid ${fires.count>0?"#fecaca":"#bbf7d0"}`, borderRadius:7, padding:"9px 12px", fontSize:13 }}>
            <span style={{ fontWeight:600, color:fires.count>0?"#dc2626":"#059669" }}>{fires.count} active fires</span>
            <span style={{ color:"#6b7280", marginLeft:6 }}>detected (NASA FIRMS)</span>
          </div>
        </>
      )}

      <div style={{ marginTop:14, fontSize:11, color:"#9ca3af" }}>Source: {city.source}</div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Agent Page
// ─────────────────────────────────────────────
function AgentPage({ agentCity, setAgentCity, agentQ, setAgentQ, agentMsgs, agentBusy, askAgent, chatRef }) {
  const cities = ["Delhi","Mumbai","Kolkata","Chennai","Bangalore","Hyderabad","Pune","Ahmedabad","Jaipur","Lucknow"];
  const suggestions = [
    "Why is the AQI so high today?",
    "Is it safe for children to go to school?",
    "What is causing the pollution?",
    "What should elderly people do today?",
    "Are there any fires near this city?",
  ];

  return (
    <div style={{ display:"flex", height:"calc(100vh - 100px)" }}>
      {/* Sidebar */}
      <div style={{ width:240, background:"#fff", borderRight:"1px solid #e5e7eb", padding:18, display:"flex", flexDirection:"column", gap:16 }}>
        <div>
          <div style={{ fontSize:11, fontWeight:600, color:"#9ca3af", textTransform:"uppercase", letterSpacing:".05em", marginBottom:8 }}>City Context</div>
          <select value={agentCity} onChange={e=>setAgentCity(e.target.value)} style={{ width:"100%", padding:"8px 10px", border:"1px solid #d1d5db", borderRadius:7, background:"#fff", color:"#111827" }}>
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <div style={{ fontSize:11, fontWeight:600, color:"#9ca3af", textTransform:"uppercase", letterSpacing:".05em", marginBottom:8 }}>Suggested Questions</div>
          {suggestions.map(s => (
            <button key={s} onClick={() => setAgentQ(s)} style={{ display:"block", width:"100%", textAlign:"left", background:"none", border:"1px solid #e5e7eb", borderRadius:7, padding:"8px 10px", fontSize:12, color:"#374151", cursor:"pointer", marginBottom:6, lineHeight:1.4 }}
              onMouseEnter={e=>e.currentTarget.style.background="#f9fafb"}
              onMouseLeave={e=>e.currentTarget.style.background="none"}>
              {s}
            </button>
          ))}
        </div>
        <div style={{ marginTop:"auto", padding:"12px", background:"#eff6ff", borderRadius:8, fontSize:12, color:"#1e40af" }}>
          <strong>Tools available:</strong><br/>
          • Live AQI data<br/>
          • Wind & weather<br/>
          • NASA fire hotspots<br/>
          • Pollution source analysis<br/>
          • Health advisories
        </div>
      </div>

      {/* Chat */}
      <div style={{ flex:1, display:"flex", flexDirection:"column" }}>
        <div style={{ padding:"12px 20px", borderBottom:"1px solid #e5e7eb", background:"#fff", fontSize:13, color:"#6b7280" }}>
          Analysing air quality for <strong style={{ color:"#111827" }}>{agentCity}</strong> — powered by LangGraph + Groq
        </div>

        <div ref={chatRef} style={{ flex:1, overflowY:"auto", padding:24, display:"flex", flexDirection:"column", gap:16 }}>
          {agentMsgs.map((m,i) => (
            <div key={i} style={{ display:"flex", justifyContent: m.role==="user"?"flex-end":"flex-start" }}>
              <div style={{
                maxWidth:"72%",
                background: m.role==="user"?"#1d4ed8":"#fff",
                color: m.role==="user"?"#fff":"#111827",
                border: m.role==="assistant"?"1px solid #e5e7eb":"none",
                padding:"12px 16px",
                borderRadius:10,
                fontSize:14,
                lineHeight:1.65,
                whiteSpace:"pre-wrap",
              }}>
                {m.text}
              </div>
            </div>
          ))}
          {agentBusy && (
            <div style={{ display:"flex", justifyContent:"flex-start" }}>
              <div style={{ background:"#fff", border:"1px solid #e5e7eb", padding:"12px 16px", borderRadius:10, fontSize:13, color:"#6b7280" }}>
                Fetching data and analysing…
              </div>
            </div>
          )}
        </div>

        <div style={{ padding:16, borderTop:"1px solid #e5e7eb", background:"#fff", display:"flex", gap:10 }}>
          <input
            value={agentQ}
            onChange={e=>setAgentQ(e.target.value)}
            onKeyDown={e=>e.key==="Enter"&&askAgent()}
            placeholder={`Ask about air quality in ${agentCity}…`}
            style={{ flex:1, padding:"10px 14px", border:"1px solid #d1d5db", borderRadius:8, fontSize:14, color:"#111827", background:"#fff" }}
          />
          <button className="btn" onClick={askAgent} disabled={agentBusy} style={{ background:"#1d4ed8", color:"#fff", padding:"10px 20px", opacity:agentBusy?.5:1 }}>
            {agentBusy ? "…" : "Ask"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Analytics Page
// ─────────────────────────────────────────────
function AnalyticsPage({ stations }) {
  const sorted = [...stations].sort((a,b) => b.aqi - a.aqi);

  const categoryCount = stations.reduce((acc, s) => {
    acc[s.category] = (acc[s.category]||0)+1;
    return acc;
  }, {});

  const catData = Object.entries(categoryCount).map(([name,count]) => ({ name, count, color: AQI_COLORS[name]||"#6b7280" }));

  return (
    <div style={{ padding:28 }}>
      <h1 style={{ fontSize:20, fontWeight:700, marginBottom:4 }}>Analytics</h1>
      <p style={{ fontSize:13, color:"#6b7280", marginBottom:24 }}>Air quality breakdown across 15 major Indian cities.</p>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:20, marginBottom:24 }}>
        {/* Bar chart - AQI by city */}
        <div className="card" style={{ padding:20 }}>
          <div style={{ fontWeight:600, fontSize:14, marginBottom:16 }}>AQI by City (Ranked)</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={sorted} layout="vertical" margin={{ left:60, right:20 }}>
              <XAxis type="number" tick={{ fontSize:11 }} />
              <YAxis type="category" dataKey="city" tick={{ fontSize:11 }} width={60} />
              <Tooltip formatter={(v) => [`AQI: ${v}`, ""]} />
              <Bar dataKey="aqi" radius={[0,4,4,0]}>
                {sorted.map(s => <Cell key={s.city} fill={s.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Category distribution */}
        <div className="card" style={{ padding:20 }}>
          <div style={{ fontWeight:600, fontSize:14, marginBottom:16 }}>AQI Category Distribution</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={catData}>
              <XAxis dataKey="name" tick={{ fontSize:11 }} />
              <YAxis tick={{ fontSize:11 }} />
              <Tooltip />
              <Bar dataKey="count" radius={[4,4,0,0]}>
                {catData.map(d => <Cell key={d.name} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Full data table */}
      <div className="card" style={{ overflow:"hidden" }}>
        <div style={{ padding:"14px 18px", borderBottom:"1px solid #f3f4f6", fontWeight:600, fontSize:14 }}>Full Station Data</div>
        <table style={{ width:"100%", borderCollapse:"collapse" }}>
          <thead>
            <tr style={{ background:"#f9fafb" }}>
              {["City","AQI","Category","PM2.5","PM10","NO2","O3","Risk","Source"].map(h => (
                <th key={h} style={{ padding:"10px 14px", textAlign:"left", fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:".04em", borderBottom:"1px solid #e5e7eb" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map(s => (
              <tr key={s.city} style={{ borderBottom:"1px solid #f3f4f6" }}>
                <td style={{ padding:"10px 14px", fontWeight:500, fontSize:13 }}>{s.city}</td>
                <td style={{ padding:"10px 14px", fontWeight:700, fontSize:14, color:s.color }}>{s.aqi}</td>
                <td style={{ padding:"10px 14px" }}><span style={{ background:s.color+"22", color:s.color, padding:"2px 8px", borderRadius:4, fontSize:11, fontWeight:500 }}>{s.category}</span></td>
                <td style={{ padding:"10px 14px", fontSize:13, color:"#374151" }}>{s.pm25}</td>
                <td style={{ padding:"10px 14px", fontSize:13, color:"#374151" }}>{s.pm10}</td>
                <td style={{ padding:"10px 14px", fontSize:13, color:"#374151" }}>{s.no2}</td>
                <td style={{ padding:"10px 14px", fontSize:13, color:"#374151" }}>{s.o3}</td>
                <td style={{ padding:"10px 14px", fontSize:12, color:"#6b7280" }}>{s.risk}</td>
                <td style={{ padding:"10px 14px", fontSize:11, color:"#9ca3af" }}>{s.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p style={{ fontSize:11, color:"#9ca3af", marginTop:12 }}>
        Data sources: OpenAQ API · NASA FIRMS · OpenWeatherMap
      </p>
    </div>
  );
}
