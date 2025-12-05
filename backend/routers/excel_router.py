import pandas as pd
from fastapi import APIRouter, HTTPException, Response
import os

router = APIRouter(prefix="/excel", tags=["Excel"])

# Correct path based on file system check
EXCEL_PATH = "data/excel/Nvidia.xlsx"

@router.get("/sheets")
def get_sheets():
    """Returns a list of sheet names."""
    if not os.path.exists(EXCEL_PATH):
        raise HTTPException(status_code=404, detail="Excel file not found")
    
    try:
        xl = pd.ExcelFile(EXCEL_PATH, engine='openpyxl')
        return {"sheets": xl.sheet_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sheet/{name}")
def get_sheet(name: str):
    """Returns columns and rows for a specific sheet."""
    if not os.path.exists(EXCEL_PATH):
        raise HTTPException(status_code=404, detail="Excel file not found")
        
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=name, engine='openpyxl')
        
        # Handle Inf values (NaNs are handled by to_json)
        df = df.replace([float('inf'), float('-inf')], None)
        
        # Ensure columns match to_json keys (NaN -> "nan")
        columns = ["nan" if pd.isna(c) else c for c in df.columns.tolist()]
        # Use to_json to handle NaNs correctly as nulls
        rows_json = df.to_json(orient="records")
        
        # Manually construct the JSON response
        import json
        content = f'{{"columns": {json.dumps(columns)}, "rows": {rows_json}}}'
        
        return Response(content=content, media_type="application/json")
    except Exception as e:
        print(f"DEBUG: Error in get_sheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/iterate/{name}")
def iterate_sheet(name: str, value: float):
    """Multiplies numeric values in the sheet by the given value."""
    if not os.path.exists(EXCEL_PATH):
        raise HTTPException(status_code=404, detail="Excel file not found")
        
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=name, engine='openpyxl')
        
        # Iterate: Multiply numeric columns by value
        # Select only numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        df[numeric_cols] = df[numeric_cols] * value
        
        # Handle Inf values (NaNs are handled by to_json)
        df = df.replace([float('inf'), float('-inf')], None)
        
        # Ensure columns match to_json keys (NaN -> "nan")
        columns = ["nan" if pd.isna(c) else c for c in df.columns.tolist()]
        # Use to_json to handle NaNs correctly as nulls
        rows_json = df.to_json(orient="records")
        
        # Manually construct the JSON response
        import json
        content = f'{{"columns": {json.dumps(columns)}, "rows": {rows_json}}}'
        
        return Response(content=content, media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
