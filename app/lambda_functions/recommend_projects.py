import json
from langchain import Bedrock
from config import BEDROCK_MODEL_NAME

def lambda_handler(event, context):
    user_info = json.loads(event['body'])
    # Implement GitHub API call to fetch projects based on user_info
    # Example projects (replace with actual API logic)
    projects = [
        {"name": "Project A", "tech_stack": ["Python", "Django"]},
        {"name": "Project B", "tech_stack": ["JavaScript", "React"]}
    ]

    # Use Bedrock for recommendations
    bedrock = Bedrock(model_name=BEDROCK_MODEL_NAME)
    recommendations = bedrock.generate(user_info)

    return {
        'statusCode': 200,
        'body': json.dumps(recommendations)
    }
