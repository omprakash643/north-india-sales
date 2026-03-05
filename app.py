import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NIC Sales Dashboard", layout="wide")
st.title("📈 North India Compressors Sales Dashboard")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    # Clean up column names (remove hidden spaces)
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data()

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Options")
    # Using 'User' since we see it's working in your screenshot
    user_list = df['User'].dropna().unique().tolist()
    selected_users = st.sidebar.multiselect("Select User:", options=user_list, default=user_list)
    df_filtered = df[df['User'].isin(selected_users)]

    # --- KPI Calculations with Safety Checks ---
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Total Visitors
    col1.metric("Total Visitors", len(df_filtered))

    # 2. Total Leads (Checks for 'Status' or similar column)
    status_col = 'Status' if 'Status' in df_filtered.columns else None
    if status_col:
        leads = len(df_filtered[df_filtered[status_col].str.contains('Lead', na=False, case=False)])
        sales = len(df_filtered[df_filtered[status_col].str.contains('Sale', na=False, case=False)])
    else:
        leads = "N/A"
        sales = "N/A"
    
    col2.metric("Total Leads", leads)
    col3.metric("Total Sales", sales)

    # 3. Total Revenue
    rev_col = 'Amount' if 'Amount' in df_filtered.columns else ('PO Amount' if 'PO Amount' in df_filtered.columns else None)
    total_rev = df_filtered[rev_col].sum() if rev_col else 0
    col4.metric("Total Revenue", f"₹{total_rev:,.0f}")

    st.markdown("---")

    # --- Charts ---
    c1, c2 = st.columns(2)
    with c1:
        source_col = 'Source' if 'Source' in df_filtered.columns else None
        if source_col:
            st.subheader("Count of Source")
            fig = px.bar(df_filtered, x=source_col, color=source_col, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Column 'Source' not found for chart.")

    with c2:
        st.subheader("User Distribution")
        fig_user = px.pie(df_filtered, names='User', hole=0.4)
        st.plotly_chart(fig_user, use_container_width=True)

    # --- Raw Data ---
    st.subheader("Data Preview")
    st.dataframe(df_filtered)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
    st.write("Current Columns found in your sheet:", df.columns.tolist())
