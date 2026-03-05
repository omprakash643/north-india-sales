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

/* All filter buttons — pill style */
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

# ── IMPORTANT: Replace this URL with your NEW sheet's published CSV URL ───────
# Steps: File → Share → Publish to web → Sheet1 → CSV → Copy link
# The old URL below is from the OLD sheet — update it!
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?output=csv"
# ↑↑↑ REPLACE with new sheet URL from sheet ID: 1rn2WomKdekug5A5uoazpxv7AQbSneR2L2J7_3DDZxC8

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()

    # De-duplicate column names
    seen = {}
    new_cols = []
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    df.columns = new_cols

    # Standardise column names to known targets
    col_map = {}
    for col in df.columns:
        lc = col.strip().lower()
        if lc == 'date'                            and 'Date'           not in col_map.values(): col_map[col] = 'Date'
        elif lc in ('lead type','leadtype')        and 'Lead Type'      not in col_map.values(): col_map[col] = 'Lead Type'
        elif lc == 'user'                          and 'User'           not in col_map.values(): col_map[col] = 'User'
        elif 'customer' in lc                      and 'Customer Name'  not in col_map.values(): col_map[col] = 'Customer Name'
        elif 'contact' in lc                       and 'Contact Person' not in col_map.values(): col_map[col] = 'Contact Person'
        elif lc == 'state'                         and 'State'          not in col_map.values(): col_map[col] = 'State'
        elif lc in ('city','cIty','cITy','city')   and 'City'           not in col_map.values(): col_map[col] = 'City'
        elif 'remark' in lc                        and 'Remarks'        not in col_map.values(): col_map[col] = 'Remarks'
        elif 'meyer' in lc or 'existing' in lc     and 'Meyer Existing' not in col_map.values(): col_map[col] = 'Meyer Existing'
        elif lc == 'status'                        and 'Status'         not in col_map.values(): col_map[col] = 'Status'
        elif lc == 'source'                        and 'Source'         not in col_map.values(): col_map[col] = 'Source'
        elif 'amount' in lc or lc == 'po amount'   and 'Amount'         not in col_map.values(): col_map[col] = 'Amount'

    df.rename(columns=col_map, inplace=True)

    # Parse date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    return df

