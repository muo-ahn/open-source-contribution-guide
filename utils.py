# utils.py

import config
from github import Github
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI

# Initialize the GitHub API client
github = Github(config.GITHUB_API_TOKEN)

# Initialize the OpenAI Chat LLM
llm = ChatOpenAI(
    openai_api_key=config.OPENAI_API_KEY,
    temperature=0.7,
    model_name="gpt-3.5-turbo"
)

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

def summarize_readme(readme_contents):
    prompt = f"Summarize the following README content in 500 words:\n\n{readme_contents}"
    summary = llm.predict(prompt)
    return summary

def analyze_project_culture(repo_name, readme_contents):
    # Summarize the README content
    summarized_readme = summarize_readme(readme_contents)

    prompt_template = PromptTemplate(
        input_variables=["repo_name", "readme"],
        template=open('templates/culture_analysis_prompt.txt').read(),
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    analysis = chain.run(repo_name=repo_name, readme=summarized_readme)
    return analysis


def generate_contribution_guidelines(repo_name):
    prompt_template = PromptTemplate(
        input_variables=["repo_name"],
        template=open('templates/contribution_guidelines_prompt.txt').read(),
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    guidelines = chain.run(repo_name=repo_name)
    return guidelines