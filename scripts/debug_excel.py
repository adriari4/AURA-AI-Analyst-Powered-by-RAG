import pandas as pd
import os

EXCEL_PATH = "data/excel/Nvidia.xlsx"

print(f"Current working directory: {os.getcwd()}")
print(f"Checking if file exists at {EXCEL_PATH}: {os.path.exists(EXCEL_PATH)}")

try:
    df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
    print("Successfully read Excel file.")
    print(df.head())
except Exception as e:
    print(f"Error reading Excel file: {e}")
