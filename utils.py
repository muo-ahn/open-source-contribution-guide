# utils.py

import config
import boto3
from github import Github
from langchain.llms.bedrock import BedrockLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Initialize the GitHub API client
github = Github(config.GITHUB_API_TOKEN)

# Initialize the Bedrock LLM
bedrock_runtime = boto3.client('bedrock-runtime', region_name=config.AWS_REGION)
llm = BedrockLLM(
    model_id="anthropic.claude-v2",
    client=bedrock_runtime,
    model_kwargs={
        "temperature": 0.7,
        "max_tokens_to_sample": 500
    }
)

def summarize_text(text, max_words=500):
    # Limit the text to prevent exceeding context length
    max_chars = 10000  # Adjust as needed
    text = text[:max_chars]

    prompt = f"Please provide a concise summary (max {max_words} words) of the following text:\n\n{text}"
    summary = llm(prompt)
    return summary

def get_recommended_projects(tech_stack, interest_areas):
    query = f"{interest_areas} language:{tech_stack} in:description"

    repositories = github.search_repositories(query=query, sort='stars', order='desc')

    top_repos = []
    for repo in repositories:
        try:
            readme_contents = repo.get_readme().decoded_content.decode('utf-8')
        except Exception:
            readme_contents = "No README available."

        repo_info = {
            'name': repo.full_name,
            'description': repo.description or "No description provided.",
            'url': repo.html_url,
            'readme': readme_contents,
        }
        top_repos.append(repo_info)
        if len(top_repos) >= 5:
            break
    return top_repos

def analyze_project_culture(repo_name, readme_contents):
    # Summarize the README content
    summarized_readme = summarize_text(readme_contents)

    # Prepare the prompt
    prompt_template_content = open('templates/culture_analysis_prompt.txt', encoding='utf-8').read()
    prompt_template = PromptTemplate(
        input_variables=["repo_name", "readme"],
        template=prompt_template_content,
    )

    chain = LLMChain(llm=llm, prompt=prompt_template)
    analysis = chain.run(repo_name=repo_name, readme=summarized_readme)
    return analysis

def generate_contribution_guidelines(repo_name):
    prompt_template_content = open('templates/contribution_guidelines_prompt.txt', encoding='utf-8').read()
    prompt_template = PromptTemplate(
        input_variables=["repo_name"],
        template=prompt_template_content,
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    guidelines = chain.run(repo_name=repo_name)
    return guidelines
