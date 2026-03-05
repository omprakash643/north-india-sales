import { useState, useCallback, useMemo, useEffect } from "react";
import * as Papa from "papaparse";
import * as XLSX from "xlsx";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";

/* ─── DESIGN TOKENS ─────────────────────────────────────────────────────────── */
const T = {
  bg: "#080b10",
  surface: "#0d1117",
  panel: "#111820",
  card: "#141c24",
  border: "#1e2d3d",
  borderHi: "#2a4060",
  accent: "#00d4ff",
  green: "#00ff9d",
  amber: "#ffb300",
  rose: "#ff4d6d",
  violet: "#b06fff",
  text: "#cdd9e5",
  muted: "#4a6070",
  dim: "#2a3a4a",
};

const PALETTE = [
  "#00d4ff","#00ff9d","#ffb300","#ff4d6d","#b06fff",
  "#ff8c42","#4dffdb","#ff6b9d","#c8ff6b","#6b9dff",
];

const FONT_HEAD = "'Syne', system-ui, sans-serif";
const FONT_BODY = "'IBM Plex Mono', 'Courier New', monospace";

/* ─── UTILS ─────────────────────────────────────────────────────────────────── */
function detectType(values) {
  const s = values.filter(v => v != null && v !== "").slice(0, 40);
  if (!s.length) return "string";

  const nums = s.filter(v => !isNaN(parseFloat(String(v).replace(/[,₹$€£%]/g,""))));
  if (nums.length / s.length > 0.7) return "number";

  const dates = s.filter(v => !isNaN(Date.parse(String(v))));
  if (dates.length / s.length > 0.6) return "date";

  return "string";
}

function inferColumns(data) {
  if (!data?.length) return [];
  return Object.keys(data[0]).map(name => ({
    name,
    type: detectType(data.map(r => r[name]))
  }));
}

function cleanNum(v) {
  const cleaned = String(v ?? "").replace(/[,₹$€£%]/g, "").trim();
  const n = parseFloat(cleaned);
  return isNaN(n) ? 0 : n;
}

