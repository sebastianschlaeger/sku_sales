import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.inventory_management import update_initial_inventory as update_inventory
from src.s3_operations import get_daily_sales_data, get_summary_data
from src.sku_names import SKU_NAMES

def overview_tab():
    # Anfangsbestand-Verwaltung
    st.subheader("Anfangsbestand verwalten")
    col1, col2, col3 = st.columns(3)
    with col1:
        sku_initial = st.text_input("SKU (Anfangsbestand)")
    with col2:
        quantity_initial = st.number_input("Anfangsbestand", min_value=0, step=1)
    with col3:
        date_initial = st.date_input("Datum (Anfangsbestand)")

    if st.button("Anfangsbestand aktualisieren"):
        updated_inventory = update_inventory(sku_initial, quantity_initial, date_initial)
        st.success(f"Anfangsbestand für SKU {sku_initial} wurde aktualisiert.")

    st.markdown("---")

    # Neuer Chart: Tägliche Verkäufe nach SKU
    st.subheader("Tägliche Verkäufe nach SKU")

    # Zeitraumauswahl
    time_range = st.selectbox("Zeitraum auswählen", [7, 14, 30], index=2)

    # Hole die täglichen Verkaufsdaten
    daily_sales = get_daily_sales_data(days=time_range + 1)  # +1 um sicherzustellen, dass wir genug Daten haben

    if not daily_sales.empty:
        # Entferne den aktuellen Tag
        daily_sales = daily_sales[daily_sales.index < pd.Timestamp.now().floor('D')]

        # Erstelle Checkboxen für jede SKU und eine für die Summe
        st.write("SKUs auswählen:")
        
        # Checkbox für die Summe aller SKUs
        show_sum = st.checkbox("Summe aller SKUs", value=True)
        
        # Erstelle Spalten für die SKU-Checkboxen
        cols = st.columns(4)  # Anpassen Sie die Anzahl der Spalten nach Bedarf
        sku_checkboxes = {}
        
        for i, sku in enumerate(daily_sales.columns):
            with cols[i % 4]:
                sku_str = str(sku)
                sku_name = SKU_NAMES.get(sku_str, f"Unbekannte SKU {sku_str}")
                sku_checkboxes[sku] = st.checkbox(f"{sku_str} - {sku_name}", value=False, key=f"checkbox_{sku_str}")

        # Erstelle den Chart
        fig = go.Figure()

        # Füge die Summe aller SKUs hinzu, wenn ausgewählt
        if show_sum:
            sum_data = daily_sales.sum(axis=1)
            fig.add_trace(go.Scatter(
                x=daily_sales.index.strftime('%Y-%m-%d'),
                y=sum_data,
                mode='lines+markers',
                name='Summe aller SKUs',
                line=dict(color='black', width=2),
                hovertemplate='Datum: %{x}<br>Gesamtverkäufe: %{y}<extra></extra>'
            ))

        # Füge individuelle SKU-Linien hinzu
        for sku in daily_sales.columns:
            if sku_checkboxes[sku]:
                sku_str = str(int(sku))
                sku_name = SKU_NAMES.get(sku_str, f"Unbekannte SKU {sku_str}")
                fig.add_trace(go.Scatter(
                    x=daily_sales.index.strftime('%Y-%m-%d'),
                    y=daily_sales[sku],
                    mode='lines+markers',
                    name=f'{sku_str} - {sku_name}',
                    hovertemplate='Datum: %{x}<br>Verkäufe: %{y}<extra></extra>'
                ))

        fig.update_layout(
            title=f'Tägliche Verkäufe der letzten {time_range} Tage',
            xaxis_title='Datum',
            yaxis_title='Verkaufsmenge',
            hovermode='closest'
        )

        st.plotly_chart(fig)
    else:
        st.info("Keine Verkaufsdaten für den ausgewählten Zeitraum verfügbar.")

    st.markdown("---")

    # Lade die Zusammenfassungsdaten
    summary_data = get_summary_data()
    summary_data['SKU'] = summary_data['SKU'].apply(lambda x: str(int(x)))
    
    if not summary_data.empty:
        st.subheader("Zusammenfassung der Verkäufe")
        
        # Filter summary_data to include only SKUs with Last30DaysQuantity > 0
        filtered_summary_data = summary_data[summary_data['Last30DaysQuantity'] > 0]
        
        # Zeige die Zusammenfassungstabelle
        display_columns = ['SKU', 'SKU_Name', 'Last30DaysQuantity', 'AvgDailyQuantity', 'CurrentQuantity', 'PlannedDeliveries', 'InventoryDays', 'AdjustedInventoryDays', 'AdjustedInventoryDaysWithDeliveries', 'Trend']
        
        # Only include columns that are present in the DataFrame
        available_columns = [col for col in display_columns if col in filtered_summary_data.columns]
        
        st.dataframe(filtered_summary_data[available_columns].style.format({
            'Last30DaysQuantity': '{:.0f}',
            'AvgDailyQuantity': '{:.2f}',
            'CurrentQuantity': '{:.0f}',
            'PlannedDeliveries': '{:.0f}',
            'InventoryDays': '{:.1f}',
            'AdjustedInventoryDays': '{:.1f}',
            'AdjustedInventoryDaysWithDeliveries': '{:.1f}',
            'Trend': '{:.2f}%'
        }))
    
        total_quantity_sold = summary_data['Last30DaysQuantity'].sum()
        total_current_quantity = summary_data['CurrentQuantity'].sum()
        total_planned_deliveries = summary_data['PlannedDeliveries'].sum()
        st.write(f"Gesamtmenge verkaufter Artikel in den letzten 30 Tagen: {total_quantity_sold:.0f}")
        st.write(f"Aktueller Gesamtbestand: {total_current_quantity:.0f}")
        st.write(f"Gesamte geplante Lieferungen: {total_planned_deliveries:.0f}")
    else:
        st.info("Keine Zusammenfassungsdaten verfügbar.")