import requests

url = "http://localhost:8000/"
try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
except Exception as e:
    print(f"Error: {e}")
