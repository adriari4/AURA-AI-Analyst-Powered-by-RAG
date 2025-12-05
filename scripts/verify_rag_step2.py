from backend.pipeline.thesis_pipeline import get_thesis_data

def verify_step2():
    print("--- Verifying Step 2: RAG Retrieval ---")
    
    company = "NVIDIA"
    print(f"Requesting thesis for: {company}")
    
    result = get_thesis_data(company)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    print("\n--- Generated Summary ---")
    print(result['summary'])
    
    print("\n--- Financial Data ---")
    print(result['financial_data'])
    
    print("\n--- Verification ---")
    if result['summary'] and "No investment thesis found" not in result['summary']:
        print("SUCCESS: Summary generated.")
    else:
        print("FAILURE: No summary generated.")

if __name__ == "__main__":
    verify_step2()
