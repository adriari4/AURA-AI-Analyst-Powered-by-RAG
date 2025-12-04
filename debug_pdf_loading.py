import os
from langchain_community.document_loaders import PDFPlumberLoader

PDF_PATH = "data/pdfs/INVESTEMENT_THESIS_NVIDIA.pdf"

print(f"Checking PDF at {PDF_PATH}...")
if not os.path.exists(PDF_PATH):
    print("PDF not found!")
else:
    try:
        loader = PDFPlumberLoader(PDF_PATH)
        docs = loader.load()
        print(f"Loaded {len(docs)} pages.")
        if len(docs) > 0:
            print(f"Page 0 content length: {len(docs[0].page_content)}")
            print(f"Page 0 content repr: {repr(docs[0].page_content[:100])}")
        else:
            print("PDF loaded but has 0 pages/content.")
    except Exception as e:
        print(f"Error loading PDF: {e}")
