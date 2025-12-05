import os
import time
from typing import List
from dotenv import load_dotenv
from langchain_community.document_loaders import YoutubeLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langsmith import traceable
import yt_dlp
import whisper

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

def read_video_links(file_path: str) -> List[str]:
    """Reads YouTube links from a text file."""
    with open(file_path, "r") as f:
        links = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
    return links

def download_audio_and_transcribe(url: str) -> str:
    """Downloads audio via yt-dlp and transcribes with Whisper."""
    print(f"Downloading audio for {url}...")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'temp_audio.%(ext)s',
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        print("Transcribing with Whisper...")
        model = whisper.load_model("base")
        result = model.transcribe("temp_audio.mp3")
        text = result["text"]
        
        # Cleanup
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
            
        return text
    except Exception as e:
        print(f"Error in Whisper transcription: {e}")
        return ""

@traceable(name="process_video")
def process_video(url: str, vector_store):
    """Processes a single video: Transcribe -> Chunk -> Embed -> Store."""
    print(f"Processing: {url}")
    
    # 1. Try getting transcript via YoutubeLoader
    try:
        loader = YoutubeLoader.from_youtube_url(
            url, 
            add_video_info=True,
            language=["en", "es"], # Add more languages if needed
            translation="en"
        )
        docs = loader.load()
        
        if not docs:
            raise ValueError("No transcript found.")
            
        print("Transcript found via YoutubeLoader.")
        
    except Exception as e:
        print(f"YoutubeLoader failed or no transcript ({e}). Falling back to Whisper.")
        text = download_audio_and_transcribe(url)
        if not text:
            print(f"Skipping {url} - Could not transcribe.")
            return
        
        # Create a Document manually if Whisper is used
        from langchain_core.documents import Document
        # We might want to fetch metadata separately if YoutubeLoader failed completely, 
        # but for now let's use basic info or try to extract it via yt-dlp if needed.
        # For simplicity in fallback, we'll use the URL as source.
        docs = [Document(page_content=text, metadata={"source": url, "title": "Whisper Transcription"})]

    # 2. Chunking
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)
    
    # 3. Embedding & Storage
    if splits:
        vector_store.add_documents(documents=splits)
        print(f"Successfully added {len(splits)} chunks to Pinecone.")
    else:
        print("No content to add.")

def ingest_all_videos():
    """Main ingestion function."""
    links = read_video_links("videos_link.txt")
    print(f"Found {len(links)} videos to process.")
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    
    for link in links:
        try:
            # Optional: Check if already processed (naive check, can be improved)
            # For now, we just process. 
            process_video(link, vector_store)
        except Exception as e:
            print(f"Failed to process {link}: {e}")

if __name__ == "__main__":
    ingest_all_videos()
