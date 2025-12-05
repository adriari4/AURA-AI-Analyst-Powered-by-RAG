import requests

urls = [
    "https://unpkg.com/@grapecity/spread-sheets/dist/gc.spread.sheets.all.min.js",
    "https://unpkg.com/@grapecity/spread-excelio/dist/gc.spread.excelio.min.js"
]

for url in urls:
    try:
        response = requests.head(url, allow_redirects=True)
        print(f"URL: {url}")
        print(f"Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error checking {url}: {e}")
