#!/usr/bin/env python3
"""Convert a sheet of an Excel file (.xlsx / .xlsm) into a column-oriented JSON file.

Output format:
{
  "columns": ["column1", "column2", ...],
  "column1": [value, value, ...],
  "column2": [value, value, ...]
}

Requires: pip install openpyxl

Usage:
    python excel_to_json.py input.xlsx                    # first sheet -> input.json
    python excel_to_json.py input.xlsx -s "Sales"         # a specific sheet
    python excel_to_json.py input.xlsx -o output.json
"""

import argparse
import json
import sys
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    sys.exit("This script needs openpyxl. Install it with: pip install openpyxl")


def _json_default(value):
    """Serialize the cell types JSON can't handle natively."""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def excel_to_column_json(xlsx_path, sheet=None):
    """Read one sheet and return a dict with a "columns" list plus one list per column."""
    # data_only=True returns the cached result of formulas instead of the formula text
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    try:
        if sheet is None:
            ws = wb.worksheets[0]
        elif sheet in wb.sheetnames:
            ws = wb[sheet]
        else:
            raise ValueError(f'Sheet "{sheet}" not found. Available sheets: {wb.sheetnames}')

        rows = ws.iter_rows(values_only=True)

        # The first non-empty row is the header
        header = None
        for row in rows:
            if any(cell is not None for cell in row):
                header = list(row)
                break
        if header is None:
            raise ValueError("The sheet is empty.")

        # Excel often reports extra empty columns on the right; drop them
        while header and header[-1] is None:
            header.pop()
        if any(h is None for h in header):
            raise ValueError("The header row has a blank cell between column names.")
        header = [str(h) for h in header]

        if "columns" in header:
            raise ValueError(
                'A column is named "columns", which clashes with the reserved '
                '"columns" key in the output. Please rename it.'
            )
        duplicates = sorted({name for name in header if header.count(name) > 1})
        if duplicates:
            raise ValueError(f"Duplicate column names found: {duplicates}")

        data = {"columns": header}
        for name in header:
            data[name] = []

        for row in rows:
            values = list(row[: len(header)])
            values += [None] * (len(header) - len(values))
            if all(v is None for v in values):  # skip blank rows
                continue
            for name, value in zip(header, values):
                data[name].append(value)
    finally:
        wb.close()

    return data


def main():
    parser = argparse.ArgumentParser(
        description="Convert an Excel sheet into a column-oriented JSON file."
    )
    parser.add_argument("excel_file", help="Path to the input .xlsx/.xlsm file")
    parser.add_argument("-s", "--sheet", help="Sheet name (default: first sheet)")
    parser.add_argument(
        "-o", "--output", help="Path to the output JSON file (default: same name as input, .json)"
    )
    parser.add_argument(
        "--indent", type=int, default=2, help="JSON indentation (default: 2)"
    )
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else Path(args.excel_file).with_suffix(".json")

    try:
        data = excel_to_column_json(args.excel_file, sheet=args.sheet)
    except (OSError, ValueError) as e:
        sys.exit(f"Error: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=args.indent, ensure_ascii=False, default=_json_default)

    n_rows = len(data[data["columns"][0]])
    print(f"Wrote {len(data['columns'])} columns and {n_rows} rows to {output_path}")


if __name__ == "__main__":
    main()