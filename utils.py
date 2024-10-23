# utils.py

import config
import boto3
from github import Github
from langchain_aws import ChatBedrock
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
import tiktoken, json

MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"  # 사용 중인 모델 ID
TEMPERATURE = 0.7  # 모델의 출력 다양성 조절 (낮을수록 보수적, 높을수록 다양)
MAX_TOKENS = 1000  # 최대 토큰 수 설정
REGION_NAME = 'us-east-1'  # AWS Bedrock 실행 리전

# Initialize the GitHub API client
github = Github(config.GITHUB_API_TOKEN)

# Initialize the Bedrock Client
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Initialize the Bedrock LLM
llm = ChatBedrock(
    model_id=MODEL_ID,
    client=bedrock_runtime,
    model_kwargs={
        "temperature": TEMPERATURE,  # 다양성 설정
        "max_tokens": MAX_TOKENS  # 최대 토큰 수 설정
    }
)

def truncate_text(text, max_tokens):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)

    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
        text = tokenizer.decode(tokens) + "\n[Text truncated due to length.]"

    return text

def summarize_text(text, max_tokens=MAX_TOKENS):
    """
    주어진 텍스트를 LLM을 사용하여 요약합니다.
    """
    # 템플릿 파일에서 프롬프트를 읽어옴
    with open("templates/read_sum_prompt.txt", "r", encoding='utf-8') as file:
        prompt_template = file.read()
    
    # 템플릿에 요약할 텍스트 삽입
    prompt = prompt_template.replace("{{ text }}", text)

    # LLM을 통해 요약을 생성하여 반환
    response = llm.invoke(prompt)
    return response.content  # 객체의 content 속성에 직접 접근
    
def summarize_with_template(text, max_length=MAX_TOKENS):
    """
    주어진 텍스트를 지정된 템플릿을 사용해 요약합니다.
    """
    with open('templates/description_prompt.txt', 'r', encoding='utf-8') as file:
        template_content = file.read()

    # 템플릿에서 최대 길이와 텍스트를 대체
    prompt = template_content.replace('{{ max_length }}', str(max_length))
    prompt = prompt.replace('{{ text }}', text)

    try:
        # LLM을 호출하여 요약 생성
        response = llm.invoke(prompt)
        return response.content  # content 속성에 직접 접근
    except Exception as e:
        return f"Error during summarization: {str(e)}"

def get_recommended_projects(tech_stack, interest_areas):
    query = f"{interest_areas} language:{tech_stack} in:description"

    repositories = github.search_repositories(query=query, sort='stars', order='desc')

    top_repos = []
    for repo in repositories:
        try:
            readme_contents = repo.get_readme().decoded_content.decode('utf-8')
        except Exception:
            readme_contents = "No README available."

        # 설명이 없으면 기본 값 설정
        description = repo.description or "No description provided."
        
        # README 파일이 없는 경우 메시지 출력
        if not readme_contents:
            description = "README.md not provided."
        elif len(description) > 180:
            # 설명이 너무 길 경우 요약
            description = summarize_with_template(description, max_length=170)

        # 프로젝트 정보 저장
        repo_info = {
            'name': repo.full_name,
            'description': description,
            'url': repo.html_url,
            'forks': repo.forks_count,
            'stars': repo.stargazers_count,
            'readme': readme_contents if readme_contents else "README.md not provided.",  # README 파일이 없으면 메시지 추가
        }
        top_repos.append(repo_info)
        if len(top_repos) >= 5:
            break
    return top_repos

def analyze_project_culture(repo_name, readme_contents):
    summarized_readme = summarize_text(readme_contents, max_tokens=MAX_TOKENS)
    summarized_readme = truncate_text(summarized_readme, 2000)

    # 템플릿에서 프롬프트를 읽어옴
    prompt_template_content = open('templates/culture_analysis_prompt.txt', encoding='utf-8').read()
    prompt_template = PromptTemplate(
        input_variables=["repo_name", "readme"],
        template=prompt_template_content,
    )

    # 템플릿에 값 대입
    prompt_text = prompt_template.format(repo_name=repo_name, readme=summarized_readme)

    # LLM 체인을 통해 분석 수행
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

# Claude 3.5 Sonnet을 사용하여 텍스트 번역
def translate_text_with_claude(text, target_language):
    """
    Claude 3.5 Sonnet을 사용하여 텍스트를 지정된 언어로 번역합니다.
    """
    prompt = (
        f"Translate the following text into {target_language}. "
        f"Provide only the translated text without any additional comments or explanations.\n\n"
        f"{text}"
    )
    try:
        response = llm.invoke(prompt)
        return response.content  # content 속성에 직접 접근
    except Exception as e:
        return f"Error during translation: {str(e)}"

# 언어 JSON 파일 로드
def load_language(language):
    """
    주어진 언어에 맞는 JSON 파일을 로드합니다.
    """
    file_path = f'lang_json/{language}.json'
    try:
        # JSON 파일 열기
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# 별(star)과 포크(fork) 수를 포맷팅
def format_number(num):
    """
    숫자를 읽기 쉬운 형식으로 변환합니다.
    1000 이상은 'k', 100만 이상은 'M'을 사용합니다.
    """
    if num >= 1000000:
        return f"{num / 1000000:.1f}M"
    elif num >= 1000:
        return f"{num / 1000:.1f}k"
    else:
        return str(num)
