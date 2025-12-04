import os
import json
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()

INDEX_NAME = "youtube-rag-index"

def get_nvidia_chart():
    return {
        "title": "Intrinsic Value Projection (2027e–2031e)",
        "years": ["2027e", "2028e", "2029e", "2030e", "2031e"],
        "intrinsic_values": [194.69, 265.88, 266.37, 314.81, 364.83],
        "current_price": [190, 190, 190, 190, 190]   # Your benchmark dotted line
    }

def get_thesis_data(company_name: str):
    """
    Retrieves PDF data for a company, summarizes the thesis, 
    and extracts financial data for graphing.
    """
    
    # 1. Setup Vector Store with PDF Filter
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    
    # Filter for PDFs only - Restored as per user request to see PDF info
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 10,
            "filter": {"type": "pdf"} 
        }
    )
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # 2. Define Prompts
    
    # Thesis Summary Prompt
    summary_template = """You are an expert investment analyst. 
    Based ONLY on the provided PDF documents, summarize the investment thesis for {question}.
    Focus on:
    - Key Growth Drivers
    - Competitive Moats
    - Risks
    
    If the information is not in the PDFs, say "No investment thesis found in uploaded PDFs."
    
    Respond in English.
    
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
    Return the data in strict JSON format. Do not add markdown formatting. Respond in English.
    
    JSON Structure:
    {{
        "revenue": {{"years": [2021, 2022, 2023], "values": [100, 120, 150]}},
        "net_income": {{"years": [2021, 2022, 2023], "values": [10, 15, 20]}},
        "valuation": {{
            "pe_ratio": 25.5,
            "ps_ratio": 10.2,
            "fcf_yield": 0.03
        }}
    }}
    
    If data is missing for a specific field, use null or empty lists. 
    Try to find at least 3 years of historical data for trends.
    
    Context:
    {context}
    
    Company: {question}
    
    JSON:"""
    
    data_prompt = PromptTemplate(
        template=data_template,
        input_variables=["context", "question"]
    )
    
    data_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": data_prompt}
    )
    
    # 3. Execute Chains
    try:
        # Check for pre-processed JSON first
        # Use absolute path to ensure we find the file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, "data", "thesis_data", f"{company_name}.json")
        
        print(f"Current CWD: {os.getcwd()}")
        print(f"Base Dir: {base_dir}")
        print(f"Checking for JSON at: {json_path}")
        print(f"File exists? {os.path.exists(json_path)}")
        
        if os.path.exists(json_path):
            print("JSON found!")
            with open(json_path, "r", encoding="utf-8") as f:
                pre_processed_data = json.load(f)
                
            summary = pre_processed_data.get("summary", "")
            
            # Extract graphics for frontend
            graphics = []
            for page in pre_processed_data.get("pages", []):
                page_num = page.get("page_number")
                for g in page.get("graphics", []):
                    graphics.append({
                        "page": page_num,
                        "type": g.get("type"),
                        "caption": g.get("caption"),
                        "content": g.get("content")
                    })
            
            # If we have static data, skip the expensive RAG for financial data for now to ensure speed/reliability
            # or we could try to parse it from the JSON if we had it. 
            # For now, return empty/mock financial data so the frontend doesn't break.
            financial_data = {
                "revenue": {"years": [], "values": []},
                "net_income": {"years": [], "values": []},
                "valuation": {}
            }
            
            return {
                "company": company_name,
                "summary": summary,
                "financial_data": financial_data,
                "graphics": graphics
            }

        else:
            # Fallback to RAG
            summary = summary_chain.run(company_name)
            graphics = []

            raw_json = data_chain.run(company_name)
            
            # Clean JSON string if needed (sometimes LLMs add ```json ... ```)
            raw_json = raw_json.replace("```json", "").replace("```", "").strip()
            financial_data = json.loads(raw_json)
            
            return {
                "company": company_name,
                "summary": summary,
                "financial_data": financial_data,
                "graphics": graphics
            }
        
    except Exception as e:
        return {
            "error": str(e),
            "company": company_name
        }
