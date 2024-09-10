import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.s3_utils import get_s3_fs
import logging
from src.sku_names import SKU_NAMES
import json
from src.inventory_management import load_initial_inventory, load_supplier_deliveries
from src.trend_analysis import calculate_trend
from datetime import datetime, timedelta
from src.billbee_api import billbee_api
from src.data_processor import process_orders
import time

# Setze das Logging-Level für dieses Modul auf WARNING
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

SALES_FILE = "all_sales_data_original_sku.csv"

def save_to_s3(new_data, date, overwrite=False):
    try:
        s3 = get_s3_fs()
        bucket_name = st.secrets['aws']['S3_BUCKET_NAME']
        full_path = f"{bucket_name}/{SALES_FILE}"
        
        new_data['Date'] = pd.to_datetime(date).date()
        
        if s3.exists(full_path):
            existing_data = load_existing_data(s3, full_path)
            existing_data['Date'] = pd.to_datetime(existing_data['Date']).dt.date
            if overwrite:
                existing_data = existing_data[existing_data['Date'] != new_data['Date'].iloc[0]]
            elif date_exists(existing_data, new_data['Date'].iloc[0]):
                logger.info(f"Daten für {date} existieren bereits. Überspringe diesen Tag.")
                return SALES_FILE
            combined_data = pd.concat([existing_data, new_data], ignore_index=True)
        else:
            combined_data = new_data
        
        combined_data['Date'] = pd.to_datetime(combined_data['Date']).dt.date
        combined_data = combined_data.sort_values('Date')
        save_combined_data(s3, full_path, combined_data)
        logger.info(f"Neue Daten für {date} gespeichert.")
        
        return SALES_FILE
    except Exception as e:
        logger.error(f"Fehler beim Speichern in S3: {str(e)}")
        raise

def load_existing_data(s3, full_path):
    with s3.open(full_path, 'r') as f:
        data = pd.read_csv(f, parse_dates=['Date'])
    data['Quantity'] = data['Quantity'].astype(int)
    data['Date'] = data['Date'].dt.date  # Convert to datetime.date objects
    data['Platform'] = data['Platform'].astype(str)  # Ensure Platform is loaded as string
    return data

def date_exists(data, date):
    return date in set(data['Date'])  # Use set for faster lookup

def save_combined_data(s3, full_path, combined_data):
    with s3.open(full_path, 'w') as f:
        combined_data.to_csv(f, index=False)

def get_all_data_since_date(start_date):
    """Holt alle Daten seit einem bestimmten Datum."""
    try:
        s3 = get_s3_fs()
        bucket_name = st.secrets['aws']['S3_BUCKET_NAME']
        full_path = f"{bucket_name}/{SALES_FILE}"
        
        if s3.exists(full_path):
            with s3.open(full_path, 'r') as f:
                all_data = pd.read_csv(f, parse_dates=['Date'])
            all_data['Date'] = pd.to_datetime(all_data['Date']).dt.date
            start_date = pd.to_datetime(start_date).date()
            return all_data[all_data['Date'] >= start_date]
        else:
            logger.warning("Keine Verkaufsdaten gefunden.")
            return pd.DataFrame(columns=['Date', 'SKU', 'Quantity', 'Platform'])
    except Exception as e:
        logger.error(f"Fehler beim Laden der Daten aus S3: {str(e)}")
        return pd.DataFrame(columns=['Date', 'SKU', 'Quantity', 'Platform'])

