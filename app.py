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
hr { border-color:#b8a040; opacity:0.35; }
</style>
""", unsafe_allow_html=True)

# ── Sheet URLs (all 3 tabs published) ────────────────────────────────────────
VISITOR_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=0&single=true&output=csv"
LEAD_URL    = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=2066525621&single=true&output=csv"
SALES_URL   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=23552387&single=true&output=csv"

@st.cache_data(ttl=60)
def load_all():
    # ── Visitor sheet ─────────────────────────────────────────────────────────
    # Cols: Date, Lead Type, User, Customer Name, Contact Person,
    #       State, City, Meyer Existing Customer, Remarks
    vdf = pd.read_csv(VISITOR_URL)
    vdf.columns = vdf.columns.str.strip()
    vdf['_sheet'] = 'Visitor'

    # ── Lead sheet ────────────────────────────────────────────────────────────
    # Cols: Date, UQN No., Source, User, Customer Name, Contact Person,
    #       Mobile, Remarks, Address Detail, State, Lead Type,
    #       Stage, Last Follow Date, G S T No
    ldf = pd.read_csv(LEAD_URL)
    ldf.columns = ldf.columns.str.strip()
    ldf['_sheet'] = 'Lead'

    # ── Sales sheet ───────────────────────────────────────────────────────────
    # Cols: Date, Customer, User, Lead Type, Products, PO Amount, GST, State
    sdf = pd.read_csv(SALES_URL)
    sdf.columns = sdf.columns.str.strip()
    sdf.rename(columns={
        'Customer':  'Customer Name',
        'PO Amount': 'Amount',
    }, inplace=True)
    sdf['_sheet'] = 'Sales'

    # ── Parse dates ───────────────────────────────────────────────────────────
    for df in [vdf, ldf, sdf]:
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # ── Combine Visitor + Lead into activity log ──────────────────────────────
    activity = pd.concat([vdf, ldf], ignore_index=True)

    return activity, sdf

try:
    activity_df, sales_df = load_all()

    # ── Build filter options from ALL data (unfiltered) ───────────────────────
    def uniq(col):
        if col not in activity_df.columns: return []
        return sorted(activity_df[col].dropna().astype(str).unique().tolist())

    all_users  = uniq('User')
    all_leads  = uniq('Lead Type')
    all_states = uniq('State')

    # Add states from sales too
    if 'State' in sales_df.columns:
        extra = sales_df['State'].dropna().astype(str).unique().tolist()
        all_states = sorted(set(all_states) | set(extra))

    for k, v in [('su', set(all_users)), ('sl', set(all_leads)), ('ss', set(all_states))]:
        if k not in st.session_state: st.session_state[k] = v

    min_d = activity_df['Date'].dropna().min().date()
    max_d = activity_df['Date'].dropna().max().date()
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
    fc0, fc1, fc2, fc3, fc4 = st.columns([1.4, 2.5, 2.8, 3.2, 0.7])

    with fc0:
        st.markdown('<div class="filter-label">📅 Date Range</div>', unsafe_allow_html=True)
        st.session_state['fstart'] = st.date_input("From", value=st.session_state['fstart'],
            min_value=min_d, max_value=max_d, label_visibility="collapsed", key="sd")
        st.session_state['fend']   = st.date_input("To",   value=st.session_state['fend'],
            min_value=min_d, max_value=max_d, label_visibility="collapsed", key="ed")

    def pill_group(sk, all_items, label, ncols, col_ctx):
        with col_ctx:
            st.markdown(f'<div class="filter-label">{label}</div>', unsafe_allow_html=True)
            all_sel = st.session_state[sk] == set(all_items)
            if st.button("✓ Select All" if all_sel else "Select All", key=f"{sk}_all"):
                st.session_state[sk] = set(all_items) if not all_sel else set()
                st.rerun()
            for row in [all_items[i:i+ncols] for i in range(0, len(all_items), ncols)]:
                cs = st.columns(len(row))
                for ci, item in enumerate(row):
                    active = item in st.session_state[sk]
                    if cs[ci].button(f"✓ {item}" if active else item, key=f"{sk}_{item}"):
                        if active: st.session_state[sk].discard(item)
                        else:      st.session_state[sk].add(item)
                        st.rerun()

    pill_group('su', all_users,  "👤 Master User",  3, fc1)
    pill_group('sl', all_leads,  "🏷️ Master Lead",  2, fc2)
    pill_group('ss', all_states, "📍 Master State", 3, fc3)

    with fc4:
        st.markdown('<div class="filter-label">&nbsp;</div>', unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔄\nReset", key="reset"):
            for k in ['su','sl','ss','fstart','fend']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Apply Filters ─────────────────────────────────────────────────────────
    def filt(df):
        d = df.copy()
        if 'Date' in d.columns:
            d = d[(d['Date'].dt.date >= st.session_state['fstart']) &
                  (d['Date'].dt.date <= st.session_state['fend'])]
        if 'User'      in d.columns and st.session_state['su']:
            d = d[d['User'].astype(str).isin(st.session_state['su'])]
        if 'Lead Type' in d.columns and st.session_state['sl']:
            d = d[d['Lead Type'].astype(str).isin(st.session_state['sl'])]
        if 'State'     in d.columns and st.session_state['ss']:
            d = d[d['State'].astype(str).isin(st.session_state['ss'])]
        return d

    act  = filt(activity_df)
    salF = filt(sales_df)

    # ── KPIs — exact counts from each sheet ───────────────────────────────────
    visitors  = len(act[act['_sheet'] == 'Visitor'])
    leads     = len(act[act['_sheet'] == 'Lead'])
    sales_cnt = len(salF)
    revenue   = salF['Amount'].sum() if 'Amount' in salF.columns else 0

    # Quotations = Lead rows where Stage contains "Quotation"
    lead_rows = act[act['_sheet'] == 'Lead']
    if 'Stage' in lead_rows.columns:
        quot = len(lead_rows[lead_rows['Stage'].astype(str).str.contains('quot', na=False, case=False)])
    else:
        quot = 0

    def kpi(label, val):
        return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div></div>'

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.markdown(kpi("Total Visitors",       f"{visitors:,}"),  unsafe_allow_html=True)
    k2.markdown(kpi("Total Lead",           f"{leads:,}"),     unsafe_allow_html=True)
    k3.markdown(kpi("Total Sales",          f"{sales_cnt:,}"), unsafe_allow_html=True)
    k4.markdown(kpi("Total Quotation Send", f"{quot:,}"),      unsafe_allow_html=True)
    k5.markdown(kpi("Total Revenue",        f"₹{revenue:,.0f}" if revenue else "—"), unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
    GOLD = ["#8B6914","#c8a84b","#e8c870","#5a3d10","#f0d890","#3a2800","#d4b060","#a07828","#604008","#e0b840"]

    def bl(fig, h=260):
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8,r=8,t=8,b=8), height=h,
            font=dict(family="Barlow", size=11, color="#2a1a00"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font_size=9),
        )
        return fig

    def hbar(df, col, color):
        d = df[col].value_counts().reset_index(); d.columns=['x','y']
        fig = px.bar(d, x='y', y='x', orientation='h', color_discrete_sequence=[color])
        return bl(fig)

    ch1,ch2,ch3,ch4,ch5 = st.columns(5)

    # 1. Source (from Lead sheet)
    with ch1:
        st.markdown('<div class="chart-box"><div class="chart-title">Count by Source</div>', unsafe_allow_html=True)
        src = act[act['_sheet']=='Lead']
        if 'Source' in src.columns and not src.empty:
            fig = hbar(src.dropna(subset=['Source']), 'Source', "#8B6914")
            fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="",
                              yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. State pie (all activity)
    with ch2:
        st.markdown('<div class="chart-box"><div class="chart-title">State Distribution</div>', unsafe_allow_html=True)
        if 'State' in act.columns:
            d = act['State'].value_counts().reset_index(); d.columns=['x','y']
            fig = px.pie(d, names='x', values='y', hole=0.35, color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. User activity
    with ch3:
        st.markdown('<div class="chart-box"><div class="chart-title">User Activity</div>', unsafe_allow_html=True)
        if 'User' in act.columns:
            fig = hbar(act.dropna(subset=['User']), 'User', "#c8a84b")
            fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="",
                              yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. Lead Type (sales)
    with ch4:
        st.markdown('<div class="chart-box"><div class="chart-title">Lead Type (Sales)</div>', unsafe_allow_html=True)
        if not salF.empty and 'Lead Type' in salF.columns:
            fig = hbar(salF.dropna(subset=['Lead Type']), 'Lead Type', "#e8c870")
            fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="",
                              yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 5. State (sales)
    with ch5:
        st.markdown('<div class="chart-box"><div class="chart-title">State (Sales)</div>', unsafe_allow_html=True)
        if not salF.empty and 'State' in salF.columns:
            fig = hbar(salF.dropna(subset=['State']), 'State', "#f0d890")
            fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="",
                              yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Tables ────────────────────────────────────────────────────────────────
    def sc(df, cols): return [c for c in cols if c in df.columns]

    t1, t2 = st.columns([3, 2])

    with t1:
        st.markdown('<div class="sec-hdr">📋 Lead &amp; Visitor Log</div>', unsafe_allow_html=True)
        lv_cols = sc(act, ['Date','Customer Name','Contact Person','User','State',
                           'City','Lead Type','Source','Stage','Remarks','_sheet'])
        lv = act[lv_cols].reset_index(drop=True)
        if 'Date' in lv.columns: lv = lv.sort_values('Date', ascending=False).reset_index(drop=True)
        st.dataframe(lv, use_container_width=True, height=360)

    with t2:
        st.markdown('<div class="sec-hdr">💰 Sales Records</div>', unsafe_allow_html=True)
        s_cols = sc(salF, ['Date','Customer Name','User','Lead Type','Products','Amount','GST','State'])
        s_tbl = salF[s_cols].reset_index(drop=True)
        if 'Date' in s_tbl.columns: s_tbl = s_tbl.sort_values('Date', ascending=False).reset_index(drop=True)
        st.dataframe(s_tbl, use_container_width=True, height=360)

    with st.expander("🔧 Debug"):
        st.write(f"Visitors: {len(activity_df[activity_df['_sheet']=='Visitor'])} | Leads: {len(activity_df[activity_df['_sheet']=='Lead'])} | Sales: {len(sales_df)}")
        st.write("Visitor cols:", [c for c in activity_df.columns if c != '_sheet'][:12])
        st.write("Lead cols:",    list(activity_df[activity_df['_sheet']=='Lead'].columns)[:14])
        st.write("Sales cols:",   sales_df.columns.tolist())

    st.markdown("""<div style="text-align:center;color:#8a7030;font-size:0.72rem;margin-top:16px;font-style:italic;">
      NICPL · Auto-refreshes every 60 s</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error: {e}")
    import traceback
    st.code(traceback.format_exc())
