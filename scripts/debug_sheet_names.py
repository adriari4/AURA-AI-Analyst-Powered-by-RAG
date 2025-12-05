import pandas as pd

EXCEL_PATH = "data/excel/Nvidia.xlsx"

try:
    xl = pd.ExcelFile(EXCEL_PATH, engine='openpyxl')
    print("Sheet Names (repr):")
    for i, name in enumerate(xl.sheet_names):
        print(f"Index {i}: {repr(name)}")
except Exception as e:
    print(f"Error: {e}")
