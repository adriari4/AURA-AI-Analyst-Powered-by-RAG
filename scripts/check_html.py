import requests

url = "http://localhost:8000/excel.html"
try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(response.text[:500]) # Print first 500 chars
    print("...")
    print(response.text[-500:]) # Print last 500 chars
except Exception as e:
    print(f"Error: {e}")
