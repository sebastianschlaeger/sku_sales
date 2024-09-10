import streamlit as st
import pandas as pd
import plotly.express as px
from src.s3_operations import get_all_data_since_date
from src.sku_names import SKU_NAMES
from datetime import datetime, timedelta

def trending_tab():
    st.subheader("Top 20% Produkte mit höchstem Anstieg (Trending)")

    # Get data for the last 60 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=60)
    all_data = get_all_data_since_date(start_date)

    if all_data.empty:
        st.warning("Keine Daten verfügbar.")
        return

    # Calculate sales for the last 30 days and the 30 days before that
    last_30_days = all_data[all_data['Date'] > (end_date - timedelta(days=30))]
    previous_30_days = all_data[(all_data['Date'] <= (end_date - timedelta(days=30))) & (all_data['Date'] > (end_date - timedelta(days=60)))]

    last_30_days_sales = last_30_days.groupby('SKU')['Quantity'].sum().reset_index()
    previous_30_days_sales = previous_30_days.groupby('SKU')['Quantity'].sum().reset_index()

    # Merge the two periods and calculate the increase
    sales_comparison = pd.merge(last_30_days_sales, previous_30_days_sales, on='SKU', suffixes=('_last', '_previous'))
    sales_comparison['Increase'] = sales_comparison['Quantity_last'] - sales_comparison['Quantity_previous']
    sales_comparison['Increase_Percentage'] = (sales_comparison['Increase'] / sales_comparison['Quantity_previous']) * 100

    # Sort by increase and get top 20%
    top_20_percent = sales_comparison.nlargest(int(len(sales_comparison) * 0.2), 'Increase')

    # Add SKU names
    top_20_percent['SKU_Name'] = top_20_percent['SKU'].map(SKU_NAMES)

    # Create a bar chart
    fig = px.bar(
        top_20_percent,
        x='SKU',
        y='Increase',
        title='Top 20% Produkte mit höchstem Anstieg (letzte 30 Tage vs. vorherige 30 Tage)',
        labels={'Increase': 'Anstieg', 'SKU': 'SKU'},
        hover_data=['SKU_Name', 'Quantity_last', 'Quantity_previous', 'Increase_Percentage']
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    # Display data table
    st.dataframe(
        top_20_percent[['SKU', 'SKU_Name', 'Quantity_last', 'Quantity_previous', 'Increase', 'Increase_Percentage']],
        hide_index=True
    )