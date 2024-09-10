import streamlit as st
import pandas as pd
from src.inventory_management import load_supplier_deliveries, save_supplier_deliveries, update_supplier_delivery

def deliveries_tab():
    st.subheader("Anlieferungen")
    
    # Load existing deliveries
    deliveries = load_supplier_deliveries()
    
    if not deliveries.empty:
        # Convert Date column to datetime if it's not already
        deliveries['Date'] = pd.to_datetime(deliveries['Date'])
        
        # Convert SKU to integer
        deliveries['SKU'] = deliveries['SKU'].astype(int)
        
        # Create an editable dataframe
        edited_df = st.data_editor(
            deliveries,
            column_config={
                "SKU": st.column_config.TextColumn("SKU", disabled=True),
                "SupplierDelivery": st.column_config.NumberColumn("Liefermenge", min_value=0, step=1),
                "Date": st.column_config.DateColumn("Datum"),
                "Status": st.column_config.SelectboxColumn("Status", options=["Bestellt", "Bestätigt", "Angeliefert"]),
                "Delete": st.column_config.CheckboxColumn("Löschen")
            },
            hide_index=True,
            num_rows="dynamic"
        )
        
        # Always show the "Änderungen speichern" button
        if st.button("Änderungen speichern"):
            # Remove rows marked for deletion
            if 'Delete' in edited_df.columns:
                edited_df = edited_df[~edited_df['Delete']]
                edited_df = edited_df.drop(columns=['Delete'])
            
            # Save the updated dataframe
            save_supplier_deliveries(edited_df)
            st.success("Änderungen wurden erfolgreich gespeichert.")
            st.rerun()
    else:
        st.info("Keine Anlieferungen verfügbar.")

    # Add new delivery form
    st.subheader("Neue Lieferung hinzufügen")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        new_sku = st.number_input("SKU", min_value=1, step=1)
    with col2:
        new_quantity = st.number_input("Liefermenge", min_value=0, step=1)
    with col3:
        new_date = st.date_input("Datum")
    with col4:
        new_status = st.selectbox("Status", ["Bestellt", "Bestätigt", "Angeliefert"])

    if st.button("Neue Lieferung hinzufügen"):
        update_supplier_delivery(new_sku, new_quantity, new_date, new_status)
        st.success(f"Neue Lieferung für SKU {new_sku} wurde hinzugefügt.")
        st.rerun()