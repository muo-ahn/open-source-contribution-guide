import json

def lambda_handler(event, context):
    data = json.loads(event['body'])
    projects = data['projects']
    # Perform culture analysis (example data)
    culture_data = {project['name']: "Open and collaborative" for project in projects}

    return {
        'statusCode': 200,
        'body': json.dumps(culture_data)
    }
