# app.py

import streamlit as st
from langchain.llms import OpenAI
from utils import (
    get_recommended_projects,
    analyze_project_culture,
    generate_contribution_guidelines,
)
import config

# Initialize the OpenAI LLM with correct parameters
llm = OpenAI(
    openai_api_key=config.OPENAI_API_KEY,
    temperature=0.7,
    model_name="gpt-3.5-turbo"
)

# Streamlit App
st.set_page_config(page_title="Open Source Contribution Guide", layout="wide")
st.title("Open Source Contribution Guide")

# 1. User Input Stage
st.header("1. User Input")

with st.form(key='user_input_form'):
    tech_stack = st.text_input(
        "Enter your technology stack (e.g., Python, JavaScript):", value=""
    )
    interest_areas = st.text_input(
        "Enter your areas of interest (e.g., web development, data science):", value=""
    )
    available_hours = st.number_input(
        "Enter the number of hours you can contribute per week:",
        min_value=1,
        max_value=40,
        value=5,
    )
    submit_button = st.form_submit_button(label='Find Projects')

if submit_button:
    if not tech_stack or not interest_areas:
        st.error("Please provide both your technology stack and areas of interest.")
    else:
        # 2. Project Recommendation Stage
        st.header("2. Project Recommendations")

        with st.spinner("Fetching recommended projects..."):
            recommended_projects = get_recommended_projects(tech_stack, interest_areas)

        if not recommended_projects:
            st.warning("No projects found. Please try different inputs.")
        else:
            for idx, project in enumerate(recommended_projects):
                st.subheader(f"{idx + 1}. {project['name']}")
                st.write(f"**Description:** {project['description']}")
                st.write(f"**URL:** [{project['url']}]({project['url']})")

            # 3. Culture Analysis Stage
            st.header("3. Project Culture Analysis")

            for project in recommended_projects:
                st.subheader(project['name'])
                with st.spinner(f"Analyzing culture for {project['name']}..."):
                    culture_analysis = analyze_project_culture(
                        project['name'], project['readme']
                    )
                st.write(culture_analysis)

            # 4. Contribution Guidelines and Educational Materials
            st.header("4. Contribution Guidelines and Educational Materials")

            for project in recommended_projects:
                st.subheader(f"Guidelines for {project['name']}")
                with st.spinner(f"Generating guidelines for {project['name']}..."):
                    guidelines = generate_contribution_guidelines(project['name'])
                st.write(guidelines)
