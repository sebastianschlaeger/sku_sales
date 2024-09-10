import pandas as pd
from datetime import datetime
from src.sku_mappings import apply_sku_mapping

def process_sku(sku):
    return str(sku).split('-')[0]  # Remove everything after the hyphen

def process_orders(orders_data):
    orders = orders_data.get('Data', [])
    if not orders:
        return pd.DataFrame(columns=['SKU', 'Quantity'])  # Return an empty DataFrame with 'SKU' and 'Quantity' columns

    sku_quantities = {}
    
    for order in orders:
        order_items = order.get('OrderItems', [])
        for item in order_items:
            sku = item.get('Product', {}).get('SKU')
            quantity = int(item.get('Quantity', 0))
            if sku:
                sku_quantities[sku] = sku_quantities.get(sku, 0) + quantity
    
    processed_data = [
        {'SKU': sku, 'Quantity': quantity}
        for sku, quantity in sku_quantities.items()
    ]
    
    return pd.DataFrame(processed_data)