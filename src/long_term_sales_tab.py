import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.s3_operations import get_all_data_since_date
from src.sku_names import SKU_NAMES

def long_term_sales_tab():
    st.header("Langfristige Verkaufsanalyse")

    # Lade alle Daten
    start_date = datetime(2024, 1, 1)  # You might want to make this dynamic
    all_data = get_all_data_since_date(start_date)
    all_data['SKU'] = all_data['SKU'].astype(str)

    # Zeitraumauswahl
    time_period = st.selectbox("Zeitraum auswählen", ["Jahr", "Letzte 12 Monate"])
    
    if time_period == "Jahr":
        current_year = datetime.now().year
        selected_year = st.selectbox("Jahr auswählen", range(current_year, 2023, -1), index=0)
        start_date = datetime(selected_year, 1, 1)
        end_date = datetime(selected_year, 12, 31)
    else:  # Letzte 12 Monate
        end_date = datetime.now().replace(day=1) - timedelta(days=1)  # Letzter Tag des Vormonats
        start_date = end_date - timedelta(days=365)
    
    # Filtere Daten basierend auf dem ausgewählten Zeitraum
    filtered_data = all_data[(all_data['Date'] >= start_date) & (all_data['Date'] <= end_date)]
    
    if filtered_data.empty:
        st.warning("Keine Daten für den ausgewählten Zeitraum verfügbar.")
        return

    # Gruppiere Daten nach Monat und SKU
    monthly_data = filtered_data.groupby([pd.Grouper(key='Date', freq='ME'), 'SKU'])['Quantity'].sum().reset_index()
    monthly_data['Month'] = monthly_data['Date'].dt.strftime('%Y-%m')
    
    # SKU-Auswahl
    all_skus = sorted(list(set(all_data['SKU'].unique()) & set(SKU_NAMES.keys())))
    selected_skus = st.multiselect("SKUs auswählen", all_skus, default=all_skus[:5], format_func=lambda x: f"{x} - {SKU_NAMES.get(x, 'Unbekannt')}")
    
    # Filtere Daten basierend auf ausgewählten SKUs
    filtered_monthly_data = monthly_data[monthly_data['SKU'].isin(selected_skus)]
    
    if filtered_monthly_data.empty:
        st.warning("Keine Daten für die ausgewählten SKUs im gewählten Zeitraum verfügbar.")
        return

    # Erstelle Farbzuordnung für SKUs
    color_scale = px.colors.qualitative.Plotly
    color_map = {sku: color_scale[i % len(color_scale)] for i, sku in enumerate(all_skus)}
    
    # Erstelle Balkendiagramm für einzelne SKUs
    fig_individual = go.Figure()
    for sku in selected_skus:
        sku_data = filtered_monthly_data[filtered_monthly_data['SKU'] == sku]
        fig_individual.add_trace(go.Bar(
            x=sku_data['Month'],
            y=sku_data['Quantity'],
            name=f"{sku} - {SKU_NAMES.get(sku, 'Unbekannt')}",
            marker_color=color_map[sku]
        ))
    
    fig_individual.update_layout(
        title="Monatliche Verkaufsmenge pro SKU",
        xaxis_title="Monat",
        yaxis_title="Verkaufsmenge",
        barmode='group',
        hovermode="x unified"
    )
    
    # Erstelle Balkendiagramm für Gesamtsumme
    total_monthly_data = filtered_monthly_data.groupby('Month')['Quantity'].sum().reset_index()
    fig_total = go.Figure()
    fig_total.add_trace(go.Bar(
        x=total_monthly_data['Month'],
        y=total_monthly_data['Quantity'],
        name="Gesamtsumme",
        marker_color='rgba(0, 0, 0, 0.7)'  # Dunkelgrau für die Gesamtsumme
    ))
    
    fig_total.update_layout(
        title="Monatliche Gesamtverkaufsmenge",
        xaxis_title="Monat",
        yaxis_title="Verkaufsmenge",
        hovermode="x unified"
    )
    
    # Füge interaktive Tooltips hinzu
    for fig in [fig_individual, fig_total]:
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Menge: %{y}<br>%{customdata}",
            customdata=[f"SKU: {sku}" for sku in filtered_monthly_data['SKU']]
        )
    
    # Zeige Diagramme
    st.plotly_chart(fig_individual, use_container_width=True)
    st.plotly_chart(fig_total, use_container_width=True)
    
    # Dynamische Zusammenfassung
    st.subheader("Zusammenfassung")
    total_sales = filtered_monthly_data['Quantity'].sum()
    unique_months = filtered_monthly_data['Month'].nunique()
    
    avg_monthly_sales = total_sales / unique_months if unique_months > 0 else 0
    max_sales = filtered_monthly_data.groupby('SKU')['Quantity'].sum().max()
    min_sales = filtered_monthly_data.groupby('SKU')['Quantity'].sum().min()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gesamtverkäufe", f"{total_sales:,.0f}")
    col2.metric("Durchschnittliche monatliche Verkäufe", f"{avg_monthly_sales:,.0f}")
    col3.metric("Höchste/Niedrigste SKU-Verkäufe", f"{max_sales:,.0f} / {min_sales:,.0f}")
    
    # Tabellarische Übersicht
    st.subheader("Tabellarische Übersicht")
    table_data = filtered_monthly_data.pivot(index='SKU', columns='Month', values='Quantity').reset_index()
    table_data['Gesamtmenge'] = table_data.sum(axis=1, numeric_only=True)
    table_data['SKU_Name'] = table_data['SKU'].map(SKU_NAMES)
    table_data = table_data.sort_values('Gesamtmenge', ascending=False)
    
    # Formatieren der Tabelle
    formatted_table = table_data.style.format({col: '{:,.0f}' for col in table_data.columns if col not in ['SKU', 'SKU_Name']})
    st.dataframe(formatted_table, use_container_width=True)