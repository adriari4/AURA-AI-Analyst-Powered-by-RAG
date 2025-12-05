import os
import sys
from dotenv import load_dotenv

# Add root to path so we can import backend
sys.path.append(os.getcwd())

from backend.pipeline.thesis_pipeline import get_thesis_data

load_dotenv()

def debug_real_pipeline(company_name: str):
    print(f"--- Debugging Real Pipeline for {company_name} ---")
    try:
        result = get_thesis_data(company_name)
        print("\n--- Result ---")
        print(f"Company: {result.get('company')}")
        print(f"Summary: {result.get('summary')}")
        print(f"Financial Data: {result.get('financial_data')}")
        
        if result.get('error'):
            print(f"ERROR: {result.get('error')}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_real_pipeline("NVIDIA")
