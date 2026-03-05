import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

st.set_page_config(
    page_title="NIC Sales Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── THEME / CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@700&display=swap');

  html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }

  /* Gold/beige background matching Power BI theme */
  .stApp { background-color: #f5f0dc; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2c2c2c 0%, #1a1a1a 100%);
    color: #f0e6c8;
  }
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stMarkdown { color: #f0e6c8 !important; }

  /* Header */
  .nic-header {
    background: linear-gradient(135deg, #c8a84b 0%, #e8d080 50%, #c8a84b 100%);
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
  }
  .nic-header h1 {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #1a1a1a;
    margin: 0;
  }
  .nic-header p { color: #5a4a1a; margin: 0; font-size: 0.85rem; font-style: italic; }

  /* KPI Cards */
  .kpi-card {
    background: linear-gradient(135deg, #d4c070 0%, #e8d890 100%);
    border: 2px solid #b8a040;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: 3px 3px 8px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.3);
    min-height: 110px;
  }
  .kpi-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #3a2a00;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
  }
  .kpi-value {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #1a1200;
  }

  /* Chart containers */
  .chart-box {
    background: linear-gradient(135deg, #ddd090 0%, #ede8b0 100%);
    border: 1.5px solid #b8a040;
    border-radius: 10px;
    padding: 12px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.15);
    margin-bottom: 12px;
  }
  .chart-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #2a1a00;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  /* Tables */
  .section-header {
    background: linear-gradient(90deg, #8a7030, #c8a84b);
    color: white;
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
    padding: 8px 16px;
    border-radius: 6px 6px 0 0;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  /* Streamlit dataframe */
  [data-testid="stDataFrame"] { border-radius: 0 0 8px 8px; overflow: hidden; }

  /* Divider */
  hr { border-color: #b8a040; opacity: 0.4; }

  /* Multiselect tags */
  .stMultiSelect span[data-baseweb="tag"] {
    background-color: #c8a84b !important;
    color: #1a1200 !important;
  }
</style>
""", unsafe_allow_html=True)

# ─── DATA LOADING ────────────────────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()
    # Parse date column
    for col in ['Date', 'date', 'DATE']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df.rename(columns={col: 'Date'}, inplace=True)
            break
    return df

try:
    df = load_data()

    # ─── HEADER ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="nic-header">
      <div style="background:#fff; border-radius:50%; width:56px; height:56px;
                  display:flex; align-items:center; justify-content:center;
                  font-weight:900; font-size:1.3rem; color:#c8a84b; flex-shrink:0;">NIC</div>
      <div>
        <h1>North India Compressors &nbsp;<span style="font-size:1.2rem;color:#5a4000;">(Jan &amp; Feb)</span></h1>
        <p>a multi product company</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── SIDEBAR FILTERS ─────────────────────────────────────────────────────
    st.sidebar.markdown("## 🔍 Filter Options")

    # Date range
    if 'Date' in df.columns:
        min_date = df['Date'].min().date() if pd.notna(df['Date'].min()) else date(2026, 1, 1)
        max_date = df['Date'].max().date() if pd.notna(df['Date'].max()) else date(2026, 2, 28)
    else:
        min_date, max_date = date(2026, 1, 1), date(2026, 2, 28)

    start_date = st.sidebar.date_input("From Date", value=min_date)
    end_date   = st.sidebar.date_input("To Date",   value=max_date)

    st.sidebar.markdown("---")

    # Master User
    user_col = next((c for c in df.columns if 'user' in c.lower()), None)
    if user_col:
        all_users = sorted(df[user_col].dropna().unique().tolist())
        selected_users = st.sidebar.multiselect("Master User", options=all_users, default=all_users)
    else:
        selected_users = []

    # Master Lead (product type)
    lead_type_col = next((c for c in df.columns if 'lead type' in c.lower() or 'product' in c.lower() or 'machine' in c.lower()), None)
    if lead_type_col:
        all_leads = sorted(df[lead_type_col].dropna().unique().tolist())
        selected_leads = st.sidebar.multiselect("Master Lead", options=all_leads, default=all_leads)
    else:
        selected_leads = []

    # Master State
    state_col = next((c for c in df.columns if 'state' in c.lower()), None)
    if state_col:
        all_states = sorted(df[state_col].dropna().unique().tolist())
        selected_states = st.sidebar.multiselect("Master State", options=all_states, default=all_states)
    else:
        selected_states = []

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Reset All Filters"):
        st.rerun()

    # ─── APPLY FILTERS ───────────────────────────────────────────────────────
    dff = df.copy()
    if 'Date' in dff.columns:
        dff = dff[(dff['Date'].dt.date >= start_date) & (dff['Date'].dt.date <= end_date)]
    if user_col and selected_users:
        dff = dff[dff[user_col].isin(selected_users)]
    if lead_type_col and selected_leads:
        dff = dff[dff[lead_type_col].isin(selected_leads)]
    if state_col and selected_states:
        dff = dff[dff[state_col].isin(selected_states)]

    # ─── KPI CALCULATIONS ────────────────────────────────────────────────────
    status_col = next((c for c in dff.columns if c.lower() == 'status'), None)

    total_visitors = len(dff)
    total_leads    = len(dff[dff[status_col].str.contains('lead', na=False, case=False)]) if status_col else "N/A"
    total_sales    = len(dff[dff[status_col].str.contains('sale', na=False, case=False)]) if status_col else "N/A"

    quot_col = next((c for c in dff.columns if 'quot' in c.lower()), None)
    total_quot = len(dff[dff[status_col].str.contains('quot', na=False, case=False)]) if status_col else (dff[quot_col].sum() if quot_col else "N/A")

    rev_col = next((c for c in dff.columns if 'amount' in c.lower() or 'revenue' in c.lower() or 'po' in c.lower()), None)
    total_rev = dff[rev_col].sum() if rev_col else 0

    # ─── KPI ROW ─────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)

    def kpi_html(label, value):
        return f"""<div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
        </div>"""

    k1.markdown(kpi_html("Total Visitors",        f"{total_visitors:,}"), unsafe_allow_html=True)
    k2.markdown(kpi_html("Total Lead",            f"{total_leads:,}" if isinstance(total_leads, int) else total_leads), unsafe_allow_html=True)
    k3.markdown(kpi_html("Total Sales",           f"{total_sales:,}" if isinstance(total_sales, int) else total_sales), unsafe_allow_html=True)
    k4.markdown(kpi_html("Total Quotation Send",  f"{total_quot:,}"  if isinstance(total_quot, int)  else total_quot),  unsafe_allow_html=True)
    k5.markdown(kpi_html("Total Revenue",         f"₹{total_rev:,.0f}" if rev_col else "N/A"), unsafe_allow_html=True)

    st.markdown("---")

    # ─── CHART COLOURS ───────────────────────────────────────────────────────
    GOLD_PALETTE = ["#c8a84b","#8B6914","#e8c870","#5a3d10","#f0d890","#3a2800","#d4b060","#a07828"]
    CHART_BG     = "rgba(0,0,0,0)"
    PAPER_BG     = "rgba(0,0,0,0)"

    def chart_layout(fig, title=""):
        fig.update_layout(
            title=None,
            plot_bgcolor=CHART_BG, paper_bgcolor=PAPER_BG,
            margin=dict(l=8, r=8, t=8, b=8),
            font=dict(family="Barlow", color="#2a1a00"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font_size=10),
            height=220,
        )
        return fig

    # ─── CHARTS ROW ──────────────────────────────────────────────────────────
    ch1, ch2, ch3, ch4, ch5 = st.columns(5)

    # 1. Count of Source
    source_col = next((c for c in dff.columns if 'source' in c.lower()), None)
    with ch1:
        st.markdown('<div class="chart-box"><div class="chart-title">Count of Source by Source</div>', unsafe_allow_html=True)
        if source_col:
            src_data = dff[source_col].value_counts().reset_index()
            src_data.columns = ['Source', 'Count']
            fig = px.bar(src_data, x='Source', y='Count', color='Source',
                         color_discrete_sequence=GOLD_PALETTE)
            fig = chart_layout(fig)
            fig.update_layout(showlegend=False, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No 'Source' column found")
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. Competitors
    comp_col = next((c for c in dff.columns if 'compet' in c.lower()), None)
    with ch2:
        st.markdown('<div class="chart-box"><div class="chart-title">Competitors (Visit)</div>', unsafe_allow_html=True)
        if comp_col:
            comp_data = dff[comp_col].value_counts().reset_index()
            comp_data.columns = ['Competitor', 'Count']
            fig = px.pie(comp_data, names='Competitor', values='Count', hole=0.3,
                         color_discrete_sequence=GOLD_PALETTE)
            fig = chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No 'Competitor' column found")
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. User Sales
    with ch3:
        st.markdown('<div class="chart-box"><div class="chart-title">User Sales</div>', unsafe_allow_html=True)
        if user_col and status_col:
            sales_df = dff[dff[status_col].str.contains('sale', na=False, case=False)]
            user_sales = sales_df[user_col].value_counts().reset_index()
            user_sales.columns = ['User', 'Count']
            fig = px.bar(user_sales, x='Count', y='User', orientation='h',
                         color_discrete_sequence=["#8B6914"])
            fig = chart_layout(fig)
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need 'User' + 'Status' columns")
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. Lead Type Sales
    with ch4:
        st.markdown('<div class="chart-box"><div class="chart-title">Lead Type Sales</div>', unsafe_allow_html=True)
        if lead_type_col and status_col:
            lt_sales = dff[dff[status_col].str.contains('sale', na=False, case=False)]
            lt_data = lt_sales[lead_type_col].value_counts().reset_index()
            lt_data.columns = ['LeadType', 'Count']
            fig = px.bar(lt_data, x='Count', y='LeadType', orientation='h',
                         color_discrete_sequence=["#c8a84b"])
            fig = chart_layout(fig)
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No lead type / status columns")
        st.markdown('</div>', unsafe_allow_html=True)

    # 5. State Sales
    with ch5:
        st.markdown('<div class="chart-box"><div class="chart-title">State Sales</div>', unsafe_allow_html=True)
        if state_col and status_col:
            st_sales = dff[dff[status_col].str.contains('sale', na=False, case=False)]
            st_data = st_sales[state_col].value_counts().reset_index()
            st_data.columns = ['State', 'Count']
            fig = px.bar(st_data, x='Count', y='State', orientation='h',
                         color_discrete_sequence=["#e8c870"])
            fig = chart_layout(fig)
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No state / status columns")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ─── BOTTOM TABLES ───────────────────────────────────────────────────────
    tbl1, tbl2 = st.columns([3, 2])

    with tbl1:
        st.markdown('<div class="section-header">📋 Lead &amp; Visitor</div>', unsafe_allow_html=True)
        lead_visitor_cols = [c for c in ['Date', 'Customer Name', 'Contact Person', 'User', 'Remark', 'Source', 'Status']
                             if c in dff.columns]
        if not lead_visitor_cols:
            lead_visitor_cols = dff.columns.tolist()
        lv_df = dff[lead_visitor_cols] if lead_visitor_cols else dff
        st.dataframe(
            lv_df.sort_values('Date', ascending=False) if 'Date' in lv_df.columns else lv_df,
            use_container_width=True, height=320
        )

    with tbl2:
        st.markdown('<div class="section-header">💰 Sales</div>', unsafe_allow_html=True)
        if status_col:
            sales_only = dff[dff[status_col].str.contains('sale', na=False, case=False)]
        else:
            sales_only = dff
        sales_cols = [c for c in ['Date', 'Customer Name', 'User', rev_col, 'State'] if c and c in sales_only.columns]
        if not sales_cols:
            sales_cols = sales_only.columns.tolist()
        st.dataframe(
            sales_only[sales_cols].sort_values('Date', ascending=False) if 'Date' in sales_only.columns else sales_only[sales_cols],
            use_container_width=True, height=320
        )

    # ─── FOOTER ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; color:#8a7030; font-size:0.75rem; margin-top:24px; font-style:italic;">
      North India Compressors Pvt Ltd (NICPL) · Dashboard auto-refreshes every 60 seconds
    </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
    try:
        st.write("Columns found:", df.columns.tolist())
    except:
        st.write("Could not load data from Google Sheet.")
