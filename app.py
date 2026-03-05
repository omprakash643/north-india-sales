import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="NIC Sales Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@700&display=swap');
* { font-family: 'Barlow', sans-serif; }
.stApp { background-color: #f0ead0; }
[data-testid="stSidebar"] { display: none; }
.nic-header { background: linear-gradient(135deg, #c8a84b, #e8d080, #c8a84b); border-radius: 12px; padding: 16px 28px; margin-bottom: 14px; display: flex; align-items: center; gap: 18px; box-shadow: 0 4px 16px rgba(0,0,0,0.2); }
.nic-logo { background:#fff; border-radius:50%; width:54px; height:54px; display:flex; align-items:center; justify-content:center; font-weight:900; font-size:1.15rem; color:#c8a84b; flex-shrink:0; }
.nic-title { font-family:'Barlow Condensed',sans-serif; font-size:1.9rem; font-weight:700; color:#1a1a1a; }
.nic-sub { font-style:italic; font-size:0.82rem; color:#5a4a1a; }
.kpi-card { background: linear-gradient(135deg, #d4c070, #e8d890); border: 2px solid #b8a040; border-radius: 10px; padding: 14px 8px; text-align: center; box-shadow: 3px 3px 8px rgba(0,0,0,0.18); min-height: 100px; }
.kpi-label { font-family:'Barlow Condensed',sans-serif; font-size:0.72rem; font-weight:700; color:#3a2a00; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:5px; }
.kpi-value { font-family:'Barlow Condensed',sans-serif; font-size:2rem; font-weight:700; color:#1a1200; }
.filter-section { background: linear-gradient(135deg, #2a2a2a, #1a1a1a); border-radius: 12px; padding: 14px 18px; margin-bottom: 14px; }
.filter-label { font-family:'Barlow Condensed',sans-serif; font-size:0.85rem; font-weight:700; color:#e8d080; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px; }
div[data-testid="stButton"] > button { border-radius:20px !important; padding:3px 12px !important; font-size:0.76rem !important; font-weight:600 !important; margin:2px 1px !important; border:1.5px solid #b8a040 !important; background:#e8d880 !important; color:#3a2800 !important; min-height:0 !important; height:auto !important; line-height:1.5 !important; white-space:nowrap !important; }
div[data-testid="stButton"] > button:hover { background:#8B6914 !important; color:#fff !important; border-color:#5a3d10 !important; }
.chart-box { background: linear-gradient(135deg, #ddd090, #ede8b0); border:1.5px solid #b8a040; border-radius:10px; padding:12px; margin-bottom:12px; box-shadow:2px 2px 6px rgba(0,0,0,0.12); }
.chart-title { font-family:'Barlow Condensed',sans-serif; font-size:0.95rem; font-weight:700; color:#2a1a00; text-transform:uppercase; margin-bottom:2px; }
.sec-hdr { background:linear-gradient(90deg,#7a6020,#c8a84b); color:#fff; font-family:'Barlow Condensed',sans-serif; font-weight:700; font-size:1rem; padding:8px 16px; border-radius:6px 6px 0 0; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)

VISITOR_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=0&single=true&output=csv"
LEAD_URL    = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=2066525621&single=true&output=csv"
SALES_URL   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=23552387&single=true&output=csv"

def clean_amount(val):
    try:
        if pd.isna(val): return 0.0
        return float(str(val).replace(',','').replace('₹','').replace(' ','').strip())
    except: return 0.0

@st.cache_data(ttl=300)
def load_all():
    vdf = pd.read_csv(VISITOR_URL)
    ldf = pd.read_csv(LEAD_URL)
    sdf = pd.read_csv(SALES_URL)

    # ── Clean column names ───────────────────────────────────────────────
    for df in [vdf, ldf, sdf]:
        df.columns = df.columns.str.strip()

    # Rename PO Amount → Amount
    if 'PO Amount' in sdf.columns:
        sdf.rename(columns={'PO Amount': 'Amount', 'Customer': 'Customer Name'}, inplace=True)
    if 'Amount' in sdf.columns:
        sdf['Amount'] = sdf['Amount'].apply(clean_amount)

    # More robust date parsing
    for df in [vdf, ldf, sdf]:
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')

    # ── Aggressive normalization of filter columns ────────────────────────
    for df in [vdf, ldf, sdf]:
        for col in ['User', 'Lead Type', 'State', 'Source', 'Stage']:
            if col in df.columns:
                df[col] = (
                    df[col].astype(str)
                       .str.strip()
                       .str.replace(r'\s+', ' ', regex=True)   # collapse multiple spaces
                       .str.upper()
                       .replace(['NAN', 'NONE', ''], pd.NA)
                )

    # Tag source
    vdf['_src'] = 'Visitor'
    ldf['_src'] = 'Lead'
    sdf['_src'] = 'Sales'

    combined = pd.concat([vdf, ldf], ignore_index=True)

    # Master lists AFTER normalization
    def master(col, *dfs):
        vals = set()
        for d in dfs:
            if col in d.columns:
                vals |= set(d[col].dropna().unique())
        return sorted(v for v in vals if v)

    master_users  = master('User',      vdf, ldf, sdf)
    master_leads  = master('Lead Type', vdf, ldf, sdf)
    master_states = master('State',     vdf, ldf, sdf)

    return vdf, ldf, sdf, combined, master_users, master_leads, master_states


# ───────────────────────────────────────────────────────────────
# Load data
# ───────────────────────────────────────────────────────────────
try:
    vdf, ldf, sdf, combined, master_users, master_leads, master_states = load_all()

    # Session state defaults
    for k, v in [('su', set(master_users)), ('sl', set(master_leads)), ('ss', set(master_states))]:
        if k not in st.session_state:
            st.session_state[k] = v

    min_d = combined['Date'].dropna().min().date() if combined['Date'].notna().any() else date.today()
    max_d = combined['Date'].dropna().max().date() if combined['Date'].notna().any() else date.today()

    if 'fstart' not in st.session_state: st.session_state['fstart'] = min_d
    if 'fend'   not in st.session_state: st.session_state['fend']   = max_d

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="nic-header">
      <div class="nic-logo">NIC</div>
      <div>
        <div class="nic-title">North India Compressors
          <span style="font-size:1.1rem;color:#5a4000;">(Jan &amp; Feb)</span></div>
        <div class="nic-sub">a multi product company</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── FILTER PANEL ──────────────────────────────────────────────────────────
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    fc0, fc1, fc2, fc3, fc4 = st.columns([1.5, 2.5, 2.8, 3.2, 0.7])

    with fc0:
        st.markdown('<div class="filter-label">📅 Date Range</div>', unsafe_allow_html=True)
        st.session_state['fstart'] = st.date_input("From", value=st.session_state['fstart'],
            min_value=min_d, max_value=max_d, label_visibility="collapsed", key="sd_from")
        st.session_state['fend'] = st.date_input("To", value=st.session_state['fend'],
            min_value=min_d, max_value=max_d, label_visibility="collapsed", key="sd_to")

    def pill_group(sk, items, label, ncols, ctx):
        with ctx:
            st.markdown(f'<div class="filter-label">{label}</div>', unsafe_allow_html=True)
            all_on = (st.session_state[sk] == set(items))
            if st.button("✓ All" if all_on else "Select All", key=f"{sk}_all_btn"):
                st.session_state[sk] = set(items) if not all_on else set()
                st.rerun()
            for row in [items[i:i+ncols] for i in range(0, len(items), ncols)]:
                cols = st.columns(len(row))
                for ci, item in enumerate(row):
                    active = item in st.session_state[sk]
                    lbl = f"✓ {item}" if active else item
                    if cols[ci].button(lbl, key=f"{sk}_{item.replace(' ','_')}"):
                        if active:
                            st.session_state[sk].discard(item)
                        else:
                            st.session_state[sk].add(item)
                        st.rerun()

    pill_group('su', master_users,  "👤 Master User",   3, fc1)
    pill_group('sl', master_leads,  "🏷️ Master Lead",   2, fc2)
    pill_group('ss', master_states, "📍 Master State",  3, fc3)

    with fc4:
        st.markdown('<div class="filter-label">&nbsp;</div>', unsafe_allow_html=True)
        if st.button("🔄 Reset Filters", key="reset_filters"):
            for k in ['su','sl','ss','fstart','fend']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── FIXED FILTER FUNCTION ─────────────────────────────────────────────────
    def filt(df):
        if df.empty:
            return df

        d = df.copy()

        # Date filter (only if column exists and has valid dates)
        if 'Date' in d.columns and d['Date'].notna().any():
            d = d[
                (d['Date'].dt.date >= st.session_state['fstart']) &
                (d['Date'].dt.date <= st.session_state['fend'])
            ]

        # Apply dimension filters ONLY if user actually selected something
        if 'User' in d.columns and st.session_state['su']:
            d = d[d['User'].isin(st.session_state['su'])]

        if 'Lead Type' in d.columns and st.session_state['sl']:
            d = d[d['Lead Type'].isin(st.session_state['sl'])]

        if 'State' in d.columns and st.session_state['ss']:
            d = d[d['State'].isin(st.session_state['ss'])]

        return d

    vF = filt(vdf)
    lF = filt(ldf)
    sF = filt(sdf)
    actF = filt(combined)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    tv = len(vF)
    tl = len(lF)
    ts = len(sF)
    tr = float(sF['Amount'].sum()) if 'Amount' in sF.columns and not sF.empty else 0.0
    tq = len(lF[lF['Stage'].str.contains('QUOTATION|HOT', case=False, na=False)]) if 'Stage' in lF.columns else 0

    def fmt_rev(v):
        if v == 0: return "—"
        if v >= 1e7: return f"₹{v/1e7:.2f} Cr"
        if v >= 1e5: return f"₹{v/1e5:.2f} L"
        return f"₹{v:,.0f}"

    def kpi(label, val):
        return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div></div>'

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(kpi("Total Visitors", f"{tv:,}" if tv else "—"), unsafe_allow_html=True)
    k2.markdown(kpi("Total Lead",     f"{tl:,}" if tl else "—"), unsafe_allow_html=True)
    k3.markdown(kpi("Total Sales",     f"{ts:,}" if ts else "—"), unsafe_allow_html=True)
    k4.markdown(kpi("Total Quotation", f"{tq:,}" if tq else "—"), unsafe_allow_html=True)
    k5.markdown(kpi("Total Revenue",   fmt_rev(tr)), unsafe_allow_html=True)

    st.markdown("---")

    # ── Rest of your charts and tables remain the same ───────────────────────
    # (I left them unchanged – just make sure the dataframes vF, lF, sF, actF are used)

    # ... your chart code here ...

    # Tables
    t1, t2 = st.columns([3, 2])
    with t1:
        st.markdown('<div class="sec-hdr">📋 Lead & Visitor Log</div>', unsafe_allow_html=True)
        lv = actF.copy()
        if 'Date' in lv.columns:
            lv = lv.sort_values('Date', ascending=False)
        st.dataframe(lv, use_container_width=True, height=360)

    with t2:
        st.markdown('<div class="sec-hdr">💰 Sales Records</div>', unsafe_allow_html=True)
        if not sF.empty:
            st.dataframe(sF.sort_values('Date', ascending=False) if 'Date' in sF else sF,
                        use_container_width=True, height=360)
        else:
            st.info("No sales data in selected filters")

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
