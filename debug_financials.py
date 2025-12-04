from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

load_dotenv()

INDEX_NAME = "youtube-rag-index"

def inspect_financials():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    
    terms = ["Revenue", "Ingresos", "Ventas", "EPS", "Beneficio", "Margin", "Margen", "Valuation", "Valoración"]
    
    print("--- Searching for Financial Terms ---")
    for term in terms:
        print(f"\nSearching for: {term}")
        results = vector_store.similarity_search(
            term, 
            k=3, 
            filter={"source": "NVIDIA_Thesis_INVESTMENT.pdf"}
        )
        
        for i, doc in enumerate(results):
            print(f"  Match {i+1}: {doc.page_content[:200]}...")

if __name__ == "__main__":
    inspect_financials()
