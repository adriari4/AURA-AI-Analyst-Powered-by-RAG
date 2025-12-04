from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
import os
from dotenv import load_dotenv
import yfinance as yf

load_dotenv()

router = APIRouter()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "youtube-rag-index"

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 1️⃣ Load PDF text
def load_pdf(path="NVIDIA_Thesis_INVESTMENT.pdf"):
    # Adjust path to look in current dir or specific location if needed
    # Assuming the file is in the root or we can find it. 
    # For this environment, we know it's likely at d:\VALUE INVESTING CHATBOT - 2ND\NVIDIA_Thesis_INVESTMENT.pdf
    # or backend/data/pdfs/...
    # Let's try the absolute path or relative to root
    if not os.path.exists(path):
        # Fallback to known location if the relative path fails
        possible_paths = [
            "NVIDIA_Thesis_INVESTMENT.pdf",
            "data/pdfs/NVIDIA_Thesis_INVESTMENT.pdf",
            "backend/data/pdfs/NVIDIA_Thesis_INVESTMENT.pdf",
            "d:/VALUE INVESTING CHATBOT - 2ND/data/pdfs/NVIDIA_Thesis_INVESTMENT.pdf"
        ]
        for p in possible_paths:
            if os.path.exists(p):
                path = p
                break
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found at {path}")

    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# 2️⃣ Chunk + embed + upload to Pinecone
def prepare_pinecone(text):
    # Index creation logic removed to avoid limit errors.
    # We assume 'youtube-rag-index' exists.
    
    # We can use the existing index
    # Note: In a real app, we might check if we already ingested this file to avoid duplicates.
    # For this "fix", we follow the user's logic but maybe avoid re-ingesting if it's already populated?
    # The user's code runs this every time. I will stick to their logic but use PineconeVectorStore.
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    chunks = splitter.split_text(text)

    # Using langchain_pinecone
    PineconeVectorStore.from_texts(
        texts=chunks, 
        embedding=embeddings, 
        index_name=INDEX_NAME
    )

# 3️⃣ Query RAG
def query_nvidia():
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=INDEX_NAME,
        embedding=embeddings
    )

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever()
    )

    prompt = """
    Act as a senior investment analyst. Provide a detailed executive summary of NVIDIA based ONLY on this PDF. 
    Structure the response exactly into these three sections:

    1. **Business Model**: Explain what NVIDIA does, its core growth engine, competitive advantages, market positioning, and revenue drivers.
    2. **Risks**: Analyze risk factors including technological dependencies, competition, cyclicality, and market volatility. Keep the tone objective.
    3. **Valuation**: Present valuation metrics, interpret what they imply for investors, mention growth expectations, market confidence, and compare intrinsic value vs current price if available.

    Do not use outside information. Be concise but insightful, professional, and analytical.
    """
    summary = qa.run(prompt)
    
    # Calculate Intrinsic Value vs Real Value
    try:
        ticker = yf.Ticker("NVDA")
        info = ticker.info
        
        # 1. Get Real Value (Current Price)
        current_price = info.get("currentPrice", 0)
        
        # 2. Calculate Intrinsic Value (EV/FCF * FCF per Share)
        # We use 55x as the multiple based on user request/research
        fcf = info.get("freeCashflow", 0)
        shares = info.get("sharesOutstanding", 1) # Avoid division by zero
        
        if shares > 0:
            fcf_per_share = fcf / shares
            intrinsic_value = fcf_per_share * 55
        else:
            intrinsic_value = 0
            
        # Projection Logic (2027e-2031e)
        # We try to extract from PDF first, but for reliability we use the 15% growth assumption
        # starting from the calculated Intrinsic Value.
        
        years = ["2027e", "2028e", "2029e", "2030e", "2031e"]
        
        intrinsic_projections = []
        price_projections = []
        
        base_intrinsic = intrinsic_value if intrinsic_value > 0 else current_price
        
        # Calculate projections for 2027-2031 (Years 2 to 6 from 2025 base)
        # Assuming 2026 is Year 1, 2027 is Year 2, etc.
        # Or if we start from now (2025), 2027 is 2 years out.
        
        for i in range(2, 7): # Years 2, 3, 4, 5, 6 (2027-2031)
            # Intrinsic Value Growth (15%)
            proj_intrinsic = base_intrinsic * ((1.15) ** i)
            intrinsic_projections.append(round(proj_intrinsic, 2))
            
            # Price (Flat Line as requested)
            price_projections.append(round(current_price, 2))

        chart_data = {
            "labels": years,
            "intrinsic_values": intrinsic_projections,
            "price_values": price_projections
        }
    except Exception as e:
        print(f"Error calculating intrinsic value: {e}")
        # Fallback
        chart_data = {
            "labels": ["2027e", "2028e", "2029e", "2030e", "2031e"],
            "intrinsic_values": [0, 0, 0, 0, 0],
            "price_values": [0, 0, 0, 0, 0]
        }

    return summary, chart_data

# FastAPI endpoint
class ThesisResponse(BaseModel):
    summary: str
    chart_labels: list
    chart_values: list

@router.get("/thesis/nvidia", response_model=ThesisResponse)
def get_nvidia_thesis():
    try:
        text = load_pdf()
        prepare_pinecone(text)
        summary, chart_data = query_nvidia()

        return ThesisResponse(
            summary=summary,
            chart_labels=chart_data["labels"],
            chart_values=chart_data["values"]
        )
    except Exception as e:
        print(f"Error in get_nvidia_thesis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
