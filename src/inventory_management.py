import pandas as pd
import streamlit as st
from src.s3_utils import get_s3_fs
from datetime import datetime
import logging

# Fügen Sie diese Zeile am Anfang der Datei hinzu
logger = logging.getLogger(__name__)

def save_initial_inventory(df):
    s3 = get_s3_fs()
    bucket_name = st.secrets['aws']['S3_BUCKET_NAME']
    filename = "initial_inventory_original_sku.csv"
    full_path = f"{bucket_name}/{filename}"
    
    with s3.open(full_path, 'w') as f:
        df.to_csv(f, index=False)

def load_initial_inventory():
    try:
        s3 = get_s3_fs()
        bucket_name = st.secrets['aws']['S3_BUCKET_NAME']
        filename = "initial_inventory_original_sku.csv"
        full_path = f"{bucket_name}/{filename}"
        
        if s3.exists(full_path):
            with s3.open(full_path, 'r') as f:
                df = pd.read_csv(f)
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            df['SKU'] = df['SKU'].apply(lambda x: str(int(float(x))))
            return df[['SKU', 'InitialQuantity', 'Date']]
        else:
            return pd.DataFrame(columns=['SKU', 'InitialQuantity', 'Date'])
    except Exception as e:
        st.error(f"Fehler beim Laden des Anfangsbestands: {str(e)}")
        return pd.DataFrame(columns=['SKU', 'InitialQuantity', 'Date'])

def update_initial_inventory(sku, quantity, date):
    inventory_df = load_initial_inventory()
    
    if sku in inventory_df['SKU'].values:
        inventory_df.loc[inventory_df['SKU'] == sku, ['InitialQuantity', 'Date']] = [quantity, date]
    else:
        new_row = pd.DataFrame({'SKU': [sku], 'InitialQuantity': [quantity], 'Date': [date]})
        inventory_df = pd.concat([inventory_df, new_row], ignore_index=True)
    
    save_initial_inventory(inventory_df)
    return inventory_df

def save_supplier_deliveries(df):
    s3 = get_s3_fs()
    bucket_name = st.secrets['aws']['S3_BUCKET_NAME']
    filename = "supplier_deliveries_original_sku.csv"
    full_path = f"{bucket_name}/{filename}"
    
    with s3.open(full_path, 'w') as f:
        df.to_csv(f, index=False)

def load_supplier_deliveries():
    try:
        s3 = get_s3_fs()
        bucket_name = st.secrets['aws']['S3_BUCKET_NAME']
        filename = "supplier_deliveries_original_sku.csv"
        full_path = f"{bucket_name}/{filename}"
        
        if s3.exists(full_path):
            with s3.open(full_path, 'r') as f:
                df = pd.read_csv(f)
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            df['SKU'] = df['SKU'].astype(str)
            return df
        else:
            return pd.DataFrame(columns=['SKU', 'SupplierDelivery', 'Date', 'Status'])
    except Exception as e:
        logger.error(f"Fehler beim Laden der Lieferantenanlieferungen: {str(e)}")
        return pd.DataFrame(columns=['SKU', 'SupplierDelivery', 'Date', 'Status'])

def update_supplier_delivery(sku, quantity, date, status):
    deliveries_df = load_supplier_deliveries()
    
    mask = (deliveries_df['SKU'] == sku) & (deliveries_df['Date'] == date)
    if mask.any():
        deliveries_df.loc[mask, 'SupplierDelivery'] = quantity
        deliveries_df.loc[mask, 'Status'] = status
    else:
        new_row = pd.DataFrame({'SKU': [sku], 'SupplierDelivery': [quantity], 'Date': [date], 'Status': [status]})
        deliveries_df = pd.concat([deliveries_df, new_row], ignore_index=True)
    
    save_supplier_deliveries(deliveries_df)
    return deliveries_df