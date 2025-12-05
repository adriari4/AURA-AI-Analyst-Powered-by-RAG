import os
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

if not os.getenv("LANGCHAIN_API_KEY"):
    print("Error: LANGCHAIN_API_KEY not found.")
    exit(1)

client = Client()

dataset_name = "RAG_test_Antigravity"

# check if dataset exists
if client.has_dataset(dataset_name=dataset_name):
    print(f"Dataset '{dataset_name}' already exists.")
else:
    print(f"Creating dataset '{dataset_name}'...")
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Test dataset for Antigravity RAG evaluation",
    )
    
    # Add examples
    # These are based on the examples in the system prompt
    examples = [
        {
            "inputs": {"question": "What is Apple's competitive advantage?"},
            "outputs": {"answer": "Apple's competitive advantage is its ecosystem."}
        },
        {
            "inputs": {"question": "What does Warren Buffett advise?"},
            "outputs": {"answer": "Warren Buffett advises to buy businesses that have a moat."}
        },
        {
            "inputs": {"question": "Who is the president of France?"},
            "outputs": {"answer": "This information does not appear in the Invertir Desde Cero videos."}
        }
    ]

    client.create_examples(
        inputs=[e["inputs"] for e in examples],
        outputs=[e["outputs"] for e in examples],
        dataset_id=dataset.id,
    )
    print(f"Created {len(examples)} examples in dataset '{dataset_name}'.")
