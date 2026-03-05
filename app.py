import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# ─── 1. PAGE SETUP & THEME ──────────────────────────────────────────────────
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
.kpi-card { background: linear-gradient(135deg, #d4c070, #e8d890); border: 2px solid #b8a040; border-radius: 10px; padding: 14px 8px; text-align: center; box-shadow: 3px 3px 8px rgba(0,0,0,0.18); min-height: 100px; }
.kpi-label { font-family:'Barlow Condensed',sans-serif; font-size:0.72rem; font-weight:700; color:#3a2a00; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:5px; }
.kpi-value { font-family:'Barlow Condensed',sans-serif; font-size:2rem; font-weight:700; color:#1a1200; }
.filter-section { background: linear-gradient(135deg, #2a2a2a, #1a1a1a); border-radius: 12px; padding: 14px 18px; margin-bottom: 14px; }
.filter-label { font-family:'Barlow Condensed',sans-serif; font-size:0.85rem; font-weight:700; color:#e8d080; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px; }
div[data-testid="stButton"] > button { border-radius:20px !important; padding:3px 12px !important; font-size:0.76rem !important; font-weight:600 !important; margin:2px 1px !important; border:1.5px solid #b8a040 !important; background:#e8d880 !important; color:#3a2800 !important; min-height:0 !important; height:auto !important; line-height:1.5 !important; white-space:nowrap !important; }
div[data-testid="stButton"] > button:hover { background:#8B6914 !important; color:#fff !important; }
.sec-hdr { background:linear-gradient(90deg,#7a6020,#c8a84b); color:#fff; font-family:'Barlow Condensed',sans-serif; font-weight:700; font-size:1rem; padding:8px 16px; border-radius:6px 6px 0 0; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)

# ─── 2. DATA LOADING & NORMALIZATION ───────────────────────────────────────
VISITOR_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=0&single=true&output=csv"
LEAD_URL    = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=2066525621&single=true&output=csv"
SALES_URL   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=23552387&single=true&output=csv"

def clean_amt(v):
    try: return float(str(v).replace(',','').replace('₹','').replace(' ','').strip())
    except: return 0.0

@st.cache_data(ttl=60)
def load_all():
    vdf, ldf, sdf = pd.read_csv(VISITOR_URL), pd.read_csv(LEAD_URL), pd.read_csv(SALES_URL)
    for df in [vdf, ldf, sdf]:
        df.columns = df.columns.str.strip()
        # Normalise strings to UPPERCASE so buttons match data exactly
        for col in ['User', 'Lead Type', 'State', 'Source', 'Stage']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
    
    sdf.rename(columns={'Customer':'Customer Name','PO Amount':'Amount'}, inplace=True)
    if 'Amount' in sdf.columns: sdf['Amount'] = sdf['Amount'].apply(clean_amt)
    for df in [vdf, ldf, sdf]:
        if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    combined = pd.concat([vdf, ldf], ignore_index=True)

    def master(col, *dfs):
        vals = set()
        for d in dfs:
            if col in d.columns: vals |= set(d[col].dropna().unique())
        return sorted([v for v in vals if v and v != 'NAN'])

    return vdf, ldf, sdf, combined, master('User',vdf,ldf,sdf), master('Lead Type',vdf,ldf,sdf), master('State',vdf,ldf,sdf)

try:
    vdf, ldf, sdf, combined, m_users, m_leads, m_states = load_all()

    # ─── 3. SHARED SESSION STATE ──────────────────────────────────────────────
    if 'su' not in st.session_state: st.session_state['su'] = set(m_users)
    if 'sl' not in st.session_state: st.session_state['sl'] = set(m_leads)
    if 'ss' not in st.session_state: st.session_state['ss'] = set(m_states)

    # ─── 4. FILTER PANEL ──────────────────────────────────────────────────────
    st.markdown('<div class="nic-header"><div class="nic-logo">NIC</div><div class="nic-title">North India Compressors Dashboard</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    f_user, f_lead, f_state, f_reset = st.columns([3, 3, 3, 1])

    def pill_group(sk, items, label, ncols, ctx):
        with ctx:
            st.markdown(f'<div class="filter-label">{label}</div>', unsafe_allow_html=True)
            all_on = (st.session_state[sk] == set(items))
            if st.button("✓ All" if all_on else "Select All", key=f"{sk}_all"):
                st.session_state[sk] = set(items) if not all_on else set()
                st.rerun()
            for row in [items[i:i+ncols] for i in range(0, len(items), ncols)]:
                cs = st.columns(len(row))
                for ci, item in enumerate(row):
                    active = item in st.session_state[sk]
                    if cs[ci].button(f"✓ {item}" if active else item, key=f"{sk}_{item}"):
                        if active: st.session_state[sk].discard(item)
                        else: st.session_state[sk].add(item)
                        st.rerun()

    pill_group('su', m_users, "👤 Master User", 3, f_user)
    pill_group('sl', m_leads, "🏷️ Master Lead", 2, f_lead)
    pill_group('ss', m_states, "📍 Master State", 3, f_state)
    
    with f_reset:
        if st.button("🔄 Reset"):
            for k,v in [('su',set(m_users)),('sl',set(m_leads)),('ss',set(m_states))]: st.session_state[k] = v
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ─── 5. APPLY FILTERS ENGINE (The Connection Fix) ──────────────────────────
    def apply_filt(df_to_filter):
        d = df_to_filter.copy()
        if 'User' in d.columns:
            if not st.session_state['su']: return d.iloc[0:0]
            d = d[d['User'].isin(st.session_state['su'])]
        if 'Lead Type' in d.columns:
            if not st.session_state['sl']: return d.iloc[0:0]
            d = d[d['Lead Type'].isin(st.session_state['sl'])]
        if 'State' in d.columns:
            if not st.session_state['ss']: return d.iloc[0:0]
            d = d[d['State'].isin(st.session_state['ss'])]
        return d

    vF, lF, sF, actF = apply_filt(vdf), apply_filt(ldf), apply_filt(sdf), apply_filt(combined)

    # ─── 6. KPIs ────────────────────────────────────────────────────────────────
    t_quot = len(lF[lF['Stage'].isin(['QUOTATION SEND','HOT LEAD'])]) if 'Stage' in lF.columns else 0
    k1,k2,k3,k4,k5 = st.columns(5)
    def k_box(l, v): return f'<div class="kpi-card"><div class="kpi-label">{l}</div><div class="kpi-value">{v}</div></div>'
    k1.markdown(k_box("Total Visitors", len(vF)), unsafe_allow_html=True)
    k2.markdown(k_box("Total Lead", len(lF)), unsafe_allow_html=True)
    k3.markdown(k_box("Total Sales", len(sF)), unsafe_allow_html=True)
    k4.markdown(k_box("Total Quotations", t_quot), unsafe_allow_html=True)
    k5.markdown(k_box("Total Revenue", f"₹{sF['Amount'].sum():,.0f}"), unsafe_allow_html=True)

    st.markdown("---")
    st.dataframe(actF, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
