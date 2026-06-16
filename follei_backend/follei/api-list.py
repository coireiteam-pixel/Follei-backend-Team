import requests
# Replace this with the successful URL you found in Step 1
url = "http://127.0.0.1:8000/docs/"

try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    print(f"--- Found endpoints in {data.get('info', {}).get('title', 'API')} ---")
    
    # Loop through paths and extract methods
    for path, methods in data.get("paths", {}).items():
        for method in methods.keys():
            # Skip parameters or metadata keys if any exist
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                print(f"[{method.upper()}] {path}")

except requests.exceptions.RequestException as e:
    print(f"Error fetching data. Is your app running? Details: {e}")
