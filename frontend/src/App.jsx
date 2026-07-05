import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const API = "http://localhost:8000";

const AQI_COLORS = {
  "Good":"#00c853","Satisfactory":"#ffd600","Moderate":"#ff6d00",
  "Poor":"#d50000","Very Poor":"#6a1b9a","Severe":"#37474f",
};

export default function App() {
  const [page,setPage]=useState("map");
  const [stations,setStations]=useState([]);
  const [selected,setSelected]=useState(null);
  const [loading,setLoading]=useState(true);
  const [agentCity,setAgentCity]=useState("Delhi");
  const [agentQ,setAgentQ]=useState("");
  const [agentMsgs,setAgentMsgs]=useState([{role:"assistant",text:"Hello! I'm AirSentinel. Ask me anything about air quality anywhere in the world."}]);
  const [agentBusy,setAgentBusy]=useState(false);
  const chatRef=useRef(null);

  useEffect(()=>{
    fetch(`${API}/api/global-stations`).then(r=>r.json()).then(d=>{setStations(d);setLoading(false);}).catch(()=>setLoading(false));
  },[]);

  useEffect(()=>{if(chatRef.current)chatRef.current.scrollTop=chatRef.current.scrollHeight;},[agentMsgs]);

  async function askAgent(){
    if(!agentQ.trim()||agentBusy)return;
    const q=agentQ.trim();setAgentQ("");
    setAgentMsgs(p=>[...p,{role:"user",text:q}]);setAgentBusy(true);
    try{
      const r=await fetch(`${API}/api/agent`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:q,city:agentCity})});
      const d=await r.json();
      setAgentMsgs(p=>[...p,{role:"assistant",text:d.answer||"Sorry, I couldn't process that."}]);
    }catch{setAgentMsgs(p=>[...p,{role:"assistant",text:"Backend unavailable. Make sure FastAPI is running on port 8000."}]);}
    setAgentBusy(false);
  }

  const avgAqi=stations.length>0?Math.round(stations.reduce((s,c)=>s+c.aqi,0)/stations.length):0;
  const worst=stations.length>0?stations.reduce((a,b)=>a.aqi>b.aqi?a:b,stations[0]):null;
  const best=stations.length>0?stations.reduce((a,b)=>a.aqi<b.aqi?a:b,stations[0]):null;

  const NAV=[{id:"map",label:"Live Map"},{id:"agent",label:"AI Agent"},{id:"analytics",label:"Analytics"},{id:"forecast",label:"Forecast"}];

  return(
    <div style={{minHeight:"100vh",background:"#f8fafc",fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",color:"#111827"}}>
      <style>{`.btn{border:none;border-radius:7px;padding:8px 16px;font-size:13px;font-weight:500;cursor:pointer;transition:opacity .15s;font-family:inherit;}.btn:hover{opacity:.85;}.card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;}input,select,textarea{font-family:inherit;font-size:13px;outline:none;}::-webkit-scrollbar{width:4px;}::-webkit-scrollbar-thumb{background:#d1d5db;border-radius:4px;}`}</style>
      <header style={{background:"#fff",borderBottom:"1px solid #e5e7eb",padding:"0 28px",display:"flex",alignItems:"center",justifyContent:"space-between",height:54}}>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <div style={{width:30,height:30,background:"#1d4ed8",borderRadius:7,display:"flex",alignItems:"center",justifyContent:"center",color:"#fff",fontWeight:700,fontSize:14}}>A</div>
          <span style={{fontWeight:700,fontSize:16,color:"#111827"}}>AirSentinel</span>
          <span style={{fontSize:12,color:"#9ca3af",marginLeft:4}}>Global Air Quality Intelligence</span>
        </div>
        <nav style={{display:"flex",gap:4}}>
          {NAV.map(({id,label})=>(
            <button key={id} className="btn" onClick={()=>setPage(id)} style={{background:page===id?"#eff6ff":"transparent",color:page===id?"#1d4ed8":"#6b7280",fontWeight:page===id?600:400}}>{label}</button>
          ))}
        </nav>
      </header>
      {stations.length>0&&(
        <div style={{background:"#fff",borderBottom:"1px solid #e5e7eb",padding:"10px 28px",display:"flex",gap:32,alignItems:"center"}}>
          <div style={{fontSize:12,color:"#6b7280"}}><span style={{fontWeight:600,color:"#111827",fontSize:14}}>{stations.length}</span> cities monitored globally</div>
          <div style={{fontSize:12,color:"#6b7280"}}>Global avg AQI: <span style={{fontWeight:600,color:avgAqi>200?"#dc2626":avgAqi>100?"#d97706":"#059669",fontSize:14}}>{avgAqi}</span></div>
          {worst&&<div style={{fontSize:12,color:"#6b7280"}}>Most polluted: <span style={{fontWeight:600,color:"#dc2626"}}>{worst.city} ({worst.aqi})</span></div>}
          {best&&<div style={{fontSize:12,color:"#6b7280"}}>Cleanest: <span style={{fontWeight:600,color:"#059669"}}>{best.city} ({best.aqi})</span></div>}
          <div style={{marginLeft:"auto",fontSize:11,color:"#9ca3af"}}>Source: OpenAQ · NASA FIRMS · WHO · Updated live</div>
        </div>
      )}
      {page==="map"&&<MapPage stations={stations} loading={loading} selected={selected} setSelected={setSelected}/>}
      {page==="agent"&&<AgentPage agentCity={agentCity} setAgentCity={setAgentCity} agentQ={agentQ} setAgentQ={setAgentQ} agentMsgs={agentMsgs} agentBusy={agentBusy} askAgent={askAgent} chatRef={chatRef}/>}
      {page==="analytics"&&<AnalyticsPage stations={stations}/>}
      {page==="forecast"&&<ForecastPage/>}
    </div>
  );
}

function MapPage({stations,loading,selected,setSelected}){
  if(loading)return<div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"calc(100vh - 100px)",color:"#6b7280",fontSize:14}}>Loading global AQI data…</div>;
  return(
    <div style={{display:"flex",height:"calc(100vh - 100px)"}}>
      <div style={{flex:1,position:"relative"}}>
        <MapContainer center={[20,0]} zoom={2} style={{height:"100%",width:"100%"}}>
          <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" attribution='&copy; <a href="https://carto.com/">CARTO</a>'/>
          {stations.map(s=>(
            <CircleMarker key={s.city} center={[s.lat,s.lon]} radius={Math.max(10,s.aqi/22)} pathOptions={{fillColor:s.color,color:"#fff",weight:1.5,fillOpacity:0.85}} eventHandlers={{click:()=>setSelected(s)}}>
              <Popup>
                <div style={{fontFamily:"system-ui",minWidth:160}}>
                  <div style={{fontWeight:700,fontSize:15,marginBottom:2}}>{s.city}</div>
                  <div style={{fontSize:12,color:"#6b7280",marginBottom:4}}>{s.country}</div>
                  <div style={{fontSize:22,fontWeight:700,color:s.color}}>{s.aqi}</div>
                  <div style={{fontSize:12,color:"#6b7280",marginBottom:6}}>AQI — {s.category}</div>
                  <div style={{fontSize:12}}>PM2.5: {s.pm25} µg/m³</div>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
        <div style={{position:"absolute",bottom:20,left:12,zIndex:1000,background:"rgba(255,255,255,0.95)",border:"1px solid #e5e7eb",borderRadius:9,padding:"12px 16px",fontSize:12}}>
          <div style={{fontWeight:600,marginBottom:8,color:"#111827"}}>AQI Scale</div>
          {[["Good","#00c853","0–50"],["Satisfactory","#ffd600","51–100"],["Moderate","#ff6d00","101–200"],["Poor","#d50000","201–300"],["Very Poor","#6a1b9a","301–400"],["Severe","#37474f","400+"]].map(([l,c,r])=>(
            <div key={l} style={{display:"flex",alignItems:"center",gap:8,marginBottom:4}}>
              <div style={{width:12,height:12,borderRadius:"50%",background:c}}/>
              <span style={{color:"#374151"}}>{l}</span>
              <span style={{color:"#9ca3af",marginLeft:"auto"}}>{r}</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{width:300,background:"#fff",borderLeft:"1px solid #e5e7eb",overflowY:"auto",padding:16}}>
        {selected?<CityDetail city={selected} onClose={()=>setSelected(null)}/>:(
          <>
            <div style={{fontWeight:600,fontSize:14,marginBottom:14,color:"#111827"}}>All Cities</div>
            {[...stations].sort((a,b)=>b.aqi-a.aqi).map(s=>(
              <div key={s.city} onClick={()=>setSelected(s)} style={{display:"flex",alignItems:"center",gap:10,padding:"9px 0",borderBottom:"1px solid #f3f4f6",cursor:"pointer"}} onMouseEnter={e=>e.currentTarget.style.background="#fafafa"} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                <div style={{width:10,height:10,borderRadius:"50%",background:s.color,flexShrink:0}}/>
                <div style={{flex:1}}>
                  <div style={{fontSize:13,fontWeight:500}}>{s.city}</div>
                  <div style={{fontSize:11,color:"#9ca3af"}}>{s.country}</div>
                </div>
                <span style={{fontSize:14,fontWeight:700,color:s.color}}>{s.aqi}</span>
                <span style={{fontSize:11,color:"#9ca3af"}}>{s.category}</span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function CityDetail({city,onClose}){
  const [weather,setWeather]=useState(null);
  const [fires,setFires]=useState(null);
  useEffect(()=>{
    fetch(`${API}/api/weather?city=${city.city}`).then(r=>r.json()).then(setWeather).catch(()=>{});
    fetch(`${API}/api/fires?lat=${city.lat}&lon=${city.lon}`).then(r=>r.json()).then(setFires).catch(()=>{});
  },[city.city]);
  const pollutants=[{name:"PM2.5",val:city.pm25,unit:"µg/m³",safe:60},{name:"PM10",val:city.pm10,unit:"µg/m³",safe:100},{name:"NO2",val:city.no2,unit:"µg/m³",safe:80},{name:"O3",val:city.o3,unit:"µg/m³",safe:100}].filter(p=>p.val!==null);
  return(
    <div>
      <button onClick={onClose} style={{background:"none",border:"none",color:"#6b7280",cursor:"pointer",fontSize:13,marginBottom:12,padding:0}}>← All cities</button>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:14}}>
        <div>
          <div style={{fontWeight:700,fontSize:18}}>{city.city}</div>
          <div style={{fontSize:12,color:"#6b7280",marginTop:2}}>{city.country}</div>
        </div>
        <div style={{textAlign:"right"}}>
          <div style={{fontSize:32,fontWeight:700,color:city.color,lineHeight:1}}>{city.aqi}</div>
          <div style={{fontSize:12,color:city.color,fontWeight:500}}>{city.category}</div>
        </div>
      </div>
      <div style={{background:city.color+"18",border:`1px solid ${city.color}44`,borderRadius:8,padding:"10px 12px",marginBottom:14,fontSize:13,color:"#374151"}}>{city.risk}</div>
      <div style={{fontWeight:600,fontSize:12,color:"#6b7280",textTransform:"uppercase",letterSpacing:".05em",marginBottom:8}}>Pollutants</div>
      {pollutants.map(p=>(
        <div key={p.name} style={{marginBottom:10}}>
          <div style={{display:"flex",justifyContent:"space-between",fontSize:12,marginBottom:3}}>
            <span style={{color:"#374151"}}>{p.name}</span>
            <span style={{fontWeight:600}}>{p.val} {p.unit}</span>
          </div>
          <div style={{background:"#f3f4f6",borderRadius:4,height:6}}>
            <div style={{width:`${Math.min((p.val/p.safe)*100,100)}%`,height:"100%",background:p.val>p.safe?"#dc2626":"#059669",borderRadius:4}}/>
          </div>
        </div>
      ))}
      {weather&&(
        <>
          <div style={{fontWeight:600,fontSize:12,color:"#6b7280",textTransform:"uppercase",letterSpacing:".05em",margin:"14px 0 8px"}}>Wind & Weather</div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
            {[["Wind",`${weather.wind_speed} m/s ${weather.wind_direction}`],["Temp",`${weather.temp}°C`],["Humidity",`${weather.humidity}%`],["Conditions",weather.description]].map(([k,v])=>(
              <div key={k} style={{background:"#f9fafb",borderRadius:7,padding:"8px 10px"}}>
                <div style={{fontSize:11,color:"#9ca3af"}}>{k}</div>
                <div style={{fontSize:13,fontWeight:500,marginTop:2}}>{v}</div>
              </div>
            ))}
          </div>
        </>
      )}
      {fires&&(
        <>
          <div style={{fontWeight:600,fontSize:12,color:"#6b7280",textTransform:"uppercase",letterSpacing:".05em",margin:"14px 0 8px"}}>Fire Hotspots (500km)</div>
          <div style={{background:fires.count>0?"#fef2f2":"#f0fdf4",border:`1px solid ${fires.count>0?"#fecaca":"#bbf7d0"}`,borderRadius:7,padding:"9px 12px",fontSize:13}}>
            <span style={{fontWeight:600,color:fires.count>0?"#dc2626":"#059669"}}>{fires.count} active fires</span>
            <span style={{color:"#6b7280",marginLeft:6}}>detected (NASA FIRMS)</span>
          </div>
        </>
      )}
      <div style={{marginTop:14,fontSize:11,color:"#9ca3af"}}>Source: {city.source}</div>
    </div>
  );
}

function AgentPage({agentCity,setAgentCity,agentQ,setAgentQ,agentMsgs,agentBusy,askAgent,chatRef}){
  const cities=["Delhi","Mumbai","Kolkata","Chennai","Bangalore","Hyderabad","Pune","Ahmedabad","Jaipur","Lucknow","Beijing","Tokyo","Seoul","Bangkok","Jakarta","Karachi","Dhaka","London","Paris","Berlin","Moscow","Istanbul","Cairo","Lagos","Nairobi","New York","Los Angeles","Mexico City","Sao Paulo","Sydney","Dubai"];
  const suggestions=["Why is the AQI so high today?","Is it safe for children to go to school?","What is causing the pollution?","What should elderly people do today?","Are there any fires near this city?","How does this city compare to WHO guidelines?"];
  return(
    <div style={{display:"flex",height:"calc(100vh - 100px)"}}>
      <div style={{width:240,background:"#fff",borderRight:"1px solid #e5e7eb",padding:18,display:"flex",flexDirection:"column",gap:16}}>
        <div>
          <div style={{fontSize:11,fontWeight:600,color:"#9ca3af",textTransform:"uppercase",letterSpacing:".05em",marginBottom:8}}>City Context</div>
          <select value={agentCity} onChange={e=>setAgentCity(e.target.value)} style={{width:"100%",padding:"8px 10px",border:"1px solid #d1d5db",borderRadius:7,background:"#fff",color:"#111827"}}>
            {cities.map(c=><option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <div style={{fontSize:11,fontWeight:600,color:"#9ca3af",textTransform:"uppercase",letterSpacing:".05em",marginBottom:8}}>Suggested Questions</div>
          {suggestions.map(s=>(
            <button key={s} onClick={()=>setAgentQ(s)} style={{display:"block",width:"100%",textAlign:"left",background:"none",border:"1px solid #e5e7eb",borderRadius:7,padding:"8px 10px",fontSize:12,color:"#374151",cursor:"pointer",marginBottom:6,lineHeight:1.4}} onMouseEnter={e=>e.currentTarget.style.background="#f9fafb"} onMouseLeave={e=>e.currentTarget.style.background="none"}>{s}</button>
          ))}
        </div>
        <div style={{marginTop:"auto",padding:"12px",background:"#eff6ff",borderRadius:8,fontSize:12,color:"#1e40af"}}>
          <strong>Tools available:</strong><br/>• Live AQI data<br/>• Wind & weather<br/>• NASA fire hotspots<br/>• Pollution source analysis<br/>• WHO document search (RAG)<br/>• Health advisories
        </div>
      </div>
      <div style={{flex:1,display:"flex",flexDirection:"column"}}>
        <div style={{padding:"12px 20px",borderBottom:"1px solid #e5e7eb",background:"#fff",fontSize:13,color:"#6b7280"}}>
          Analysing air quality for <strong style={{color:"#111827"}}>{agentCity}</strong> — powered by LangChain + Groq LLaMA 3.3
        </div>
        <div ref={chatRef} style={{flex:1,overflowY:"auto",padding:24,display:"flex",flexDirection:"column",gap:16}}>
          {agentMsgs.map((m,i)=>(
            <div key={i} style={{display:"flex",justifyContent:m.role==="user"?"flex-end":"flex-start"}}>
              <div style={{maxWidth:"72%",background:m.role==="user"?"#1d4ed8":"#fff",color:m.role==="user"?"#fff":"#111827",border:m.role==="assistant"?"1px solid #e5e7eb":"none",padding:"12px 16px",borderRadius:10,fontSize:14,lineHeight:1.65,whiteSpace:"pre-wrap"}}>{m.text}</div>
            </div>
          ))}
          {agentBusy&&<div style={{display:"flex",justifyContent:"flex-start"}}><div style={{background:"#fff",border:"1px solid #e5e7eb",padding:"12px 16px",borderRadius:10,fontSize:13,color:"#6b7280"}}>Fetching data and analysing…</div></div>}
        </div>
        <div style={{padding:16,borderTop:"1px solid #e5e7eb",background:"#fff",display:"flex",gap:10}}>
          <input value={agentQ} onChange={e=>setAgentQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&askAgent()} placeholder={`Ask about air quality in ${agentCity}…`} style={{flex:1,padding:"10px 14px",border:"1px solid #d1d5db",borderRadius:8,fontSize:14,color:"#111827",background:"#fff"}}/>
          <button className="btn" onClick={askAgent} disabled={agentBusy} style={{background:"#1d4ed8",color:"#fff",padding:"10px 20px",opacity:agentBusy?0.5:1}}>{agentBusy?"…":"Ask"}</button>
        </div>
      </div>
    </div>
  );
}

function AnalyticsPage({stations}){
  const [filter,setFilter]=useState("All");
  const countries=["All",...new Set(stations.map(s=>s.country).filter(Boolean))].sort();
  const filtered=filter==="All"?stations:stations.filter(s=>s.country===filter);
  const sorted=[...filtered].sort((a,b)=>b.aqi-a.aqi);
  const categoryCount=filtered.reduce((acc,s)=>{acc[s.category]=(acc[s.category]||0)+1;return acc;},{});
  const catData=Object.entries(categoryCount).map(([name,count])=>({name,count,color:AQI_COLORS[name]||"#6b7280"}));
  return(
    <div style={{padding:28}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:24}}>
        <div>
          <h1 style={{fontSize:20,fontWeight:700,marginBottom:4}}>Analytics</h1>
          <p style={{fontSize:13,color:"#6b7280"}}>Air quality across {stations.length} cities in {new Set(stations.map(s=>s.country)).size} countries.</p>
        </div>
        <select value={filter} onChange={e=>setFilter(e.target.value)} style={{padding:"8px 12px",border:"1px solid #d1d5db",borderRadius:8,fontSize:13,background:"#fff"}}>
          {countries.map(c=><option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:20,marginBottom:24}}>
        <div className="card" style={{padding:20}}>
          <div style={{fontWeight:600,fontSize:14,marginBottom:16}}>AQI by City (Top 20)</div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={sorted.slice(0,20)} layout="vertical" margin={{left:80,right:20}}>
              <XAxis type="number" tick={{fontSize:11}}/>
              <YAxis type="category" dataKey="city" tick={{fontSize:10}} width={80}/>
              <Tooltip formatter={v=>[`AQI: ${v}`,""]}/>
              <Bar dataKey="aqi" radius={[0,4,4,0]}>{sorted.slice(0,20).map(s=><Cell key={s.city} fill={s.color}/>)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card" style={{padding:20}}>
          <div style={{fontWeight:600,fontSize:14,marginBottom:16}}>Category Distribution</div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={catData}>
              <XAxis dataKey="name" tick={{fontSize:11}}/>
              <YAxis tick={{fontSize:11}}/>
              <Tooltip/>
              <Bar dataKey="count" radius={[4,4,0,0]}>{catData.map(d=><Cell key={d.name} fill={d.color}/>)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card" style={{overflow:"hidden"}}>
        <div style={{padding:"14px 18px",borderBottom:"1px solid #f3f4f6",fontWeight:600,fontSize:14}}>Full Station Data</div>
        <table style={{width:"100%",borderCollapse:"collapse"}}>
          <thead>
            <tr style={{background:"#f9fafb"}}>
              {["City","Country","AQI","Category","PM2.5","PM10","NO2","O3","Risk","Source"].map(h=>(
                <th key={h} style={{padding:"10px 14px",textAlign:"left",fontSize:11,fontWeight:600,color:"#6b7280",textTransform:"uppercase",letterSpacing:".04em",borderBottom:"1px solid #e5e7eb"}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map(s=>(
              <tr key={s.city} style={{borderBottom:"1px solid #f3f4f6"}}>
                <td style={{padding:"10px 14px",fontWeight:500,fontSize:13}}>{s.city}</td>
                <td style={{padding:"10px 14px",fontSize:13,color:"#6b7280"}}>{s.country}</td>
                <td style={{padding:"10px 14px",fontWeight:700,fontSize:14,color:s.color}}>{s.aqi}</td>
                <td style={{padding:"10px 14px"}}><span style={{background:s.color+"22",color:s.color,padding:"2px 8px",borderRadius:4,fontSize:11,fontWeight:500}}>{s.category}</span></td>
                <td style={{padding:"10px 14px",fontSize:13,color:"#374151"}}>{s.pm25}</td>
                <td style={{padding:"10px 14px",fontSize:13,color:"#374151"}}>{s.pm10}</td>
                <td style={{padding:"10px 14px",fontSize:13,color:"#374151"}}>{s.no2}</td>
                <td style={{padding:"10px 14px",fontSize:13,color:"#374151"}}>{s.o3}</td>
                <td style={{padding:"10px 14px",fontSize:12,color:"#6b7280"}}>{s.risk}</td>
                <td style={{padding:"10px 14px",fontSize:11,color:"#9ca3af"}}>{s.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ForecastPage(){
  const [city,setCity]=useState("Delhi");
  const [data,setData]=useState(null);
  const [loading,setLoading]=useState(false);
  const cities=["Ahmedabad","Aizawl","Amaravati","Amritsar","Bengaluru","Bhopal","Chennai","Coimbatore","Delhi","Gurugram","Guwahati","Hyderabad","Jaipur","Kochi","Kolkata","Lucknow","Mumbai","Patna","Shillong","Talcher","Thiruvananthapuram","Visakhapatnam"];

  useEffect(()=>{fetchForecast();},[city]);

  async function fetchForecast(){
    setLoading(true);
    try{const r=await fetch(`${API}/api/forecast?city=${city}&days=7`);const d=await r.json();setData(d);}
    catch{setData(null);}
    setLoading(false);
  }

  const allData=data?[...(data.historical||[]).slice(-14),...(data.predictions||[]).map(p=>({...p,forecast:true}))]:[];
  const maxAqi=allData.length?Math.max(...allData.map(d=>d.aqi))+20:300;
  const rc=v=>v>200?"#d50000":v>100?"#ff6d00":v>50?"#ffd600":"#00c853";
  const rl=v=>v>200?"Poor":v>100?"Moderate":v>50?"Satisfactory":"Good";

  return(
    <div style={{padding:28}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:24}}>
        <div>
          <h1 style={{fontSize:20,fontWeight:700,marginBottom:4}}>AQI Forecast</h1>
          <p style={{fontSize:13,color:"#6b7280"}}>7-day AQI prediction using 5 years of historical CPCB data for Indian cities.</p>
        </div>
        <select value={city} onChange={e=>setCity(e.target.value)} style={{padding:"8px 12px",border:"1px solid #d1d5db",borderRadius:8,fontSize:14,background:"#fff"}}>
          {cities.map(c=><option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {loading&&<div style={{textAlign:"center",padding:"60px 0",color:"#6b7280",fontSize:14}}>Loading forecast…</div>}

      {data&&!loading&&(
        <>
          <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:14,marginBottom:24}}>
            {[
              {label:"Latest AQI",val:data.historical?.slice(-1)[0]?.aqi||"—"},
              {label:"7-Day Avg",val:data.predictions?Math.round(data.predictions.reduce((s,p)=>s+p.aqi,0)/data.predictions.length):"—"},
              {label:"Trend",val:data.stats?.trend||"—"},
              {label:"Model",val:data.model||"—"},
            ].map(s=>(
              <div key={s.label} className="card" style={{padding:"16px 18px"}}>
                <div style={{fontSize:11,color:"#6b7280",textTransform:"uppercase",letterSpacing:".05em",marginBottom:6}}>{s.label}</div>
                <div style={{fontSize:18,fontWeight:600,color:"#111827"}}>{s.val}</div>
              </div>
            ))}
          </div>

          <div className="card" style={{padding:24,marginBottom:20}}>
            <div style={{fontWeight:600,fontSize:14,marginBottom:4}}>Historical + 7-Day Forecast — {city}</div>
            <div style={{fontSize:12,color:"#6b7280",marginBottom:16}}>Solid bars = historical · Dashed = forecast</div>
            <div style={{display:"flex",alignItems:"flex-end",gap:3,height:200}}>
              {allData.map((d,i)=>{
                const h=Math.max(4,(d.aqi/maxAqi)*180);
                const c=rc(d.aqi);
                return(
                  <div key={i} style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",gap:3}}>
                    <div style={{fontSize:8,color:"#6b7280"}}>{Math.round(d.aqi)}</div>
                    <div style={{width:"100%",height:h,background:d.forecast?"transparent":c,border:d.forecast?`2px dashed ${c}`:"none",borderRadius:3}} title={`${d.date}: AQI ${d.aqi}`}/>
                    <div style={{fontSize:7,color:"#9ca3af",writingMode:"vertical-rl",transform:"rotate(180deg)"}}>{d.date?.slice(5)}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="card" style={{overflow:"hidden",marginBottom:16}}>
            <div style={{padding:"14px 18px",borderBottom:"1px solid #f3f4f6",fontWeight:600,fontSize:14}}>7-Day Forecast Detail</div>
            <table style={{width:"100%",borderCollapse:"collapse"}}>
              <thead>
                <tr style={{background:"#f9fafb"}}>
                  {["Date","Predicted AQI","Lower Bound","Upper Bound","Risk Level"].map(h=>(
                    <th key={h} style={{padding:"10px 14px",textAlign:"left",fontSize:11,fontWeight:600,color:"#6b7280",textTransform:"uppercase",letterSpacing:".04em",borderBottom:"1px solid #e5e7eb"}}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.predictions?.map(p=>(
                  <tr key={p.date} style={{borderBottom:"1px solid #f3f4f6"}}>
                    <td style={{padding:"10px 14px",fontSize:13}}>{p.date}</td>
                    <td style={{padding:"10px 14px",fontWeight:700,color:rc(p.aqi),fontSize:15}}>{p.aqi}</td>
                    <td style={{padding:"10px 14px",fontSize:13,color:"#6b7280"}}>{p.aqi_low}</td>
                    <td style={{padding:"10px 14px",fontSize:13,color:"#6b7280"}}>{p.aqi_high}</td>
                    <td style={{padding:"10px 14px"}}><span style={{background:rc(p.aqi)+"22",color:rc(p.aqi),padding:"2px 8px",borderRadius:4,fontSize:11,fontWeight:500}}>{rl(p.aqi)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{fontSize:11,color:"#9ca3af"}}>Data: Kaggle Air Quality Data in India (rohanrao) · CPCB daily readings 2015-2020 · {data.stats?.data_points} data points</p>
        </>
      )}
    </div>
  );
}
