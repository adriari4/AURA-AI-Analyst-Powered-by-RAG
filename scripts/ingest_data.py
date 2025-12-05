import os
import time
from typing import List
from dotenv import load_dotenv
from langchain_community.document_loaders import YoutubeLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langsmith import traceable
import yt_dlp
import whisper
import shutil

# Load environment variables
load_dotenv()

# Handle potential typo in .env or standard name
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") or os.getenv("PINECONE APY KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = "youtube-rag-index"

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in environment variables.")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Check if index exists, create if not
existing_indexes = [index.name for index in pc.list_indexes()]
if INDEX_NAME not in existing_indexes:
    print(f"Creating Pinecone index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536, # OpenAI text-embedding-3-small dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# --- Data Paths ---
DATA_DIR = "data"
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")
PDFS_DIR = os.path.join(DATA_DIR, "pdfs")

# Ensure directories exist
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(PDFS_DIR, exist_ok=True)

def read_video_links(file_path: str) -> List[str]:
    """Reads YouTube links from a text file."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        links = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
    return links

def download_audio_and_transcribe(url: str, video_id: str) -> str:
    """Downloads audio via yt-dlp and transcribes with Whisper."""
    print(f"Downloading audio for {url}...")
    
    audio_path = os.path.join(AUDIO_DIR, f"{video_id}.mp3")
    
    # Check if audio already exists
    if os.path.exists(audio_path):
        print(f"Audio already exists at {audio_path}")
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(AUDIO_DIR, f"{video_id}.%(ext)s"),
            'quiet': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return ""

    # Check if transcript already exists
    transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{video_id}.txt")
    if os.path.exists(transcript_path):
        print(f"Transcript already exists at {transcript_path}")
        with open(transcript_path, "r", encoding="utf-8") as f:
            return f.read()

    print("Transcribing with Whisper...")
    try:
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        text = result["text"]
        
        # Save transcript
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        return text
    except Exception as e:
        print(f"Error in Whisper transcription: {e}")
        return ""

@traceable(name="process_video")
def process_video(url: str, vector_store):
    """Processes a single video: Transcribe -> Chunk -> Embed -> Store."""
    print(f"Processing Video: {url}")
    
    # Extract Video ID for filenames
    try:
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        else:
            video_id = url.split("/")[-1]
    except:
        video_id = str(int(time.time()))

    # 1. Try getting transcript via YoutubeLoader
    docs = []
    try:
        loader = YoutubeLoader.from_youtube_url(
            url, 
            add_video_info=True,
            language=["en", "es"],
            translation="en"
        )
        docs = loader.load()
        print("Transcript found via YoutubeLoader.")
    except Exception as e:
        print(f"YoutubeLoader failed: {e}")

    # 2. Fallback to Whisper
    if not docs:
        print("Fallback to Whisper...")
        text = download_audio_and_transcribe(url, video_id)
        if text:
            from langchain.docstore.document import Document
            docs = [Document(page_content=text, metadata={"source": url, "title": f"Video {video_id}"})]
    
    if not docs:
        print(f"Could not process video {url}")
        return

    # 3. Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)
    
    # 4. Embed and Store
    print(f"Upserting {len(splits)} chunks to Pinecone...")
    vector_store.add_documents(documents=splits)
    print("Done.")

@traceable(name="process_pdfs")
def process_pdfs(vector_store):
    """Processes all PDFs in the data/pdfs directory using OCR if needed."""
    print("Processing PDFs...")
    
    pdf_files = [f for f in os.listdir(PDFS_DIR) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDFs found.")
        return

    # Initialize OCR
    HAS_OCR = False
    USE_HUNYUAN = True # Enabled per user request
    
    ocr_model = None
    ocr_processor = None
    rapid_ocr = None

    # Try HunyuanOCR first
    if USE_HUNYUAN:
        try:
            print("Initializing HunyuanOCR (this may take time to download model)...")
            from transformers import AutoProcessor, AutoModelForVision2Seq
            import torch
            from PIL import Image
            import io
            
            # Load model and processor
            # Using trust_remote_code=True is essential for custom models
            ocr_processor = AutoProcessor.from_pretrained("tencent/HunyuanOCR", trust_remote_code=True)
            ocr_model = AutoModelForVision2Seq.from_pretrained("tencent/HunyuanOCR", trust_remote_code=True)
            
            HAS_OCR = True
            print("HunyuanOCR initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize HunyuanOCR: {e}")
            print("Falling back to RapidOCR.")
            USE_HUNYUAN = False

    # Fallback to RapidOCR
    if not USE_HUNYUAN:
        try:
            from rapidocr_onnxruntime import RapidOCR
            rapid_ocr = RapidOCR()
            HAS_OCR = True
            print("RapidOCR initialized.")
        except ImportError:
            print("OCR libraries not found. Falling back to standard loader.")
            HAS_OCR = False

    import fitz  # PyMuPDF (needed for image extraction in both cases)

    for pdf_file in pdf_files:
        file_path = os.path.join(PDFS_DIR, pdf_file)
        print(f"Processing PDF: {pdf_file}")
        
        try:
            # 1. Try Standard Loader first to check text length
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            
            # Check if text is empty
            total_text_len = sum([len(d.page_content.strip()) for d in docs])
            
            if total_text_len < 100 and HAS_OCR:
                print(f"Standard loader returned empty/low text ({total_text_len} chars). Using OCR...")
                
                ocr_docs = []
                doc = fitz.open(file_path)
                
                for i, page in enumerate(doc):
                    pix = page.get_pixmap()
                    img_bytes = pix.tobytes("png")
                    
                    text = ""
                    if USE_HUNYUAN and ocr_model and ocr_processor:
                        try:
                            # Convert bytes to PIL Image
                            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                            
                            # Prepare inputs
                            # Note: The prompt might need adjustment based on specific model requirements
                            # Standard VLM prompt for OCR
                            prompt = "OCR" 
                            inputs = ocr_processor(images=image, text=prompt, return_tensors="pt")
                            
                            # Generate
                            outputs = ocr_model.generate(**inputs, max_new_tokens=1024)
                            text = ocr_processor.batch_decode(outputs, skip_special_tokens=True)[0]
                            
                        except Exception as e:
                            print(f"HunyuanOCR error on page {i}: {e}")
                            # Fallback to RapidOCR for this page if Hunyuan fails?
                            # For now just log error.
                    
                    elif rapid_ocr:
                        # RapidOCR
                        result, _ = rapid_ocr(img_bytes)
                        if result:
                            text = "\n".join([line[1] for line in result])
                    
                    if text:
                        from langchain.docstore.document import Document
                        ocr_docs.append(Document(page_content=text, metadata={"source": pdf_file, "page": i, "type": "pdf"}))
                    else:
                        print(f"Page {i}: No text extracted.")

                if ocr_docs:
                    docs = ocr_docs
                    print(f"OCR extracted {len(docs)} pages.")
                else:
                    print("OCR failed to extract text.")

            # Add metadata (ensure it's set for all docs)
            for doc in docs:
                doc.metadata["source"] = pdf_file
                doc.metadata["type"] = "pdf"

            # Split Text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            splits = text_splitter.split_documents(docs)
            
            # Embed and Store
            if splits:
                print(f"Upserting {len(splits)} chunks from {pdf_file} to Pinecone...")
                vector_store.add_documents(documents=splits)
                print("Done.")
            else:
                print(f"No text to upsert for {pdf_file}")
            
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

def ingest_all_data():
    # Initialize Vector Store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    
    # 1. Process PDFs (Prioritize this!)
    print("\n--- Processing PDFs ---")
    process_pdfs(vector_store)

    # 2. Process Videos
    print("\n--- Processing Videos ---")
    links = read_video_links("videos_link.txt")
    for link in links:
        process_video(link, vector_store)

if __name__ == "__main__":
    ingest_all_data()
