import os
import fitz  # PyMuPDF
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "youtube-rag-index"
PDF_PATH = os.path.join("data", "pdfs", "NVIDIA_Thesis_INVESTMENT.pdf")

def ingest_specific_pdf():
    print(f"--- Ingesting {PDF_PATH} ---")
    
    if not os.path.exists(PDF_PATH):
        print(f"ERROR: File not found at {PDF_PATH}")
        return

    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

    # Process PDF with direct text extraction (No OCR)
    docs = []
    try:
        doc = fitz.open(PDF_PATH)
        print(f"Processing {len(doc)} pages...")
        
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                docs.append(Document(
                    page_content=text, 
                    metadata={
                        "source": "NVIDIA_Thesis_INVESTMENT.pdf", 
                        "page": i, 
                        "type": "pdf"
                    }
                ))
                print(f"Page {i}: Extracted {len(text)} chars")
            else:
                print(f"Page {i}: No text found (or image only)")
                
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return

    if not docs:
        print("No text extracted from PDF.")
        return

    # Chunking
    print(f"\nSplitting {len(docs)} pages into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    splits = text_splitter.split_documents(docs)
    print(f"Created {len(splits)} chunks.")

    # Upsert to Pinecone
    print(f"Upserting to Pinecone index '{INDEX_NAME}'...")
    vector_store.add_documents(splits)
    print("--- Ingestion Complete ---")

if __name__ == "__main__":
    ingest_specific_pdf()
