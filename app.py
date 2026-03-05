import streamlit as st
import pandas as pd
import plotly.express as px

# Power BI Style Configuration
st.set_page_config(page_title="NIC Sales Dashboard", layout="wide")

# Custom CSS to match your gold/yellow Power BI theme
st.markdown("""
    <style>
    .main { background-color: #f4e8c1; }
    .stMetric { background-color: #d4af37; padding: 10px; border-radius: 5px; color: black; }
    </style>
    """, unsafe_allow_html=True)

st.title("📂 North India Compressors (Jan & Feb)")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip() # Remove extra spaces
    return df

try:
    df = load_data()

    # --- Sidebar ---
    st.sidebar.header("Filters")
    user_list = df['User'].dropna().unique().tolist()
    selected_users = st.sidebar.multiselect("Master User", options=user_list, default=user_list)
    df_filtered = df[df['User'].isin(selected_users)]

    # --- Top KPIs (Gold Boxes) ---
    # IMPORTANT: Change 'Status' or 'Amount' below to match your EXACT sheet headers
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Visitors", len(df_filtered))
    
    # Check for 'Status' column to count Leads/Sales
    if 'Status' in df_filtered.columns:
        col2.metric("Total Lead", len(df_filtered[df_filtered['Status'] == 'Lead']))
        col3.metric("Total Sales", len(df_filtered[df_filtered['Status'] == 'Sale']))
    else:
        col2.metric("Total Lead", "Missing 'Status' Col")
        col3.metric("Total Sales", "Missing 'Status' Col")

    # Check for Revenue Column
    rev_col = 'Revenue' if 'Revenue' in df_filtered.columns else ('Amount' if 'Amount' in df_filtered.columns else None)
    if rev_col:
        total_rev = df_filtered[rev_col].sum()
        col4.metric("Total Revenue", f"₹{total_rev:,.0f}")
    else:
        col4.metric("Total Revenue", "Check Col Name")

    st.markdown("---")

    # --- Charts (Matching Power BI Layout) ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Count of Source by Source")
        if 'Source' in df_filtered.columns:
            fig_source = px.bar(df_filtered, x='Source', template="plotly_white", color_discrete_sequence=['#4A90E2'])
            st.plotly_chart(fig_source, use_container_width=True)
        else:
            st.error("Cannot find 'Source' column")

    with c2:
        st.subheader("User Sales")
        fig_user = px.bar(df_filtered, y='User', orientation='h', template="plotly_white")
        st.plotly_chart(fig_user, use_container_width=True)

    # --- Bottom Tables ---
    st.subheader("Lead & Visitor Details")
    st.dataframe(df_filtered, use_container_width=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
