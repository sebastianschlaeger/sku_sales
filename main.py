import streamlit as st
from src.overview_tab import overview_tab
from src.detail_analysis_tab import detail_analysis_tab
from src.deliveries_tab import deliveries_tab
from src.data_fetcher import fetch_and_save_missing_data
from src.billbee_api import billbee_api
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("Procurement App - Original SKU Analysis")

tab1, tab2, tab3, tab4 = st.tabs(["Übersicht", "Detailanalyse", "Anlieferungen", "Neueste Bestellung"])

with tab1:
    overview_tab()

with tab2:
    detail_analysis_tab()

with tab3:
    deliveries_tab()

with tab4:
    display_latest_order()

# Sidebar
st.sidebar.info("This app manages inventory and analyzes sales data using original SKUs.")

overwrite_data = st.sidebar.checkbox("Overwrite existing data")
if st.sidebar.button("Fetch and Save Missing Data"):
    fetch_and_save_missing_data(overwrite_data)

def display_latest_order():
    st.subheader("Latest Order Details")
    
    # Fetch the latest order
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    latest_order = billbee_api.get_orders(yesterday, today)
    
    if latest_order and 'Data' in latest_order and latest_order['Data']:
        order = latest_order['Data'][0]  # Get the first (latest) order
        st.json(order)  # Display the full JSON response
    else:
        st.info("No orders found in the last 24 hours.")