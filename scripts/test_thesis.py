from backend.thesis_logic import get_thesis_data

print("Testing Thesis Logic for NVIDIA...")
try:
    result = get_thesis_data("NVIDIA")
    print("Success!")
    print("Summary Length:", len(result.get("summary", "")))
    print("Financial Data Keys:", result.get("financial_data", {}).keys())
except Exception as e:
    print("Error:", e)
