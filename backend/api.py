from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import shutil
import tempfile
import base64
from openai import OpenAI
from pinecone import Pinecone

# Import internal modules
# Import internal modules
from .rag_chain import answer_question
from .speech_to_text import transcribe_audio
from .thesis_logic import get_thesis_data
from ingest_videos import INDEX_NAME

# Import Routers
from .routers import nvidia_thesis_summary
from .routers import nvidia_chart

app = FastAPI(title="Value Investing AI API")

# Include Routers
app.include_router(nvidia_thesis_summary.router)
app.include_router(nvidia_chart.router)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextQuery(BaseModel):
    query: str

# Mount static files
app.mount("/static", StaticFiles(directory="frontend_static"), name="static") # Keep for backup/reference if needed
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")

# --- Frontend Routes ---
@app.get("/")
def read_root():
    return FileResponse("frontend/index.html")

@app.get("/index.html")
def read_index():
    return FileResponse("frontend/index.html")

@app.get("/dashboard.html")
def read_dashboard():
    return FileResponse("frontend/dashboard.html")

@app.get("/thesis.html")
def read_thesis():
    return FileResponse("frontend/thesis.html")

# --- Helper Functions ---
client = OpenAI()

def generate_audio(text: str) -> Optional[str]:
    """Generates TTS audio and returns base64 string."""
    try:
        if len(text) > 4096:
            text = text[:4096]
            
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return base64.b64encode(response.content).decode("utf-8")
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

# --- API Endpoints ---

@app.post("/ask-text")
def ask_text(query: TextQuery):
    try:
        answer = answer_question(query.query)
        audio_b64 = generate_audio(answer)
        return {"answer": answer, "audio_base64": audio_b64}
    except Exception as e:
        return {"error": str(e)}

@app.post("/ask-audio")
def ask_audio(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        text = transcribe_audio(tmp_path)
        os.remove(tmp_path)
        
        if not text:
            return {"error": "Could not transcribe audio"}
            
        answer = answer_question(text)
        audio_b64 = generate_audio(answer)
        return {"transcription": text, "answer": answer, "audio_base64": audio_b64}
        
    except Exception as e:
        return {"error": str(e)}

class ThesisQuery(BaseModel):
    company: str

@app.post("/analyze-thesis")
def analyze_thesis(query: ThesisQuery):
    try:
        result = get_thesis_data(query.company)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/stats")
def get_stats():
    try:
        PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        
        return {
            "total_vectors": stats.total_vector_count,
            "namespaces": stats.namespaces
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/fear-and-greed")
def get_fear_and_greed():
    try:
        import requests
        import datetime
        
        # CNN Fear & Greed API
        # We need a start date. Let's just get the last few days to ensure we have the latest.
        # Actually, the API returns historical data. We just need the latest point.
        # URL pattern: https://production.dataviz.cnn.io/index/fearandgreed/graphdata/YYYY-MM-DD
        
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=7) # Get last week
        url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{start_date}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # The data structure is usually:
        # { "fear_and_greed": { "score": 45.6, "rating": "Neutral", "timestamp": ... } }
        # But the graphdata endpoint returns a list of points: { "fear_and_greed_historical": { "data": [ { "x": 123, "y": 45, "rating": "fear" } ... ] } }
        
        # Let's try to parse the graph data to get the latest point
        if "fear_and_greed_historical" in data and "data" in data["fear_and_greed_historical"]:
            points = data["fear_and_greed_historical"]["data"]
            if points:
                latest = points[-1]
                score = int(latest["y"])
                rating = latest["rating"]
                
                # Capitalize rating
                rating = rating.title()
                
                return {
                    "score": score,
                    "rating": rating,
                    "timestamp": latest["x"]
                }
        
        return {"error": "Could not parse Fear & Greed data"}
        
    except Exception as e:
        print(f"Fear & Greed Error: {e}")
        return {"error": str(e)}

@app.get("/ticker")
def get_ticker():
    try:
        import yfinance as yf
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "BRK-B", "JPM", "V"]
        data = []
        
        # Fetch data in bulk for efficiency
        tickers = yf.Tickers(" ".join(symbols))
        
        for symbol in symbols:
            try:
                info = tickers.tickers[symbol].info
                # Use current price or previous close if market closed
                price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
                previous_close = info.get("previousClose")
                
                if price and previous_close:
                    change_percent = ((price - previous_close) / previous_close) * 100
                    up = change_percent >= 0
                    change_str = f"{change_percent:+.2f}%"
                    
                    data.append({
                        "symbol": symbol.replace("-", "."), # Display BRK.B instead of BRK-B
                        "price": f"{price:.2f}",
                        "change": change_str,
                        "up": up
                    })
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue
                
        return data
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
