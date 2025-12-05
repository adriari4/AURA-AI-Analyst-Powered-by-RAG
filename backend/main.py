from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from backend.routers import chat_routes, thesis_routes, ticker_routes, nvidia_thesis_summary, nvidia_chart, excel_router, company_routes
import os
from pinecone import Pinecone

app = FastAPI(title="Value Investing AI API")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
# Note: We are now serving from 'frontend' directory as per new structure
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/data", StaticFiles(directory="data"), name="data")

# Include Routers
app.include_router(chat_routes.router)
app.include_router(thesis_routes.router)
app.include_router(nvidia_thesis_summary.router)
app.include_router(nvidia_chart.router)
app.include_router(ticker_routes.router)
app.include_router(excel_router.router)
app.include_router(company_routes.router)

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

@app.get("/excel.html")
def read_excel():
    return FileResponse("frontend/excel.html")

# Serve JS and CSS files explicitly if needed, or rely on static mount
# Since the HTML files will reference /static/js/... or /static/css/..., we might need to adjust HTML or these routes.
# For now, let's assume the HTMLs will be updated to point to relative paths which might resolve via the static mount if configured right.
# However, serving specific files from root is safer for existing links.

@app.get("/style.css")
def read_css():
    return FileResponse("frontend/css/style.css")

@app.get("/app.js")
def read_js():
    # This is a legacy route, but we are splitting app.js. 
    # We should probably serve the new chat.js here or update HTML.
    # Let's serve chat.js as a fallback or just error if not updated.
    return FileResponse("frontend/js/chat.js") 

@app.get("/thesis.js")
def read_thesis_js():
    return FileResponse("frontend/js/thesis.js")

@app.get("/stats")
def get_stats():
    try:
        PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        INDEX_NAME = "youtube-rag-index"
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        
        return {
            "total_vectors": stats.total_vector_count,
            "namespaces": stats.namespaces
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
