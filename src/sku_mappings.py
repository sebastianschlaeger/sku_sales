from datetime import datetime

SKU_MAPPINGS = {
    '80524-44': '80534',
    '80523-20': '80536',
    # Add more mappings here
}

def apply_sku_mapping(sku, quantity, order_date=None):
    quantity = int(quantity)
    sku = str(sku)  # Ensure sku is a string for comparison
    
    # Spezielle Behandlung für SKU 8000
    if sku == '8000':
        return [('80534', quantity), ('80536', quantity)]
    
    # Ignoriere SKUs 8001 - 8004
    if sku in ['8001', '8002', '8003', '8004']:
        return []
    
    # Rest der Funktion bleibt unverändert
    if sku in SKU_MAPPINGS:
        mapped_items = SKU_MAPPINGS[sku]
        if isinstance(mapped_items, (int, str)):
            return [(str(mapped_items), quantity)]
        elif isinstance(mapped_items, list):
            return [(str(item[0]), item[1] * quantity) for item in mapped_items]
    
    return [(sku, quantity)]
