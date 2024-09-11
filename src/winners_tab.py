import streamlit as st
import pandas as pd
import plotly.express as px
from src.s3_operations import get_summary_data, get_daily_sales_data
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

    # Get daily sales data for the last 30 days
    daily_sales = get_daily_sales_data(days=30)

    # Ensure 'SKU' column exists in daily_sales
    if 'SKU' not in daily_sales.columns:
        st.warning("SKU column not found in daily sales data.")
        return

    # Filter daily sales data for top 20 SKUs
    top_20_daily = daily_sales[daily_sales['SKU'].isin(top_20['SKU'])]

    # Melt the dataframe to create a format suitable for line plot
    melted_data = top_20_daily.melt(id_vars=['Date', 'SKU'], value_vars=['Quantity'], var_name='Metric', value_name='Quantity')

    # Add SKU names
    melted_data['SKU_Name'] = melted_data['SKU'].map(SKU_NAMES)

    # Create a line chart
    fig = px.line(
        melted_data,
        x='Date',
        y='Quantity',
        color='SKU_Name',
        title='Top 20 Produkte nach Verkaufsmenge (letzte 30 Tage)',
        labels={'Quantity': 'Verkaufsmenge', 'Date': 'Datum'},
        hover_data=['SKU']
    )
    fig.update_xaxes(title='Datum')
    fig.update_yaxes(title='Verkaufsmenge')
    st.plotly_chart(fig, use_container_width=True)

    # Display data table
    st.dataframe(
        top_20[['SKU', 'SKU_Name', 'Last30DaysQuantity', 'AvgDailyQuantity', 'CurrentQuantity', 'InventoryDays']],
        hide_index=True
    )