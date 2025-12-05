import requests

url = "https://cdn.grapecity.com/spreadjs/hosted/latest/gc.spread.sheets.all.min.js"
try:
    response = requests.head(url)
    print(f"Status Code: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
