import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import * as Papa from "papaparse";
import * as XLSX from "xlsx";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, FunnelChart, Funnel, LabelList
} from "recharts";

#/* ─── DESIGN TOKENS ─────────────────────────────────────────────────────────── */
const T = {
  bg:      "#080b10",
  surface: "#0d1117",
  panel:   "#111820",
  card:    "#141c24",
  border:  "#1e2d3d",
  borderHi:"#2a4060",
  accent:  "#00d4ff",
  green:   "#00ff9d",
  amber:   "#ffb300",
  rose:    "#ff4d6d",
  violet:  "#b06fff",
  text:    "#cdd9e5",
  muted:   "#4a6070",
  dim:     "#2a3a4a",
};

const PALETTE = [
  "#00d4ff","#00ff9d","#ffb300","#ff4d6d","#b06fff",
  "#ff8c42","#4dffdb","#ff6b9d","#c8ff6b","#6b9dff",
];

const FONT_HEAD = "'Syne', 'Segoe UI', sans-serif";
const FONT_BODY = "'IBM Plex Mono', 'Courier New', monospace";

#/* ─── UTILS ─────────────────────────────────────────────────────────────────── */
function detectType(values) {
  const s = values.filter(v => v !== null && v !== undefined && v !== "").slice(0, 30);
  if (!s.length) return "string";
  const nums = s.filter(v => !isNaN(parseFloat(String(v).replace(/,/g,""))) && String(v).trim() !== "");
  if (nums.length / s.length > 0.75) return "number";
  const dates = s.filter(v => !isNaN(Date.parse(String(v))) && String(v).length > 5);
  if (dates.length / s.length > 0.6) return "date";
  return "string";
}

function inferColumns(data) {
  if (!data.length) return [];
  return Object.keys(data[0]).map(k => ({
    name: k,
    type: detectType(data.map(r => r[k]))
  }));
}

function cleanNum(v) {
  const n = parseFloat(String(v ?? "").replace(/,/g, "").replace(/[₹$€£]/g, ""));
  return isNaN(n) ? 0 : n;
}

function aggregate(data, groupCol, valueCol, fn = "count") {
  const map = {};
  for (const row of data) {
    const key = String(row[groupCol] ?? "(blank)").slice(0, 24);
    if (!map[key]) map[key] = [];
    map[key].push(cleanNum(row[valueCol]));
  }
  return Object.entries(map).map(([name, vals]) => ({
    name,
    value: fn === "sum" ? vals.reduce((a,b)=>a+b,0)
         : fn === "avg" ? vals.reduce((a,b)=>a+b,0)/vals.length
         : fn === "max" ? Math.max(...vals)
         : fn === "min" ? Math.min(...vals)
         : vals.length,
    count: vals.length
  })).sort((a,b) => b.value - a.value).slice(0,25);
}

