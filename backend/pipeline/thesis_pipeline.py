import os
import json
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()

import yfinance as yf

INDEX_NAME = "youtube-rag-index"

def fetch_yfinance_data(ticker: str):
    """
    Fetches financial data from Yahoo Finance as a fallback.
    """
    try:
        stock = yf.Ticker(ticker)
        
        # 1. Revenue (Income Statement)
        financials = stock.financials
        revenue = {"years": [], "values": []}
        if "Total Revenue" in financials.index:
            rev_row = financials.loc["Total Revenue"]
            # Sort by date ascending
            rev_row = rev_row.sort_index()
            # Take last 3 years
            recent = rev_row.tail(3)
            revenue["years"] = [d.strftime("%Y") for d in recent.index]
            revenue["values"] = [float(v) for v in recent.values]
        
        # 2. Net Income
        net_income = {"years": [], "values": []}
        if "Net Income" in financials.index:
            ni_row = financials.loc["Net Income"]
            ni_row = ni_row.sort_index()
            recent = ni_row.tail(3)
            net_income["years"] = [d.strftime("%Y") for d in recent.index]
            net_income["values"] = [float(v) for v in recent.values]

        # 3. Valuation
        info = stock.info
        valuation = {
            "pe_ratio": info.get("trailingPE"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "market_cap": f"{info.get('marketCap', 0) / 1e12:.2f}T" if info.get("marketCap") else None,
            "fcf_yield": None # yfinance doesn't give this directly easily, skipping for now
        }
        
        return {
            "revenue": revenue,
            "net_income": net_income,
            "valuation": valuation
        }
    except Exception as e:
        print(f"Error fetching Yahoo Finance data: {e}")
        return None

def get_thesis_data(company_name: str):
    """
    Retrieves PDF data for a company, summarizes the thesis, 
    and extracts financial data for graphing.
    """
    
    # 1. Setup Vector Store with Strict Filter
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    
    # Strict Retrieval for NVIDIA
    search_kwargs = {"k": 6}
    if company_name.upper() == "NVIDIA":
        search_kwargs["filter"] = {"source": "NVIDIA_Thesis_INVESTMENT.pdf"}

    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # 2. Define Prompts
    
    # Thesis Summary Prompt
    summary_template = """You are an expert investment analyst. 
    You are provided with text extracted from PDF documents about {question}. 
    
    Your goal is to construct the best possible Investment Thesis summary based ONLY on the provided context.
    
    CRITICAL INSTRUCTION: 
    - Use ONLY the information provided in the Context below.
    - Do NOT use any external knowledge, training data, or assumptions.
    - If the information is not in the Context, do not invent it.
    
    Focus on extracting:
    - Key Growth Drivers
    - Competitive Moats
    - Risks
    
    Context:
    {context}
    
    Company: {question}
    
    Summary:"""
    
    summary_prompt = PromptTemplate(
        template=summary_template,
        input_variables=["context", "question"]
    )
    
    summary_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": summary_prompt}
    )
    
    # Financial Data Extraction Prompt
    data_template = """You are a data extraction assistant.
    Based ONLY on the provided PDF documents for {question}, extract the following financial metrics if available.
    The text is likely in Spanish. Look for terms like "Ventas", "Ingresos", "Beneficio", "Margen", "Precio", "Capitalización".
    
    Return the data in strict JSON format. Do not add markdown formatting. Respond in English.
    
    JSON Structure:
    {{
        "revenue": {{"years": ["2021", "2022", "2023"], "values": [100, 120, 150]}},
        "net_income": {{"years": ["2021", "2022", "2023"], "values": [10, 15, 20]}},
        "valuation": {{
            "pe_ratio": 25.5,
            "ps_ratio": 10.2,
            "fcf_yield": 0.03,
            "market_cap": "1.5T"
        }}
    }}
    
    If you find a table or list of years/values, extract them. 
    If you only find a single current value (e.g. "Precio actual"), put it in the valuation object or create a single-point array.
    If data is missing, use null.
    
    Context:
    {context}
    
    Company: {question}
    
    JSON:"""
    
    data_prompt = PromptTemplate(
        template=data_template,
        input_variables=["context", "question"]
    )
    
    from langchain.chains.question_answering import load_qa_chain
    data_chain = load_qa_chain(
        llm=llm,
        chain_type="stuff",
        prompt=data_prompt
    )
    
    # 3. Execute Chains
    try:
        # Summary Generation (uses standard retriever)
        summary = summary_chain.run(company_name)
        
        # Financial Data Extraction (uses TARGETED retrieval)
        # We search specifically for financial terms to ensure we get the right chunks
        financial_docs = vector_store.similarity_search(
            "Ingresos Ventas Revenue Financials Valuation Precio", 
            k=5, 
            filter={"source": "NVIDIA_Thesis_INVESTMENT.pdf"}
        )
        
        # Run the data chain with the targeted docs
        raw_json = data_chain.run(input_documents=financial_docs, question=company_name)
        
        # Clean JSON string if needed (sometimes LLMs add ```json ... ```)
        raw_json = raw_json.replace("```json", "").replace("```", "").strip()
        financial_data = json.loads(raw_json)
        
        # --- FALLBACK LOGIC ---
        # Check if revenue data is missing or empty
        rev_missing = (
            not financial_data.get("revenue") or 
            not financial_data["revenue"].get("years") or 
            len(financial_data["revenue"]["years"]) == 0
        )
        
        if rev_missing and company_name.upper() == "NVIDIA":
            print("Missing PDF financial data. Fetching from Yahoo Finance...")
            yf_data = fetch_yfinance_data("NVDA")
            if yf_data:
                # Merge: prioritize YF for missing parts
                if rev_missing:
                    financial_data["revenue"] = yf_data["revenue"]
                    financial_data["net_income"] = yf_data["net_income"]
                
                # Merge valuation if missing
                val = financial_data.get("valuation", {})
                yf_val = yf_data["valuation"]
                
                if not val.get("pe_ratio"): val["pe_ratio"] = yf_val["pe_ratio"]
                if not val.get("market_cap"): val["market_cap"] = yf_val["market_cap"]
                if not val.get("ps_ratio"): val["ps_ratio"] = yf_val["ps_ratio"]
                
                financial_data["valuation"] = val
        # ----------------------
        
        return {
            "company": company_name,
            "summary": summary,
            "financial_data": financial_data
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "company": company_name
        }