def get_summary_data(days=30):
    """Erstellt eine Zusammenfassung der Verkaufsdaten."""
    try:
        logger.info("Starting get_summary_data function")
        start_date = datetime(2024, 1, 1).date()  # Angepasst auf 01.01.2024
        all_data = get_all_data_since_date(start_date)
        
        if all_data.empty:
            logger.warning("No data available")
            return pd.DataFrame(columns=['SKU', 'SKU_Name', 'Last30DaysQuantity', 'AvgDailyQuantity', 'CurrentQuantity', 'PlannedDeliveries', 'InventoryDays', 'AdjustedInventoryDays', 'AdjustedInventoryDaysWithDeliveries', 'Trend', 'Platforms'])
        
        all_data['Date'] = pd.to_datetime(all_data['Date'])
        
        end_date = datetime.now().date() - timedelta(days=1)
        start_date_30d = end_date - timedelta(days=days-1)
        
        all_data['SKU'] = all_data['SKU'].astype(str)
        
        summary_data = calculate_summary_data(all_data, start_date_30d)
        summary_data = add_inventory_data(summary_data, all_data)
        summary_data = add_trend_data(all_data, summary_data)
        summary_data = calculate_inventory_days(summary_data)
        summary_data = add_sku_names(summary_data)
        summary_data = add_platform_data(all_data, summary_data)
        
        return sort_summary_data(summary_data)
    except Exception as e:
        logger.error(f"Error in get_summary_data: {str(e)}", exc_info=True)
        return pd.DataFrame(columns=['SKU', 'SKU_Name', 'Last30DaysQuantity', 'AvgDailyQuantity', 'CurrentQuantity', 'PlannedDeliveries', 'InventoryDays', 'AdjustedInventoryDays', 'AdjustedInventoryDaysWithDeliveries', 'Trend', 'Platforms'])


def calculate_summary_data(all_data, start_date_30d):
    """Berechnet die Zusammenfassungsdaten."""
    # Konvertiere start_date_30d zu datetime64[ns]
    start_date_30d = pd.to_datetime(start_date_30d)
    
    # Filtere die Daten für die letzten 30 Tage
    last_30d_data = all_data[all_data['Date'] >= start_date_30d]
    
    # Berechne die Zusammenfassung für die letzten 30 Tage
    summary_data = last_30d_data.groupby('SKU').agg({
        'Quantity': ['sum', 'count'],
        'Date': ['min', 'max']
    }).reset_index()
    summary_data.columns = ['SKU', 'Last30DaysQuantity', 'DaysWithSales', 'FirstDate', 'LastDate']
    
    # Berechne AvgDailyQuantity basierend auf den letzten 30 Tagen
    summary_data['AvgDailyQuantity'] = summary_data['Last30DaysQuantity'] / 30
    
    # Füge Informationen über den gesamten Zeitraum hinzu
    total_data = all_data.groupby('SKU').agg({
        'Quantity': 'sum',
        'Date': ['min', 'max']
    }).reset_index()
    total_data.columns = ['SKU', 'TotalQuantity', 'FirstEverDate', 'LastEverDate']
    
    # Verknüpfe die Daten
    summary_data = pd.merge(summary_data, total_data, on='SKU', how='outer')
    
    # Fülle NaN-Werte für SKUs, die in den letzten 30 Tagen keine Verkäufe hatten
    summary_data['Last30DaysQuantity'] = summary_data['Last30DaysQuantity'].fillna(0)
    summary_data['AvgDailyQuantity'] = summary_data['AvgDailyQuantity'].fillna(0)
    
    return summary_data

