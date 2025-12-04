import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain.memory import ConversationBufferWindowMemory
from langchain import hub
from langsmith import traceable

# Import external modules for tools
# Ensure root directory is in path to import ingest_videos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import ingest_videos
    from backend import speech_to_text
except ImportError:
    print("Warning: Could not import ingest_videos or speech_to_text. Some tools may fail.")

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "youtube-rag-index"

# Global Memory
memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    k=5,
    return_messages=True
)

@traceable(name="get_agent_executor")
def get_agent_executor():
    # 1. Setup Vector Store & Retriever
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    # Filter out PDFs to only use YouTube captions (assuming PDFs have type='pdf')
    retriever = vector_store.as_retriever(search_kwargs={"k": 5, "filter": {"type": {"$ne": "pdf"}}})

    # 2. LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # 3. Define Tool Functions
    
    # Tool 1: RAG Answer Tool (RetrievalQA)
    # Tool 1: RAG Answer Tool (RetrievalQA)
    
    # Strict System Prompt
    template = """You are a specialized assistant for "Invertir Desde Cero" YouTube videos. 
    Answer the question strictly based on the following context from the video captions. 
    Do NOT analyze the video itself, only the captions provided in the context.
    Do not use outside knowledge. 
    
    If the answer is not contained in the context, you must answer EXACTLY:
    "This information does not appear in the Invertir Desde Cero videos."

    Here are some examples of how you should answer:

    Example 1:
    Context: "In this video, we discuss that Apple's competitive advantage is its ecosystem."
    Question: "What is Apple's competitive advantage?"
    Answer: "Apple's competitive advantage is its ecosystem."

    Example 2:
    Context: "We are analyzing Tesla's production numbers for 2023."
    Question: "Who is the president of France?"
    Answer: "This information does not appear in the Invertir Desde Cero videos."

    Example 3:
    Context: "Warren Buffett advises to buy businesses with a moat."
    Question: "What does Warren Buffett advise?"
    Answer: "Warren Buffett advises to buy businesses that have a moat."

    Now, answer the following question based ONLY on the context provided below.

    Context:
    {context}

    Question:
    {question}

    Answer:"""

    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )

    # Tool 2: YouTube Ingestion Tool
    def ingest_video_func(url: str):
        try:
            ingest_videos.process_video(url, vector_store)
            return f"Successfully ingested video: {url}"
        except Exception as e:
            return f"Error ingesting video: {str(e)}"

    # Tool 3: Speech to Text Tool
    def speech_to_text_func(file_path: str):
        try:
            text = speech_to_text.transcribe_audio(file_path)
            return text if text else "No transcription available."
        except Exception as e:
            return f"Error transcribing audio: {str(e)}"

    # Tool 4: Retriever Tool (Raw retrieval)
    def retriever_func(query: str):
        docs = retriever.get_relevant_documents(query)
        return "\n\n".join([f"Content: {d.page_content}\nSource: {d.metadata.get('source', 'Unknown')}" for d in docs])

    # 4. Create Tool Objects
    tools = [
        Tool(
            name="rag_answer_tool",
            func=qa_chain.run,
            description="Use this to answer questions about value investing based on the video knowledge base. Input should be a fully formed question."
        ),
        Tool(
            name="youtube_ingestion_tool",
            func=ingest_video_func,
            description="Use this to ingest a new YouTube video into the knowledge base. Input should be a valid YouTube URL."
        ),
        Tool(
            name="speech_to_text_tool",
            func=speech_to_text_func,
            description="Use this to transcribe an audio file to text. Input should be a local file path."
        ),
        Tool(
            name="retriever_tool",
            func=retriever_func,
            description="Use this to retrieve raw documents/context from the vector store without generating an answer. Input is a search query."
        )
    ]

    # 5. Pull ReAct Prompt
    prompt = hub.pull("hwchase17/react-chat")

    # 6. Create Agent
    agent = create_react_agent(llm, tools, prompt)

    # 7. Create Executor with Memory
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent_executor

@traceable(name="answer_question")
def answer_question(question: str):
    agent_executor = get_agent_executor()
    
    # The ReAct agent expects 'input' key
    response = agent_executor.invoke({"input": question})
    
    # The output key for AgentExecutor is usually 'output'
    return response["output"]
