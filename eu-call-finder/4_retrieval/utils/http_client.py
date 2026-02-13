'''python
# eu-call-finder/4_retrieval/utils/http_client.py
# Shared request logic

import requests

def fetch_url(url: str):
    # Implement shared HTTP request logic here
    response = requests.get(url)
    response.raise_for_status()
    return response.text
'''