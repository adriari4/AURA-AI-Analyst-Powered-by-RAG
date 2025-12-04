from fastapi import APIRouter
from pydantic import BaseModel
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "youtube-rag-index" # Using the existing index where data is likely stored
embeddings = OpenAIEmbeddings()

class SummaryResponse(BaseModel):
    executive_summary: str

from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz # PyMuPDF

# Helper to load PDF
def load_pdf(path="NVIDIA_Thesis_INVESTMENT.pdf"):
    if not os.path.exists(path):
        # Fallback paths
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

@router.get("/thesis/nvidia/summary", response_model=SummaryResponse)
def get_nvidia_summary():
    
    html_content = """
    <div class='sum-wrapper'>

        <h3 class='sum-header'>1. Business Model</h3>
        <p>NVIDIA is a global leader in accelerated computing, founded in 1993 by Jensen Huang and two engineers from Sun Microsystems and IBM. The company builds high-performance GPUs, AI accelerators, and advanced software platforms powering applications across gaming, data centers, robotics, and scientific computing.</p>

        <h4 class='sum-subheader'>Core Markets</h4>
        <ul class='sum-list'>
            <li><strong>Gaming:</strong> NVIDIA’s flagship GeForce ecosystem with strong brand loyalty and market dominance.</li>
            <li><strong>Data Centers:</strong> NVIDIA’s fastest-growing segment, driven by explosive global AI adoption.</li>
            <li><strong>Automotive & Robotics:</strong> AI compute platforms for autonomous driving, robotics, and simulation.</li>
            <li><strong>Professional Visualization:</strong> GPUs for engineering, simulation, and digital content creation.</li>
        </ul>

        <h4 class='sum-subheader'>Revenue Drivers</h4>
        <ul class='sum-list'>
            <li>High-performance GPUs (RTX series) and AI accelerators (H100, A100).</li>
            <li>CUDA platform, enabling high switching costs and deep ecosystem lock-in.</li>
            <li>Growing demand for AI training and inference globally.</li>
        </ul>

        <h4 class='sum-subheader'>Competitive Advantages</h4>
        <ul class='sum-list'>
            <li><strong>CUDA Dominance:</strong> The industry-standard AI compute platform.</li>
            <li><strong>Technological Leadership:</strong> Continuous innovation in GPU and AI chip design.</li>
            <li><strong>Ecosystem Strength:</strong> Robust developer community and advanced software stack.</li>
            <li><strong>Brand Recognition:</strong> NVIDIA is widely recognized as the backbone of AI computing.</li>
        </ul>

        <hr class='sum-divider' />

        <h3 class='sum-header'>2. Risks</h3>

        <h4 class='sum-subheader'>Operational Risks</h4>
        <ul class='sum-list'>
            <li>Heavy reliance on TSMC for advanced node manufacturing.</li>
            <li>Potential supply bottlenecks due to unprecedented AI chip demand.</li>
        </ul>

        <h4 class='sum-subheader'>Market Risks</h4>
        <ul class='sum-list'>
            <li>AI and GPU demand is cyclical and sensitive to macroeconomic trends.</li>
            <li>Customer budgets, especially in enterprise, may fluctuate.</li>
        </ul>

        <h4 class='sum-subheader'>Technological Risks</h4>
        <ul class='sum-list'>
            <li>Competition accelerating from AMD, Intel, and custom ASICs (e.g., Google TPU).</li>
            <li>Rapid innovation cycles require sustained R&D investment.</li>
        </ul>

        <h4 class='sum-subheader'>Regulatory & Geopolitical Risks</h4>
        <ul class='sum-list'>
            <li>Export restrictions (particularly to China) may limit revenue growth.</li>
            <li>Semiconductor supply chains remain geopolitically fragile.</li>
        </ul>

        <h4 class='sum-subheader'>Volatility Considerations</h4>
        <ul class='sum-list'>
            <li>NVIDIA’s stock is highly sensitive to AI sentiment and earnings expectations.</li>
        </ul>

    </div>
    """
    return SummaryResponse(executive_summary=html_content)
