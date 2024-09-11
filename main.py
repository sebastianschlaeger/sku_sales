import streamlit as st
from src.overview_tab import overview_tab
from src.detail_analysis_tab import detail_analysis_tab
from src.deliveries_tab import deliveries_tab
from src.data_fetcher import fetch_and_save_missing_data
from src.winners_tab import winners_tab
from src.trending_tab import trending_tab
from src.losing_tab import losing_tab

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(layout="wide")
st.title("Procurement App - Original SKU Analysis")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Übersicht", "Detailanalyse", "Anlieferungen", "Winners", "Trending", "Losing"])

with tab1:
    overview_tab()

with tab2:
    detail_analysis_tab()

with tab3:
    deliveries_tab()

with tab4:
    winners_tab()

with tab5:
    trending_tab()

with tab6:
    losing_tab()

# Sidebar
st.sidebar.info("This app manages inventory and analyzes sales data using original SKUs.")

overwrite_data = st.sidebar.checkbox("Overwrite existing data")
if st.sidebar.button("Fetch and Save Missing Data"):
    fetch_and_save_missing_data(overwrite_data)