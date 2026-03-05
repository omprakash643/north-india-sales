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

VISITOR_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=0&single=true&output=csv"
LEAD_URL    = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=2066525621&single=true&output=csv"
SALES_URL   = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?gid=23552387&single=true&output=csv"

def clean_amount(val):
    try:
        if pd.isna(val): return 0.0
        return float(str(val).replace(',','').replace('₹','').replace(' ','').strip())
    except: return 0.0

@st.cache_data(ttl=60)
def load_all():
    vdf = pd.read_csv(VISITOR_URL)
    ldf = pd.read_csv(LEAD_URL)
    sdf = pd.read_csv(SALES_URL)

    # ── Step 1: Clean column names ────────────────────────────────────────────
    for df in [vdf, ldf, sdf]:
        df.columns = df.columns.str.strip()

    # ── Step 2: Rename cols before normalising ────────────────────────────────
    sdf.rename(columns={'Customer': 'Customer Name', 'PO Amount': 'Amount'}, inplace=True)
    if 'Amount' in sdf.columns:
        sdf['Amount'] = sdf['Amount'].apply(clean_amount)

    # Rename Remark variants in visitor + lead
    for df in [vdf, ldf]:
        for c in list(df.columns):
            if 'remark' in c.lower() and c != 'Remark':
                df.rename(columns={c: 'Remark'}, inplace=True); break

    # Rename Competitors in visitor
    for c in list(vdf.columns):
        if any(k in c.lower() for k in ['competitor', 'meyer', 'existing']):
            vdf.rename(columns={c: 'Competitors'}, inplace=True); break

    # ── Step 3: UPPERCASE normalise ALL key filter cols (the connection fix) ──
    for df in [vdf, ldf, sdf]:
        for col in ['User', 'Lead Type', 'State', 'Source', 'Stage']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()

    # ── Step 4: Parse dates ───────────────────────────────────────────────────
    for df in [vdf, ldf, sdf]:
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # ── Step 5: Tag source ────────────────────────────────────────────────────
    vdf['_src'] = 'Visitor'
    ldf['_src'] = 'Lead'
    sdf['_src'] = 'Sales'

    # ── Step 6: Combined activity log (Visitor + Lead) ────────────────────────
    combined = pd.concat([vdf, ldf], ignore_index=True)

    # ── Step 7: Build master filter lists FROM the normalised data ────────────
    def master(col, *dfs):
        vals = set()
        for d in dfs:
            if col in d.columns:
                vals |= set(d[col].dropna().unique())
        return sorted([v for v in vals if v and v != 'NAN'])

    master_users  = master('User',      vdf, ldf, sdf)
    master_leads  = master('Lead Type', vdf, ldf, sdf)
    master_states = master('State',     vdf, ldf, sdf)

    return vdf, ldf, sdf, combined, master_users, master_leads, master_states

try:
    vdf, ldf, sdf, combined, master_users, master_leads, master_states = load_all()

    # ── Session state ─────────────────────────────────────────────────────────
    for k, v in [('su', set(master_users)), ('sl', set(master_leads)), ('ss', set(master_states))]:
        if k not in st.session_state: st.session_state[k] = v

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

    pill_group('su', master_users,  "👤 Master User",  3, fc1)
    pill_group('sl', master_leads,  "🏷️ Master Lead",  2, fc2)
    pill_group('ss', master_states, "📍 Master State", 3, fc3)

    with fc4:
        st.markdown('<div class="filter-label">&nbsp;</div>', unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔄 Reset", key="reset_all"):
            for k in ['su', 'sl', 'ss', 'fstart', 'fend']:
                if k in st.session_state: del st.session_state[k]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Filter engine — data is already UPPERCASE so matching is exact ────────
    def filt(df):
        d = df.copy()
        if 'Date' in d.columns:
            d = d[(d['Date'].dt.date >= st.session_state['fstart']) &
                  (d['Date'].dt.date <= st.session_state['fend'])]
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

    vF   = filt(vdf)
    lF   = filt(ldf)
    sF   = filt(sdf)
    actF = filt(combined)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    tv = len(vF)
    tl = len(lF)
    ts = len(sF)
    tr = float(sF['Amount'].sum()) if 'Amount' in sF.columns and len(sF) > 0 else 0.0
    # Quotation = QUOTATION SEND + HOT LEAD (uppercase now matches)
    tq = len(lF[lF['Stage'].isin(['QUOTATION SEND', 'HOT LEAD'])]) \
         if 'Stage' in lF.columns and len(lF) > 0 else 0

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

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(kpi("Total Visitors",       f"{tv:,}" if tv else "—"), unsafe_allow_html=True)
    k2.markdown(kpi("Total Lead",           f"{tl:,}" if tl else "—"), unsafe_allow_html=True)
    k3.markdown(kpi("Total Sales",          f"{ts:,}" if ts else "—"), unsafe_allow_html=True)
    k4.markdown(kpi("Total Quotation Send", f"{tq:,}" if tq else "—"), unsafe_allow_html=True)
    k5.markdown(kpi("Total Revenue",        fmt_rev(tr)),               unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
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

    def nd():
        st.markdown('<p style="color:#8a7030;font-size:0.8rem;padding:12px 0">No data</p>',
                    unsafe_allow_html=True)

    ch1, ch2, ch3, ch4, ch5 = st.columns(5)

    with ch1:
        st.markdown('<div class="chart-box"><div class="chart-title">Count of Source by Source</div>', unsafe_allow_html=True)
        if 'Source' in lF.columns and not lF.empty:
            d = lF['Source'].value_counts().reset_index(); d.columns = ['Source','Count']
            fig = px.bar(d, x='Source', y='Count', color='Source', color_discrete_sequence=GOLD)
            fig = bl(fig); fig.update_layout(showlegend=False, xaxis_tickangle=-35, yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else: nd()
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div class="chart-box"><div class="chart-title">Competitors (Visit)</div>', unsafe_allow_html=True)
        comp_col = 'Competitors' if 'Competitors' in vF.columns else None
        if comp_col and not vF.empty:
            d = vF[comp_col].value_counts().reset_index(); d.columns = ['x','y']
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

    # ── Debug expander ────────────────────────────────────────────────────────
    with st.expander("🔧 Debug — verify filter connection"):
        st.write(f"**Unfiltered:** Visitors={len(vdf)}, Leads={len(ldf)}, Sales={len(sdf)}")
        st.write(f"**Filtered:**   Visitors={len(vF)}, Leads={len(lF)}, Sales={len(sF)}")
        st.write("**Active Users:**",  sorted(st.session_state['su']))
        st.write("**Active Leads:**",  sorted(st.session_state['sl']))
        st.write("**Active States:**", sorted(st.session_state['ss']))
        if 'Stage' in ldf.columns:
            st.write("**All Stage values:**")
            st.dataframe(ldf['Stage'].value_counts().reset_index())

    st.markdown("""<div style="text-align:center;color:#8a7030;font-size:0.72rem;margin-top:16px;font-style:italic;">
      NICPL · Auto-refreshes every 60 s</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Error: {e}")
    import traceback; st.code(traceback.format_exc())
