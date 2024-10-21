#util_aws.py

import config
import boto3
from github import Github
from langchain_aws import BedrockLLM
from langchain.prompts import PromptTemplate  # 올바른 PromptTemplate import
from langchain.chains import LLMChain
import tiktoken


# Initialize the GitHub API client
github = Github(config.GITHUB_API_TOKEN)

# Initialize the Bedrock Client
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Initialize the Bedrock LLM
llm = BedrockLLM(
    model_id="anthropic.claude-v2",
    client=bedrock_runtime,
    model_kwargs={
        "temperature": 0.7,
        "max_tokens_to_sample": 500
    }
)

def truncate_text(text, max_tokens):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)

    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
        text = tokenizer.decode(tokens) + "\n[Text truncated due to length.]"

    return text

def summarize_text(text, max_tokens=500):
    max_input_tokens = 3000
    text = truncate_text(text, max_input_tokens)

    prompt = f"Please provide a concise summary (max {max_tokens} words) of the following text:\n\n{text}"
    summary = llm.invoke(prompt)
    return summary


# 새로운 요약 기능: 프롬프트 템플릿을 사용하여 설명을 요약
def summarize_with_template(text, max_length=170):
    # 템플릿 파일 불러오기
    with open('templates/description_prompt.txt', 'r', encoding='utf-8') as file:
        template_content = file.read()

    # {{ max_length }}와 {{ text }}를 실제 값으로 대체
    prompt = template_content.replace('{{ max_length }}', str(max_length))
    prompt = prompt.replace('{{ text }}', text)

    try:
        # LLM에게 요약 요청
        response = llm.invoke(prompt)
        return response
    except Exception as e:
        return f"Error during summarization: {str(e)}"


# GitHub 프로젝트를 추천하고, 설명을 요약하는 함수
def get_recommended_projects(tech_stack, interest_areas):
    query = f"{interest_areas} language:{tech_stack} in:description"

    repositories = github.search_repositories(query=query, sort='stars', order='desc')

    top_repos = []
    for repo in repositories:
        try:
            readme_contents = repo.get_readme().decoded_content.decode('utf-8')
        except Exception:
            readme_contents = "No README available."

        # Description 요약 기능 추가
        description = repo.description or "No description provided."
        if len(description) > 180:  # 180자 이상일 경우
            # 템플릿을 사용해 요약
            description = summarize_with_template(description, max_length=170)

        repo_info = {
            'name': repo.full_name,
            'description': description,  # 요약된 description을 사용
            'url': repo.html_url,
            'forks': repo.forks_count,  # 포크 수
            'stars': repo.stargazers_count,  # 스타 수
            'readme': readme_contents,
        }
        top_repos.append(repo_info)
        if len(top_repos) >= 5:
            break
    return top_repos


def analyze_project_culture(repo_name, readme_contents):
    # Summarize the README content
    summarized_readme = summarize_text(readme_contents, max_tokens=500)

    # Truncate the summary if necessary
    summarized_readme = truncate_text(summarized_readme, 2000)

    # Prepare the prompt
    prompt_template_content = open('templates/culture_analysis_prompt.txt', encoding='utf-8').read()
    prompt_template = PromptTemplate(
        input_variables=["repo_name", "readme"],
        template=prompt_template_content,
    )

    # Estimate tokens
    tokenizer = tiktoken.get_encoding("cl100k_base")
    prompt_text = prompt_template.format(repo_name=repo_name, readme=summarized_readme)
    prompt_tokens = len(tokenizer.encode(prompt_text))
    max_allowed_tokens = 16384  # For gpt-3.5-turbo-16k
    max_response_tokens = 1000  # Estimate of the maximum tokens in the response

    if prompt_tokens + max_response_tokens > max_allowed_tokens:
        # Truncate the summarized_readme further
        allowed_tokens_for_readme = max_allowed_tokens - prompt_tokens - max_response_tokens
        summarized_readme = truncate_text(summarized_readme, allowed_tokens_for_readme)
        # Recalculate prompt_tokens
        prompt_text = prompt_template.format(repo_name=repo_name, readme=summarized_readme)
        prompt_tokens = len(tokenizer.encode(prompt_text))

    chain = LLMChain(llm=llm, prompt=prompt_template)
    analysis = chain.run(repo_name=repo_name, readme=summarized_readme)
    return analysis


def generate_contribution_guidelines(repo_name):
    prompt_template = PromptTemplate(
        input_variables=["repo_name"],
        template=open('templates/contribution_guidelines_prompt.txt', encoding='utf-8').read(),
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    guidelines = chain.run(repo_name=repo_name)
    return guidelines


# translate
def translate_text_with_claude(text, target_language):
    prompt = f"Please translate the following text into {target_language}:\n\n{text}"
    
    try:
        # Claude 모델을 사용한 번역 요청
        response = llm.invoke(prompt)
        return response
    except Exception as e:
        return f"Error during translation: {str(e)}"
        

