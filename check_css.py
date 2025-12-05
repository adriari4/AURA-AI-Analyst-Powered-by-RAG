import requests

url = "https://unpkg.com/@grapecity/spread-sheets/styles/gc.spread.sheets.excel2013white.css"
try:
    response = requests.head(url, allow_redirects=True)
    print(f"URL: {url}")
    print(f"Status Code: {response.status_code}")
except Exception as e:
    print(f"Error checking {url}: {e}")
