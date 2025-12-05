import os
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

client = Client()

# List projects to find the one to rename
projects = list(client.list_projects())
# Look for the specific project we just ran
# It usually starts with the prefix we set: "antigravity-v1-validation"
target_prefix = "antigravity-v1-validation"
target_project = None

# Find the most recent project matching the prefix
matching_projects = [p for p in projects if p.name.startswith(target_prefix)]
if matching_projects:
    # Sort by start_time descending
    target_project = sorted(matching_projects, key=lambda p: p.start_time, reverse=True)[0]

if target_project:
    print(f"Found project to rename: {target_project.name} (ID: {target_project.id})")
    try:
        # Update the project name
        client.update_project(project_id=target_project.id, name="VALIDATION AURA")
        print("Successfully renamed project to 'VALIDATION AURA'")
    except Exception as e:
        print(f"Failed to rename project: {e}")
else:
    print(f"No project found starting with '{target_prefix}'")
