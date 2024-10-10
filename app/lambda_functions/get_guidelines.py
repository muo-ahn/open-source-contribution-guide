import json
from langchain import Bedrock
from config import BEDROCK_MODEL_NAME

def lambda_handler(event, context):
    data = json.loads(event['body'])
    projects = data['projects']
    bedrock = Bedrock(model_name=BEDROCK_MODEL_NAME)

    guidelines = {}
    for project in projects:
        guidelines[project['name']] = bedrock.generate(f"Provide contribution guidelines for {project['name']}")

    return {
        'statusCode': 200,
        'body': json.dumps(guidelines)
    }