function fmtNum(v) {
  if (v >= 1e7) return `${(v/1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `${(v/1e5).toFixed(2)} L`;
  if (v >= 1e3) return `${(v/1e3).toFixed(1)}K`;
  return Number.isInteger(v) ? String(v) : v.toFixed(2);
}

async function parseFile(file) {
  return new Promise((resolve, reject) => {
    const ext = file.name.split(".").pop().toLowerCase();
    if (ext === "csv") {
      Papa.parse(file, {
        header: true, skipEmptyLines: true, dynamicTyping: false,
        complete: r => resolve(r.data),
        error: reject,
      });
    } else if (["xlsx","xls"].includes(ext)) {
      const fr = new FileReader();
      fr.onload = e => {
        try {
          const wb = XLSX.read(e.target.result, { type: "array" });
          const ws = wb.Sheets[wb.SheetNames[0]];
          resolve(XLSX.utils.sheet_to_json(ws, { defval: "" }));
        } catch(err) { reject(err); }
      };
      fr.readAsArrayBuffer(file);
    } else {
      reject(new Error("Unsupported: " + ext));
    }
  });
}

/* ─── SMALL COMPONENTS ──────────────────────────────────────────────────────── */
const Pill = ({ label, active, color = T.accent, onClick }) => (
  <span onClick={onClick} style={{
    display:"inline-flex", alignItems:"center",
    padding:"3px 11px", borderRadius:20, fontSize:11, fontFamily:FONT_BODY,
    fontWeight:600, cursor:"pointer", userSelect:"none", margin:"2px 2px",
    border:`1px solid ${active ? color : T.border}`,
    background: active ? `${color}22` : "transparent",
    color: active ? color : T.muted,
    transition:"all .12s",
  }}>{label}</span>
);

const Badge = ({ type }) => {
  const map = { number: [T.green,"Σ"], date: [T.amber,"D"], string: [T.violet,"A"] };
  const [col, lbl] = map[type] || [T.muted,"?"];
  return <span style={{ color:col, fontSize:10, fontWeight:800, fontFamily:FONT_BODY, minWidth:14 }}>{lbl}</span>;
};

const DropTarget = ({ label, value, accent, onDrop, onClear }) => {
  const [over, setOver] = useState(false);
  return (
    <div
      onDragOver={e=>{e.preventDefault();setOver(true);}}
      onDragLeave={()=>setOver(false)}
      onDrop={e=>{e.preventDefault();setOver(false);onDrop(e.dataTransfer.getData("field"));}}
      style={{
        flex:1, minHeight:32, borderRadius:7,
        border:`1.5px dashed ${over ? accent : T.border}`,
        background: over ? `${accent}12` : T.bg,
        display:"flex", alignItems:"center", padding:"0 10px", gap:6,
        fontSize:11, fontFamily:FONT_BODY,
        color: value ? T.text : T.muted,
        transition:"all .12s", cursor:"default",
      }}
    >
      <span style={{color:accent, fontSize:9, fontWeight:800, textTransform:"uppercase", letterSpacing:"0.1em", minWidth:30}}>{label}</span>
      <span style={{flex:1, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap"}}>{value||"drop field"}</span>
      {value && <span onClick={onClear} style={{cursor:"pointer",color:T.muted,fontSize:16,lineHeight:1,marginLeft:4}}>×</span>}
    </div>
  );
};

const Btn = ({ children, onClick, accent = T.accent, sm, active }) => (
  <button onClick={onClick} style={{
    background: active ? `${accent}22` : "none",
    border:`1px solid ${active ? accent : T.border}`,
    color: active ? accent : T.muted,
    borderRadius:7, padding: sm ? "3px 10px" : "5px 14px",
    cursor:"pointer", fontSize: sm ? 11 : 12,
    fontFamily:FONT_BODY, fontWeight:600,
    transition:"all .12s",
  }}>{children}</button>
);

/* ─── KPI CARD ───────────────────────────────────────────────────────────────── */
const KpiCard = ({ label, value, color, sub }) => (
  <div style={{
    background:`linear-gradient(145deg,${T.card},${T.panel})`,
    border:`1px solid ${color}33`, borderRadius:12,
    padding:"14px 18px", flex:1, minWidth:130,
    boxShadow:`0 0 24px ${color}10, inset 0 1px 0 ${color}20`,
    position:"relative", overflow:"hidden",
  }}>
    <div style={{position:"absolute",top:-20,right:-20,width:80,height:80,borderRadius:"50%",background:`${color}08`}}/>
    <div style={{fontSize:10,color:T.muted,textTransform:"uppercase",letterSpacing:"0.12em",fontFamily:FONT_BODY,marginBottom:6}}>{label}</div>
    <div style={{fontSize:26,fontWeight:800,color,fontFamily:FONT_HEAD,lineHeight:1}}>{value}</div>
    {sub && <div style={{fontSize:10,color:T.muted,marginTop:4,fontFamily:FONT_BODY}}>{sub}</div>}
  </div>
);

/* ─── CHART PANEL ───────────────────────────────────────────────────────────── */
let chartCounter = 1;

function ChartPanel({ data, columns, onRemove }) {
  const [type, setType]       = useState("bar");
  const [xField, setXField]   = useState("");
  const [yField, setYField]   = useState("");
  const [fn, setFn]           = useState("count");
  const [title, setTitle]     = useState(`Visual ${chartCounter++}`);
  const [editTitle, setEditTitle] = useState(false);

  const chartData = useMemo(() => {
    if (!xField) return [];
    return aggregate(data, xField, yField || Object.keys(data[0]||{})[0], fn);
  }, [data, xField, yField, fn]);

  const ttp = { contentStyle:{background:T.panel,border:`1px solid ${T.border}`,borderRadius:8,color:T.text,fontSize:11,fontFamily:FONT_BODY}, labelStyle:{color:T.text} };

  const renderViz = () => {
    if (!chartData.length) return (
      <div style={{height:200,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",color:T.muted,gap:8}}>
        <span style={{fontSize:32}}>📊</span>
        <span style={{fontSize:12,fontFamily:FONT_BODY}}>Set Axis + Value to visualise</span>
      </div>
    );

    if (type === "pie") return (
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%"
            outerRadius={85} innerRadius={30}
            label={({name,percent})=>`${name} ${(percent*100).toFixed(0)}%`} labelLine={false}
            stroke="none">
            {chartData.map((_,i)=><Cell key={i} fill={PALETTE[i%PALETTE.length]}/>)}
          </Pie>
          <Tooltip {...ttp}/>
        </PieChart>
      </ResponsiveContainer>
    );

    if (type === "line") return (
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData} margin={{top:4,right:8,left:0,bottom:36}}>
          <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
          <XAxis dataKey="name" tick={{fill:T.muted,fontSize:10,fontFamily:FONT_BODY}} angle={-35} textAnchor="end" interval={0}/>
          <YAxis tick={{fill:T.muted,fontSize:10}} tickFormatter={v=>fmtNum(v)}/>
          <Tooltip {...ttp} formatter={v=>[fmtNum(v),"Value"]}/>
          <Line type="monotone" dataKey="value" stroke={T.accent} strokeWidth={2.5}
            dot={{fill:T.accent,r:4,strokeWidth:0}} activeDot={{r:6,strokeWidth:0,fill:T.green}}/>
        </LineChart>
      </ResponsiveContainer>
    );

    if (type === "area") return (
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={chartData} margin={{top:4,right:8,left:0,bottom:36}}>
          <defs>
            <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={T.accent} stopOpacity={0.35}/>
              <stop offset="95%" stopColor={T.accent} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
          <XAxis dataKey="name" tick={{fill:T.muted,fontSize:10,fontFamily:FONT_BODY}} angle={-35} textAnchor="end" interval={0}/>
          <YAxis tick={{fill:T.muted,fontSize:10}} tickFormatter={v=>fmtNum(v)}/>
          <Tooltip {...ttp} formatter={v=>[fmtNum(v),"Value"]}/>
          <Area type="monotone" dataKey="value" stroke={T.accent} strokeWidth={2.5} fill="url(#ag)"/>
        </AreaChart>
      </ResponsiveContainer>
    );

    if (type === "hbar") return (
      <ResponsiveContainer width="100%" height={Math.max(200, chartData.length*30+40)}>
        <BarChart data={chartData} layout="vertical" margin={{top:4,right:50,left:90,bottom:4}}>
          <CartesianGrid strokeDasharray="3 3" stroke={T.border} horizontal={false}/>
          <XAxis type="number" tick={{fill:T.muted,fontSize:10}} tickFormatter={v=>fmtNum(v)}/>
          <YAxis type="category" dataKey="name" tick={{fill:T.text,fontSize:11,fontFamily:FONT_BODY}} width={85}/>
          <Tooltip {...ttp} formatter={v=>[fmtNum(v),"Value"]}/>
          <Bar dataKey="value" radius={[0,4,4,0]} label={{position:"right",fill:T.muted,fontSize:10,formatter:v=>fmtNum(v)}}>
            {chartData.map((_,i)=><Cell key={i} fill={PALETTE[i%PALETTE.length]}/>)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );

    // default: vertical bar
    return (
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={chartData} margin={{top:4,right:8,left:0,bottom:36}}>
          <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
          <XAxis dataKey="name" tick={{fill:T.muted,fontSize:10,fontFamily:FONT_BODY}} angle={-35} textAnchor="end" interval={0}/>
          <YAxis tick={{fill:T.muted,fontSize:10}} tickFormatter={v=>fmtNum(v)}/>
          <Tooltip {...ttp} formatter={v=>[fmtNum(v),"Value"]}/>
          <Bar dataKey="value" radius={[4,4,0,0]} label={{position:"top",fill:T.muted,fontSize:9,formatter:v=>fmtNum(v)}}>
            {chartData.map((_,i)=><Cell key={i} fill={PALETTE[i%PALETTE.length]}/>)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div style={{background:T.card,border:`1px solid ${T.border}`,borderRadius:14,padding:16,display:"flex",flexDirection:"column",gap:10,position:"relative"}}>
      {/* Title row */}
      <div style={{display:"flex",alignItems:"center",gap:8}}>
        {editTitle
          ? <input value={title} onChange={e=>setTitle(e.target.value)} onBlur={()=>setEditTitle(false)} autoFocus
              style={{flex:1,background:T.bg,border:`1px solid ${T.accent}`,borderRadius:6,color:T.text,padding:"3px 8px",fontSize:13,fontFamily:FONT_HEAD,outline:"none"}}/>
          : <span onClick={()=>setEditTitle(true)} style={{flex:1,fontSize:13,fontWeight:700,fontFamily:FONT_HEAD,color:T.text,cursor:"text"}}>{title}</span>
        }
        <button onClick={onRemove} style={{background:"none",border:"none",color:T.muted,cursor:"pointer",fontSize:18,lineHeight:1,padding:"0 4px"}}>×</button>
      </div>

      {/* Chart type */}
      <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>
        {[["bar","▦"],["hbar","◫"],["line","∿"],["area","◭"],["pie","◕"]].map(([t,ic])=>(
          <Btn key={t} sm active={type===t} accent={T.accent} onClick={()=>setType(t)}>{ic} {t}</Btn>
        ))}
      </div>

      {/* Drop zones */}
      <div style={{display:"flex",gap:6}}>
        <DropTarget label="Axis" value={xField} accent={T.amber}
          onDrop={f=>setXField(f)} onClear={()=>setXField("")}/>
        <DropTarget label="Value" value={yField} accent={T.green}
          onDrop={f=>setYField(f)} onClear={()=>setYField("")}/>
      </div>

      {/* Aggregation */}
      <div style={{display:"flex",gap:3}}>
        {["count","sum","avg","max","min"].map(f=>(
          <Pill key={f} label={f} active={fn===f} color={T.green} onClick={()=>setFn(f)}/>
        ))}
      </div>

      {/* Chart */}
      {renderViz()}

      {/* Footer */}
      <div style={{fontSize:10,color:T.muted,textAlign:"right",fontFamily:FONT_BODY}}>
        {chartData.length} groups · {data.length.toLocaleString()} rows
      </div>
    </div>
  );
}

/* ─── FILTER BAR ─────────────────────────────────────────────────────────────── */
function FilterBar({ columns, rawData, filters, setFilters }) {
  const [collapsed, setCollapsed] = useState(false);
  const strCols = columns.filter(c=>c.type==="string").slice(0,7);

  return (
    <div style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:12,marginBottom:14,overflow:"hidden"}}>
      <div onClick={()=>setCollapsed(o=>!o)} style={{
        padding:"10px 16px",display:"flex",alignItems:"center",justifyContent:"space-between",
        cursor:"pointer",borderBottom:collapsed?"none":`1px solid ${T.border}`,
      }}>
        <span style={{fontWeight:700,fontSize:12,fontFamily:FONT_BODY,color:T.accent,textTransform:"uppercase",letterSpacing:"0.1em"}}>
          ⬡ Filters
          {Object.keys(filters).length > 0 &&
            <span style={{marginLeft:8,background:T.rose,color:"#fff",borderRadius:10,padding:"1px 7px",fontSize:10}}>{Object.keys(filters).length} active</span>}
        </span>
        <span style={{color:T.muted,fontSize:12}}>{collapsed?"▼":"▲"}</span>
      </div>
      {!collapsed && (
        <div style={{padding:"12px 16px",display:"flex",flexWrap:"wrap",gap:20,alignItems:"flex-start"}}>
          {strCols.map(col=>{
            const allVals = [...new Set(rawData.map(r=>String(r[col.name]??"")))].filter(Boolean).sort().slice(0,40);
            const active = filters[col.name] || new Set(allVals);
            return (
              <div key={col.name} style={{minWidth:120}}>
                <div style={{fontSize:9,color:T.violet,fontWeight:800,fontFamily:FONT_BODY,textTransform:"uppercase",letterSpacing:"0.1em",marginBottom:4}}>
                  {col.name}
                </div>
                <div>
                  <Pill label="All" active={active.size===allVals.length} color={T.muted}
                    onClick={()=>setFilters(f=>{const n={...f};if(active.size===allVals.length)n[col.name]=new Set();else delete n[col.name];return n;})}/>
                  {allVals.map(v=>(
                    <Pill key={v} label={v.slice(0,20)} active={active.has(v)} color={T.accent}
                      onClick={()=>setFilters(f=>{
                        const cur=f[col.name]?new Set(f[col.name]):new Set(allVals);
                        cur.has(v)?cur.delete(v):cur.add(v);
                        return{...f,[col.name]:cur};
                      })}/>
                  ))}
                </div>
              </div>
            );
          })}
          {Object.keys(filters).length>0&&(
            <button onClick={()=>setFilters({})} style={{
              alignSelf:"flex-end",background:"none",border:`1px solid ${T.rose}`,
              color:T.rose,borderRadius:8,padding:"4px 12px",cursor:"pointer",fontSize:11,fontFamily:FONT_BODY
            }}>✕ Clear All</button>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── DATA TABLE ─────────────────────────────────────────────────────────────── */
function DataTable({ data, columns }) {
  const [sort, setSort] = useState({ col: null, dir: 1 });
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const PER = 50;

  const sorted = useMemo(() => {
    let d = [...data];
    if (search) d = d.filter(row=>Object.values(row).some(v=>String(v).toLowerCase().includes(search.toLowerCase())));
    if (sort.col) d.sort((a,b)=>{
      const av=a[sort.col]??"", bv=b[sort.col]??"";
      const an=cleanNum(av), bn=cleanNum(bv);
      if (!isNaN(an)&&!isNaN(bn)) return (an-bn)*sort.dir;
      return String(av).localeCompare(String(bv))*sort.dir;
    });
    return d;
  }, [data, sort, search]);

  const page_data = sorted.slice(page*PER, (page+1)*PER);
  const pages = Math.ceil(sorted.length/PER);

  return (
    <div style={{display:"flex",flexDirection:"column",height:"100%",gap:10}}>
      {/* toolbar */}
      <div style={{display:"flex",alignItems:"center",gap:10}}>
        <input value={search} onChange={e=>{setSearch(e.target.value);setPage(0);}} placeholder="Search…"
          style={{flex:1,background:T.card,border:`1px solid ${T.border}`,borderRadius:8,
            color:T.text,padding:"6px 12px",fontSize:12,fontFamily:FONT_BODY,outline:"none"}}/>
        <span style={{color:T.muted,fontSize:11,fontFamily:FONT_BODY}}>{sorted.length.toLocaleString()} rows</span>
      </div>
      {/* table */}
      <div style={{overflowX:"auto",borderRadius:10,border:`1px solid ${T.border}`,flex:1,overflowY:"auto"}}>
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
          <thead style={{position:"sticky",top:0,zIndex:2}}>
            <tr style={{background:T.panel}}>
              {columns.map(col=>(
                <th key={col.name} onClick={()=>setSort(s=>({col:col.name,dir:s.col===col.name?-s.dir:1}))}
                  style={{padding:"10px 12px",textAlign:"left",fontWeight:700,whiteSpace:"nowrap",cursor:"pointer",
                    borderBottom:`1px solid ${T.border}`,fontFamily:FONT_BODY,
                    color:sort.col===col.name?T.accent:col.type==="number"?T.green:col.type==="date"?T.amber:T.violet}}>
                  <div style={{display:"flex",alignItems:"center",gap:4}}>
                    <Badge type={col.type}/>
                    {col.name}
                    {sort.col===col.name&&<span style={{fontSize:9}}>{sort.dir>0?"▲":"▼"}</span>}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {page_data.map((row,i)=>(
              <tr key={i} onMouseEnter={e=>e.currentTarget.style.background=T.panel}
                onMouseLeave={e=>e.currentTarget.style.background="transparent"}
                style={{transition:"background .1s"}}>
                {columns.map(col=>(
                  <td key={col.name} style={{padding:"7px 12px",borderBottom:`1px solid ${T.border}22`,
                    color:col.type==="number"?T.green:T.text,fontFamily:FONT_BODY,
                    whiteSpace:"nowrap",maxWidth:200,overflow:"hidden",textOverflow:"ellipsis"}}>
                    {String(row[col.name]??"")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* pagination */}
      {pages>1&&(
        <div style={{display:"flex",gap:6,justifyContent:"center"}}>
          <Btn sm onClick={()=>setPage(0)} accent={T.muted}>«</Btn>
          <Btn sm onClick={()=>setPage(p=>Math.max(0,p-1))} accent={T.muted}>‹</Btn>
          <span style={{color:T.muted,fontSize:11,fontFamily:FONT_BODY,padding:"3px 8px"}}>
            {page+1} / {pages}
          </span>
          <Btn sm onClick={()=>setPage(p=>Math.min(pages-1,p+1))} accent={T.muted}>›</Btn>
          <Btn sm onClick={()=>setPage(pages-1)} accent={T.muted}>»</Btn>
        </div>
      )}
    </div>
  );
}

/* ─── MODEL VIEW ─────────────────────────────────────────────────────────────── */
function ModelView({ tables, activeTable, setActiveTable, setColumns }) {
  const names = Object.keys(tables);
  return (
    <div style={{padding:24}}>
      <div style={{fontFamily:FONT_HEAD,fontWeight:800,fontSize:18,color:T.text,marginBottom:6}}>Data Model</div>
      <div style={{color:T.muted,fontSize:12,fontFamily:FONT_BODY,marginBottom:20}}>
        {names.length} table{names.length!==1?"s":""} loaded
      </div>
      {names.length===0&&(
        <div style={{color:T.muted,fontSize:14,fontFamily:FONT_BODY}}>No data yet — import a file to begin.</div>
      )}
      <div style={{display:"flex",flexWrap:"wrap",gap:16}}>
        {names.map(name=>{
          const cols = inferColumns(tables[name]);
          const isActive = name===activeTable;
          return (
            <div key={name} onClick={()=>{setActiveTable(name);setColumns(inferColumns(tables[name]));}}
              style={{background:T.card,border:`1px solid ${isActive?T.accent:T.border}`,borderRadius:14,
                padding:16,minWidth:200,cursor:"pointer",
                boxShadow:isActive?`0 0 0 1px ${T.accent}44,0 4px 20px ${T.accent}18`:"none",
                transition:"all .2s"}}>
              <div style={{fontWeight:800,color:T.accent,marginBottom:8,fontSize:13,fontFamily:FONT_HEAD}}>
                ⊞ {name}
              </div>
              <div style={{fontSize:10,color:T.muted,fontFamily:FONT_BODY,marginBottom:10}}>
                {tables[name].length.toLocaleString()} rows · {cols.length} cols
              </div>
              <div style={{display:"flex",flexDirection:"column",gap:2}}>
                {cols.map(col=>(
                  <div key={col.name} style={{display:"flex",alignItems:"center",gap:6,padding:"2px 0",fontSize:11,fontFamily:FONT_BODY}}>
                    <Badge type={col.type}/>
                    <span style={{color:T.text,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{col.name}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─── MAIN APP ───────────────────────────────────────────────────────────────── */
export default function App() {
  const [tables, setTables]         = useState({});
  const [activeTable, setActiveTable] = useState(null);
  const [columns, setColumns]       = useState([]);
  const [charts, setCharts]         = useState([]);
  const [filters, setFilters]       = useState({});
  const [tab, setTab]               = useState("canvas");
  const [draggingFile, setDraggingFile] = useState(false);
  const [loading, setLoading]       = useState(false);
  const [nextId, setNextId]         = useState(1);
  const fileRef                     = useRef();

  const handleFile = useCallback(async file => {
    setLoading(true);
    try {
      const rows = await parseFile(file);
      const name = file.name.replace(/\.[^.]+$/,"");
      setTables(t=>({...t,[name]:rows}));
      setActiveTable(name);
      setColumns(inferColumns(rows));
      setFilters({});
      setTab("canvas");
    } catch(e) {
      alert("Could not read file: "+e.message);
    }
    setLoading(false);
  },[]);

  const rawData = activeTable ? (tables[activeTable]||[]) : [];

  const filteredData = useMemo(()=>{
    if(!Object.keys(filters).length) return rawData;
    return rawData.filter(row=>
      Object.entries(filters).every(([col,vals])=>
        !vals.size || vals.has(String(row[col]??""))
      )
    );
  },[rawData,filters]);

  // Auto KPI cards for numeric cols
  const numCols = columns.filter(c=>c.type==="number").slice(0,5);
  const kpis = [
    { label:"Total Rows", value:filteredData.length.toLocaleString(), color:T.accent },
    ...numCols.map((col,i)=>{
      const vals = filteredData.map(r=>cleanNum(r[col.name])).filter(v=>v!==0||String(rawData[0]?.[col.name]||"0").trim()==="0");
      const total = vals.reduce((a,b)=>a+b,0);
      return { label:col.name, value:fmtNum(total), color:PALETTE[(i+1)%PALETTE.length], sub:`avg ${fmtNum(total/(vals.length||1))}` };
    })
  ];

  const addChart = () => {
    setCharts(c=>[...c,{id:nextId}]);
    setNextId(n=>n+1);
  };

  return (
    <div style={{minHeight:"100vh",background:T.bg,color:T.text,display:"flex",flexDirection:"column",fontFamily:FONT_BODY}}>

      {/* ── Top bar ── */}
      <header style={{
        height:50,background:T.surface,borderBottom:`1px solid ${T.border}`,
        display:"flex",alignItems:"center",padding:"0 16px",gap:12,
        position:"sticky",top:0,zIndex:200,
        boxShadow:`0 1px 0 ${T.border}`,
      }}>
        {/* Logo */}
        <div style={{fontFamily:FONT_HEAD,fontWeight:900,fontSize:16,color:T.accent,letterSpacing:"0.05em",display:"flex",alignItems:"center",gap:6}}>
          <span style={{background:`linear-gradient(135deg,${T.accent},${T.violet})`,WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>◈ DataStudio</span>
        </div>

        <div style={{width:1,height:24,background:T.border}}/>

        {/* Table switcher */}
        {Object.keys(tables).map(name=>(
          <button key={name} onClick={()=>{setActiveTable(name);setColumns(inferColumns(tables[name]));setFilters({});}}
            style={{background:activeTable===name?`${T.accent}18`:"none",border:`1px solid ${activeTable===name?T.accent:T.border}`,
              color:activeTable===name?T.accent:T.muted,borderRadius:8,padding:"3px 12px",cursor:"pointer",
              fontSize:11,fontFamily:FONT_BODY,fontWeight:600,transition:"all .12s"}}>
            ⊞ {name}
          </button>
        ))}

        <button onClick={()=>fileRef.current.click()}
          style={{background:"none",border:`1px dashed ${T.borderHi}`,color:T.muted,borderRadius:8,
            padding:"3px 12px",cursor:"pointer",fontSize:11,fontFamily:FONT_BODY,transition:"all .12s"}}
          onMouseEnter={e=>{e.currentTarget.style.borderColor=T.accent;e.currentTarget.style.color=T.accent;}}
          onMouseLeave={e=>{e.currentTarget.style.borderColor=T.borderHi;e.currentTarget.style.color=T.muted;}}>
          {loading?"Loading…":"＋ Import CSV / XLSX"}
        </button>
        <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" style={{display:"none"}}
          onChange={e=>e.target.files[0]&&handleFile(e.target.files[0])}/>

        <div style={{flex:1}}/>

        {/* View tabs */}
        {[["canvas","◈ Canvas"],["data","⊟ Data"],["model","⬡ Model"]].map(([id,lbl])=>(
          <button key={id} onClick={()=>setTab(id)} style={{
            background:tab===id?`${T.accent}18`:"none",
            border:`1px solid ${tab===id?T.accent:T.border}`,
            color:tab===id?T.accent:T.muted,
            borderRadius:8,padding:"4px 14px",cursor:"pointer",fontSize:11,
            fontFamily:FONT_BODY,fontWeight:600,transition:"all .12s"}}>
            {lbl}
          </button>
        ))}
      </header>

      {/* ── Empty state ── */}
      {!activeTable&&(
        <div
          onDragOver={e=>{e.preventDefault();setDraggingFile(true);}}
          onDragLeave={()=>setDraggingFile(false)}
          onDrop={e=>{e.preventDefault();setDraggingFile(false);const f=e.dataTransfer.files[0];if(f)handleFile(f);}}
          onClick={()=>fileRef.current.click()}
          style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",
            cursor:"pointer",gap:16,margin:40,borderRadius:20,
            border:`2px dashed ${draggingFile?T.accent:T.border}`,
            background:draggingFile?`${T.accent}08`:T.surface,transition:"all .2s"}}>
          <div style={{width:80,height:80,borderRadius:"50%",background:`${T.accent}12`,
            display:"flex",alignItems:"center",justifyContent:"center",fontSize:36,
            boxShadow:`0 0 40px ${T.accent}22`}}>📂</div>
          <div style={{fontSize:20,fontWeight:800,color:T.text,fontFamily:FONT_HEAD}}>Drop a data file to begin</div>
          <div style={{fontSize:13,color:T.muted}}>CSV · XLSX · XLS supported</div>
          <div style={{fontSize:11,color:T.dim,fontFamily:FONT_BODY,marginTop:4,textAlign:"center",maxWidth:360,lineHeight:1.7}}>
            Once imported, drag fields onto charts to build visuals.<br/>
            Filters, KPIs and aggregations update instantly.
          </div>
          <div style={{padding:"8px 24px",background:`${T.accent}18`,border:`1px solid ${T.accent}`,
            borderRadius:10,color:T.accent,fontSize:12,fontFamily:FONT_BODY,marginTop:8}}>
            click to browse or drag & drop
          </div>
        </div>
      )}

      {/* ── Main layout ── */}
      {activeTable&&(
        <div style={{flex:1,display:"flex",overflow:"hidden"}}>

          {/* Fields sidebar — only on canvas */}
          {tab==="canvas"&&(
            <aside style={{width:210,background:T.surface,borderRight:`1px solid ${T.border}`,
              display:"flex",flexDirection:"column",overflow:"hidden",flexShrink:0}}>
              <div style={{padding:"12px 12px 8px",borderBottom:`1px solid ${T.border}`}}>
                <div style={{fontSize:9,color:T.muted,textTransform:"uppercase",letterSpacing:"0.12em",marginBottom:2,fontFamily:FONT_BODY}}>
                  Fields
                </div>
                <div style={{fontSize:9,color:T.dim,fontFamily:FONT_BODY}}>drag to chart zones ↓</div>
              </div>
              <div style={{flex:1,overflowY:"auto",padding:8}}>
                {["number","string","date"].map(type=>{
                  const cols=columns.filter(c=>c.type===type);
                  if(!cols.length) return null;
                  const lbl={number:"Σ Measures",string:"A Dimensions",date:"D Dates"}[type];
                  return (
                    <div key={type} style={{marginBottom:14}}>
                      <div style={{fontSize:9,color:T.muted,textTransform:"uppercase",
                        letterSpacing:"0.1em",fontFamily:FONT_BODY,marginBottom:5,paddingLeft:4}}>{lbl}</div>
                      {cols.map(col=>(
                        <div key={col.name} draggable
                          onDragStart={e=>e.dataTransfer.setData("field",col.name)}
                          style={{display:"flex",alignItems:"center",gap:6,
                            padding:"5px 8px",borderRadius:7,marginBottom:2,
                            background:T.card,border:`1px solid ${T.border}`,
                            cursor:"grab",fontSize:11,color:T.text,
                            transition:"border-color .12s"}}
                          onMouseEnter={e=>e.currentTarget.style.borderColor=type==="number"?T.green:type==="date"?T.amber:T.violet}
                          onMouseLeave={e=>e.currentTarget.style.borderColor=T.border}>
                          <Badge type={col.type}/>
                          <span style={{overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap",flex:1,fontFamily:FONT_BODY}}>{col.name}</span>
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>
              <div style={{padding:10,borderTop:`1px solid ${T.border}`}}>
                <button onClick={addChart} style={{
                  width:"100%",fontFamily:FONT_HEAD,fontWeight:700,fontSize:13,
                  background:`linear-gradient(135deg,${T.accent}22,${T.violet}22)`,
                  border:`1px solid ${T.accent}`,color:T.accent,
                  borderRadius:10,padding:"9px 0",cursor:"pointer",
                  transition:"all .15s",letterSpacing:"0.03em"}}
                  onMouseEnter={e=>{e.currentTarget.style.background=`linear-gradient(135deg,${T.accent}44,${T.violet}44)`;}}
                  onMouseLeave={e=>{e.currentTarget.style.background=`linear-gradient(135deg,${T.accent}22,${T.violet}22)`;}}
                >+ Add Visual</button>
              </div>
            </aside>
          )}

          {/* ── Canvas tab ── */}
          {tab==="canvas"&&(
            <main style={{flex:1,overflowY:"auto",padding:16}}>
              {/* Filters */}
              <FilterBar columns={columns} rawData={rawData} filters={filters} setFilters={setFilters}/>

              {/* KPI cards */}
              <div style={{display:"flex",gap:12,marginBottom:16,flexWrap:"wrap"}}>
                {kpis.map((k,i)=><KpiCard key={i} {...k}/>)}
              </div>

              {/* Charts */}
              {charts.length===0?(
                <div style={{display:"flex",flexDirection:"column",alignItems:"center",
                  justifyContent:"center",height:280,color:T.muted,gap:12,
                  border:`1px dashed ${T.border}`,borderRadius:14}}>
                  <span style={{fontSize:36}}>📊</span>
                  <span style={{fontSize:15,fontFamily:FONT_HEAD,fontWeight:700,color:T.dim}}>Click "+ Add Visual" to start</span>
                  <span style={{fontSize:12,fontFamily:FONT_BODY}}>Then drag fields from the sidebar into each chart</span>
                </div>
              ):(
                <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(460px,1fr))",gap:14}}>
                  {charts.map(c=>(
                    <ChartPanel key={c.id} data={filteredData} columns={columns}
                      onRemove={()=>setCharts(cs=>cs.filter(x=>x.id!==c.id))}/>
                  ))}
                </div>
              )}
            </main>
          )}

          {/* ── Data tab ── */}
          {tab==="data"&&(
            <main style={{flex:1,padding:16,display:"flex",flexDirection:"column",overflow:"hidden"}}>
              <DataTable data={filteredData} columns={columns}/>
            </main>
          )}

          {/* ── Model tab ── */}
          {tab==="model"&&(
            <main style={{flex:1,overflowY:"auto"}}>
              <ModelView tables={tables} activeTable={activeTable}
                setActiveTable={setActiveTable} setColumns={setColumns}/>
            </main>
          )}
        </div>
      )}
    </div>
  );
}
