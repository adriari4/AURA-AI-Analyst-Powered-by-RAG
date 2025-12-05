import os
import sys
import subprocess
from dotenv import load_dotenv
from ingest_data import ingest_all_data

# Load environment variables
load_dotenv()

def main():
    print("--- Starting System ---")
    
    # 1. Run Ingestion (Background)
    # import threading
    # def run_ingestion():
    #     print("--- Running Automatic Ingestion (Background) ---")
    #     try:
    #         ingest_all_data()
    #     except Exception as e:
    #         print(f"Ingestion failed: {e}")

    # ingestion_thread = threading.Thread(target=run_ingestion, daemon=True)
    # ingestion_thread.start()
    
    # 2. Start Web UI
    print("--- Starting Web UI (FastAPI) ---")
    # Run the backend API as a module to support relative imports
    subprocess.run([sys.executable, "-m", "backend.api"])

if __name__ == "__main__":
    main()
