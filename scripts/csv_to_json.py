#!/usr/bin/env python3
"""Convert a CSV file into a column-oriented JSON file.

Output format:
{
  "columns": ["column1", "column2", ...],
  "column1": [value, value, ...],
  "column2": [value, value, ...]
}

Usage:
    python csv_to_json.py input.csv                 # writes input.json
    python csv_to_json.py input.csv -o output.json
    python csv_to_json.py input.csv -d ";"          # custom delimiter
"""

import argparse
import csv
import json
import sys
from pathlib import Path


def csv_to_column_json(csv_path, delimiter=","):
    """Read a CSV file and return a dict with a "columns" list plus one list per column."""
    # utf-8-sig strips the BOM that Excel adds to CSV files
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=delimiter)

        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("The CSV file is empty.")

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

        for line_num, row in enumerate(reader, start=2):
            if not row:  # skip blank lines
                continue
            if len(row) != len(header):
                print(
                    f"Warning: line {line_num} has {len(row)} values, "
                    f"expected {len(header)}. Padding/truncating.",
                    file=sys.stderr,
                )
                row = (row + [""] * len(header))[: len(header)]
            for name, value in zip(header, row):
                data[name].append(value)

    return data


def main():
    parser = argparse.ArgumentParser(
        description="Convert a CSV file into a column-oriented JSON file."
    )
    parser.add_argument("csv_file", help="Path to the input CSV file")
    parser.add_argument(
        "-o", "--output", help="Path to the output JSON file (default: same name as input, .json)"
    )
    parser.add_argument(
        "-d", "--delimiter", default=",", help="CSV delimiter (default: ',')"
    )
    parser.add_argument(
        "--indent", type=int, default=2, help="JSON indentation (default: 2)"
    )
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else Path(args.csv_file).with_suffix(".json")

    try:
        data = csv_to_column_json(args.csv_file, delimiter=args.delimiter)
    except (OSError, ValueError) as e:
        sys.exit(f"Error: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=args.indent, ensure_ascii=False)

    n_rows = len(data[data["columns"][0]]) if data["columns"] else 0
    print(f"Wrote {len(data['columns'])} columns and {n_rows} rows to {output_path}")


if __name__ == "__main__":
    main()