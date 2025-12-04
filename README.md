# Value Investing Chatbot (Invertir Desde Cero)

A multimodal RAG (Retrieval Augmented Generation) system designed to answer value investing questions strictly based on the "Invertir Desde Cero" YouTube channel content.

## 🚀 Features

- **Strict RAG**: Answers are grounded **exclusively** in the provided video content. The agent refuses to answer general questions or use external knowledge.
- **Multimodal Interaction**:
  - **Voice Input**: Record questions using the microphone button (Whisper integration).
  - **Voice Output**: Answers are automatically spoken aloud (OpenAI TTS).
- **ReAct Agent**: Powered by LangChain's ReAct architecture to intelligently route queries and handle tools.
- **Modern UI**: A premium, dark-themed web interface with a smooth stock ticker and responsive design.
- **Dashboard**: View system statistics like total vectors and ingested videos.

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, LangChain, OpenAI (GPT-4o), Pinecone (Vector DB).
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (served statically by FastAPI).
- **OCR**: `RapidOCR` (ONNX) for PDF text extraction (Fallback). *HunyuanOCR supported for advanced extraction.*
- **AI Models**:
  - LLM: `gpt-4o`
  - Embeddings: `text-embedding-3-small`
  - Audio Transcription: `openai/whisper`
  - Text-to-Speech: `tts-1`

## 📂 Project Structure

```
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── pipeline/            # RAG & Thesis pipelines
│   │   ├── rag_pipeline.py
│   │   └── thesis_pipeline.py
│   ├── routers/             # API Routes
│   │   ├── chat_routes.py
│   │   ├── thesis_routes.py
│   │   └── ticker_routes.py
│   ├── tools/               # Agent tools
│   │   └── stt_tool.py
│   └── services/            # Business logic services
├── frontend/                # Static frontend files
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── chat.js
│   │   ├── thesis.js
│   │   └── ticker.js
│   ├── index.html
│   ├── thesis.html
│   └── dashboard.html
├── data/
│   ├── pdfs/                # PDF storage
│   └── videos/              # Video storage
├── ingest_data.py           # Data ingestion script (PDF & YouTube)
├── requirements.txt         # Dependencies
└── .env                     # Environment variables
```

## ⚙️ Setup & Installation

1.  **Clone the repository** (or navigate to the project folder).

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**:
    Create a `.env` file in the root directory with the following keys:
    ```env
    OPENAI_API_KEY=sk-...
    PINECONE_API_KEY=...
    LANGCHAIN_API_KEY=...
    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_PROJECT=ValueInvestingChatbot
    ```

## 🏃‍♂️ How to Run

### 1. Start the Application
Run the FastAPI backend (which also serves the frontend):

```bash
python -m backend.main
```

### 2. Access the UI
Open your browser and navigate to:
**http://localhost:8000**

### 3. Ingest New Videos (Optional)
To add more videos to the knowledge base:
1. Add YouTube URLs to `videos_link.txt` (if using a file list).
2. Place PDFs in `data/pdfs/`.
3. Run the ingestion script:
   ```bash
   python ingest_data.py
   ```

## 📓 Tutorial
Check out `rag_tutorial.ipynb` for a step-by-step walkthrough of how the ReAct agent and RAG chain are constructed.

## 🔒 Strict Mode Rules
The agent is configured with a custom system prompt to:
1.  **Never** use outside knowledge.
2.  **Always** cite the source as: `Source: Invertir Desde Cero (Pinecone)`.
3.  **Fallback** phrase: "This information does not appear in the Invertir Desde Cero videos."
