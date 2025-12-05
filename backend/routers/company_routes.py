from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import glob
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import yfinance as yf

load_dotenv()

router = APIRouter(prefix="/companies", tags=["Companies"])

# Configuration
PDF_DIR = "data/pdfs"
INDEX_NAME = "youtube-rag-index"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Expanded Ticker Mapping
TICKER_MAPPING = {
    "NVIDIA": "NVDA",
    "NVIDIA_Thesis_INVESTMENT": "NVDA",
    "ALPHABET": "GOOGL",
    "Alphabet": "GOOGL",
    "Google": "GOOGL",
    "ASML": "ASML",
    "Amazon": "AMZN",
    "FERRARI": "RACE",
    "Ferrari": "RACE",
    "META": "META",
    "Microsoft": "MSFT",
    "TSMC": "TSM",
    "TSMC ": "TSM", # Handle potential trailing space
    "Apple": "AAPL",
    "Netflix": "NFLX",
    "Tesla": "TSLA"
}

# Valuation Multiples (EV/FCF) - Can be adjusted per industry
VALUATION_MULTIPLES = {
    "NVDA": 55,
    "RACE": 40,  # Luxury/High margin
    "ASML": 35,  # Semi monopoly
    "TSM": 20,   # Geopolitical risk discount
    "GOOGL": 25,
    "MSFT": 30,
    "AMZN": 30,
    "META": 25,
    "AAPL": 28,
    "NFLX": 30
}

class CompanyListResponse(BaseModel):
    companies: list[str]

class ThesisResponse(BaseModel):
    summary: str

class ChartResponse(BaseModel):
    title: str
    years: list[str]
    intrinsic_values: list[float]
    current_price: list[float]

# --- Helper Functions ---

def get_pdf_path(company_name: str):
    # Try exact match first
    path = os.path.join(PDF_DIR, f"{company_name}.pdf")
    if os.path.exists(path):
        return path
    
    # Try finding any pdf that contains the company name
    for file in os.listdir(PDF_DIR):
        if company_name.lower() in file.lower() and file.endswith(".pdf"):
            return os.path.join(PDF_DIR, file)
            
    return None

