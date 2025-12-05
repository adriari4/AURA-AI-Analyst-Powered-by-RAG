import pandas as pd
import openpyxl

EXCEL_PATH = "data/excel/Nvidia.xlsx"

try:
    xl = pd.ExcelFile(EXCEL_PATH, engine='openpyxl')
    print("Sheet Names and Indices:")
    for i, name in enumerate(xl.sheet_names):
        print(f"Index {i}: {name}")
        
    # Check visibility using openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH)
    print("\nSheet Visibility:")
    for sheet in wb.worksheets:
        state = sheet.sheet_state
        print(f"Sheet '{sheet.title}': {state}")
        
except Exception as e:
    print(f"Error: {e}")
