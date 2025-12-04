import os
import shutil
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

# Ensure temp directory exists
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

def process_pdf(file: UploadFile):
    """
    Saves the uploaded PDF, ingests it into Pinecone, and returns a summary.
    """
    file_path = os.path.join(TEMP_DIR, file.filename)
    
    # Save file temporarily
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 1. Load PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # 2. Split Text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)

        # 3. Embed and Upsert to Pinecone
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        index_name = "youtube-index" # Using the same index
        
        # Add metadata to distinguish source
        for doc in docs:
            doc.metadata["source"] = "Uploaded Document"
            doc.metadata["title"] = file.filename

        PineconeVectorStore.from_documents(
            docs,
            embeddings,
            index_name=index_name
        )

        # 4. Generate Summary
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # Combine first few pages for summary to avoid token limits if large
        # Or just use map-reduce, but for simplicity let's summarize the first 3000 chars
        full_text = " ".join([doc.page_content for doc in documents])
        summary_text = full_text[:10000] # Limit context

        prompt = f"""You are a helpful assistant. 
        Summarize the following document content in a concise and professional manner (bullet points).
        
        Document Content:
        {summary_text}
        
        Summary:"""

        response = llm.invoke([HumanMessage(content=prompt)])
        summary = response.content

        return {"filename": file.filename, "summary": summary}

    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
