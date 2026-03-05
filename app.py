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

# ═══════════════════════════════════════════════════════════════════════════════
# ⚠️  REPLACE THESE 3 URLs with published CSV links from your Google Sheet
#
#  How to get each URL:
#  1. Open the sheet → File → Share → Publish to web
#  2. In dropdown 1 choose the TAB name (e.g. "Visitor_Related_data")
#  3. In dropdown 2 choose "Comma-separated values (.csv)"
#  4. Click Publish → Copy the link → paste below
# ═══════════════════════════════════════════════════════════════════════════════
VISITOR_URL = "PASTE_VISITOR_SHEET_CSV_URL_HERE"
LEAD_URL    = "PASTE_LEAD_SHEET_CSV_URL_HERE"
SALES_URL   = "PASTE_SALES_SHEET_CSV_URL_HERE"

# Fallback: old combined sheet (used if individual tabs not yet published)
FALLBACK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?output=csv"

def try_load(url):
    try:
        if "PASTE_" in url: return None
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df if len(df) > 0 else None
    except:
        return None

@st.cache_data(ttl=60)
def load_all():
    visitor_df = try_load(VISITOR_URL)
    lead_df    = try_load(LEAD_URL)
    sales_df   = try_load(SALES_URL)

    # ── Visitor sheet ─────────────────────────────────────────────────────────
    # Columns: Date, Lead Type, User, Customer Name, Contact Person, State, City, Meyer Existing Customer, Remarks
    if visitor_df is not None:
        visitor_df = visitor_df.rename(columns=lambda c: c.strip())
        visitor_df['_sheet'] = 'Visitor'
    else:
        visitor_df = pd.DataFrame()

    # ── Lead sheet ────────────────────────────────────────────────────────────
    # Columns: Date, UQN No., Source, User, Customer Name, Contact Person, Mobile,
    #          Remarks, Address Detail, State, Lead Type, Stage, Last Follow Date, G S T No
    if lead_df is not None:
        lead_df = lead_df.rename(columns=lambda c: c.strip())
        lead_df['_sheet'] = 'Lead'
    else:
        lead_df = pd.DataFrame()

    # ── Sales sheet ───────────────────────────────────────────────────────────
    # Columns: Date, Customer, User, Lead Type, Products, PO Amount, GST, State
    if sales_df is not None:
        sales_df = sales_df.rename(columns=lambda c: c.strip())
        # Rename 'Customer' → 'Customer Name' to unify
        if 'Customer' in sales_df.columns and 'Customer Name' not in sales_df.columns:
            sales_df.rename(columns={'Customer': 'Customer Name'}, inplace=True)
        if 'PO Amount' in sales_df.columns and 'Amount' not in sales_df.columns:
            sales_df.rename(columns={'PO Amount': 'Amount'}, inplace=True)
        sales_df['_sheet'] = 'Sales'
    else:
        sales_df = pd.DataFrame()

    # ── If no individual tabs loaded, use old fallback combined sheet ─────────
    if visitor_df.empty and lead_df.empty and sales_df.empty:
        fb = try_load(FALLBACK_URL)
        if fb is not None:
            fb['_sheet'] = 'Combined'
            visitor_df = fb  # treat as visitor for now

    # ── Combine visitor + lead for the main activity view ────────────────────
    common_cols = ['Date','User','Customer Name','State','Lead Type','_sheet']
    frames = []
    for df in [visitor_df, lead_df]:
        if not df.empty:
            # Normalise: ensure common cols exist
            for col in common_cols:
                if col not in df.columns: df[col] = None
            frames.append(df)

    if frames:
        activity_df = pd.concat(frames, ignore_index=True)
    elif not sales_df.empty:
        activity_df = sales_df.copy()
    else:
        activity_df = pd.DataFrame(columns=common_cols)

    # Parse dates
    for df in [activity_df, sales_df]:
        if not df.empty and 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    if not sales_df.empty and 'Date' in sales_df.columns:
        sales_df['Date'] = pd.to_datetime(sales_df['Date'], errors='coerce')

    # Normalise Remarks column name
    for df in [activity_df]:
        if not df.empty:
            for c in df.columns:
                if 'remark' in c.lower() and c != 'Remarks':
                    df.rename(columns={c: 'Remarks'}, inplace=True)
                    break

    return activity_df, sales_df

