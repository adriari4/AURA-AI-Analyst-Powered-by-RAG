import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

INDEX_NAME = "youtube-rag-index"

def check_new_file_indexed(company_name: str):
    print(f"--- Checking Index for {company_name} ---")
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    
    # Retrieve Chunks
    print("\nRetrieving Chunks (Filter: type='pdf')...")
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 20, # Get more chunks to see if new file is there
            "filter": {"type": "pdf"} 
        }
    )
    docs = retriever.invoke(company_name)
    
    found_new = False
    for i, doc in enumerate(docs):
        source = doc.metadata.get('source')
        if "NVIDIA_Thesis_INVESTMENT" in source:
            found_new = True
            print(f"\n[NEW FILE FOUND] Chunk {i}")
            print(f"Source: {source}")
            print(f"Content Preview: {doc.page_content[:500]}...") # Print more content
        else:
            pass # Skip printing old file chunks to reduce noise

    if found_new:
        print("\nSUCCESS: New file chunks found in index.")
    else:
        print("\nWAITING: New file chunks NOT found yet.")

if __name__ == "__main__":
    check_new_file_indexed("NVIDIA")
