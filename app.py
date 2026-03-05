import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="NIC Sales Dashboard", layout="wide", initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@700&display=swap');
* { font-family: 'Barlow', sans-serif; }
.stApp { background-color: #f0ead0; }

/* Hide default sidebar toggle on mobile */
[data-testid="stSidebar"] { display: none; }

/* ── Header ── */
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

/* ── KPI ── */
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

/* ── Filter Panel ── */
.filter-panel {
  background: linear-gradient(135deg, #2a2a2a, #1a1a1a);
  border-radius: 12px; padding: 16px 20px; margin-bottom: 16px;
}
.filter-title {
  font-family: 'Barlow Condensed',sans-serif; font-size: 1rem;
  font-weight: 700; color: #e8d080; text-transform: uppercase;
  letter-spacing: 0.08em; margin-bottom: 10px;
}

/* ── Pill / chip buttons ── */
div[data-testid="stButton"] > button {
  border-radius: 20px !important;
  padding: 4px 14px !important;
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  margin: 2px !important;
  border: 1.5px solid #b8a040 !important;
  background: #e8d880 !important;
  color: #3a2800 !important;
  transition: all 0.15s !important;
  min-height: 0 !important;
  height: auto !important;
  line-height: 1.4 !important;
}
div[data-testid="stButton"] > button:hover {
  background: #c8a84b !important;
  color: #fff !important;
}

/* ── Chart boxes ── */
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

/* ── Section header ── */
.sec-hdr {
  background: linear-gradient(90deg, #7a6020, #c8a84b); color: #fff;
  font-family: 'Barlow Condensed',sans-serif; font-weight: 700; font-size: 1rem;
  padding: 8px 16px; border-radius: 6px 6px 0 0; text-transform: uppercase;
}

hr { border-color: #b8a040; opacity: 0.35; }
div[data-testid="stDataFrame"] { border-radius: 0 0 8px 8px; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()

    # 1. De-duplicate columns first
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

    # 2. Parse date
    for col in df.columns:
        if col.strip().lower() == 'date':
            df['Date'] = pd.to_datetime(df[col], errors='coerce')
            if col != 'Date': df.drop(columns=[col], inplace=True)
            break

    # 3. Safe rename helper
    def safe_rename(df, keywords, target, exact=False):
        if target in df.columns: return df
        kws = [keywords] if isinstance(keywords, str) else keywords
        for col in df.columns:
            lc = col.strip().lower()
            match = (lc in kws) if exact else any(k in lc for k in kws)
            if match and col != target:
                return df.rename(columns={col: target})
        return df

    df = safe_rename(df, ['user'],              'User',           exact=True)
    df = safe_rename(df, ['customer name','customer'], 'Customer Name')
    df = safe_rename(df, ['contact person','contact'], 'Contact Person')
    df = safe_rename(df, ['remark'],            'Remark',         exact=True)
    df = safe_rename(df, ['state'],             'State',          exact=True)
    df = safe_rename(df, ['lead type','leadtype'], 'Lead Type')
    df = safe_rename(df, ['status'],            'Status',         exact=True)
    df = safe_rename(df, ['source'],            'Source',         exact=True)
    df = safe_rename(df, ['competitor','compet'], 'Competitor')
    df = safe_rename(df, ['po amount','amount'], 'Amount')
    return df

try:
    df = load_data()

    # ── Session state for filters ─────────────────────────────────────────────
    def get_unique(col):
        return sorted(df[col].dropna().unique().tolist()) if col in df.columns else []

    all_users  = get_unique('User')
    all_leads  = get_unique('Lead Type')
    all_states = get_unique('State')

    if 'sel_users'  not in st.session_state: st.session_state['sel_users']  = set(all_users)
    if 'sel_leads'  not in st.session_state: st.session_state['sel_leads']  = set(all_leads)
    if 'sel_states' not in st.session_state: st.session_state['sel_states'] = set(all_states)

    if 'Date' in df.columns:
        min_d = df['Date'].dropna().min().date()
        max_d = df['Date'].dropna().max().date()
    else:
        min_d, max_d = date(2026,1,1), date(2026,2,28)

    if 'start_date' not in st.session_state: st.session_state['start_date'] = min_d
    if 'end_date'   not in st.session_state: st.session_state['end_date']   = max_d

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="nic-header">
      <div class="nic-logo">NIC</div>
      <div>
        <div class="nic-title">North India Compressors <span style="font-size:1.1rem;color:#5a4000;">(Jan &amp; Feb)</span></div>
        <div class="nic-sub">a multi product company</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── FILTER PANEL (inline, not sidebar) ───────────────────────────────────
    with st.container():
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)

        fcol_date, fcol_user, fcol_lead, fcol_state, fcol_reset = st.columns([2, 3, 3, 3, 1])

        with fcol_date:
            st.markdown('<div class="filter-title">📅 Date Range</div>', unsafe_allow_html=True)
            st.session_state['start_date'] = st.date_input("From", value=st.session_state['start_date'],
                                                            min_value=min_d, max_value=max_d,
                                                            label_visibility="collapsed", key="sd")
            st.session_state['end_date']   = st.date_input("To",   value=st.session_state['end_date'],
                                                            min_value=min_d, max_value=max_d,
                                                            label_visibility="collapsed", key="ed")

        with fcol_user:
            st.markdown('<div class="filter-title">👤 Master User</div>', unsafe_allow_html=True)
            u_cols = st.columns(3)
            for i, u in enumerate(all_users):
                active = u in st.session_state['sel_users']
                label  = f"✓ {u}" if active else u
                if u_cols[i % 3].button(label, key=f"u_{u}"):
                    if active: st.session_state['sel_users'].discard(u)
                    else:      st.session_state['sel_users'].add(u)
                    st.rerun()

        with fcol_lead:
            st.markdown('<div class="filter-title">🏷️ Master Lead</div>', unsafe_allow_html=True)
            l_cols = st.columns(2)
            for i, l in enumerate(all_leads):
                active = l in st.session_state['sel_leads']
                label  = f"✓ {l}" if active else l
                if l_cols[i % 2].button(label, key=f"l_{l}"):
                    if active: st.session_state['sel_leads'].discard(l)
                    else:      st.session_state['sel_leads'].add(l)
                    st.rerun()

        with fcol_state:
            st.markdown('<div class="filter-title">📍 Master State</div>', unsafe_allow_html=True)
            s_cols = st.columns(3)
            for i, s in enumerate(all_states):
                active = s in st.session_state['sel_states']
                label  = f"✓ {s}" if active else s
                if s_cols[i % 3].button(label, key=f"s_{s}"):
                    if active: st.session_state['sel_states'].discard(s)
                    else:      st.session_state['sel_states'].add(s)
                    st.rerun()

        with fcol_reset:
            st.markdown('<div class="filter-title">&nbsp;</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Reset", key="reset_all"):
                st.session_state['sel_users']  = set(all_users)
                st.session_state['sel_leads']  = set(all_leads)
                st.session_state['sel_states'] = set(all_states)
                st.session_state['start_date'] = min_d
                st.session_state['end_date']   = max_d
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Apply Filters ─────────────────────────────────────────────────────────
    dff = df.copy()
    if 'Date' in dff.columns:
        dff = dff[(dff['Date'].dt.date >= st.session_state['start_date']) &
                  (dff['Date'].dt.date <= st.session_state['end_date'])]
    if st.session_state['sel_users']  and 'User'      in dff.columns:
        dff = dff[dff['User'].isin(st.session_state['sel_users'])]
    if st.session_state['sel_leads']  and 'Lead Type' in dff.columns:
        dff = dff[dff['Lead Type'].isin(st.session_state['sel_leads'])]
    if st.session_state['sel_states'] and 'State'     in dff.columns:
        dff = dff[dff['State'].isin(st.session_state['sel_states'])]

    # ── KPI — detect from Status OR Remark OR Lead_Related vs Visitor data ───
    has_status = 'Status' in dff.columns
    has_remark = 'Remark' in dff.columns

    # Keywords that actually appear in NICPL data (from screenshot)
    SALE_KW = r'po received|advance payment|advance received|finali|install|sale confirm|order confirm|payment done'
    QUOT_KW = r'quotation send|quotation sent|quote send|quot send'
    LEAD_KW = r'enquir|lead|interest|need|require|looking|want|discuss|meeting|visit'

    total_visitors = len(dff)

    if has_status:
        total_leads = len(dff[dff['Status'].str.contains('lead', na=False, case=False)])
        total_sales = len(dff[dff['Status'].str.contains('sale', na=False, case=False)])
        total_quot  = len(dff[dff['Status'].str.contains('quot', na=False, case=False)])
    elif has_remark:
        total_leads = len(dff[dff['Remark'].str.contains(LEAD_KW, na=False, case=False)])
        total_sales = len(dff[dff['Remark'].str.contains(SALE_KW, na=False, case=False)])
        total_quot  = len(dff[dff['Remark'].str.contains(QUOT_KW, na=False, case=False)])
    else:
        total_leads = total_sales = total_quot = 0

    total_rev = dff['Amount'].sum() if 'Amount' in dff.columns else 0

    # ── KPI Row ───────────────────────────────────────────────────────────────
    def kpi_card(label, val):
        return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div></div>'

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.markdown(kpi_card("Total Visitors",       f"{total_visitors:,}"), unsafe_allow_html=True)
    k2.markdown(kpi_card("Total Lead",           f"{total_leads:,}"),    unsafe_allow_html=True)
    k3.markdown(kpi_card("Total Sales",          f"{total_sales:,}"),    unsafe_allow_html=True)
    k4.markdown(kpi_card("Total Quotation Send", f"{total_quot:,}"),     unsafe_allow_html=True)
    k5.markdown(kpi_card("Total Revenue",        f"₹{total_rev:,.0f}" if total_rev else "—"), unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
    GOLD = ["#8B6914","#c8a84b","#e8c870","#5a3d10","#f0d890","#3a2800","#d4b060","#a07828","#604008","#e0b840"]

    def bl(fig, h=250):
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8,r=8,t=8,b=8), height=h,
            font=dict(family="Barlow", size=11, color="#2a1a00"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font_size=10),
        )
        return fig

    ch1, ch2, ch3, ch4, ch5 = st.columns(5)

    # 1. Count by Lead Type (since no Source col)
    with ch1:
        st.markdown('<div class="chart-box"><div class="chart-title">Lead Type Count</div>', unsafe_allow_html=True)
        col = 'Source' if 'Source' in dff.columns else ('Lead Type' if 'Lead Type' in dff.columns else None)
        if col:
            d = dff[col].value_counts().reset_index(); d.columns=['x','y']
            fig = px.bar(d, x='y', y='x', orientation='h', color='y',
                         color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_layout(showlegend=False,
                xaxis_title="Count", yaxis_title="", yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. State pie
    with ch2:
        st.markdown('<div class="chart-box"><div class="chart-title">State Distribution</div>', unsafe_allow_html=True)
        col2 = 'Competitor' if 'Competitor' in dff.columns else ('State' if 'State' in dff.columns else None)
        if col2:
            d = dff[col2].value_counts().reset_index(); d.columns=['x','y']
            fig = px.pie(d, names='x', values='y', hole=0.35, color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. User Activity
    with ch3:
        st.markdown('<div class="chart-box"><div class="chart-title">User Activity</div>', unsafe_allow_html=True)
        if 'User' in dff.columns:
            d = dff['User'].value_counts().reset_index(); d.columns=['x','y']
            fig = px.bar(d, x='y', y='x', orientation='h', color_discrete_sequence=["#8B6914"])
            fig = bl(fig); fig.update_layout(showlegend=False,
                xaxis_title="Count", yaxis_title="", yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. Lead Type Sales (from remark/status)
    with ch4:
        st.markdown('<div class="chart-box"><div class="chart-title">Lead Type (Sales)</div>', unsafe_allow_html=True)
        if 'Lead Type' in dff.columns:
            if has_status:
                sub = dff[dff['Status'].str.contains('sale', na=False, case=False)]
            elif has_remark:
                sub = dff[dff['Remark'].str.contains(SALE_KW, na=False, case=False)]
            else:
                sub = dff
            d = sub['Lead Type'].value_counts().reset_index(); d.columns=['x','y']
            fig = px.bar(d, x='y', y='x', orientation='h', color_discrete_sequence=["#c8a84b"])
            fig = bl(fig); fig.update_layout(showlegend=False,
                xaxis_title="Count", yaxis_title="", yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 5. State Sales
    with ch5:
        st.markdown('<div class="chart-box"><div class="chart-title">State (Sales)</div>', unsafe_allow_html=True)
        if 'State' in dff.columns:
            if has_status:
                sub = dff[dff['Status'].str.contains('sale', na=False, case=False)]
            elif has_remark:
                sub = dff[dff['Remark'].str.contains(SALE_KW, na=False, case=False)]
            else:
                sub = dff
            d = sub['State'].value_counts().reset_index(); d.columns=['x','y']
            fig = px.bar(d, x='y', y='x', orientation='h', color_discrete_sequence=["#e8c870"])
            fig = bl(fig); fig.update_layout(showlegend=False,
                xaxis_title="Count", yaxis_title="", yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Tables ────────────────────────────────────────────────────────────────
    def safe_cols(wanted):
        return [c for c in wanted if c in dff.columns]

    t1, t2 = st.columns([3, 2])

    with t1:
        st.markdown('<div class="sec-hdr">📋 Lead &amp; Visitor Log</div>', unsafe_allow_html=True)
        cols_lv = safe_cols(['Date','Customer Name','Contact Person','User','State','Lead Type','Remark'])
        lv = (dff[cols_lv] if cols_lv else dff).reset_index(drop=True)
        if 'Date' in lv.columns: lv = lv.sort_values('Date', ascending=False).reset_index(drop=True)
        st.dataframe(lv, use_container_width=True, height=360)

    with t2:
        st.markdown('<div class="sec-hdr">💰 Sales / PO Records</div>', unsafe_allow_html=True)
        if has_status:
            sdf = dff[dff['Status'].str.contains('sale', na=False, case=False)].copy()
        elif has_remark:
            sdf = dff[dff['Remark'].str.contains(SALE_KW, na=False, case=False)].copy()
        else:
            sdf = dff.copy()
        sc = safe_cols(['Date','Customer Name','User','State','Lead Type','Amount','Remark'])
        s_tbl = (sdf[sc] if sc else sdf).reset_index(drop=True)
        if 'Date' in s_tbl.columns: s_tbl = s_tbl.sort_values('Date', ascending=False).reset_index(drop=True)
        st.dataframe(s_tbl, use_container_width=True, height=360)

    # ── Debug ─────────────────────────────────────────────────────────────────
    with st.expander("🔧 Debug — columns & sample"):
        st.write("**Columns:**", df.columns.tolist())
        st.write(f"**Rows:** {len(df)}")
        st.dataframe(df.head(3))

    st.markdown("""<div style="text-align:center;color:#8a7030;font-size:0.72rem;margin-top:16px;font-style:italic;">
      NICPL · Auto-refreshes every 60 s</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error: {e}")
    import traceback
    st.code(traceback.format_exc())
    try: st.write("Columns:", df.columns.tolist())
    except: pass
