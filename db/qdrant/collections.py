# Qdrant collection configuration and schemas.

import requests
from core.config import get_config


def init_qdrant():
    config = get_config()
    return {
        "url": config.qdrant_url,
        "api_key": config.qdrant_api_key,
        "collection_name": config.qdrant_collection_name,
    }
    
def http_qdrant(endpoint: str, method: str = "GET"):

    init = init_qdrant()

    url = f"{init['url']}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {init['api_key']}",
    }

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers)
        elif method ==  "PUT":
            response = requests.put(url, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Invalid method: {method}")

        response.raise_for_status()

        if response.content:
            return response.json()
        return None 

    except requests.exceptions.RequestException as e:
        raise ValueError(f"HTTP request failed method: {e}")