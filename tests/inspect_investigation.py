"""Inspect investigation Excel file."""
from openpyxl import load_workbook
import sys

wb = load_workbook(sys.argv[1])
ws = wb.active

print("Investigation Excel Content:")
print("=" * 80)
for i, row in enumerate(ws.iter_rows(max_row=50, values_only=True), 1):
    print(f"Row {i:2d}: {row}")
