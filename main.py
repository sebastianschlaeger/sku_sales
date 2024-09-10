import streamlit as st
from src.overview_tab import overview_tab
from src.detail_analysis_tab import detail_analysis_tab
from src.deliveries_tab import deliveries_tab
from src.data_fetcher import fetch_and_save_missing_data

st.set_page_config(layout="wide")
st.title("Procurement App - Original SKU Analysis")

tab1, tab2, tab3 = st.tabs(["Übersicht", "Detailanalyse", "Anlieferungen"])

with tab1:
    overview_tab()

with tab2:
    detail_analysis_tab()

with tab3:
    deliveries_tab()

# Sidebar
st.sidebar.info("This app manages inventory and analyzes sales data using original SKUs.")

overwrite_data = st.sidebar.checkbox("Overwrite existing data")
if st.sidebar.button("Fetch and Save Missing Data"):
    fetch_and_save_missing_data(overwrite_data)