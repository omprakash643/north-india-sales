import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="NIC Sales Dashboard", layout="wide")
st.title("📈 North India Compressors Sales Dashboard")

# 2. Load Data from your Published CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJKBgkAtx6Fm5B4-mbaWwJ8lTdMMgsYo2zuXM9rEmoIQ_AlEqd6GudLDaIoAViA5OE1ppjqmujNOAj/pub?output=csv"

@st.cache_data(ttl=60) # Refresh data every minute
def load_data():
    # Read the CSV and skip any empty rows
    df = pd.read_csv(SHEET_URL)
    return df

try:
    df = load_data()

    # 3. Sidebar Filters
    st.sidebar.header("Filter Options")
    # Clean up 'User' column for filtering
    user_list = df['User'].dropna().unique().tolist()
    selected_users = st.sidebar.multiselect("Select User:", options=user_list, default=user_list)
    
    # Apply Filter
    df_filtered = df[df['User'].isin(selected_users)]

    # 4. KPI Metrics (Top Row)
    # Note: Adjust column names if your sheet uses different headers
    total_visitors = len(df_filtered)
    total_leads = len(df_filtered[df_filtered['Status'].str.contains('Lead', na=False)])
    total_sales = len(df_filtered[df_filtered['Status'].str.contains('Sale', na=False)])
    
    # Calculate revenue if an 'Amount' or 'PO Amount' column exists
    revenue_col = 'Amount' if 'Amount' in df_filtered.columns else None
    total_revenue = df_filtered[revenue_col].sum() if revenue_col else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Visitors", total_visitors)
    col2.metric("Total Leads", total_leads)
    col3.metric("Total Sales", total_sales)
    col4.metric("Total Revenue", f"₹{total_revenue:,.0f}")

    st.markdown("---")

    # 5. Charts (Middle Row)
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Count of Source")
        fig_source = px.bar(df_filtered, x='Source', color='Source', template="plotly_white")
        st.plotly_chart(fig_source, use_container_width=True)

    with chart_col2:
        st.subheader("User Sales Performance")
        fig_user = px.pie(df_filtered, names='User', hole=0.4)
        st.plotly_chart(fig_user, use_container_width=True)

    # 6. Detailed Data Table
    st.subheader("Lead & Visitor Details")
    st.dataframe(df_filtered, use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.info("Check if your Google Sheet column names match: 'User', 'Source', 'Status', and 'Amount'.")
