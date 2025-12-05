import os
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "youtube-rag-index"

pc = Pinecone(api_key=PINECONE_API_KEY)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=INDEX_NAME,
    embedding=embeddings
)

llm = ChatOpenAI(model="gpt-4o", temperature=0)
qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever()
)

query = "What is the estimated Intrinsic Value (Valor Intrínseco) or Fair Value of NVIDIA according to the document? Return just the number if found, or 'Not found'."
print(qa.run(query))