def add_inventory_data(summary_data, all_data):
    """Fügt Bestandsdaten zur Zusammenfassung hinzu und berechnet die CurrentQuantity korrekt."""
    try:
        initial_inventory = load_initial_inventory()
        supplier_deliveries = load_supplier_deliveries()
        
        initial_inventory['SKU'] = initial_inventory['SKU'].astype(str)
        supplier_deliveries['SKU'] = supplier_deliveries['SKU'].astype(str)
        
        # Ensure Date column is datetime
        initial_inventory['Date'] = pd.to_datetime(initial_inventory['Date'])
        
        # Merge initial inventory data
        summary_data = pd.merge(summary_data, initial_inventory[['SKU', 'InitialQuantity', 'Date']], on='SKU', how='left')
        
        # Process supplier deliveries
        delivered = supplier_deliveries[supplier_deliveries['Status'] == 'Angeliefert'].groupby('SKU')['SupplierDelivery'].sum().reset_index(name='SupplierDelivery_Delivered')
        planned = supplier_deliveries[supplier_deliveries['Status'].isin(['Bestellt', 'Bestätigt'])].groupby('SKU')['SupplierDelivery'].sum().reset_index(name='SupplierDelivery_Planned')
        
        summary_data = pd.merge(summary_data, delivered, on='SKU', how='left')
        summary_data = pd.merge(summary_data, planned, on='SKU', how='left')
        
        # Fill NaN values with 0 and convert to float
        for col in ['InitialQuantity', 'SupplierDelivery_Delivered', 'SupplierDelivery_Planned']:
            summary_data[col] = summary_data[col].fillna(0).astype('float64')
        
        # Ensure Date column is datetime
        summary_data['Date'] = pd.to_datetime(summary_data['Date'])
        all_data['Date'] = pd.to_datetime(all_data['Date'])
        
        # Calculate CurrentQuantity correctly
        def calculate_current_quantity(row):
            initial_date = row['Date']
            sales_after_initial = row['TotalQuantity'] - row['SalesBeforeInitial']
            return row['InitialQuantity'] + row['SupplierDelivery_Delivered'] - sales_after_initial

        # Calculate sales before initial inventory date
        summary_data['SalesBeforeInitial'] = summary_data.apply(
            lambda row: row['TotalQuantity'] if pd.isnull(row['Date']) 
            else all_data[(all_data['SKU'] == row['SKU']) & (all_data['Date'] < row['Date'])]['Quantity'].sum(),
            axis=1
        )
        
        # Apply the calculation
        summary_data['CurrentQuantity'] = summary_data.apply(calculate_current_quantity, axis=1)
        summary_data['PlannedDeliveries'] = summary_data['SupplierDelivery_Planned']
        
        # Calculate AdjustedInventoryDays and AdjustedInventoryDaysWithDeliveries
        summary_data['AdjustedInventoryDays'] = np.where(summary_data['AvgDailyQuantity'] > 0,
                                                         summary_data['CurrentQuantity'] / summary_data['AvgDailyQuantity'],
                                                         np.inf)
        summary_data['AdjustedInventoryDaysWithDeliveries'] = np.where(summary_data['AvgDailyQuantity'] > 0,
                                                                       (summary_data['CurrentQuantity'] + summary_data['PlannedDeliveries']) / summary_data['AvgDailyQuantity'],
                                                                       np.inf)
        
        return summary_data
    except Exception as e:
        logger.error(f"Error in add_inventory_data: {str(e)}", exc_info=True)
        raise

def calculate_inventory_days(summary_data):
    """Berechnet die Bestandsreichweite."""
    summary_data['InventoryDays'] = np.where(summary_data['AvgDailyQuantity'] > 0, 
                                             summary_data['CurrentQuantity'] / summary_data['AvgDailyQuantity'], 
                                             np.inf)
    return summary_data

def add_trend_data(all_data, summary_data):
    """Fügt Trenddaten zur Zusammenfassung hinzu."""
    trend_data = all_data.groupby('SKU').apply(calculate_trend).reset_index()
    trend_data.columns = ['SKU', 'Trend']
    return pd.merge(summary_data, trend_data, on='SKU', how='left')

def add_sku_names(summary_data):
    """Fügt SKU-Namen zur Zusammenfassung hinzu."""
    summary_data['SKU_Name'] = summary_data['SKU'].map(SKU_NAMES)
    return summary_data

def add_platform_data(all_data, summary_data):
    """Fügt Plattformdaten zur Zusammenfassung hinzu."""
    def safe_join(x):
        return ', '.join(sorted(set(str(item) for item in x if pd.notna(item))))
    
    platform_data = all_data.groupby('SKU')['Platform'].apply(safe_join).reset_index()
    platform_data = platform_data.rename(columns={'Platform': 'Platforms'})
    return pd.merge(summary_data, platform_data, on='SKU', how='left')

def sort_summary_data(summary_data):
    """Sortiert die Zusammenfassungsdaten."""
    columns = ['SKU', 'SKU_Name', 'Last30DaysQuantity', 'AvgDailyQuantity', 'CurrentQuantity', 'PlannedDeliveries',
               'InventoryDays', 'AdjustedInventoryDays', 'AdjustedInventoryDaysWithDeliveries', 'Trend', 'Platforms']
    return summary_data[columns].sort_values('InventoryDays', ascending=True)

