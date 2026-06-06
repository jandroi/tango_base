"""
Serializers — consistent CSV/XLSX read and write, value normalization.
"""
import csv
import io
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def read_file(file_path: Path) -> pd.DataFrame:
    """Read an Excel or CSV file into a pandas DataFrame."""
    suffix = file_path.suffix.lower()
    if suffix == ".xlsx":
        df = pd.read_excel(file_path, engine="openpyxl", dtype=str)
    elif suffix == ".csv":
        df = pd.read_csv(file_path, encoding="utf-8", dtype=str)
    else:
        raise ValueError(f"Unsupported file format: {suffix!r}. Expected .xlsx or .csv")
    # Skip comment rows (first cell starts with #)
    if not df.empty:
        first_col = df.columns[0]
        df = df[~df[first_col].astype(str).str.startswith('#')]
        df = df.reset_index(drop=True)
    return df


def normalize_value(value: Any) -> Any:
    """
    Normalize a raw cell value:
    - Empty strings and pandas NA → None
    - Whitespace stripped from strings
    """
    if value is None:
        return None
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return None
    if isinstance(value, str):
        value = value.strip()
        if value == "" or value.lower() in ("nan", "none", "null"):
            return None
    return value


def coerce_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None


def normalize_dataframe(df: pd.DataFrame) -> list[dict]:
    """
    Convert a DataFrame to a list of dicts with normalized values.
    Strips whitespace, converts NA → None.
    """
    rows = []
    for _, row in df.iterrows():
        normalized = {col: normalize_value(val) for col, val in row.items()}
        rows.append(normalized)
    return rows


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

def write_csv(rows: list[dict], dest_path: Path) -> None:
    """Write a list of dicts to a CSV file."""
    if not rows:
        dest_path.write_text("", encoding="utf-8")
        return
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_excel(rows: list[dict], dest_path: Path) -> None:
    """Write a list of dicts to an XLSX file."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_excel(dest_path, index=False, engine="openpyxl")