try:
    activity_df, sales_df = load_all()

    # ── Session state ─────────────────────────────────────────────────────────
    def uniq(df, col):
        if df.empty or col not in df.columns: return []
        return sorted(df[col].dropna().astype(str).unique().tolist())

    all_users  = uniq(activity_df, 'User')
    all_leads  = uniq(activity_df, 'Lead Type')
    all_states = uniq(activity_df, 'State')

    for k, v in [('sel_users',set(all_users)),('sel_leads',set(all_leads)),('sel_states',set(all_states))]:
        if k not in st.session_state: st.session_state[k] = v

    if not activity_df.empty and 'Date' in activity_df.columns:
        min_d = activity_df['Date'].dropna().min().date()
        max_d = activity_df['Date'].dropna().max().date()
    else:
        min_d, max_d = date(2026,1,1), date(2026,2,28)

    if 'fstart' not in st.session_state: st.session_state['fstart'] = min_d
    if 'fend'   not in st.session_state: st.session_state['fend']   = max_d

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="nic-header">
      <div class="nic-logo">NIC</div>
      <div>
        <div class="nic-title">North India Compressors <span style="font-size:1.1rem;color:#5a4000;">(Jan &amp; Feb)</span></div>
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

    def pill_group(state_key, all_items, label, n_cols, col_ctx):
        with col_ctx:
            st.markdown(f'<div class="filter-label">{label}</div>', unsafe_allow_html=True)
            all_sel = set(all_items) == st.session_state[state_key]
            if st.button("✓ Select All" if all_sel else "Select All", key=f"{state_key}_all"):
                st.session_state[state_key] = set(all_items) if not all_sel else set()
                st.rerun()
            for row in [all_items[i:i+n_cols] for i in range(0, len(all_items), n_cols)]:
                cs = st.columns(len(row))
                for ci, item in enumerate(row):
                    active = item in st.session_state[state_key]
                    if cs[ci].button(f"✓ {item}" if active else item, key=f"{state_key}_{item}"):
                        if active: st.session_state[state_key].discard(item)
                        else:      st.session_state[state_key].add(item)
                        st.rerun()

    pill_group('sel_users',  all_users,  "👤 Master User",  3, fc1)
    pill_group('sel_leads',  all_leads,  "🏷️ Master Lead",  2, fc2)
    pill_group('sel_states', all_states, "📍 Master State", 3, fc3)

    with fc4:
        st.markdown('<div class="filter-label">&nbsp;</div>', unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔄\nReset", key="reset"):
            for k in ['sel_users','sel_leads','sel_states','fstart','fend']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Apply Filters to activity + sales ─────────────────────────────────────
    def apply_filters(df):
        if df.empty: return df
        d = df.copy()
        if 'Date' in d.columns:
            d = d[(d['Date'].dt.date >= st.session_state['fstart']) &
                  (d['Date'].dt.date <= st.session_state['fend'])]
        if st.session_state['sel_users']  and 'User'      in d.columns:
            d = d[d['User'].astype(str).isin(st.session_state['sel_users'])]
        if st.session_state['sel_leads']  and 'Lead Type' in d.columns:
            d = d[d['Lead Type'].astype(str).isin(st.session_state['sel_leads'])]
        if st.session_state['sel_states'] and 'State'     in d.columns:
            d = d[d['State'].astype(str).isin(st.session_state['sel_states'])]
        return d

    dff      = apply_filters(activity_df)
    sales_f  = apply_filters(sales_df)

    # ── KPIs — now accurate because each sheet is separate ───────────────────
    # Visitors  = Visitor_Related_data rows
    # Leads     = Lead_Related_Data rows  (has Stage column with "Hot Lead", "New", etc.)
    # Sales     = Sales_Related_Data rows
    # Quotation = Lead_Related_Data rows where Stage = "Quotation Send"

    visitor_count = len(dff[dff['_sheet']=='Visitor'])  if '_sheet' in dff.columns else len(dff)
    lead_count    = len(dff[dff['_sheet']=='Lead'])     if '_sheet' in dff.columns else 0
    sales_count   = len(sales_f)
    total_revenue = sales_f['Amount'].sum() if 'Amount' in sales_f.columns else 0

    # Quotation count: from lead sheet where Stage contains "Quotation"
    quot_count = 0
    if '_sheet' in dff.columns and 'Stage' in dff.columns:
        lead_rows = dff[dff['_sheet']=='Lead']
        quot_count = len(lead_rows[lead_rows['Stage'].astype(str).str.contains('quot', na=False, case=False)])
    elif 'Remarks' in dff.columns:
        quot_count = len(dff[dff['Remarks'].astype(str).str.contains('quotation|quot send|quatation', na=False, case=False)])

    def kpi(label, val):
        return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div></div>'

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.markdown(kpi("Total Visitors",       f"{visitor_count:,}"),  unsafe_allow_html=True)
    k2.markdown(kpi("Total Lead",           f"{lead_count:,}"),     unsafe_allow_html=True)
    k3.markdown(kpi("Total Sales",          f"{sales_count:,}"),    unsafe_allow_html=True)
    k4.markdown(kpi("Total Quotation Send", f"{quot_count:,}"),     unsafe_allow_html=True)
    k5.markdown(kpi("Total Revenue",        f"₹{total_revenue:,.0f}" if total_revenue else "—"), unsafe_allow_html=True)

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
        fig = bl(fig)
        fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="",
                          yaxis={'categoryorder':'total ascending'})
        return fig

    ch1,ch2,ch3,ch4,ch5 = st.columns(5)

    with ch1:
        st.markdown('<div class="chart-box"><div class="chart-title">Source (Visits)</div>', unsafe_allow_html=True)
        src_col = 'Source' if 'Source' in dff.columns else None
        if src_col:
            fig = hbar(dff.dropna(subset=[src_col]), src_col, "#8B6914")
            st.plotly_chart(fig, use_container_width=True)
        elif 'Lead Type' in dff.columns:
            fig = hbar(dff.dropna(subset=['Lead Type']), 'Lead Type', "#8B6914")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div class="chart-box"><div class="chart-title">State Distribution</div>', unsafe_allow_html=True)
        if 'State' in dff.columns:
            d = dff['State'].value_counts().reset_index(); d.columns=['x','y']
            fig = px.pie(d, names='x', values='y', hole=0.35, color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch3:
        st.markdown('<div class="chart-box"><div class="chart-title">User Activity</div>', unsafe_allow_html=True)
        if 'User' in dff.columns:
            fig = hbar(dff.dropna(subset=['User']), 'User', "#c8a84b")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch4:
        st.markdown('<div class="chart-box"><div class="chart-title">Lead Type (Sales)</div>', unsafe_allow_html=True)
        if not sales_f.empty and 'Lead Type' in sales_f.columns:
            fig = hbar(sales_f.dropna(subset=['Lead Type']), 'Lead Type', "#e8c870")
            st.plotly_chart(fig, use_container_width=True)
        elif 'Lead Type' in dff.columns:
            fig = hbar(dff.dropna(subset=['Lead Type']), 'Lead Type', "#e8c870")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch5:
        st.markdown('<div class="chart-box"><div class="chart-title">State (Sales)</div>', unsafe_allow_html=True)
        if not sales_f.empty and 'State' in sales_f.columns:
            fig = hbar(sales_f.dropna(subset=['State']), 'State', "#f0d890")
            st.plotly_chart(fig, use_container_width=True)
        elif 'State' in dff.columns:
            fig = hbar(dff.dropna(subset=['State']), 'State', "#f0d890")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Tables ────────────────────────────────────────────────────────────────
    def sc(df, wanted): return [c for c in wanted if c in df.columns]

    t1, t2 = st.columns([3, 2])

    with t1:
        st.markdown('<div class="sec-hdr">📋 Lead &amp; Visitor Log</div>', unsafe_allow_html=True)
        lv_cols = sc(dff, ['Date','Customer Name','Contact Person','User','State','City','Lead Type','Stage','Remarks','_sheet'])
        lv = dff[lv_cols].reset_index(drop=True) if lv_cols else dff.reset_index(drop=True)
        if 'Date' in lv.columns: lv = lv.sort_values('Date', ascending=False).reset_index(drop=True)
        st.dataframe(lv, use_container_width=True, height=360)

    with t2:
        st.markdown('<div class="sec-hdr">💰 Sales Records</div>', unsafe_allow_html=True)
        if not sales_f.empty:
            s_cols = sc(sales_f, ['Date','Customer Name','User','Lead Type','Products','Amount','GST','State'])
            s_tbl = sales_f[s_cols].reset_index(drop=True) if s_cols else sales_f.reset_index(drop=True)
            if 'Date' in s_tbl.columns: s_tbl = s_tbl.sort_values('Date', ascending=False).reset_index(drop=True)
            st.dataframe(s_tbl, use_container_width=True, height=360)
        else:
            st.info("Sales data not yet loaded. Please add SALES_URL above.")

    # ── Setup instructions ────────────────────────────────────────────────────
    with st.expander("📌 Setup: How to connect all 3 sheets (one-time, 5 minutes)"):
        st.markdown(f"""
Your Google Sheet has **3 tabs** — you need to publish each one separately:

| Tab Name | Variable to update |
|---|---|
| `Visitor_Related_data` | `VISITOR_URL` |
| `Lead_Realated_Data` | `LEAD_URL` |
| `Sales_Related_Data` | `SALES_URL` |

**For each tab:**
1. Open your sheet → **File → Share → Publish to web**
2. Dropdown 1 → select the **tab name** (e.g. `Visitor_Related_data`)
3. Dropdown 2 → select **Comma-separated values (.csv)**
4. Click **Publish** → Copy the link
5. Paste it in the matching variable at the top of this `.py` file

Once all 3 URLs are set, the KPIs will show **exact numbers** (not estimates):
- **Total Visitors** = rows from `Visitor_Related_data`
- **Total Leads** = rows from `Lead_Realated_Data`
- **Total Sales** = rows from `Sales_Related_Data`
- **Total Revenue** = sum of `PO Amount` from `Sales_Related_Data`
- **Total Quotation** = rows where `Stage = Quotation Send` in `Lead_Realated_Data`
        """)

    with st.expander("🔧 Debug — loaded data info"):
        st.write(f"Activity rows: {len(activity_df)}, Sales rows: {len(sales_df)}")
        st.write("Activity columns:", activity_df.columns.tolist() if not activity_df.empty else "none")
        st.write("Sales columns:", sales_df.columns.tolist() if not sales_df.empty else "none")
        if not activity_df.empty: st.dataframe(activity_df.head(3))

    st.markdown("""<div style="text-align:center;color:#8a7030;font-size:0.72rem;margin-top:16px;font-style:italic;">
      NICPL · Auto-refreshes every 60 s</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error: {e}")
    import traceback
    st.code(traceback.format_exc())