try:
    df = load_data()

    # ── Keyword detection from Remarks (your actual column) ──────────────────
    # Based on real data seen: "finalised", "order finalised", "quotation", "enquiry"
    SALE_KW = r'finali|po received|advance|payment done|order confirm|install|sale confirm|purchased'
    QUOT_KW = r'quotation|quote|quot send|want quotation|want quatation'
    LEAD_KW = r'enquir|interest|need|require|discussion|plan|want|looking|meeting|visit'

    # ── Session state ─────────────────────────────────────────────────────────
    def uniq(col):
        return sorted(df[col].dropna().astype(str).unique().tolist()) if col in df.columns else []

    all_users  = uniq('User')
    all_leads  = uniq('Lead Type')
    all_states = uniq('State')

    for k, v in [('sel_users', set(all_users)), ('sel_leads', set(all_leads)), ('sel_states', set(all_states))]:
        if k not in st.session_state: st.session_state[k] = v

    if 'Date' in df.columns:
        min_d = df['Date'].dropna().min().date()
        max_d = df['Date'].dropna().max().date()
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

    # ── FILTER PANEL ─────────────────────────────────────────────────────────
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)

    fc0, fc1, fc2, fc3, fc4 = st.columns([1.4, 2.5, 2.8, 3.2, 0.7])

    # Date
    with fc0:
        st.markdown('<div class="filter-label">📅 Date Range</div>', unsafe_allow_html=True)
        st.session_state['fstart'] = st.date_input("From", value=st.session_state['fstart'],
            min_value=min_d, max_value=max_d, label_visibility="collapsed", key="sd")
        st.session_state['fend']   = st.date_input("To",   value=st.session_state['fend'],
            min_value=min_d, max_value=max_d, label_visibility="collapsed", key="ed")

    # Master User
    with fc1:
        st.markdown('<div class="filter-label">👤 Master User</div>', unsafe_allow_html=True)
        # Select All toggle
        all_u_selected = len(st.session_state['sel_users']) == len(all_users)
        if st.button("✓ Select All" if all_u_selected else "Select All", key="u_all"):
            st.session_state['sel_users'] = set(all_users) if not all_u_selected else set()
            st.rerun()
        # Individual user buttons — 3 per row
        rows_u = [all_users[i:i+3] for i in range(0, len(all_users), 3)]
        for row in rows_u:
            cols = st.columns(len(row))
            for ci, u in enumerate(row):
                active = u in st.session_state['sel_users']
                if cols[ci].button(f"✓ {u}" if active else u, key=f"u_{u}"):
                    if active: st.session_state['sel_users'].discard(u)
                    else:      st.session_state['sel_users'].add(u)
                    st.rerun()

    # Master Lead
    with fc2:
        st.markdown('<div class="filter-label">🏷️ Master Lead</div>', unsafe_allow_html=True)
        all_l_selected = len(st.session_state['sel_leads']) == len(all_leads)
        if st.button("✓ Select All" if all_l_selected else "Select All", key="l_all"):
            st.session_state['sel_leads'] = set(all_leads) if not all_l_selected else set()
            st.rerun()
        rows_l = [all_leads[i:i+2] for i in range(0, len(all_leads), 2)]
        for row in rows_l:
            cols = st.columns(len(row))
            for ci, l in enumerate(row):
                active = l in st.session_state['sel_leads']
                if cols[ci].button(f"✓ {l}" if active else l, key=f"l_{l}"):
                    if active: st.session_state['sel_leads'].discard(l)
                    else:      st.session_state['sel_leads'].add(l)
                    st.rerun()

    # Master State
    with fc3:
        st.markdown('<div class="filter-label">📍 Master State</div>', unsafe_allow_html=True)
        all_s_selected = len(st.session_state['sel_states']) == len(all_states)
        if st.button("✓ Select All" if all_s_selected else "Select All", key="s_all"):
            st.session_state['sel_states'] = set(all_states) if not all_s_selected else set()
            st.rerun()
        rows_s = [all_states[i:i+3] for i in range(0, len(all_states), 3)]
        for row in rows_s:
            cols = st.columns(len(row))
            for ci, s in enumerate(row):
                active = s in st.session_state['sel_states']
                if cols[ci].button(f"✓ {s}" if active else s, key=f"s_{s}"):
                    if active: st.session_state['sel_states'].discard(s)
                    else:      st.session_state['sel_states'].add(s)
                    st.rerun()

    # Reset
    with fc4:
        st.markdown('<div class="filter-label">&nbsp;</div>', unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔄\nReset", key="reset"):
            for k in ['sel_users','sel_leads','sel_states']:
                del st.session_state[k]
            st.session_state['fstart'] = min_d
            st.session_state['fend']   = max_d
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Apply Filters ─────────────────────────────────────────────────────────
    dff = df.copy()
    if 'Date' in dff.columns:
        dff = dff[(dff['Date'].dt.date >= st.session_state['fstart']) &
                  (dff['Date'].dt.date <= st.session_state['fend'])]
    if st.session_state['sel_users']  and 'User'      in dff.columns:
        dff = dff[dff['User'].astype(str).isin(st.session_state['sel_users'])]
    if st.session_state['sel_leads']  and 'Lead Type' in dff.columns:
        dff = dff[dff['Lead Type'].astype(str).isin(st.session_state['sel_leads'])]
    if st.session_state['sel_states'] and 'State'     in dff.columns:
        dff = dff[dff['State'].astype(str).isin(st.session_state['sel_states'])]

    # ── KPIs ─────────────────────────────────────────────────────────────────
    has_status = 'Status'  in dff.columns
    has_remark = 'Remarks' in dff.columns   # ← correct column name

    total_visitors = len(dff)

    if has_status:
        total_leads = len(dff[dff['Status'].str.contains('lead',  na=False, case=False)])
        total_sales = len(dff[dff['Status'].str.contains('sale',  na=False, case=False)])
        total_quot  = len(dff[dff['Status'].str.contains('quot',  na=False, case=False)])
    elif has_remark:
        total_leads = len(dff[dff['Remarks'].str.contains(LEAD_KW, na=False, case=False)])
        total_sales = len(dff[dff['Remarks'].str.contains(SALE_KW, na=False, case=False)])
        total_quot  = len(dff[dff['Remarks'].str.contains(QUOT_KW, na=False, case=False)])
    else:
        total_leads = total_sales = total_quot = 0

    total_rev = dff['Amount'].sum() if 'Amount' in dff.columns else 0

    def kpi(label, val):
        return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div></div>'

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.markdown(kpi("Total Visitors",       f"{total_visitors:,}"), unsafe_allow_html=True)
    k2.markdown(kpi("Total Lead",           f"{total_leads:,}"),    unsafe_allow_html=True)
    k3.markdown(kpi("Total Sales",          f"{total_sales:,}"),    unsafe_allow_html=True)
    k4.markdown(kpi("Total Quotation Send", f"{total_quot:,}"),     unsafe_allow_html=True)
    k5.markdown(kpi("Total Revenue",        f"₹{total_rev:,.0f}" if total_rev else "—"), unsafe_allow_html=True)

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

    ch1,ch2,ch3,ch4,ch5 = st.columns(5)

    with ch1:
        st.markdown('<div class="chart-box"><div class="chart-title">Lead Type Count</div>', unsafe_allow_html=True)
        if 'Lead Type' in dff.columns:
            d = dff['Lead Type'].value_counts().reset_index(); d.columns=['x','y']
            fig = px.bar(d, x='y', y='x', orientation='h', color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="",
                                             yaxis={'categoryorder':'total ascending'})
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
            d = dff['User'].value_counts().reset_index(); d.columns=['x','y']
            fig = px.bar(d, x='y', y='x', orientation='h', color_discrete_sequence=["#8B6914"])
            fig = bl(fig); fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="",
                                             yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch4:
        st.markdown('<div class="chart-box"><div class="chart-title">Lead Type (Sales)</div>', unsafe_allow_html=True)
        if 'Lead Type' in dff.columns and has_remark:
            sub = dff[dff['Remarks'].str.contains(SALE_KW, na=False, case=False)]
            d = sub['Lead Type'].value_counts().reset_index(); d.columns=['x','y']
            fig = px.bar(d, x='y', y='x', orientation='h', color_discrete_sequence=["#c8a84b"])
            fig = bl(fig); fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="",
                                             yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch5:
        st.markdown('<div class="chart-box"><div class="chart-title">State (Sales)</div>', unsafe_allow_html=True)
        if 'State' in dff.columns and has_remark:
            sub = dff[dff['Remarks'].str.contains(SALE_KW, na=False, case=False)]
            d = sub['State'].value_counts().reset_index(); d.columns=['x','y']
            fig = px.bar(d, x='y', y='x', orientation='h', color_discrete_sequence=["#e8c870"])
            fig = bl(fig); fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="",
                                             yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Tables ────────────────────────────────────────────────────────────────
    def sc(wanted): return [c for c in wanted if c in dff.columns]

    t1, t2 = st.columns([3, 2])

    with t1:
        st.markdown('<div class="sec-hdr">📋 Lead &amp; Visitor Log</div>', unsafe_allow_html=True)
        lv_cols = sc(['Date','Customer Name','Contact Person','User','State','City','Lead Type','Remarks'])
        lv = (dff[lv_cols] if lv_cols else dff).reset_index(drop=True)
        if 'Date' in lv.columns: lv = lv.sort_values('Date', ascending=False).reset_index(drop=True)
        st.dataframe(lv, use_container_width=True, height=360)

    with t2:
        st.markdown('<div class="sec-hdr">💰 Sales / PO Records</div>', unsafe_allow_html=True)
        if has_remark:
            sdf = dff[dff['Remarks'].str.contains(SALE_KW, na=False, case=False)].copy()
        else:
            sdf = dff.copy()
        s_cols = sc(['Date','Customer Name','User','State','Lead Type','Amount','Remarks'])
        s_tbl = (sdf[s_cols] if s_cols else sdf).reset_index(drop=True)
        if 'Date' in s_tbl.columns: s_tbl = s_tbl.sort_values('Date', ascending=False).reset_index(drop=True)
        st.dataframe(s_tbl, use_container_width=True, height=360)

    # ── Sheet URL warning + debug ─────────────────────────────────────────────
    st.info("⚠️ **Action needed:** Go to your new Google Sheet → File → Share → Publish to web → Sheet: Combined_Activity_Log → Format: CSV → Copy the link → Replace `SHEET_URL` in this file with the new link.")

    with st.expander("🔧 Debug — columns & sample data"):
        st.write("**Columns detected:**", df.columns.tolist())
        st.write(f"**Total rows:** {len(df)}")
        st.dataframe(df.head(5))

    st.markdown("""<div style="text-align:center;color:#8a7030;font-size:0.72rem;margin-top:16px;font-style:italic;">
      NICPL · Auto-refreshes every 60 s</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error: {e}")
    import traceback
    st.code(traceback.format_exc())
    try: st.write("Columns:", df.columns.tolist())
    except: pass
