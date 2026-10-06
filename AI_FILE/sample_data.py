"""
Sample Inventory Data Generation
Provides a default retail dataset and creates an Excel file for download.
"""
import pandas as pd
import numpy as np
import os
from typing import List, Dict, Any

def get_sample_inventory_data() -> List[Dict[str, Any]]:
    """
    Returns a list of sample inventory items with realistic retail demand history.
    """
    np.random.seed(42)
    items = []

    # Product catalog
    products = [
        {"sku": "SKU-1001", "name": "Wireless Headphones Pro", "category": "Electronics", "cost": 45.0, "price": 89.99},
        {"sku": "SKU-1002", "name": "Smart Fitness Tracker", "category": "Wearables", "cost": 30.0, "price": 59.99},
        {"sku": "SKU-1003", "name": "USB-C Hub Adapter", "category": "Accessories", "cost": 12.0, "price": 24.99},
        {"sku": "SKU-1004", "name": "Wireless Charging Pad", "category": "Electronics", "cost": 18.0, "price": 34.99},
        {"sku": "SKU-1005", "name": "Bluetooth Speaker", "category": "Audio", "cost": 28.0, "price": 49.99},
        {"sku": "SKU-1006", "name": "Gaming Mouse", "category": "Peripherals", "cost": 22.0, "price": 39.99},
        {"sku": "SKU-1007", "name": "Mechanical Keyboard", "category": "Peripherals", "cost": 35.0, "price": 69.99},
        {"sku": "SKU-1008", "name": "Portable Power Bank", "category": "Accessories", "cost": 15.0, "price": 29.99},
        {"sku": "SKU-1009", "name": "Webcam HD", "category": "Electronics", "cost": 25.0, "price": 44.99},
        {"sku": "SKU-1010", "name": "Smartphone Stand", "category": "Accessories", "cost": 8.0, "price": 14.99},
    ]

    for idx, prod in enumerate(products):
        # Generate 12 months of historical demand with trend + seasonality + noise
        base = np.random.randint(40, 120)
        trend = np.linspace(0, np.random.randint(-10, 20), 12)
        seasonal = 10 * np.sin(np.linspace(0, 2 * np.pi, 12))
        noise = np.random.normal(0, 8, 12)
        history = np.maximum(5, base + trend + seasonal + noise).astype(int).tolist()
        # Current stock: randomly between 50 and 300
        current_stock = np.random.randint(50, 300)
        # Lead time: 5 to 30 days
        lead_time = np.random.randint(5, 30)
        items.append({
            "sku": prod["sku"],
            "name": prod["name"],
            "category": prod["category"],
            "current_stock": current_stock,
            "lead_time_days": lead_time,
            "unit_cost": prod["cost"],
            "unit_price": prod["price"],
            "demand_history": history
        })
    return items

def generate_sample_excel(filename: str = "sample_inventory_data.xlsx") -> str:

    #Generates an Excel file with sample inventory data and returns the file path.
    data = get_sample_inventory_data()
    rows = []
    for it in data:
        # Flatten demand history into columns: Month_1, Month_2, ..., Month_12
        row = {
            "SKU": it["sku"],
            "Product Name": it["name"],
            "Category": it["category"],
            "Current Stock": it["current_stock"],
            "Lead Time (days)": it["lead_time_days"],
            "Unit Cost ($)": it["unit_cost"],
            "Unit Price ($)": it["unit_price"],
        }
        for i, demand in enumerate(it["demand_history"], 1):
            row[f"Month_{i}"] = demand
        rows.append(row)

    df = pd.DataFrame(rows)
    # Ensure the directory exists
    dir_name = os.path.dirname(filename)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)

    df.to_excel(filename, index=False, engine="openpyxl")
    return os.path.abspath(filename)
if __name__ == "__main__":
    # Quick test
    path = generate_sample_excel()
    print(f"Sample Excel generated at: {path}")
    data = get_sample_inventory_data()
    print(f"Generated {len(data)} sample items.")