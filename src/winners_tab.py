import streamlit as st
import pandas as pd
import plotly.express as px
from src.s3_operations import get_summary_data
from src.sku_names import SKU_NAMES

def winners_tab():
    st.subheader("Top 20 Produkte (Winners)")

    # Get summary data
    summary_data = get_summary_data()

    if summary_data.empty:
        st.warning("Keine Daten verfügbar.")
        return

    # Sort by Last30DaysQuantity and get top 20
    top_20 = summary_data.nlargest(20, 'Last30DaysQuantity')

    # Create a line chart
    fig = px.line(
        top_20,
        x='SKU_Name',
        y='Last30DaysQuantity',
        title='Top 20 Produkte nach Verkaufsmenge (letzte 30 Tage)',
        labels={'Last30DaysQuantity': 'Verkaufsmenge', 'SKU_Name': 'Produkt'},
        hover_data=['SKU', 'AvgDailyQuantity', 'CurrentQuantity']
    )
    fig.update_xaxes(tickangle=45)
    fig.update_traces(mode='lines+markers')
    st.plotly_chart(fig, use_container_width=True)

    # Display data table
    st.dataframe(
        top_20[['SKU', 'SKU_Name', 'Last30DaysQuantity', 'AvgDailyQuantity', 'CurrentQuantity', 'InventoryDays']],
        hide_index=True
    )