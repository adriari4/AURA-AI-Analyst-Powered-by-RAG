import os
import openai
from dotenv import load_dotenv
from langchain import hub
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from langsmith.evaluation import evaluate

# Load environment variables
load_dotenv()

# Ensure API keys are present
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables.")
if not os.getenv("PINECONE_API_KEY"):
    raise ValueError("PINECONE_API_KEY not found in environment variables.")
if not os.getenv("LANGCHAIN_API_KEY"):
    print("Warning: LANGCHAIN_API_KEY not found. LangSmith tracing may not work.")

# --- 1. SETUP RETRIEVER ---
INDEX_NAME = "youtube-rag-index"
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
# Filter out PDFs to match the main pipeline's logic if needed, or keep all. 
# The user's prompt didn't specify filtering, but the main pipeline does. 
# I'll include the filter for consistency with the "Antigravity" system.
retriever = vector_store.as_retriever(search_kwargs={"k": 5, "filter": {"type": {"$ne": "pdf"}}})

# --- 2. THE ANTIGRAVITY AGENT ---
class AntigravityRagBot:
    def __init__(self, retriever, model: str = "gpt-4-turbo"):
        self._retriever = retriever
        self._client = wrap_openai(openai.Client())
        self._model = model

    @traceable()
    def retrieve_docs(self, question):
        return self._retriever.invoke(question)

    @traceable()
    def get_answer(self, question: str):
        # Retrieve context
        similar = self.retrieve_docs(question)
        
        # ANTIGRAVITY SPECIFIC INSTRUCTION
        system_instruction = (
            "You are an expert technical assistant specializing in the 'Antigravity' project. "
            "Your task is to answer the user's question using ONLY the provided context documents below.\n\n"
            "Guidelines:\n"
            "1. Role: You are a senior developer for Antigravity. Be concise and technical.\n"
            "2. Grounding: Do not use outside knowledge. If the answer is not in the Docs, admit it.\n"
            "3. Code: Format all code snippets clearly.\n\n"
            f"## Docs\n\n{similar}"
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": question},
            ],
        )

        # Return format expected by Evaluators
        return {
            "answer": response.choices[0].message.content,
            "contexts": [str(doc) for doc in similar],
        }

# --- 3. THE JUDGES (EVALUATORS) ---

# A. QA Correctness (Response vs Reference)
def answer_correctness_evaluator(run, example) -> dict:
    # Logic: Does the RAG answer match the Ground Truth?
    prediction = run.outputs["answer"]
    reference = example.outputs["answer"]
    input_question = example.inputs["question"]
    
    # Load Judge Prompt
    grade_prompt = hub.pull("langchain-ai/rag-answer-vs-reference")
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
    
    grader = grade_prompt | llm
    score = grader.invoke({
        "question": input_question,
        "correct_answer": reference,
        "student_answer": prediction
    })
    return {"key": "correctness", "score": score["Score"]}

# B. Hallucination (Faithfulness)
def faithfulness_evaluator(run, example) -> dict:
    # Logic: Is the answer derived ONLY from the retrieved docs?
    prediction = run.outputs["answer"]
    contexts = run.outputs["contexts"]
    
    grade_prompt = hub.pull("langchain-ai/rag-answer-hallucination")
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
    
    grader = grade_prompt | llm
    score = grader.invoke({
        "documents": contexts,
        "student_answer": prediction
    })
    return {"key": "faithfulness_no_hallucination", "score": score["Score"]}

# C. Document Relevance
def doc_relevance_evaluator(run, example) -> dict:
    # Logic: Did the retriever find docs actually related to the question?
    input_question = example.inputs["question"]
    contexts = run.outputs["contexts"]
    
    grade_prompt = hub.pull("langchain-ai/rag-document-relevance")
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
    
    grader = grade_prompt | llm
    score = grader.invoke({
        "question": input_question,
        "documents": contexts
    })
    return {"key": "doc_relevance", "score": score["Score"]}

# --- 4. RUNNING THE VALIDATION ---

if __name__ == "__main__":
    print("Initializing Antigravity RAG Bot...")
    rag_bot = AntigravityRagBot(retriever)

    # Define the Wrapper Function for LangSmith
    def predict_antigravity_rag(example: dict):
        response = rag_bot.get_answer(example["question"])
        return {"answer": response["answer"], "contexts": response["contexts"]}

    # Execute Evaluation
    dataset_name = "RAG_test_Antigravity" 
    
    print(f"Starting evaluation on dataset: {dataset_name}")
    try:
        results = evaluate(
            predict_antigravity_rag,
            data=dataset_name,
            evaluators=[
                answer_correctness_evaluator, 
                faithfulness_evaluator, 
                doc_relevance_evaluator
            ],
            experiment_prefix="VALIDATION AURA",
            metadata={
                "project": "Antigravity",
                "model": "gpt-4-turbo",
                "description": "Initial validation of Antigravity docs retrieval"
            },
        )
        print("Validation Complete. Results:")
        print(results)
        # Attempt to print aggregate metrics if available
        try:
             df = results.to_pandas()
             print(df.describe())
        except:
             pass
    except Exception as e:
        print(f"Evaluation failed: {e}")
        print("Ensure the dataset 'RAG_test_Antigravity' exists in your LangSmith project.")
