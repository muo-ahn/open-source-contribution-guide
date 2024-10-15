# utils.py

import config
from github import Github
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI

# Initialize APIs
github = Github(config.GITHUB_API_TOKEN)
llm = OpenAI(api_key=config.OPENAI_API_KEY, temperature=0.7)

def get_recommended_projects(tech_stack, interest_areas):
    query = f"language:{tech_stack} {interest_areas} in:description"
    repositories = github.search_repositories(query=query, sort='stars', order='desc')

    top_repos = []
    for repo in repositories[:5]:
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
    return top_repos

def analyze_project_culture(repo_name, readme_contents):
    prompt_template = PromptTemplate(
        input_variables=["repo_name", "readme"],
        template=open('templates/culture_analysis_prompt.txt').read(),
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    analysis = chain.run(repo_name=repo_name, readme=readme_contents)
    return analysis

def generate_contribution_guidelines(repo_name):
    prompt_template = PromptTemplate(
        input_variables=["repo_name"],
        template=open('templates/contribution_guidelines_prompt.txt').read(),
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    guidelines = chain.run(repo_name=repo_name)
    return guidelines
