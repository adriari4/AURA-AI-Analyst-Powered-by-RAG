import os
import glob

PDF_DIR = "data/pdfs"

print(f"DEBUG: CWD is {os.getcwd()}")
print(f"DEBUG: Looking for PDFs in {os.path.abspath(PDF_DIR)}")

if not os.path.exists(PDF_DIR):
    print("DEBUG: PDF_DIR does not exist")
else:
    files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    print(f"DEBUG: Found files: {files}")
    companies = [os.path.splitext(os.path.basename(f))[0] for f in files]
    print(f"DEBUG: Companies: {companies}")
