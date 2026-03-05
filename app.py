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
.nic-sub   { font-style:italic; font-size:0.82rem; color:#5a4a1a; }
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

# ── Sheet URLs ────────────────────────────────────────────────────────────────
VISITOR_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=0&single=true&output=csv"
LEAD_URL    = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=2066525621&single=true&output=csv"
SALES_URL   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=23552387&single=true&output=csv"

def clean_amount(val):
    try:
        if pd.isna(val): return 0.0
        return float(str(val).replace(',','').replace('₹','').replace(' ','').strip())
    except: return 0.0

# ══════════════════════════════════════════════════════════════════════════════
# POWER QUERY EQUIVALENT — same steps Power BI does on each table
# ══════════════════════════════════════════════════════════════════════════════
def transform_table(df, key_cols):
    """Equivalent to Power Query: Trim, Clean, UPPER on key columns."""
    df = df.copy()
    df.columns = df.columns.str.strip()
    for col in key_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace('NAN', pd.NA)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    # Drop completely empty rows
    df.dropna(how='all', inplace=True)
    return df

@st.cache_data(ttl=60)
def load_and_build_model():
    """
    Replicates the Power BI data model:
    ┌──────────────────┐    ┌─────────────────────┐    ┌──────────────────────┐
    │ Visitor_Related  │    │ Lead_Realated_Data   │    │ Sales_Related_Data   │
    │  - User          │    │  - User              │    │  - User              │
    │  - Lead Type     │◄───│  - Lead Type         │◄───│  - Lead Type         │
    │  - State         │    │  - State             │    │  - State             │
    └────────┬─────────┘    └──────────┬──────────┘    └──────────┬───────────┘
             │                         │                            │
             ▼                         ▼                            ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │               Master User / Master Lead / Master State                  │
    │         (1-to-many: Master → each fact table)                           │
    └─────────────────────────────────────────────────────────────────────────┘
    """

    # ── Load raw sheets ───────────────────────────────────────────────────────
    raw_v = pd.read_csv(VISITOR_URL)
    raw_l = pd.read_csv(LEAD_URL)
    raw_s = pd.read_csv(SALES_URL)

    # ── Transform: Visitor_Related_data ──────────────────────────────────────
    # Cols: Date, Lead Type, User, Customer Name, Contact Person,
    #       State, City, Competitors (was Meyer Existing Customer), Remark
    vdf = transform_table(raw_v, ['User','Lead Type','State'])
    # Rename ambiguous columns
    for c in list(vdf.columns):
        lc = c.lower()
        if 'remark' in lc and c != 'Remark':
            vdf.rename(columns={c:'Remark'}, inplace=True); break
    for c in list(vdf.columns):
        if any(k in c.lower() for k in ['competitor','meyer','existing']):
            vdf.rename(columns={c:'Competitors'}, inplace=True); break
    vdf['_src'] = 'Visitor'

    # ── Transform: Lead_Realated_Data ─────────────────────────────────────────
    # Cols: Date, UQN No., Source, User, Customer Name, Contact Person,
    #       Mobile, Remark, Address Detail, State, Lead Type, Stage,
    #       Last Follow Date, G S T No
    ldf = transform_table(raw_l, ['User','Lead Type','State','Stage','Source'])
    for c in list(ldf.columns):
        if 'remark' in c.lower() and c != 'Remark':
            ldf.rename(columns={c:'Remark'}, inplace=True); break
    ldf['_src'] = 'Lead'

    # ── Transform: Sales_Related_Data ────────────────────────────────────────
    # Cols: Date, Customer, User, Lead Type, Products, PO Amount, GST, State
    sdf = transform_table(raw_s, ['User','Lead Type','State'])
    sdf.rename(columns={'Customer':'Customer Name', 'PO Amount':'Amount'}, inplace=True)
    if 'Amount' in sdf.columns:
        sdf['Amount'] = sdf['Amount'].apply(clean_amount)
    sdf['_src'] = 'Sales'

    # ── Build Master Tables (1-side of 1:many relationships) ─────────────────
    # Master User = DISTINCT(User) across ALL 3 fact tables — sorted
    master_user = sorted(set(
        list(vdf['User'].dropna().unique()) +
        list(ldf['User'].dropna().unique()) +
        list(sdf['User'].dropna().unique())
    ))

    # Master Lead = DISTINCT(Lead Type) across ALL 3 fact tables
    master_lead = sorted(set(
        (list(vdf['Lead Type'].dropna().unique()) if 'Lead Type' in vdf.columns else []) +
        (list(ldf['Lead Type'].dropna().unique()) if 'Lead Type' in ldf.columns else []) +
        (list(sdf['Lead Type'].dropna().unique()) if 'Lead Type' in sdf.columns else [])
    ))

    # Master State = DISTINCT(State) across ALL 3 fact tables
    master_state = sorted(set(
        (list(vdf['State'].dropna().unique()) if 'State' in vdf.columns else []) +
        (list(ldf['State'].dropna().unique()) if 'State' in ldf.columns else []) +
        (list(sdf['State'].dropna().unique()) if 'State' in sdf.columns else [])
    ))

    # ── Combined_Activity_Log = UNION(Visitor, Lead) ─────────────────────────
    combined = pd.concat([vdf, ldf], ignore_index=True)

    return vdf, ldf, sdf, combined, master_user, master_lead, master_state

try:
    vdf, ldf, sdf, combined, MASTER_USER, MASTER_LEAD, MASTER_STATE = load_and_build_model()

    # ── Session state — slicers default to ALL selected ───────────────────────
    if 'su' not in st.session_state: st.session_state['su'] = set(MASTER_USER)
    if 'sl' not in st.session_state: st.session_state['sl'] = set(MASTER_LEAD)
    if 'ss' not in st.session_state: st.session_state['ss'] = set(MASTER_STATE)

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

    # ── FILTER PANEL — Master tables as slicers ───────────────────────────────
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
            if st.button("✓ All" if all_on else "Select All", key=f"{sk}_all"):
                st.session_state[sk] = set(items) if not all_on else set()
                st.rerun()
            for row in [items[i:i+ncols] for i in range(0, len(items), ncols)]:
                cols = st.columns(len(row))
                for ci, item in enumerate(row):
                    active = item in st.session_state[sk]
                    if cols[ci].button(f"✓ {item}" if active else item, key=f"{sk}_{item}"):
                        if active: st.session_state[sk].discard(item)
                        else:      st.session_state[sk].add(item)
                        st.rerun()

    pill_group('su', MASTER_USER,  "👤 Master User",  3, fc1)
    pill_group('sl', MASTER_LEAD,  "🏷️ Master Lead",  2, fc2)
    pill_group('ss', MASTER_STATE, "📍 Master State", 3, fc3)

    with fc4:
        st.markdown('<div class="filter-label">&nbsp;</div>', unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔄 Reset", key="reset_all"):
            for k in ['su','sl','ss','fstart','fend']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # RELATIONSHIP ENGINE
    # Replicates Power BI's 1:many filter propagation:
    #   Master User[Master User] → Visitor[User]
    #   Master User[Master User] → Lead[User]
    #   Master User[Master User] → Sales[User]
    #   (same for Lead Type and State)
    # ══════════════════════════════════════════════════════════════════════════
    def apply_relationships(df):
        """Filter a fact table using the active slicer selections."""
        d = df.copy()

        # Date relationship (Master Date → all tables)
        if 'Date' in d.columns:
            d = d[(d['Date'].dt.date >= st.session_state['fstart']) &
                  (d['Date'].dt.date <= st.session_state['fend'])]

        # Master User → User column
        if 'User' in d.columns:
            sel = st.session_state['su']
            if not sel: return d.iloc[0:0]  # nothing selected = no rows
            d = d[d['User'].isin(sel)]

        # Master Lead → Lead Type column
        if 'Lead Type' in d.columns:
            sel = st.session_state['sl']
            if not sel: return d.iloc[0:0]
            d = d[d['Lead Type'].isin(sel)]

        # Master State → State column
        if 'State' in d.columns:
            sel = st.session_state['ss']
            if not sel: return d.iloc[0:0]
            d = d[d['State'].isin(sel)]

        return d

    # Apply to each fact table independently (like Power BI does)
    vF   = apply_relationships(vdf)      # Visitor filtered
    lF   = apply_relationships(ldf)      # Lead filtered
    sF   = apply_relationships(sdf)      # Sales filtered
    actF = apply_relationships(combined) # Combined filtered

    # ══════════════════════════════════════════════════════════════════════════
    # MEASURES — equivalent to Power BI DAX measures
    # ══════════════════════════════════════════════════════════════════════════
    # Total Visitors  = COUNTROWS(Visitor_Related_data)
    total_visitors = len(vF)

    # Total Lead = COUNTROWS(Lead_Realated_Data)
    total_leads = len(lF)

    # Total Sales = COUNTROWS(Sales_Related_Data)
    total_sales = len(sF)

    # Total Revenue = SUM(Sales_Related_Data[PO Amount])
    total_rev = float(sF['Amount'].sum()) if 'Amount' in sF.columns and len(sF) > 0 else 0.0

    # Total Quotation Send = COUNTROWS filtered Stage IN ("QUOTATION SEND","HOT LEAD")
    total_quot = 0
    if 'Stage' in lF.columns and len(lF) > 0:
        total_quot = len(lF[lF['Stage'].isin(['QUOTATION SEND', 'HOT LEAD'])])

    def fmt_rev(v):
        try:
            v = float(v)
            if v == 0: return "—"
            if v >= 1e7: return f"₹{v/1e7:.2f} Cr"
            if v >= 1e5: return f"₹{v/1e5:.2f} L"
            return f"₹{v:,.0f}"
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

    # ══════════════════════════════════════════════════════════════════════════
    # VISUALS — each uses its own filtered fact table
    # ══════════════════════════════════════════════════════════════════════════
    GOLD = ["#8B6914","#c8a84b","#e8c870","#5a3d10","#f0d890",
            "#3a2800","#d4b060","#a07828","#604008","#e0b840"]

    def bl(fig, h=260):
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8,r=8,t=8,b=8), height=h,
            font=dict(family="Barlow", size=11, color="#2a1a00"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font_size=9))
        return fig

    def hbar(df, col, color):
        if df.empty or col not in df.columns: return None
        d = df[col].value_counts().reset_index(); d.columns = ['x','y']
        fig = px.bar(d, x='y', y='x', orientation='h', color_discrete_sequence=[color])
        fig = bl(fig)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="",
                          yaxis={'categoryorder':'total ascending'})
        return fig

    def nd(): st.markdown('<p style="color:#8a7030;font-size:0.8rem;padding:12px 0">No data</p>', unsafe_allow_html=True)

    ch1,ch2,ch3,ch4,ch5 = st.columns(5)

    with ch1:  # Count of Source — from Lead table (Source col)
        st.markdown('<div class="chart-box"><div class="chart-title">Count of Source by Source</div>', unsafe_allow_html=True)
        if 'Source' in lF.columns and not lF.empty:
            d = lF['Source'].value_counts().reset_index(); d.columns = ['Source','Count']
            fig = px.bar(d, x='Source', y='Count', color='Source', color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_layout(showlegend=False, xaxis_tickangle=-35, yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else: nd()
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:  # Competitors — from Visitor table
        st.markdown('<div class="chart-box"><div class="chart-title">Competitors (Visit)</div>', unsafe_allow_html=True)
        if 'Competitors' in vF.columns and not vF.empty:
            d = vF['Competitors'].value_counts().reset_index(); d.columns = ['x','y']
            fig = px.pie(d, names='x', values='y', hole=0.3, color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else: nd()
        st.markdown('</div>', unsafe_allow_html=True)

    with ch3:  # User Sales — from Sales table
        st.markdown('<div class="chart-box"><div class="chart-title">User Sales</div>', unsafe_allow_html=True)
        fig = hbar(sF, 'User', "#c8a84b")
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: nd()
        st.markdown('</div>', unsafe_allow_html=True)

    with ch4:  # Lead Type Sales — from Sales table
        st.markdown('<div class="chart-box"><div class="chart-title">Lead Type Sales</div>', unsafe_allow_html=True)
        fig = hbar(sF, 'Lead Type', "#e8c870")
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: nd()
        st.markdown('</div>', unsafe_allow_html=True)

    with ch5:  # State Sales — from Sales table
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
        lv = actF[sc(actF, ['Date','Customer Name','Contact Person','User',
                            'State','City','Lead Type','Source','Stage',
                            'Remark','Competitors','_src'])].reset_index(drop=True)
        if 'Date' in lv.columns:
            lv = lv.sort_values('Date', ascending=False).reset_index(drop=True)
        st.dataframe(lv, use_container_width=True, height=360)

    with t2:
        st.markdown('<div class="sec-hdr">💰 Sales Records</div>', unsafe_allow_html=True)
        s_cols = sc(sF, ['Date','Customer Name','User','Lead Type','Products','Amount','GST','State'])
        if s_cols and not sF.empty:
            s_tbl = sF[s_cols].reset_index(drop=True)
            if 'Date' in s_tbl.columns:
                s_tbl = s_tbl.sort_values('Date', ascending=False).reset_index(drop=True)
            st.dataframe(s_tbl, use_container_width=True, height=360)
        else:
            st.info("No sales for selected filters")

    # ── Data Model Inspector (replaces Debug) ─────────────────────────────────
    with st.expander("📊 Data Model Inspector — verify all tables & relationships"):
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Master User","Master Lead","Master State","Stage Values","Row Counts"])

        with tab1:
            st.write("**Master User table** (used as slicer source):")
            st.dataframe(pd.DataFrame({'Master User': MASTER_USER}))

        with tab2:
            st.write("**Master Lead table:**")
            st.dataframe(pd.DataFrame({'Master Lead': MASTER_LEAD}))

        with tab3:
            st.write("**Master State table:**")
            st.dataframe(pd.DataFrame({'Master State': MASTER_STATE}))

        with tab4:
            if 'Stage' in ldf.columns:
                st.write("**Stage values in Lead table** (for Quotation KPI):")
                st.dataframe(ldf['Stage'].value_counts().reset_index().rename(
                    columns={'Stage':'Count','index':'Stage'}))
                st.write("ℹ️ Quotation KPI counts: **QUOTATION SEND** + **HOT LEAD**")

        with tab5:
            cols = st.columns(3)
            cols[0].metric("Visitor rows", len(vdf), f"filtered: {len(vF)}")
            cols[1].metric("Lead rows",    len(ldf), f"filtered: {len(lF)}")
            cols[2].metric("Sales rows",   len(sdf), f"filtered: {len(sF)}")
            st.write(f"Revenue: ₹{sdf['Amount'].sum():,.0f}" if 'Amount' in sdf.columns else "")

    st.markdown("""<div style="text-align:center;color:#8a7030;font-size:0.72rem;margin-top:16px;font-style:italic;">
      NICPL · Auto-refreshes every 60 s</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error: {e}")
    import traceback; st.code(traceback.format_exc())
