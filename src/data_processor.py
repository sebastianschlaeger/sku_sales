import pandas as pd
from datetime import datetime

def process_orders(orders_data):
    orders = orders_data.get('Data', [])
    if not orders:
        return pd.DataFrame(columns=['SKU', 'Quantity', 'Platform'])

    processed_data = []
    
    for order in orders:
        order_items = order.get('OrderItems', [])
        platform = order.get('Seller', {}).get('BillbeeShopName', 'Unknown')
        for item in order_items:
            sku = item.get('Product', {}).get('SKU')
            quantity = int(item.get('Quantity', 0))
            if sku:
                processed_data.append({
                    'SKU': sku,
                    'Quantity': quantity,
                    'Platform': platform
                })
    
    return pd.DataFrame(processed_data)