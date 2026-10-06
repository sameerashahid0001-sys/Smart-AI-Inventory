"""
Data Ingestion and Normalization Module
Handles Excel (.xlsx, .xls), CSV, and Google Sheets loading.
Auto-detects and standardizes column mappings for inventory records.
"""
import io
import re
import requests
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple


class InventoryDataLoader:
    """
    Robust data loader with tolerant column header mapping.
    """
    SKU_ALIASES = ["sku", "item_code", "product_id", "item_id", "code", "part_number", "id"]
    NAME_ALIASES = ["name", "product_name", "item_name", "title", "description", "product"]
    CATEGORY_ALIASES = ["category", "dept", "department", "group", "class", "family", "type"]
    STOCK_ALIASES = ["current_stock", "stock", "on_hand", "quantity", "qty", "inventory", "stock_on_hand", "units_available"]
    LEAD_TIME_ALIASES = ["lead_time", "lead_time_days", "supplier_lead_time", "leadtime", "delivery_days", "lt_days"]
    COST_ALIASES = ["unit_cost", "cost", "unit_purchase_price", "purchase_cost", "cogs", "buy_price"]
    PRICE_ALIASES = ["unit_price", "price", "selling_price", "retail_price", "msrp", "sale_price"]

    @classmethod
    def load_from_bytes(cls, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Parses binary upload content (Excel or CSV).
        """
        filename_lower = filename.lower()
        if filename_lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            # Attempt CSV first, then Excel
            try:
                df = pd.read_csv(io.BytesIO(file_bytes))
            except Exception:
                df = pd.read_excel(io.BytesIO(file_bytes))
        return cls.process_dataframe(df)

    @classmethod
    def load_from_google_sheet(cls, sheet_url: str) -> List[Dict[str, Any]]:
        """
        Converts public Google Sheet link to direct CSV export and downloads it.
        Example: https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit -> export?format=csv
        """
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
        if not match:
            raise ValueError("Invalid Google Sheets URL format. Expected 'https://docs.google.com/spreadsheets/d/<SHEET_ID>/...'")

        sheet_id = match.group(1)
        csv_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        response = requests.get(csv_export_url, timeout=15)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch Google Sheet. Status code: {response.status_code}. Ensure the sheet is shared as 'Anyone with the link can view'.")
        df = pd.read_csv(io.StringIO(response.text))
        return cls.process_dataframe(df)

    @classmethod
    def _match_column(cls, df_columns: List[str], aliases: List[str]) -> str:
        """
        Finds the closest column matching given aliases.
        """
        # Exact clean match
        clean_map = {re.sub(r"[^a-zA-Z0-9]", "_", str(col)).strip("_").lower(): col for col in df_columns}
        for alias in aliases:
            if alias in clean_map:
                return clean_map[alias]
        # Partial match
        for alias in aliases:
            for clean_col, orig_col in clean_map.items():
                if alias in clean_col:
                    return orig_col
        return ""

    @classmethod
    def process_dataframe(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Standardizes raw DataFrame into structured inventory items.
        """
        if df.empty:
            return []

        df_cols = list(df.columns)
        sku_col = cls._match_column(df_cols, cls.SKU_ALIASES)
        name_col = cls._match_column(df_cols, cls.NAME_ALIASES)
        cat_col = cls._match_column(df_cols, cls.CATEGORY_ALIASES)
        stock_col = cls._match_column(df_cols, cls.STOCK_ALIASES)
        lead_time_col = cls._match_column(df_cols, cls.LEAD_TIME_ALIASES)
        cost_col = cls._match_column(df_cols, cls.COST_ALIASES)
        price_col = cls._match_column(df_cols, cls.PRICE_ALIASES)

        # Identify demand / sales history columns (e.g. Month_1, Month_2, Jan, Feb, Demand_t1, etc.)
        reserved_cols = {sku_col, name_col, cat_col, stock_col, lead_time_col, cost_col, price_col}
        demand_cols = []
        # Look for explicit demand/sales/month/week or numeric historical columns
        for col in df_cols:
            if col in reserved_cols or not col:
                continue
            col_str = str(col).lower()
            if any(k in col_str for k in ["demand", "sales", "month", "period", "m_", "wk", "qtr", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "202", "history"]):
                demand_cols.append(col)

        # If no explicit named demand columns found, treat any remaining numeric columns as history
        if not demand_cols:
            for col in df_cols:
                if col in reserved_cols or not col:
                    continue
                if pd.api.types.is_numeric_dtype(df[col]):
                    demand_cols.append(col)

        # Process each row
        records = []
        for idx, row in df.iterrows():
            sku = str(row[sku_col]).strip() if sku_col and pd.notna(row[sku_col]) else f"SKU-{idx+1:04d}"
            name = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else f"Item {sku}"
            category = str(row[cat_col]).strip() if cat_col and pd.notna(row[cat_col]) else "General"

            # Parse numeric attributes safely
            try:
                current_stock = float(row[stock_col]) if stock_col and pd.notna(row[stock_col]) else 0.0
            except (ValueError, TypeError):
                current_stock = 0.0

            try:
                lead_time = float(row[lead_time_col]) if lead_time_col and pd.notna(row[lead_time_col]) else 14.0
            except (ValueError, TypeError):
                lead_time = 14.0

            try:
                unit_cost = float(row[cost_col]) if cost_col and pd.notna(row[cost_col]) else 10.0
            except (ValueError, TypeError):
                unit_cost = 10.0

            try:
                unit_price = float(row[price_col]) if price_col and pd.notna(row[price_col]) else (unit_cost * 1.5)
            except (ValueError, TypeError):
                unit_price = unit_cost * 1.5

            # Extract demand history
            history = []
            if demand_cols:
                for d_col in demand_cols:
                    val = row[d_col]
                    try:
                        f_val = float(val)
                        if not np.isnan(f_val):
                            history.append(max(0.0, f_val))
                        else:
                            history.append(0.0)
                    except (ValueError, TypeError):
                        history.append(0.0)
            else:
                # If no history columns at all, create a default baseline from stock
                history = [max(10.0, current_stock * 0.5), max(12.0, current_stock * 0.55), max(15.0, current_stock * 0.6)]

            records.append({
                "sku": sku,
                "name": name,
                "category": category,
                "current_stock": max(0.0, current_stock),
                "lead_time_days": max(1.0, lead_time),
                "unit_cost": max(0.01, unit_cost),
                "unit_price": max(0.01, unit_price),
                "demand_history": history,
                "history_periods_count": len(history)
            })

        return records