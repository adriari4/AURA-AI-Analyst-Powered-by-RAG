import pandas as pd

try:
    # Load the specific sheet, header=None to use 0-based indexing for rows
    df = pd.read_excel("data/excel/Nvidia.xlsx", sheet_name="4.Valoracion", header=None)
    
    # Row 34 in Excel is index 33 in DataFrame
    target_row_idx = 33
    
    if target_row_idx < len(df):
        row_values = df.iloc[target_row_idx].tolist()
        print(f"Row {target_row_idx+1} (Excel Row 34) Values:")
        for i, val in enumerate(row_values):
            print(f"  Col {i+1}: {val}")
            
    # Also check surrounding rows just in case
    print("\nChecking surrounding rows for 194.62...")
    for r_idx in range(max(0, target_row_idx-5), min(len(df), target_row_idx+5)):
        row = df.iloc[r_idx]
        for c_idx, val in enumerate(row):
            if isinstance(val, (int, float)) and abs(val - 194.62) < 1.0: # Approximate match
                print(f"Found ~194.62 at Row {r_idx+1}, Col {c_idx+1}: {val}")

except Exception as e:
    print(f"Error: {e}")
