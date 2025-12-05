import pandas as pd

try:
    # Load the specific sheet
    df = pd.read_excel("data/excel/Nvidia.xlsx", sheet_name="4.Valoracion", header=None)
    
    # Search for "EV/FCF" string
    found = False
    for r_idx, row in df.iterrows():
        for c_idx, value in row.items():
            if isinstance(value, str) and "EV/FCF" in value:
                print(f"Found 'EV/FCF' at Row: {r_idx+1}, Col: {c_idx+1} (Value: {value})")
                # Check neighbors for the actual value
                if c_idx + 1 < len(row):
                    print(f"  Neighbor (Right): {row[c_idx+1]}")
                found = True
    
    if not found:
        print("String 'EV/FCF' not found in sheet '4.Valoracion'.")
        
except Exception as e:
    print(f"Error: {e}")
