import os
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path so we can import backend modules
sys.path.append(os.getcwd())

load_dotenv()

from backend.routers.company_routes import get_company_summary, get_pdf_path

# Test with a company that likely exists
COMPANY_TO_TEST = "Amazon" 

print(f"DEBUG: Testing summary generation for {COMPANY_TO_TEST}")

# 1. Check PDF Path
pdf_path = get_pdf_path(COMPANY_TO_TEST)
print(f"DEBUG: Resolved PDF Path: {pdf_path}")

if not pdf_path:
    print("ERROR: PDF not found via get_pdf_path")
    sys.exit(1)

# 2. Try generating summary
try:
    print("DEBUG: Calling get_company_summary...")
    # Note: get_company_summary is an async function or regular? 
    # In the router it's defined as 'def', so it's synchronous (unless it uses await inside which it doesn't seem to based on previous view).
    # Let's check the file content again if needed. 
    # It uses qa.run(prompt) which is blocking in LangChain usually.
    
    result = get_company_summary(COMPANY_TO_TEST)
    print("SUCCESS: Summary generated.")
    print(str(result)[:500] + "...") # Print first 500 chars
except Exception as e:
    print(f"ERROR: Exception occurred: {e}")
    import traceback
    traceback.print_exc()