def load_pdf_text(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def get_ticker(company_name):
    # Clean up name
    clean_name = company_name.replace("_Thesis_INVESTMENT", "").strip()
    # Try exact match
    if clean_name in TICKER_MAPPING:
        return TICKER_MAPPING[clean_name]
    # Try case insensitive
    for k, v in TICKER_MAPPING.items():
        if k.lower() == clean_name.lower():
            return v
    return None

# --- Endpoints ---

@router.get("", response_model=CompanyListResponse)
def list_companies():
    """Scans the data/pdfs directory and returns available companies."""
    if not os.path.exists(PDF_DIR):
        return {"companies": []}
    
    files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    
    # Extract clean names. 
    companies = [os.path.splitext(os.path.basename(f))[0] for f in files]
    return {"companies": sorted(companies)}

@router.get("/{company_name}/summary", response_model=ThesisResponse)
def get_company_summary(company_name: str):
    """Generates an executive summary for the given company using RAG."""
    pdf_path = get_pdf_path(company_name)
    if not pdf_path:
        raise HTTPException(status_code=404, detail=f"PDF for {company_name} not found.")

    try:
        # 1. Load and Embed
        text = load_pdf_text(pdf_path)
        
        # Ingest into Pinecone (Idempotent-ish for this session)
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(text)
        PineconeVectorStore.from_texts(
            texts=chunks, 
            embedding=embeddings, 
            index_name=INDEX_NAME
        )

        # 2. Query
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=INDEX_NAME,
            embedding=embeddings
        )
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        qa = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

        prompt = f"""
        Act as a senior investment analyst. Provide a detailed executive summary of {company_name} based ONLY on the provided context.
        Structure the response exactly into these three sections with HTML tags for styling:

        <div class='sum-wrapper'>
            <h3 class='sum-header'>1. Business Model</h3>
            <p>[Explain what the company does, its core growth engine, and revenue drivers]</p>
            <h4 class='sum-subheader'>Core Markets</h4>
            <ul class='sum-list'><li>[Item]</li></ul>
            <h4 class='sum-subheader'>Revenue Drivers</h4>
            <ul class='sum-list'><li>[Item]</li></ul>
            <h4 class='sum-subheader'>Competitive Advantages</h4>
            <ul class='sum-list'><li>[Item]</li></ul>

            <hr class='sum-divider' />

            <h3 class='sum-header'>2. Risks</h3>
            <h4 class='sum-subheader'>Operational Risks</h4>
            <ul class='sum-list'><li>[Item]</li></ul>
            <h4 class='sum-subheader'>Market Risks</h4>
            <ul class='sum-list'><li>[Item]</li></ul>

            <h3 class='sum-header'>3. Valuation Commentary</h3>
            <p>[Provide a brief qualitative commentary on the valuation based on the text. Do not invent numbers if not present.]</p>
        </div>

        Do not use markdown code blocks. Return raw HTML string.
        """
        summary = qa.run(prompt)
        
        # Clean up if LLM wraps in markdown
        summary = summary.replace("```html", "").replace("```", "").strip()
        
        return {"summary": summary}

    except Exception as e:
        print(f"Error generating summary for {company_name}: {e}")
        # Fallback for Quota/API errors
        if "insufficient_quota" in str(e) or "429" in str(e):
             return {"summary": f"<div class='sum-wrapper'><h3 class='sum-header'>Analysis Unavailable</h3><p>API Quota Exceeded. Please check OpenAI billing.</p></div>"}
            
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_name}/chart", response_model=ChartResponse)
def get_company_chart(company_name: str):
    """Generates chart data for the company using EV/FCF model."""
    ticker_symbol = get_ticker(company_name)
    
    # Default/Fallback Data
    years = ["2027e", "2028e", "2029e", "2030e", "2031e"]
    fallback_data = {
        "title": f"Intrinsic Value Projection - {company_name}",
        "years": years,
        "intrinsic_values": [0, 0, 0, 0, 0],
        "current_price": [0, 0, 0, 0, 0]
    }

    if not ticker_symbol:
        print(f"No ticker found for {company_name}")
        return fallback_data

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # Fetch Financials
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        fcf = info.get("freeCashflow")
        shares = info.get("sharesOutstanding")
        
        # Fallback if FCF missing (try to estimate from operating cash flow - capex if available, or just fail gracefully)
        if fcf is None:
             # Try calculating: OCF - Capex
             ocf = info.get("operatingCashflow")
             capex = info.get("capitalExpenditures") # usually negative
             if ocf is not None and capex is not None:
                 fcf = ocf + capex # + because capex is negative
        
        if current_price == 0 or fcf is None or shares is None or shares == 0:
            print(f"Missing financial data for {ticker_symbol}: Price={current_price}, FCF={fcf}, Shares={shares}")
            return fallback_data

        # Valuation Logic
        multiple = VALUATION_MULTIPLES.get(ticker_symbol, 25) # Default to 25x if not specified
        
        fcf_per_share = fcf / shares
        intrinsic_value = fcf_per_share * multiple
        
        # Sanity check: if intrinsic value is negative (negative FCF), use current price as base but show flat or decline?
        # For this exercise, let's floor it at 0 or use price if FCF is weird.
        if intrinsic_value < 0:
            intrinsic_value = 0 # Or handle differently
        
        # Projection Logic (2027e-2031e)
        # We start projecting from the *calculated intrinsic value* today (2025)
        # 2027 is Year 2.
        
        intrinsic_projections = []
        price_projections = []

        # Growth Rate: 15% standard as requested
        growth_rate = 0.15

        # Base year (2025) -> Year 1 (2026) -> Year 2 (2027)
        # We want to show 2027-2031
        
        # Calculate future values
        for i in range(2, 7): # Years 2 to 6
            proj_val = intrinsic_value * ((1 + growth_rate) ** i)
            intrinsic_projections.append(round(proj_val, 2))
            price_projections.append(round(current_price, 2))

        return {
            "title": f"Intrinsic Value Projection - {company_name} ({ticker_symbol})",
            "years": years,
            "intrinsic_values": intrinsic_projections,
            "current_price": price_projections
        }

    except Exception as e:
        print(f"Error generating chart for {company_name}: {e}")
        return fallback_data
