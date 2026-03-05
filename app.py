import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="NIC Sales Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@700&display=swap');
  html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
  .stApp { background-color: #f5f0dc; }
  [data-testid="stSidebar"] { background: linear-gradient(180deg, #2c2c2c, #1a1a1a); }
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stMarkdown,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span { color: #f0e6c8 !important; }
  .kpi-card {
    background: linear-gradient(135deg, #d4c070, #e8d890);
    border: 2px solid #b8a040; border-radius: 10px;
    padding: 14px 10px; text-align: center;
    box-shadow: 3px 3px 8px rgba(0,0,0,0.2); min-height: 105px;
  }
  .kpi-label {
    font-family: 'Barlow Condensed', sans-serif; font-size: 0.78rem;
    font-weight: 700; color: #3a2a00; text-transform: uppercase;
    letter-spacing: 0.05em; margin-bottom: 6px;
  }
  .kpi-value { font-family: 'Barlow Condensed', sans-serif; font-size: 2.2rem; font-weight: 700; color: #1a1200; }
  .chart-box {
    background: linear-gradient(135deg, #ddd090, #ede8b0);
    border: 1.5px solid #b8a040; border-radius: 10px;
    padding: 10px; box-shadow: 2px 2px 6px rgba(0,0,0,0.15); margin-bottom: 12px;
  }
  .chart-title { font-family: 'Barlow Condensed', sans-serif; font-size: 0.95rem; font-weight: 700; color: #2a1a00; margin-bottom: 4px; text-transform: uppercase; }
  .section-header {
    background: linear-gradient(90deg, #8a7030, #c8a84b); color: white;
    font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 1.1rem;
    padding: 8px 16px; border-radius: 6px 6px 0 0; text-transform: uppercase;
  }
  hr { border-color: #b8a040; opacity: 0.4; }
  .stMultiSelect span[data-baseweb="tag"] { background-color: #c8a84b !important; color: #1a1200 !important; }
</style>
""", unsafe_allow_html=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()
    # Normalise date
    for col in df.columns:
        if col.strip().lower() == 'date':
            df.rename(columns={col: 'Date'}, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            break
    rename_map = {}
    for col in df.columns:
        lc = col.strip().lower()
        if lc == 'user':                           rename_map[col] = 'User'
        elif 'customer' in lc:                     rename_map[col] = 'Customer Name'
        elif 'contact' in lc:                      rename_map[col] = 'Contact Person'
        elif lc == 'remark':                       rename_map[col] = 'Remark'
        elif lc == 'state':                        rename_map[col] = 'State'
        elif 'lead type' in lc or lc=='leadtype':  rename_map[col] = 'Lead Type'
        elif lc == 'status':                       rename_map[col] = 'Status'
        elif lc == 'source':                       rename_map[col] = 'Source'
        elif 'compet' in lc:                       rename_map[col] = 'Competitor'
        elif 'amount' in lc or lc.startswith('po'): rename_map[col] = 'Amount'
    df.rename(columns=rename_map, inplace=True)
    return df

try:
    df = load_data()

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#c8a84b,#e8d080,#c8a84b);border-radius:12px;
                padding:14px 24px;margin-bottom:14px;display:flex;align-items:center;gap:16px;
                box-shadow:0 4px 16px rgba(0,0,0,0.25);">
      <div style="background:#fff;border-radius:50%;width:52px;height:52px;display:flex;
                  align-items:center;justify-content:center;font-weight:900;font-size:1.2rem;
                  color:#c8a84b;flex-shrink:0;">NIC</div>
      <div>
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.9rem;font-weight:700;color:#1a1a1a;">
          North India Compressors
          <span style="font-size:1.1rem;color:#5a4000;">(Jan &amp; Feb)</span>
        </div>
        <div style="color:#5a4a1a;font-size:0.82rem;font-style:italic;">a multi product company</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Sidebar filters ───────────────────────────────────────────────────────
    st.sidebar.markdown("## 🔍 Filters")

    if 'Date' in df.columns:
        min_d = df['Date'].dropna().min().date()
        max_d = df['Date'].dropna().max().date()
    else:
        min_d, max_d = date(2026,1,1), date(2026,2,28)

    start_date = st.sidebar.date_input("📅 From Date", value=min_d, min_value=min_d, max_value=max_d)
    end_date   = st.sidebar.date_input("📅 To Date",   value=max_d, min_value=min_d, max_value=max_d)
    st.sidebar.markdown("---")

    def chip_filter(label, colname):
        if colname not in df.columns:
            return []
        opts = sorted(df[colname].dropna().unique().tolist())
        return st.sidebar.multiselect(label, options=opts, default=opts, key=f"f_{colname}")

    sel_users  = chip_filter("👤 Master User",  "User")
    sel_leads  = chip_filter("🏷️ Master Lead",  "Lead Type")
    sel_states = chip_filter("📍 Master State", "State")

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Reset All Filters"):
        st.cache_data.clear()
        st.rerun()

    # ── Apply filters ─────────────────────────────────────────────────────────
    dff = df.copy()
    if 'Date' in dff.columns:
        dff = dff[(dff['Date'].dt.date >= start_date) & (dff['Date'].dt.date <= end_date)]
    if sel_users  and 'User'      in dff.columns: dff = dff[dff['User'].isin(sel_users)]
    if sel_leads  and 'Lead Type' in dff.columns: dff = dff[dff['Lead Type'].isin(sel_leads)]
    if sel_states and 'State'     in dff.columns: dff = dff[dff['State'].isin(sel_states)]

    # ── KPIs ─────────────────────────────────────────────────────────────────
    SALE_KW  = r'po received|advance|payment|sale|order confirm|finali|install'
    QUOT_KW  = r'quotation|quote sent|quot'
    LEAD_KW  = r'enquir|lead|interest|need|require|looking|want|discuss'

    135: SALE_KW  = r'po received|advance|payment|sale|order confirm|finali|install'
    136: QUOT_KW  = r'quotation|quote sent|quot'
    137: LEAD_KW  = r'enquir|lead|interest|need|require|looking|want|discuss'

    if has_status:
        total_leads = len(dff[dff['Status'].str.contains('lead|visitor', na=False, case=False)])
        total_sales = len(dff[dff['Status'].str.contains('sale',         na=False, case=False)])
        total_quot  = len(dff[dff['Status'].str.contains('quot',         na=False, case=False)])
    elif has_remark:
        total_leads = len(dff[dff['Remark'].str.contains(LEAD_KW, na=False, case=False)])
        total_sales = len(dff[dff['Remark'].str.contains(SALE_KW, na=False, case=False)])
        total_quot  = len(dff[dff['Remark'].str.contains(QUOT_KW, na=False, case=False)])
    else:
        total_leads = total_sales = total_quot = "N/A"

    total_rev = dff['Amount'].sum() if 'Amount' in dff.columns else 0

    def kpi(label, val):
        return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div></div>'

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.markdown(kpi("Total Visitors",       f"{total_visitors:,}"), unsafe_allow_html=True)
    k2.markdown(kpi("Total Lead",           f"{total_leads:,}" if isinstance(total_leads,int) else total_leads), unsafe_allow_html=True)
    k3.markdown(kpi("Total Sales",          f"{total_sales:,}" if isinstance(total_sales,int) else total_sales), unsafe_allow_html=True)
    k4.markdown(kpi("Total Quotation Send", f"{total_quot:,}"  if isinstance(total_quot,int)  else total_quot),  unsafe_allow_html=True)
    k5.markdown(kpi("Total Revenue",        f"₹{total_rev:,.0f}" if total_rev else "N/A"), unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
    GOLD = ["#c8a84b","#8B6914","#e8c870","#5a3d10","#f0d890","#3a2800","#d4b060","#a07828","#704010"]

    def bl(fig, h=220):
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=6,r=6,t=6,b=6), height=h,
            font=dict(family="Barlow", color="#2a1a00"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font_size=9),
        )
        return fig

    ch1,ch2,ch3,ch4,ch5 = st.columns(5)

    with ch1:
        st.markdown('<div class="chart-box"><div class="chart-title">Count by Source</div>', unsafe_allow_html=True)
        src_col = 'Source' if 'Source' in dff.columns else ('Lead Type' if 'Lead Type' in dff.columns else None)
        if src_col:
            d = dff[src_col].value_counts().reset_index()
            d.columns = [src_col,'Count']
            fig = px.bar(d, x=src_col, y='Count', color=src_col, color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_layout(showlegend=False, xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No Source column")
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div class="chart-box"><div class="chart-title">Competitors / State Mix</div>', unsafe_allow_html=True)
        pie_col = 'Competitor' if 'Competitor' in dff.columns else ('State' if 'State' in dff.columns else None)
        if pie_col:
            d = dff[pie_col].value_counts().reset_index()
            d.columns = [pie_col,'Count']
            fig = px.pie(d, names=pie_col, values='Count', hole=0.3, color_discrete_sequence=GOLD)
            fig = bl(fig)
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No Competitor/State column")
        st.markdown('</div>', unsafe_allow_html=True)

    with ch3:
        st.markdown('<div class="chart-box"><div class="chart-title">User Activity</div>', unsafe_allow_html=True)
        if 'User' in dff.columns:
            d = dff['User'].value_counts().reset_index(); d.columns=['User','Count']
            fig = px.bar(d, x='Count', y='User', orientation='h', color_discrete_sequence=["#8B6914"])
            fig = bl(fig); fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No User column")
        st.markdown('</div>', unsafe_allow_html=True)

    with ch4:
        st.markdown('<div class="chart-box"><div class="chart-title">Lead Type Breakdown</div>', unsafe_allow_html=True)
        if 'Lead Type' in dff.columns:
            d = dff['Lead Type'].value_counts().reset_index(); d.columns=['Lead Type','Count']
            fig = px.bar(d, x='Count', y='Lead Type', orientation='h', color_discrete_sequence=["#c8a84b"])
            fig = bl(fig); fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No Lead Type column")
        st.markdown('</div>', unsafe_allow_html=True)

    with ch5:
        st.markdown('<div class="chart-box"><div class="chart-title">State Distribution</div>', unsafe_allow_html=True)
        if 'State' in dff.columns:
            d = dff['State'].value_counts().reset_index(); d.columns=['State','Count']
            fig = px.bar(d, x='Count', y='State', orientation='h', color_discrete_sequence=["#e8c870"])
            fig = bl(fig); fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No State column")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Tables ────────────────────────────────────────────────────────────────
    tbl1, tbl2 = st.columns([3, 2])

    lv_cols = [c for c in ['Date','Customer Name','Contact Person','User','State','Lead Type','Remark'] if c in dff.columns]
    with tbl1:
        st.markdown('<div class="section-header">📋 Lead &amp; Visitor Log</div>', unsafe_allow_html=True)
        lv = dff[lv_cols] if lv_cols else dff
        if 'Date' in lv.columns: lv = lv.sort_values('Date', ascending=False)
        st.dataframe(lv, use_container_width=True, height=340)

    with tbl2:
        st.markdown('<div class="section-header">💰 Sales / PO Records</div>', unsafe_allow_html=True)
        if has_status:
            sdf = dff[dff['Status'].str.contains('sale', na=False, case=False)]
        elif has_remark:
            sdf = dff[dff['Remark'].str.contains(SALE_KW, na=False, case=False)]
        else:
            sdf = dff.head(30)
        sc = [c for c in ['Date','Customer Name','User','State','Lead Type','Amount','Remark'] if c in sdf.columns]
        s_tbl = sdf[sc] if sc else sdf
        if 'Date' in s_tbl.columns: s_tbl = s_tbl.sort_values('Date', ascending=False)
        st.dataframe(s_tbl, use_container_width=True, height=340)

    # ── Debug ─────────────────────────────────────────────────────────────────
    with st.expander("🔧 Debug: Columns & Sample Data"):
        st.write("**Detected columns:**", df.columns.tolist())
        st.write(f"**Total rows:** {len(df)}")
        st.dataframe(df.head(5))

    st.markdown("""<div style="text-align:center;color:#8a7030;font-size:0.73rem;margin-top:20px;font-style:italic;">
      North India Compressors Pvt Ltd (NICPL) · Auto-refreshes every 60 seconds</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Dashboard Error: {e}")
    import traceback
    st.code(traceback.format_exc())
    try:
        st.write("Columns found:", df.columns.tolist())
    except:
        st.write("Could not load data.")
