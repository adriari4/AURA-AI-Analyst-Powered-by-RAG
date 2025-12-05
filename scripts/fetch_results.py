import os
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

client = Client()

# List projects to find the evaluation project
projects = list(client.list_projects())
# Look for projects related to our dataset and prefix
eval_projects = [p for p in projects if "validation" in p.name.lower() and ("antigravity" in p.name.lower() or "aura" in p.name.lower())]

if not eval_projects:
    print("No evaluation projects found. Listing all projects:")
    for p in projects:
        print(f"- {p.name}")
else:
    # Get the most recent one
    latest_project = sorted(eval_projects, key=lambda p: p.start_time, reverse=True)[0]
    print(f"Found Evaluation Project: {latest_project.name}")
    print(f"URL: https://smith.langchain.com/projects/p/{latest_project.id}")
    print("-" * 40)

    # Get runs (results)
    runs = list(client.list_runs(project_name=latest_project.name, is_root=True))
    
    if not runs:
        print("No runs found in this project.")
    else:
        print(f"Total Examples Evaluated: {len(runs)}")
        
        # Aggregate Feedback
        scores = {}
        counts = {}
        
        for run in runs:
            for feedback in client.list_feedback(run_ids=[run.id]):
                key = feedback.key
                score = feedback.score
                if score is not None:
                    scores[key] = scores.get(key, 0) + score
                    counts[key] = counts.get(key, 0) + 1
        
        print("\nAggregate Scores:")
        for key in scores:
            avg_score = scores[key] / counts[key]
            print(f"- {key}: {avg_score:.2f} / 1.0")

