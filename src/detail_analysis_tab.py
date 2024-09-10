import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
from src.s3_operations import get_all_data_since_date, get_summary_data
from src.trend_analysis import analyze_all_skus
from src.sku_names import SKU_NAMES
import pandas as pd

def detail_analysis_tab():
    st.subheader("Detailanalyse und Prognose")

    start_date = datetime(2024, 2, 1).date()
    all_data = get_all_data_since_date(start_date)

    if not all_data.empty:
        analysis_results = analyze_all_skus(all_data)
        summary_data = get_summary_data()
        
        if summary_data is not None and not summary_data.empty:
            active_skus = summary_data[summary_data['Last30DaysQuantity'] > 0]['SKU'].astype(str).tolist()
        else:
            active_skus = []

        analysis_results = {str(k): v for k, v in analysis_results.items()}

        sku_options = sorted([
            (sku, f"{sku} - {SKU_NAMES.get(sku, 'Unbekannt')}")
            for sku in active_skus if sku in analysis_results
        ], key=lambda x: x[0])

        sku_options.insert(0, ("all", "Alle Produkte"))

        if sku_options:
            selected_sku = st.selectbox(
                "Wählen Sie eine SKU für die Detailanalyse:",
                options=[sku for sku, _ in sku_options],
                format_func=lambda x: next((name for sku, name in sku_options if sku == x), x)
            )

            if selected_sku == "all":
                display_all_products_analysis(analysis_results)
            elif selected_sku in analysis_results:
                display_single_product_analysis(selected_sku, analysis_results[selected_sku])
            else:
                st.warning("Keine Analysedaten für die ausgewählte SKU verfügbar.")
        else:
            st.warning("Keine SKUs für die Analyse verfügbar.")
    else:
        st.info("Keine Daten für die Detailanalyse verfügbar.")

def display_all_products_analysis(analysis_results):
    st.write("Analyse für alle Produkte")

    # Combine data from all SKUs
    combined_data = pd.DataFrame()
    for sku, result in analysis_results.items():
        if 'smoothed_data' in result and not result['smoothed_data'].empty:
            result['smoothed_data']['SKU'] = sku
            combined_data = pd.concat([combined_data, result['smoothed_data']])

    if not combined_data.empty:
        # Calculate and display total sales for the last 12 months
        today = datetime.now().date()
        one_year_ago = today - timedelta(days=365)
        combined_data['Date'] = pd.to_datetime(combined_data['Date']).dt.date
        last_12_months_data = combined_data[combined_data['Date'] > one_year_ago]
        total_last_12_months = last_12_months_data['Quantity'].sum()

        st.write(f"Gesamtverkaufsmenge aller Produkte der letzten 12 Monate: {int(total_last_12_months)}")

        fig = px.line(combined_data, x='Date', y='SmoothQuantity', color='SKU', title='Historische Daten für alle Produkte')
        st.plotly_chart(fig)

        # Display monthly sales for all products
        monthly_data = combined_data.copy()
        monthly_data['Date'] = pd.to_datetime(monthly_data['Date'])
        monthly_data = monthly_data.groupby(['Date', 'SKU'])['Quantity'].sum().reset_index()
        monthly_data = monthly_data.set_index('Date').groupby('SKU').resample('ME')['Quantity'].sum().reset_index()
        monthly_data['Month'] = monthly_data['Date'].dt.strftime('%Y-%m')
        fig_monthly = px.bar(monthly_data, x='Month', y='Quantity', color='SKU', title='Monatliche Verkaufsmenge für alle Produkte')
        st.plotly_chart(fig_monthly)
    else:
        st.warning("Nicht genügend Daten für die Erstellung eines Diagramms.")

def display_single_product_analysis(selected_sku, sku_result):
    st.write(f"Trend für SKU {selected_sku}: {sku_result['overall_trend']:.4f} Einheiten pro Tag")

    # Calculate total sales for the last 12 months
    today = datetime.now().date()
    one_year_ago = today - timedelta(days=365)
    sku_result['smoothed_data']['Date'] = pd.to_datetime(sku_result['smoothed_data']['Date']).dt.date
    last_12_months_data = sku_result['smoothed_data'][sku_result['smoothed_data']['Date'] > one_year_ago]
    total_last_12_months = last_12_months_data['Quantity'].sum()

    st.write(f"Gesamtverkaufsmenge der letzten 12 Monate: {int(total_last_12_months)}")

    if 'smoothed_data' in sku_result and not sku_result['smoothed_data'].empty:
        fig = px.line(sku_result['smoothed_data'], x='Date', y='SmoothQuantity', title=f'Historische Daten und Prognose für SKU {selected_sku}')
        
        if 'forecast' in sku_result and not sku_result['forecast'].empty:
            fig.add_scatter(x=sku_result['forecast']['Date'], y=sku_result['forecast']['Forecast'], mode='lines', name='Prognose')
            fig.add_scatter(x=sku_result['forecast']['Date'], y=sku_result['forecast']['LowerCI'], mode='lines', line=dict(dash='dash'), name='Unteres KI')
            fig.add_scatter(x=sku_result['forecast']['Date'], y=sku_result['forecast']['UpperCI'], mode='lines', line=dict(dash='dash'), name='Oberes KI')
        else:
            st.warning("Nicht genügend Daten für eine Prognose.")
        
        st.plotly_chart(fig)
    else:
        st.warning("Nicht genügend Daten für die Erstellung eines Diagramms.")

    monthly_data = sku_result['smoothed_data'].copy()
    monthly_data['Date'] = pd.to_datetime(monthly_data['Date'])
    monthly_data = monthly_data.set_index('Date').resample('ME')['Quantity'].sum().reset_index()
    monthly_data['Month'] = monthly_data['Date'].dt.strftime('%Y-%m')
    fig_monthly = px.bar(monthly_data, x='Month', y='Quantity', title=f'Monatliche Verkaufsmenge für SKU {selected_sku}')
    st.plotly_chart(fig_monthly)