def get_daily_sales_data(days=30):
    """Holt tägliche Verkaufsdaten."""
    try:
        s3 = get_s3_fs()
        bucket_name = st.secrets['aws']['S3_BUCKET_NAME']
        full_path = f"{bucket_name}/{SALES_FILE}"
        
        if s3.exists(full_path):
            all_data = load_existing_data(s3, full_path)
            return process_daily_sales_data(all_data, days)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der täglichen Verkaufsdaten: {str(e)}")
        return pd.DataFrame()

def process_daily_sales_data(all_data, days):
    """Verarbeitet die täglichen Verkaufsdaten."""
    all_data['Date'] = pd.to_datetime(all_data['Date'])
    all_data['SKU'] = all_data['SKU'].astype(str)
    
    end_date = pd.Timestamp.now().floor('D')
    start_date = end_date - pd.Timedelta(days=days)
    
    filtered_data = all_data[(all_data['Date'] >= start_date) & (all_data['Date'] <= end_date)]
    
    date_range = pd.date_range(start=start_date, end=end_date)
    
    daily_sales = filtered_data.pivot_table(
        values='Quantity', 
        index='Date', 
        columns='SKU', 
        aggfunc='sum'
    ).reindex(date_range).fillna(0)
    
    return daily_sales

def get_missing_dates(start_date, end_date):
    s3 = get_s3_fs()
    bucket_name = st.secrets['aws']['S3_BUCKET_NAME']
    full_path = f"{bucket_name}/{SALES_FILE}"
    
    if s3.exists(full_path):
        with s3.open(full_path, 'r') as f:
            all_data = pd.read_csv(f, parse_dates=['Date'])
        
        all_dates = set(all_data['Date'].dt.date)
        
        all_possible_dates = set(pd.date_range(start=start_date, end=end_date).date)
        
        missing_dates = sorted(all_possible_dates - all_dates)
        
        return missing_dates
    else:
        return list(pd.date_range(start=start_date, end=end_date).date)

def get_missing_dates_last_30_days():
    all_dates = set(pd.date_range(end=datetime.now().date(), periods=30).date)
    existing_dates = set(get_all_data_since_date(datetime.now().date() - timedelta(days=30))['Date'].dt.date)
    missing_dates = sorted(all_dates - existing_dates)
    return missing_dates[0] if missing_dates else None, missing_dates[-1] if missing_dates else None

def update_data(date=None, overwrite_existing_data=False):
    if overwrite_existing_data:
        st.success("Vorhandene Bestelldaten wurden gelöscht.")
    
    s3 = get_s3_fs()
    bucket_name = st.secrets['aws']['S3_BUCKET_NAME']
    last_import_file = "last_import_date.txt"
    last_import_path = f"{bucket_name}/{last_import_file}"

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    if date is None:
        if s3.exists(last_import_path):
            with s3.open(last_import_path, 'r') as f:
                last_import_date = datetime.strptime(f.read().strip(), "%Y-%m-%d").date()
        else:
            last_import_date = yesterday - timedelta(days=30)
        end_date = yesterday
    else:
        last_import_date = date
        end_date = date

    if last_import_date > end_date:
        st.info("Alle verfügbaren Daten wurden bereits importiert.")
        return

    current_date = end_date
    total_days = (end_date - last_import_date).days + 1
    days_processed = 0
    
    while current_date >= last_import_date:
        orders_data = billbee_api.get_orders(current_date, current_date + timedelta(days=1))
        processed_orders = process_orders(orders_data)
        save_to_s3(processed_orders, current_date, overwrite_existing_data)
        
        current_date -= timedelta(days=1)
        days_processed += 1

    with s3.open(last_import_path, 'w') as f:
        f.write(end_date.strftime("%Y-%m-%d"))

    st.success(f"Bestellungen für {days_processed} Tage wurden erfolgreich verarbeitet.")