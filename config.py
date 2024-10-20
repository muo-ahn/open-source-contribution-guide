# config.py

import os
from dotenv import load_dotenv

load_dotenv()  # Take environment variables from .env.

GITHUB_API_TOKEN = os.getenv('GITHUB_API_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AWS_REGION = os.getenv('AWS_REGION')