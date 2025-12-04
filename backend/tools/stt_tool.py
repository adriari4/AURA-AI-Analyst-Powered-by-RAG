import whisper
import os
import tempfile

# Load model once to avoid reloading overhead (global variable)
# Using "base" model for speed/accuracy trade-off. Can be "tiny", "small", "medium", "large".
MODEL_SIZE = "base"
_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading Whisper model: {MODEL_SIZE}...")
        _model = whisper.load_model(MODEL_SIZE)
    return _model

def transcribe_audio(audio_file) -> str:
    """
    Transcribes an audio file object (like from Streamlit or file path).
    Returns the transcribed text.
    """
    try:
        model = get_model()
        
        # Handle Streamlit UploadedFile or bytes
        if hasattr(audio_file, "read"):
            # Save to a temp file because Whisper expects a path or numpy array
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(audio_file.read())
                tmp_path = tmp.name
        elif isinstance(audio_file, str) and os.path.exists(audio_file):
            tmp_path = audio_file
        else:
            raise ValueError("Invalid audio input. Must be a file path or file-like object.")

        # Transcribe
        print(f"Transcribing audio: {tmp_path}")
        result = model.transcribe(tmp_path)
        text = result["text"]

        # Cleanup temp file if we created it
        if hasattr(audio_file, "read"):
            os.remove(tmp_path)

        return text.strip()
    except Exception as e:
        print(f"Error during transcription: {e}")
        return ""
