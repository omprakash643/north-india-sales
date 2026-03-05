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
.nic-header {
  background: linear-gradient(135deg, #c8a84b, #e8d080, #c8a84b);
  border-radius: 12px; padding: 16px 28px; margin-bottom: 14px;
  display: flex; align-items: center; gap: 18px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}
.nic-logo {
  background:#fff; border-radius:50%; width:54px; height:54px;
  display:flex; align-items:center; justify-content:center;
  font-weight:900; font-size:1.15rem; color:#c8a84b; flex-shrink:0;
}
.nic-title { font-family:'Barlow Condensed',sans-serif; font-size:1.9rem; font-weight:700; color:#1a1a1a; }
.nic-sub   { font-style:italic; font-size:0.82rem; color:#5a4a1a; }
.kpi-card {
  background: linear-gradient(135deg, #d4c070, #e8d890);
  border: 2px solid #b8a040; border-radius: 10px;
  padding: 14px 8px; text-align: center;
  box-shadow: 3px 3px 8px rgba(0,0,0,0.18); min-height: 100px;
}
.kpi-label {
  font-family:'Barlow Condensed',sans-serif; font-size:0.72rem; font-weight:700;
  color:#3a2a00; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:5px;
}
.kpi-value { font-family:'Barlow Condensed',sans-serif; font-size:2rem; font-weight:700; color:#1a1200; }
.filter-section {
  background: linear-gradient(135deg, #2a2a2a, #1a1a1a);
  border-radius: 12px; padding: 14px 18px; margin-bottom: 14px;
}
.filter-label {
  font-family:'Barlow Condensed',sans-serif; font-size:0.85rem; font-weight:700;
  color:#e8d080; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;
}
div[data-testid="stButton"] > button {
  border-radius:20px !important; padding:3px 12px !important;
  font-size:0.76rem !important; font-weight:600 !important;
  margin:2px 1px !important; border:1.5px solid #b8a040 !important;
  background:#e8d880 !important; color:#3a2800 !important;
  min-height:0 !important; height:auto !important; line-height:1.5 !important;
  white-space:nowrap !important;
}
div[data-testid="stButton"] > button:hover {
  background:#8B6914 !important; color:#fff !important; border-color:#5a3d10 !important;
}
.chart-box {
  background: linear-gradient(135deg, #ddd090, #ede8b0);
  border:1.5px solid #b8a040; border-radius:10px; padding:12px;
  margin-bottom:12px; box-shadow:2px 2px 6px rgba(0,0,0,0.12);
}
.chart-title {
  font-family:'Barlow Condensed',sans-serif; font-size:0.95rem;
  font-weight:700; color:#2a1a00; text-transform:uppercase; margin-bottom:2px;
}
.sec-hdr {
  background:linear-gradient(90deg,#7a6020,#c8a84b); color:#fff;
  font-family:'Barlow Condensed',sans-serif; font-weight:700; font-size:1rem;
  padding:8px 16px; border-radius:6px 6px 0 0; text-transform:uppercase;
}
</style>
""", unsafe_allow_html=True)

VISITOR_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=0&single=true&output=csv"
LEAD_URL    = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=2066525621&single=true&output=csv"
SALES_URL   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=23552387&single=true&output=csv"

# ══════════════════════════════════════════════════════════════════════════════
# MASTER TABLES — exact values from Power BI (case-insensitive match to data)
# These are the 21 users, leads, states shown in your Power BI slicers
# ══════════════════════════════════════════════════════════════════════════════
MASTER_USERS = [
    "GOVIND","SHIVGATULLA","SACHIN KUMAR 2","MURLI DAR SUKLA",
    "ASHWIN GARG","RAHUL MAHANT","UJJWAL UPADHYAY","HIMANSHU NAGAR",
    "MAHESH CHANDRA","DEEPESH","VINOD","ARVIND KUMAR","RAHUL",
    "JAIPAL","RAHUL VERMA","J PRASHANT","ROHIT KUMAR","ALOK",
    "GAJENDRA KUMAR JHA","PRADEEP","RAHUL SIR"
]

def clean_amount(val):
    try:
        if pd.isna(val): return 0.0
        return float(str(val).replace(',','').replace('₹','').replace(' ','').strip())
    except:
        return 0.0

@st.cache_data(ttl=60)
def load_all():
    vdf = pd.read_csv(VISITOR_URL)
    vdf.columns = vdf.columns.str.strip()
    for c in list(vdf.columns):
        if 'remark' in c.lower():
            vdf.rename(columns={c:'Remark'}, inplace=True); break
    for c in list(vdf.columns):
        if any(k in c.lower() for k in ['competitor','meyer','existing']):
            vdf.rename(columns={c:'Competitors'}, inplace=True); break
    vdf['_src'] = 'Visitor'

    ldf = pd.read_csv(LEAD_URL)
    ldf.columns = ldf.columns.str.strip()
    for c in list(ldf.columns):
        if 'remark' in c.lower():
            ldf.rename(columns={c:'Remark'}, inplace=True); break
    ldf['_src'] = 'Lead'

    sdf = pd.read_csv(SALES_URL)
    sdf.columns = sdf.columns.str.strip()
    sdf.rename(columns={'Customer':'Customer Name','PO Amount':'Amount'}, inplace=True)
    if 'Amount' in sdf.columns:
        sdf['Amount'] = sdf['Amount'].apply(clean_amount)
    sdf['_src'] = 'Sales'

    for df in [vdf, ldf, sdf]:
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # ⭐ KEY FIX: Normalise User to UPPERCASE stripped — matches Master User table
        if 'User' in df.columns:
            df['User'] = df['User'].astype(str).str.strip().str.upper()
        if 'Lead Type' in df.columns:
            df['Lead Type'] = df['Lead Type'].astype(str).str.strip().str.upper()
        if 'State' in df.columns:
            df['State'] = df['State'].astype(str).str.strip().str.upper()

    combined = pd.concat([vdf, ldf], ignore_index=True)

    # Build Master Lead + State from actual data (uppercase normalised)
    def master(col, *dfs):
        vals = set()
        for d in dfs:
            if col in d.columns:
                vals |= set(d[col].dropna().unique())
        return sorted(v for v in vals if v and v != 'NAN')

    master_leads  = master('Lead Type', vdf, ldf, sdf)
    master_states = master('State',     vdf, ldf, sdf)

    return vdf, ldf, sdf, combined, master_leads, master_states

try:
    vdf, ldf, sdf, combined, master_leads, master_states = load_all()

    # ── Session state ─────────────────────────────────────────────────────────
    if 'su' not in st.session_state: st.session_state['su'] = set(MASTER_USERS)
    if 'sl' not in st.session_state: st.session_state['sl'] = set(master_leads)
    if 'ss' not in st.session_state: st.session_state['ss'] = set(master_states)

    min_d = combined['Date'].dropna().min().date()
    max_d = combined['Date'].dropna().max().date()
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
            min_value=min_d, max_value=max_d, label_visibility="collapsed", key="sd")
        st.session_state['fend'] = st.date_input("To", value=st.session_state['fend'],
            min_value=min_d, max_value=max_d, label_visibility="collapsed", key="ed")

    def pill_group(sk, items, label, ncols, ctx):
        with ctx:
            st.markdown(f'<div class="filter-label">{label}</div>', unsafe_allow_html=True)
            all_on = (st.session_state[sk] == set(items))
            if st.button("✓ All" if all_on else "Select All", key=f"{sk}__all"):
                st.session_state[sk] = set(items) if not all_on else set()
                st.rerun()
            for row in [items[i:i+ncols] for i in range(0, len(items), ncols)]:
                cols = st.columns(len(row))
                for ci, item in enumerate(row):
                    active = item in st.session_state[sk]
                    if cols[ci].button(f"✓ {item}" if active else item, key=f"{sk}__{item}"):
                        if active: st.session_state[sk].discard(item)
                        else:      st.session_state[sk].add(item)
                        st.rerun()

    pill_group('su', MASTER_USERS,  "👤 Master User",  3, fc1)
    pill_group('sl', master_leads,  "🏷️ Master Lead",  2, fc2)
    pill_group('ss', master_states, "📍 Master State", 3, fc3)

    with fc4:
        st.markdown('<div class="filter-label">&nbsp;</div>', unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔄 Reset", key="reset__all"):
            for k in ['su','sl','ss','fstart','fend']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Filter function — all matching is UPPERCASE to match normalised data ──
    def filt(df):
        d = df.copy()
        if 'Date' in d.columns:
            d = d[(d['Date'].dt.date >= st.session_state['fstart']) &
                  (d['Date'].dt.date <= st.session_state['fend'])]
        if 'User' in d.columns:
            sel = st.session_state['su']
            if not sel: return d.iloc[0:0]
            d = d[d['User'].isin(sel)]
        if 'Lead Type' in d.columns:
            sel = st.session_state['sl']
            if not sel: return d.iloc[0:0]
            d = d[d['Lead Type'].isin(sel)]
        if 'State' in d.columns:
            sel = st.session_state['ss']
            if not sel: return d.iloc[0:0]
            d = d[d['State'].isin(sel)]
        return d

    vF   = filt(vdf)
    lF   = filt(ldf)
    sF   = filt(sdf)
    actF = filt(combined)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total_visitors = len(vF)
    total_leads    = len(lF)
    total_sales    = len(sF)
    total_rev      = float(sF['Amount'].sum()) if 'Amount' in sF.columns and len(sF) > 0 else 0.0
    if 'Stage' in lF.columns and len(lF) > 0:
        total_quot = len(lF[lF['Stage'].astype(str).str.strip().isin(['Quotation Send','Hot Lead'])])
    else:
        total_quot = 0

    def fmt_rev(v):
        try:
            v = float(v)
            if v == 0: return "—"
            if v >= 1_00_00_000: return f"₹{v/1_00_00_000:.2f} Cr"
            elif v >= 1_00_000:  return f"₹{v/1_00_000:.2f} L"
            else:                return f"₹{v:,.0f}"
        except: return "—"

    def kpi(label, val):
        return (f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{val}</div></div>')

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.markdown(kpi("Total Visitors",       f"{total_visitors:,}" if total_visitors else "—"), unsafe_allow_html=True)
    k2.markdown(kpi("Total Lead",           f"{total_leads:,}"    if total_leads    else "—"), unsafe_allow_html=True)
    k3.markdown(kpi("Total Sales",          f"{total_sales:,}"    if total_sales    else "—"), unsafe_allow_html=True)
    k4.markdown(kpi("Total Quotation Send", f"{total_quot:,}"     if total_quot     else "—"), unsafe_allow_html=True)
    k5.markdown(kpi("Total Revenue",        fmt_rev(total_rev)),                               unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
    GOLD = ["#8B6914","#c8a84b","#e8c870","#5a3d10","#f0d890",
            "#3a2800","#d4b060","#a07828","#604008","#e0b840"]

    def bl(fig, h=260):
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8,r=8,t=8,b=8), height=h,
            font=dict(family="Barlow", size=11, color="#2a1a00"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font_size=9),
        )
        return fig

    def hbar(df, col, color="#8B6914"):
        if df.empty or col not in df.columns: return None
        d = df[col].value_counts().reset_index(); d.columns=['x','y']
        fig = px.bar(d, x='y', y='x', orientation='h', color_discrete_sequence=[color])
        return bl(fig)

    def nd(): st.markdown('<p style="color:#8a7030;font-size:0.8rem;padding:12px 0">No data</p>', unsafe_allow_html=True)

    ch1,ch2,ch3,ch4,ch5 = st.columns(5)

    with ch1:
        st.markdown('<div class="chart-box"><div class="chart-title">Count of Source by Source</div>', unsafe_allow_html=True)
        if 'Source' in lF.columns and not lF.empty:
            d = lF['Source'].value_counts().reset_index(); d.columns=['Source','Count']
            fig = px.bar(d, x='Source', y='Count', color='Source', color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_layout(showlegend=False, xaxis_tickangle=-35, yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else: nd()
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div class="chart-box"><div class="chart-title">Competitors (Visit)</div>', unsafe_allow_html=True)
        if 'Competitors' in vF.columns and not vF.empty:
            d = vF['Competitors'].value_counts().reset_index(); d.columns=['x','y']
            fig = px.pie(d, names='x', values='y', hole=0.3, color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else: nd()
        st.markdown('</div>', unsafe_allow_html=True)

    with ch3:
        st.markdown('<div class="chart-box"><div class="chart-title">User Sales</div>', unsafe_allow_html=True)
        fig = hbar(sF, 'User', "#c8a84b")
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: nd()
        st.markdown('</div>', unsafe_allow_html=True)

    with ch4:
        st.markdown('<div class="chart-box"><div class="chart-title">Lead Type Sales</div>', unsafe_allow_html=True)
        fig = hbar(sF, 'Lead Type', "#e8c870")
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: nd()
        st.markdown('</div>', unsafe_allow_html=True)

    with ch5:
        st.markdown('<div class="chart-box"><div class="chart-title">State Sales</div>', unsafe_allow_html=True)
        fig = hbar(sF, 'State', "#f0d890")
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: nd()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Tables ────────────────────────────────────────────────────────────────
    def sc(df, cols): return [c for c in cols if c in df.columns]

    t1, t2 = st.columns([3, 2])
    with t1:
        st.markdown('<div class="sec-hdr">📋 Lead &amp; Visitor Log</div>', unsafe_allow_html=True)
        lv = actF[sc(actF,['Date','Customer Name','Contact Person','User',
                           'State','City','Lead Type','Source','Stage','Remark','Competitors','_src'])].reset_index(drop=True)
        if 'Date' in lv.columns: lv = lv.sort_values('Date', ascending=False).reset_index(drop=True)
        st.dataframe(lv, use_container_width=True, height=360)

    with t2:
        st.markdown('<div class="sec-hdr">💰 Sales Records</div>', unsafe_allow_html=True)
        s_cols = sc(sF,['Date','Customer Name','User','Lead Type','Products','Amount','GST','State'])
        if s_cols and not sF.empty:
            s_tbl = sF[s_cols].reset_index(drop=True)
            if 'Date' in s_tbl.columns: s_tbl = s_tbl.sort_values('Date', ascending=False).reset_index(drop=True)
            st.dataframe(s_tbl, use_container_width=True, height=360)
        else:
            st.info("No sales for selected filters")

    # ── Debug ─────────────────────────────────────────────────────────────────
    with st.expander("🔧 Debug"):
        st.write("**Users in Visitor sheet (after normalise):**",
                 sorted(vdf['User'].dropna().unique().tolist()) if 'User' in vdf.columns else [])
        st.write("**Users in Lead sheet (after normalise):**",
                 sorted(ldf['User'].dropna().unique().tolist()) if 'User' in ldf.columns else [])
        st.write("**Master Users (from Power BI):**", MASTER_USERS)
        st.write(f"Unfiltered → Visitors:{len(vdf)} Leads:{len(ldf)} Sales:{len(sdf)}")
        st.write(f"Filtered   → Visitors:{len(vF)} Leads:{len(lF)} Sales:{len(sF)}")
        if 'Stage' in ldf.columns:
            st.write("**Stage counts:**"); st.dataframe(ldf['Stage'].value_counts())

    st.markdown("""<div style="text-align:center;color:#8a7030;font-size:0.72rem;margin-top:16px;font-style:italic;">
      NICPL · Auto-refreshes every 60 s</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error: {e}")
    import traceback
    st.code(traceback.format_exc())
