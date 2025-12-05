import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

INDEX_NAME = "youtube-rag-index"

def debug_retrieval(company_name: str):
    print(f"--- Debugging Retrieval for {company_name} ---")
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    
    # 1. Check without filter
    print("\n1. Searching WITHOUT filter:")
    results = vector_store.similarity_search(company_name, k=3)
    for i, doc in enumerate(results):
        print(f"Doc {i}: Source={doc.metadata.get('source')}, Type={doc.metadata.get('type')}")

    # 2. Check with PDF filter
    print("\n2. Searching WITH filter {'type': 'pdf'}:")
    try:
        results_filtered = vector_store.similarity_search(
            company_name, 
            k=3, 
            filter={"type": "pdf"}
        )
        if not results_filtered:
            print("NO DOCUMENTS FOUND with pdf filter.")
        for i, doc in enumerate(results_filtered):
            print(f"Doc {i}: Source={doc.metadata.get('source')}, Type={doc.metadata.get('type')}")
            print(f"Content Preview: {doc.page_content[:100]}...")
            
    except Exception as e:
        print(f"Error during filtered search: {e}")

if __name__ == "__main__":
    debug_retrieval("NVIDIA")
