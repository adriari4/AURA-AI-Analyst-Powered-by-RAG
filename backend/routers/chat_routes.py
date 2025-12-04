from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import tempfile
import os
import base64
from typing import Optional
from pydantic import BaseModel
from openai import OpenAI
from backend.pipeline.rag_pipeline import answer_question
from backend.tools.stt_tool import transcribe_audio

router = APIRouter()
client = OpenAI()

class TextQuery(BaseModel):
    query: str

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

@router.post("/ask-text")
def ask_text(query: TextQuery):
    try:
        answer = answer_question(query.query)
        audio_b64 = generate_audio(answer)
        return {"answer": answer, "audio_base64": audio_b64}
    except Exception as e:
        return {"error": str(e)}

@router.post("/ask-audio")
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
