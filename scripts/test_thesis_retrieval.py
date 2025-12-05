import sys
import os
# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.pipeline.thesis_pipeline import get_thesis_data

print("Testing Thesis Retrieval for NVIDIA...")
try:
    result = get_thesis_data("NVIDIA")
    print("Result:")
    print(result)
except Exception as e:
    print(f"Error: {e}")
