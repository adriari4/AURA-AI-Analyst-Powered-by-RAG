import requests

url = "http://localhost:8000/data/excel/Nvidia.xlsx"
try:
    response = requests.head(url)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {response.headers.get('Content-Length')}")
except Exception as e:
    print(f"Error: {e}")
