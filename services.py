import os
import requests
from langchain import Bedrock  # Importing your language model
from utils import fetch_github_data

def recommend_projects(input_data):
    tech_stack = input_data.tech_stack
    interests = input_data.interests
    available_time = input_data.available_time

    # Logic to fetch project recommendations
    bedrock = Bedrock(model_name="your-bedrock-model-name")  # Replace with your model
    recommendations = bedrock.generate({
        "tech_stack": tech_stack,
        "interests": interests,
        "available_time": available_time
    })

    # Example: Fetch metadata for a recommended project
    # Replace 'your-repo-url' with the actual repo URL from the recommendations
    repo_metadata = fetch_github_data("https://api.github.com/repos/yourusername/yourrepo")

    return recommendations
