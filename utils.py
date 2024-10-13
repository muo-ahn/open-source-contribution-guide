import os
import requests

def fetch_github_data(repo_url):
    token = os.getenv("GITHUB_API_TOKEN")
    headers = {
        "Authorization": f"token {token}"
    }
    response = requests.get(repo_url, headers=headers)
    return response.json()
