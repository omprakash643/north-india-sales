import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# ─── 1. PAGE CONFIGURATION ──────────────────────────────────────────────────
st.set_page_config(page_title="NIC Sales Dashboard", layout="wide", initial_sidebar_state="collapsed")

# ─── 2. THEME / CUSTOM CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@700&display=swap');
* { font-family: 'Barlow', sans-serif; }
.stApp { background-color: #f0ead0; }
[data-testid="stSidebar"] { display: none; }

.nic-header {
  background: linear-gradient(135deg, #c8a84b, #e8d080, #c8a84b);
  border-radius: 12px; padding: 16px 28px; margin-bottom: 16px;
  display: flex; align-items: center; gap: 18px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}
.nic-logo {
  background: #fff; border-radius: 50%; width: 54px; height: 54px;
  display: flex; align-items: center; justify-content: center;
  font-weight: 900; font-size: 1.15rem; color: #c8a84b; flex-shrink: 0;
}
.nic-title { font-family: 'Barlow Condensed',sans-serif; font-size: 1.9rem; font-weight: 700; color: #1a1a1a; }
.nic-sub   { font-style: italic; font-size: 0.82rem; color: #5a4a1a; }

.kpi-card {
  background: linear-gradient(135deg, #d4c070, #e8d890);
  border: 2px solid #b8a040; border-radius: 10px;
  padding: 14px 8px; text-align: center;
  box-shadow: 3px 3px 8px rgba(0,0,0,0.18); min-height: 100px;
}
.kpi-label {
  font-family: 'Barlow Condensed',sans-serif; font-size: 0.72rem;
  font-weight: 700; color: #3a2a00; text-transform: uppercase;
  letter-spacing: 0.06em; margin-bottom: 5px;
}
.kpi-value { font-family: 'Barlow Condensed',sans-serif; font-size: 2rem; font-weight: 700; color: #1a1200; }

.filter-section {
  background: linear-gradient(135deg, #2a2a2a, #1a1a1a);
  border-radius: 12px; padding: 14px 18px; margin-bottom: 14px;
}
.filter-label {
  font-family: 'Barlow Condensed',sans-serif; font-size: 0.85rem;
  font-weight: 700; color: #e8d080; text-transform: uppercase;
  letter-spacing: 0.08em; margin-bottom: 8px;
}

div[data-testid="stButton"] > button {
  border-radius: 20px !important; padding: 3px 12px !important;
  font-size: 0.76rem !important; font-weight: 600 !important;
  margin: 2px 1px !important; border: 1.5px solid #b8a040 !important;
  background: #e8d880 !important; color: #3a2800 !important;
  min-height: 0 !important; height: auto !important; line-height: 1.5 !important;
  white-space: nowrap !important;
}
div[data-testid="stButton"] > button:hover,
div[data-testid="stButton"] > button[kind="primary"] {
  background: #8B6914 !important; color: #fff !important; border-color: #5a3d10 !important;
}

.chart-box {
  background: linear-gradient(135deg, #ddd090, #ede8b0);
  border: 1.5px solid #b8a040; border-radius: 10px;
  padding: 12px; margin-bottom: 12px;
  box-shadow: 2px 2px 6px rgba(0,0,0,0.12);
}
.chart-title {
  font-family: 'Barlow Condensed',sans-serif; font-size: 0.95rem;
  font-weight: 700; color: #2a1a00; text-transform: uppercase; margin-bottom: 2px;
}
.sec-hdr {
  background: linear-gradient(90deg, #7a6020, #c8a84b); color: #fff;
  font-family: 'Barlow Condensed',sans-serif; font-weight: 700; font-size: 1rem;
  padding: 8px 16px; border-radius: 6px 6px 0 0; text-transform: uppercase;
}
hr { border-color: #b8a040; opacity: 0.35; }
</style>
""", unsafe_allow_html=True)

# ─── 3. DATA LOADING AND CLEANING ────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip() # Remove hidden spaces from headers

    # Smart Renaming Logic
    col_map = {}
    for col in df.columns:
        lc = col.lower()
        if 'date' in lc: col_map[col] = 'Date'
        elif any(k in lc for k in ['user', 'executive', 'person']): col_map[col] = 'User'
        elif any(k in lc for k in ['lead type', 'product', 'machine']): col_map[col] = 'Lead Type'
        elif 'customer' in lc: col_map[col] = 'Customer Name'
        elif 'state' in lc: col_map[col] = 'State'
        elif 'remark' in lc: col_map[col] = 'Remarks'
        elif 'status' in lc: col_map[col] = 'Status'
        elif 'source' in lc: col_map[col] = 'Source'
        elif any(k in lc for k in ['amount', 'po', 'revenue', 'value']): col_map[col] = 'Amount'
    
    df.rename(columns=col_map, inplace=True)

    # Clean numeric data (Removes ₹ and commas so math works)
    if 'Amount' in df.columns:
        df['Amount'] = pd.to_numeric(df['Amount'].astype(str).replace(r'[\₹,]', '', regex=True), errors='coerce').fillna(0)
    
    # Clean dates
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    return df

try:
    df = load_data()

    # ─── 4. KPI KEYWORDS (From Remarks) ───────────────────────────────────────
    SALE_KW = r'finali|po received|advance|payment|order confirm|install|sale confirm|purchased'
    QUOT_KW = r'quotation|quote|quot send|want quotation|want quatation'
    LEAD_KW = r'enquir|interest|need|require|discussion|plan|want|looking|meeting|visit'

    # ─── 5. DYNAMIC FILTERS ───────────────────────────────────────────────────
    def uniq(col):
        return sorted(df[col].dropna().astype(str).unique().tolist()) if col in df.columns else []

    all_users = uniq('User')
    all_leads = uniq('Lead Type')
    all_states = uniq('State')

    if 'sel_users' not in st.session_state: st.session_state['sel_users'] = set(all_users)
    if 'sel_leads' not in st.session_state: st.session_state['sel_leads'] = set(all_leads)
    if 'sel_states' not in st.session_state: st.session_state['sel_states'] = set(all_states)

    # ─── 6. HEADER ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="nic-header">
      <div class="nic-logo">NIC</div>
      <div>
        <div class="nic-title">North India Compressors <span style="font-size:1.1rem;color:#5a4000;">(Jan &amp; Feb)</span></div>
        <div class="nic-sub">a multi product company</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ─── 7. FILTER PANEL ──────────────────────────────────────────────────────
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    fcol1, fcol2, fcol3 = st.columns([3, 3, 3])

    with fcol1:
        st.markdown('<div class="filter-label">👤 Master User</div>', unsafe_allow_html=True)
        u_cols = st.columns(3)
        for i, u in enumerate(all_users):
            active = u in st.session_state['sel_users']
            if u_cols[i % 3].button(f"✓ {u}" if active else u, key=f"u_{u}"):
                if active: st.session_state['sel_users'].discard(u)
                else: st.session_state['sel_users'].add(u)
                st.rerun()

    with fcol2:
        st.markdown('<div class="filter-label">🏷️ Master Lead</div>', unsafe_allow_html=True)
        l_cols = st.columns(2)
        for i, l in enumerate(all_leads):
            active = l in st.session_state['sel_leads']
            if l_cols[i % 2].button(f"✓ {l}" if active else l, key=f"l_{l}"):
                if active: st.session_state['sel_leads'].discard(l)
                else: st.session_state['sel_leads'].add(l)
                st.rerun()

    with fcol3:
        st.markdown('<div class="filter-label">📍 Master State</div>', unsafe_allow_html=True)
        s_cols = st.columns(3)
        for i, s in enumerate(all_states):
            active = s in st.session_state['sel_states']
            if s_cols[i % 3].button(f"✓ {s}" if active else s, key=f"s_{s}"):
                if active: st.session_state['sel_states'].discard(s)
                else: st.session_state['sel_states'].add(s)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ─── 8. APPLY FILTERS ─────────────────────────────────────────────────────
    dff = df.copy()
    if st.session_state['sel_users'] and 'User' in dff.columns:
        dff = dff[dff['User'].astype(str).isin(st.session_state['sel_users'])]
    if st.session_state['sel_leads'] and 'Lead Type' in dff.columns:
        dff = dff[dff['Lead Type'].astype(str).isin(st.session_state['sel_leads'])]
    if st.session_state['sel_states'] and 'State' in dff.columns:
        dff = dff[dff['State'].astype(str).isin(st.session_state['sel_states'])]

    # ─── 9. KPI BOXES ─────────────────────────────────────────────────────────
    total_visitors = len(dff)
    
    # Priority: Check 'Status' col first, then 'Remarks'
    status_col = 'Status' if 'Status' in dff.columns else ('Remarks' if 'Remarks' in dff.columns else None)
    
    if status_col:
        total_leads = len(dff[dff[status_col].str.contains(LEAD_KW, na=False, case=False)])
        total_sales = len(dff[dff[status_col].str.contains(SALE_KW, na=False, case=False)])
        total_quot  = len(dff[dff[status_col].str.contains(QUOT_KW, na=False, case=False)])
    else:
        total_leads = total_sales = total_quot = 0

    total_revenue = dff['Amount'].sum() if 'Amount' in dff.columns else 0

    def kpi_card(label, val):
        return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div></div>'

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(kpi_card("Total Visitors", f"{total_visitors:,}"), unsafe_allow_html=True)
    k2.markdown(kpi_card("Total Lead", f"{total_leads:,}"), unsafe_allow_html=True)
    k3.markdown(kpi_card("Total Sales", f"{total_sales:,}"), unsafe_allow_html=True)
    k4.markdown(kpi_card("Total Quotation", f"{total_quot:,}"), unsafe_allow_html=True)
    k5.markdown(kpi_card("Total Revenue", f"₹{total_revenue:,.0f}" if total_revenue else "—"), unsafe_allow_html=True)

    st.markdown("---")

    # ─── 10. VISUAL ANALYTICS ──────────────────────────────────────────────────
    GOLD = ["#8B6914","#c8a84b","#e8c870","#5a3d10","#f0d890"]
    
    ch1, ch2, ch3 = st.columns(3)

    with ch1:
        st.markdown('<div class="chart-box"><div class="chart-title">User Activity</div>', unsafe_allow_html=True)
        if 'User' in dff.columns:
            u_data = dff['User'].value_counts().reset_index()
            fig = px.bar(u_data, x='count', y='User', orientation='h', color_discrete_sequence=["#8B6914"])
            fig.update_layout(height=250, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div class="chart-box"><div class="chart-title">State Mix</div>', unsafe_allow_html=True)
        if 'State' in dff.columns:
            fig = px.pie(dff, names='State', hole=0.35, color_discrete_sequence=GOLD)
            fig.update_layout(height=250, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch3:
        st.markdown('<div class="chart-box"><div class="chart-title">Product Breakdown</div>', unsafe_allow_html=True)
        if 'Lead Type' in dff.columns:
            l_data = dff['Lead Type'].value_counts().reset_index()
            fig = px.bar(l_data, x='count', y='Lead Type', orientation='h', color_discrete_sequence=["#c8a84b"])
            fig.update_layout(height=250, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ─── 11. DATA TABLE ───────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">📋 Live Data Feed</div>', unsafe_allow_html=True)
    st.dataframe(dff, use_container_width=True, height=400)

except Exception as e:
    st.error(f"❌ Connection Error: {e}")
    st.info("Check if your Google Sheet is 'Published to Web' as a CSV.")