function aggregate(data, groupCol, valueCol = "", fn = "count") {
  if (!groupCol) return [];

  const map = new Map();
  for (const row of data) {
    const key = String(row[groupCol] ?? "(blank)").trim().slice(0, 28);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(cleanNum(row[valueCol]));
  }

  return Array.from(map.entries())
    .map(([name, vals]) => ({
      name,
      value:
        fn === "sum" ? vals.reduce((a,b)=>a+b, 0) :
        fn === "avg" ? (vals.reduce((a,b)=>a+b, 0) / (vals.length || 1)) :
        fn === "max" ? Math.max(...vals) :
        fn === "min" ? Math.min(...vals) :
        vals.length,
      count: vals.length
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 30);
}

function fmtNum(v) {
  if (v >= 1e7) return `${(v/1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `${(v/1e5).toFixed(1)} L`;
  if (v >= 1e3) return `${(v/1e3).toFixed(0)}K`;
  return Number.isInteger(v) ? v.toLocaleString() : v.toFixed(1);
}

async function parseFile(file) {
  return new Promise((resolve, reject) => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext === "csv") {
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        transformHeader: h => h.trim(),
        complete: r => resolve(r.data.filter(row => Object.keys(row).length > 0)),
        error: reject,
      });
    } else if (["xlsx", "xls"].includes(ext)) {
      const reader = new FileReader();
      reader.onload = e => {
        try {
          const wb = XLSX.read(e.target.result, { type: "array" });
          const ws = wb.Sheets[wb.SheetNames[0]];
          resolve(XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" })
            .filter(row => row.some(v => v != null && v !== ""))
            .map(row => {
              const obj = {};
              row.forEach((v, i) => { obj[`Col${i+1}`] = v; });
              return obj;
            }));
        } catch (err) { reject(err); }
      };
      reader.readAsArrayBuffer(file);
    } else {
      reject(new Error(`Unsupported file type: ${ext}`));
    }
  });
}

/* ─── SMALL COMPONENTS ──────────────────────────────────────────────────────── */
const Pill = ({ label, active, color = T.accent, onClick }) => (
  <span
    onClick={onClick}
    style={{
      display: "inline-flex",
      alignItems: "center",
      padding: "4px 12px",
      borderRadius: 20,
      fontSize: 11,
      fontFamily: FONT_BODY,
      fontWeight: 600,
      cursor: "pointer",
      userSelect: "none",
      margin: "3px 3px",
      border: `1px solid ${active ? color : T.border}`,
      background: active ? `${color}18` : "transparent",
      color: active ? color : T.muted,
      transition: "all 0.13s ease",
    }}
  >
    {label}
  </span>
);

const Badge = ({ type }) => {
  const map = {
    number: [T.green, "Σ"],
    date:   [T.amber, "📅"],
    string: [T.violet,"A"]
  };
  const [col, lbl] = map[type] || [T.muted, "?"];
  return (
    <span style={{
      color: col,
      fontSize: 11,
      fontWeight: 900,
      minWidth: 16,
      textAlign: "center"
    }}>
      {lbl}
    </span>
  );
};

const DropTarget = ({ label, value, accent, onDrop, onClear }) => {
  const [over, setOver] = useState(false);
  return (
    <div
      onDragOver={e => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={e => {
        e.preventDefault();
        setOver(false);
        const field = e.dataTransfer.getData("field");
        if (field) onDrop(field);
      }}
      style={{
        flex: 1,
        minHeight: 38,
        borderRadius: 8,
        border: `1.5px dashed ${over ? accent : T.border}`,
        background: over ? `${accent}10` : T.card,
        display: "flex",
        alignItems: "center",
        padding: "0 12px",
        gap: 8,
        fontSize: 12,
        fontFamily: FONT_BODY,
        color: value ? T.text : T.muted,
        transition: "all 0.14s",
        cursor: "default",
      }}
    >
      <span style={{
        color: accent,
        fontSize: 10,
        fontWeight: 900,
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        minWidth: 36
      }}>
        {label}
      </span>
      <span style={{
        flex: 1,
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap"
      }}>
        {value || "drop field here"}
      </span>
      {value && (
        <span
          onClick={e => { e.stopPropagation(); onClear(); }}
          style={{ cursor: "pointer", color: T.rose, fontSize: 16, lineHeight: 1 }}
        >
          ×
        </span>
      )}
    </div>
  );
};

/* ─── KPI CARD ──────────────────────────────────────────────────────────────── */
const KpiCard = ({ label, value, color, sub }) => (
  <div style={{
    background: `linear-gradient(145deg, ${T.card}, ${T.panel})`,
    border: `1px solid ${color}30`,
    borderRadius: 12,
    padding: "16px 20px",
    flex: "1 1 160px",
    minWidth: 140,
    maxWidth: 240,
    boxShadow: `0 4px 20px ${color}08, inset 0 1px 0 ${color}18`,
    position: "relative",
    overflow: "hidden",
  }}>
    <div style={{
      position: "absolute",
      top: -30,
      right: -30,
      width: 100,
      height: 100,
      borderRadius: "50%",
      background: `${color}08`
    }} />
    <div style={{
      fontSize: 11,
      color: T.muted,
      textTransform: "uppercase",
      letterSpacing: "0.1em",
      fontFamily: FONT_BODY,
      marginBottom: 6
    }}>
      {label}
    </div>
    <div style={{
      fontSize: 28,
      fontWeight: 800,
      color,
      fontFamily: FONT_HEAD,
      lineHeight: 1
    }}>
      {value}
    </div>
    {sub && (
      <div style={{
        fontSize: 11,
        color: T.muted,
        marginTop: 6,
        fontFamily: FONT_BODY
      }}>
        {sub}
      </div>
    )}
  </div>
);

/* ─── CHART PANEL ───────────────────────────────────────────────────────────── */
let chartCounter = 1;

function ChartPanel({ data, columns, onRemove }) {
  const [type, setType]     = useState("bar");
  const [xField, setXField] = useState("");
  const [yField, setYField] = useState("");
  const [fn, setFn]         = useState("count");
  const [title, setTitle]   = useState(`Chart ${chartCounter++}`);

  const chartData = useMemo(() => {
    return aggregate(data, xField, yField, fn);
  }, [data, xField, yField, fn]);

  const tooltipProps = {
    contentStyle: { background: T.panel, border: `1px solid ${T.border}`, borderRadius: 8, color: T.text, fontSize: 12 },
    labelStyle: { color: T.text }
  };

  const renderChart = () => {
    if (!chartData.length) {
      return (
        <div style={{
          height: 220,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          color: T.muted,
          gap: 10
        }}>
          <span style={{ fontSize: 40 }}>📊</span>
          <div style={{ fontSize: 13, fontFamily: FONT_BODY }}>Drag fields to Axis & Value</div>
        </div>
      );
    }

    const commonProps = {
      data: chartData,
      margin: { top: 10, right: 20, left: 0, bottom: 40 }
    };

    switch (type) {
      case "pie":
        return (
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={90}
                innerRadius={40}
                label={({ name, percent }) => `${name.slice(0,18)} ${(percent*100).toFixed(0)}%`}
                labelLine={false}
                stroke="none"
              >
                {chartData.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
              </Pie>
              <Tooltip {...tooltipProps} />
            </PieChart>
          </ResponsiveContainer>
        );

      case "line":
        return (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
              <XAxis dataKey="name" angle={-40} textAnchor="end" tick={{ fill: T.muted, fontSize: 10 }} />
              <YAxis tick={{ fill: T.muted, fontSize: 10 }} tickFormatter={fmtNum} />
              <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), "Value"]} />
              <Line type="monotone" dataKey="value" stroke={T.accent} strokeWidth={2.5} dot={{ r: 4, strokeWidth: 0 }} activeDot={{ r: 7, fill: T.green }} />
            </LineChart>
          </ResponsiveContainer>
        );

      case "area":
        return (
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart {...commonProps}>
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={T.accent} stopOpacity={0.4} />
                  <stop offset="95%" stopColor={T.accent} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
              <XAxis dataKey="name" angle={-40} textAnchor="end" tick={{ fill: T.muted, fontSize: 10 }} />
              <YAxis tick={{ fill: T.muted, fontSize: 10 }} tickFormatter={fmtNum} />
              <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), "Value"]} />
              <Area type="monotone" dataKey="value" stroke={T.accent} fill="url(#areaGrad)" strokeWidth={2.5} />
            </AreaChart>
          </ResponsiveContainer>
        );

      case "hbar":
        return (
          <ResponsiveContainer width="100%" height={Math.max(220, chartData.length * 32 + 40)}>
            <BarChart data={chartData} layout="vertical" margin={{ top: 10, right: 60, left: 100, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={T.border} horizontal={false} />
              <XAxis type="number" tick={{ fill: T.muted, fontSize: 10 }} tickFormatter={fmtNum} />
              <YAxis type="category" dataKey="name" tick={{ fill: T.text, fontSize: 11 }} width={90} />
              <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), "Value"]} />
              <Bar dataKey="value" radius={[0, 6, 6, 0]} minPointSize={3}>
                {chartData.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );

      default: // vertical bar
        return (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
              <XAxis dataKey="name" angle={-40} textAnchor="end" tick={{ fill: T.muted, fontSize: 10 }} />
              <YAxis tick={{ fill: T.muted, fontSize: 10 }} tickFormatter={fmtNum} />
              <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), "Value"]} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]} minPointSize={3}>
                {chartData.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div style={{
      background: T.card,
      border: `1px solid ${T.border}`,
      borderRadius: 14,
      padding: 16,
      display: "flex",
      flexDirection: "column",
      gap: 12,
      position: "relative",
      boxShadow: "0 4px 20px rgba(0,0,0,0.3)"
    }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          style={{
            flex: 1,
            background: T.bg,
            border: `1px solid ${T.border}`,
            borderRadius: 6,
            color: T.text,
            padding: "6px 10px",
            fontSize: 14,
            fontFamily: FONT_HEAD,
            outline: "none"
          }}
        />
        <button
          onClick={onRemove}
          style={{
            background: "none",
            border: "none",
            color: T.muted,
            fontSize: 20,
            cursor: "pointer",
            padding: "0 4px"
          }}
        >
          ×
        </button>
      </div>

      {/* Chart type buttons */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {[
          ["bar",  "▦ Bar"],
          ["hbar", "◫ H-Bar"],
          ["line", "∿ Line"],
          ["area", "◭ Area"],
          ["pie",  "◔ Pie"]
        ].map(([t, label]) => (
          <button
            key={t}
            onClick={() => setType(t)}
            style={{
              background: type === t ? `${T.accent}18` : "transparent",
              border: `1px solid ${type === t ? T.accent : T.border}`,
              color: type === t ? T.accent : T.muted,
              borderRadius: 6,
              padding: "4px 10px",
              fontSize: 11,
              fontFamily: FONT_BODY,
              cursor: "pointer",
              transition: "all 0.13s"
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Drop zones */}
      <div style={{ display: "flex", gap: 10, flexDirection: "column" }}>
        <DropTarget label="X-Axis" value={xField} accent={T.amber}
          onDrop={setXField} onClear={() => setXField("")} />
        <DropTarget label="Value" value={yField} accent={T.green}
          onDrop={setYField} onClear={() => setYField("")} />
      </div>

      {/* Aggregation pills */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {["count", "sum", "avg", "max", "min"].map(f => (
          <Pill
            key={f}
            label={f.toUpperCase()}
            active={fn === f}
            color={T.green}
            onClick={() => setFn(f)}
          />
        ))}
      </div>

      {/* Chart area */}
      {renderChart()}

      {/* Footer stats */}
      <div style={{
        fontSize: 11,
        color: T.muted,
        textAlign: "right",
        fontFamily: FONT_BODY
      }}>
        {chartData.length} groups • {data.length.toLocaleString()} rows
      </div>
    </div>
  );
}

/* ─── MAIN APP ──────────────────────────────────────────────────────────────── */
export default function App() {
  const [tables, setTables]         = useState({});
  const [activeTable, setActiveTable] = useState(null);
  const [columns, setColumns]       = useState([]);
  const [charts, setCharts]         = useState([]);
  const [filters, setFilters]       = useState({});
  const [tab, setTab]               = useState("canvas");
  const [loading, setLoading]       = useState(false);

  const fileInputRef = useCallback(ref => { window.fileInput = ref; }, []);

  const handleFile = useCallback(async (file) => {
    if (!file) return;
    setLoading(true);
    try {
      const rows = await parseFile(file);
      const name = file.name.replace(/\.[^.]+$/, "").replace(/[^a-zA-Z0-9]/g, "_");
      setTables(prev => ({ ...prev, [name]: rows }));
      setActiveTable(name);
      setColumns(inferColumns(rows));
      setFilters({});
      setCharts([]);
      setTab("canvas");
    } catch (err) {
      alert("Error reading file:\n" + err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const rawData = useMemo(() => {
    return activeTable ? (tables[activeTable] || []) : [];
  }, [tables, activeTable]);

  const filteredData = useMemo(() => {
    if (!Object.keys(filters).length) return rawData;

    return rawData.filter(row =>
      Object.entries(filters).every(([col, allowed]) =>
        !allowed.size || allowed.has(String(row[col] ?? ""))
      )
    );
  }, [rawData, filters]);

  const numCols = columns.filter(c => c.type === "number").slice(0, 5);

  const kpis = useMemo(() => [
    { label: "Rows", value: filteredData.length.toLocaleString(), color: T.accent },
    ...numCols.map((col, i) => {
      const vals = filteredData.map(r => cleanNum(r[col.name])).filter(v => !isNaN(v));
      const total = vals.reduce((a, b) => a + b, 0);
      const avg = vals.length ? total / vals.length : 0;
      return {
        label: col.name,
        value: fmtNum(total),
        color: PALETTE[(i + 1) % PALETTE.length],
        sub: `avg ${fmtNum(avg)}`
      };
    })
  ], [filteredData, numCols]);

  const addChart = () => {
    setCharts(prev => [...prev, { id: Date.now() }]);
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: T.bg,
      color: T.text,
      fontFamily: FONT_BODY,
      display: "flex",
      flexDirection: "column"
    }}>
      {/* Header */}
      <header style={{
        height: 52,
        background: T.surface,
        borderBottom: `1px solid ${T.border}`,
        display: "flex",
        alignItems: "center",
        padding: "0 20px",
        gap: 16,
        position: "sticky",
        top: 0,
        zIndex: 1000,
        boxShadow: "0 2px 10px rgba(0,0,0,0.4)"
      }}>
        <div style={{
          fontFamily: FONT_HEAD,
          fontWeight: 900,
          fontSize: 18,
          background: `linear-gradient(90deg, ${T.accent}, ${T.violet})`,
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent"
        }}>
          DataStudio
        </div>

        {Object.keys(tables).map(name => (
          <button
            key={name}
            onClick={() => {
              setActiveTable(name);
              setColumns(inferColumns(tables[name]));
              setFilters({});
              setCharts([]);
            }}
            style={{
              background: activeTable === name ? `${T.accent}20` : "transparent",
              border: `1px solid ${activeTable === name ? T.accent : T.border}`,
              color: activeTable === name ? T.accent : T.muted,
              borderRadius: 8,
              padding: "5px 14px",
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer"
            }}
          >
            {name}
          </button>
        ))}

        <button
          onClick={() => window.fileInput?.click()}
          disabled={loading}
          style={{
            background: loading ? `${T.muted}30` : "transparent",
            border: `1px dashed ${loading ? T.muted : T.borderHi}`,
            color: loading ? T.muted : T.accent,
            borderRadius: 8,
            padding: "6px 14px",
            fontSize: 12,
            cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "Loading..." : "+ Import CSV/XLSX"}
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          style={{ display: "none" }}
          onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
        />

        <div style={{ flex: 1 }} />

        {["canvas", "data", "model"].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              background: tab === t ? `${T.accent}20` : "transparent",
              border: `1px solid ${tab === t ? T.accent : T.border}`,
              color: tab === t ? T.accent : T.muted,
              borderRadius: 8,
              padding: "6px 14px",
              fontSize: 12,
              cursor: "pointer"
            }}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </header>

      {/* Main content */}
      {!activeTable ? (
        <div style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          color: T.muted
        }}>
          <div style={{ fontSize: 80, marginBottom: 20 }}>📊</div>
          <h2 style={{ fontFamily: FONT_HEAD, color: T.text }}>Drop CSV or Excel file to start</h2>
          <p style={{ maxWidth: 420, textAlign: "center", lineHeight: 1.6 }}>
            Supports .csv, .xlsx, .xls<br/>
            Drag fields → build charts → filter → export insights
          </p>
        </div>
      ) : (
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
          {/* Sidebar - Fields */}
          {tab === "canvas" && (
            <aside style={{
              width: 220,
              background: T.surface,
              borderRight: `1px solid ${T.border}`,
              overflowY: "auto",
              padding: 12
            }}>
              <div style={{ fontSize: 11, color: T.muted, marginBottom: 12, fontWeight: 600 }}>
                DIMENSIONS & MEASURES
              </div>
              {["string", "date", "number"].map(t => {
                const cols = columns.filter(c => c.type === t);
                if (!cols.length) return null;
                return (
                  <div key={t} style={{ marginBottom: 16 }}>
                    <div style={{
                      fontSize: 10,
                      color: t === "number" ? T.green : t === "date" ? T.amber : T.violet,
                      fontWeight: 800,
                      marginBottom: 6
                    }}>
                      {t.toUpperCase()}
                    </div>
                    {cols.map(col => (
                      <div
                        key={col.name}
                        draggable
                        onDragStart={e => e.dataTransfer.setData("field", col.name)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                          padding: "6px 8px",
                          marginBottom: 4,
                          background: T.card,
                          borderRadius: 6,
                          cursor: "grab",
                          border: `1px solid ${T.border}`,
                          fontSize: 12
                        }}
                      >
                        <Badge type={col.type} />
                        <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}>
                          {col.name}
                        </span>
                      </div>
                    ))}
                  </div>
                );
              })}

              <button
                onClick={addChart}
                style={{
                  width: "100%",
                  marginTop: 16,
                  padding: 12,
                  background: `linear-gradient(135deg, ${T.accent}30, ${T.violet}20)`,
                  border: `1px solid ${T.accent}`,
                  color: T.accent,
                  borderRadius: 8,
                  fontWeight: 700,
                  fontSize: 13,
                  cursor: "pointer"
                }}
              >
                + New Visual
              </button>
            </aside>
          )}

          {/* Main area */}
          <main style={{ flex: 1, overflow: "auto", padding: 16 }}>
            {tab === "canvas" && (
              <>
                {/* Filters */}
                {/* You can keep or simplify FilterBar — it's optional for v1 */}

                {/* KPIs */}
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
                  gap: 12,
                  marginBottom: 24
                }}>
                  {kpis.map((k, i) => (
                    <KpiCard key={i} {...k} />
                  ))}
                </div>

                {/* Charts grid */}
                {charts.length === 0 ? (
                  <div style={{
                    height: 400,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    color: T.dim,
                    gap: 16,
                    border: `2px dashed ${T.border}`,
                    borderRadius: 16
                  }}>
                    <div style={{ fontSize: 48 }}>📈</div>
                    <div style={{ fontSize: 18, fontFamily: FONT_HEAD }}>
                      Add a visual and drag fields here
                    </div>
                  </div>
                ) : (
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(480px, 1fr))",
                    gap: 16
                  }}>
                    {charts.map(c => (
                      <ChartPanel
                        key={c.id}
                        data={filteredData}
                        columns={columns}
                        onRemove={() => setCharts(prev => prev.filter(x => x.id !== c.id))}
                      />
                    ))}
                  </div>
                )}
              </>
            )}

            {tab === "data" && (
              <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
                {/* Simple data table implementation can go here */}
                <div style={{ padding: 16, background: T.card, borderRadius: 12 }}>
                  <h3 style={{ margin: 0, color: T.accent }}>Data Preview</h3>
                  <p style={{ color: T.muted }}>({filteredData.length} rows after filters)</p>
                </div>
              </div>
            )}

            {tab === "model" && (
              <div style={{ padding: 24 }}>
                <h2 style={{ color: T.text, fontFamily: FONT_HEAD }}>Data Model</h2>
                <p>{Object.keys(tables).length} table(s) loaded</p>
                {/* Table cards... */}
              </div>
            )}
          </main>
        </div>
      )}
    </div>
  );
}
