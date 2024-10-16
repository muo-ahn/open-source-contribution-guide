# app.py

import streamlit as st
import os
import pdfkit
import tempfile
import logging
from jinja2 import Template
from langchain.chat_models import ChatOpenAI
from utils import (
    get_recommended_projects,
    analyze_project_culture,
    generate_contribution_guidelines,
    summarize_text  # Import the summarize_text function
)
import config

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize the OpenAI Chat LLM
llm = ChatOpenAI(
    openai_api_key=config.OPENAI_API_KEY,
    temperature=0.7,
    model_name="gpt-3.5-turbo-16k"
)

# Streamlit App Configuration
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
    if not tech_stack.strip() or not interest_areas.strip():
        st.error("Please provide both your technology stack and areas of interest.")
    else:
        # 2. Project Recommendations
        st.header("2. Project Recommendations")

        with st.spinner("Fetching recommended projects..."):
            recommended_projects = get_recommended_projects(tech_stack, interest_areas)

        if not recommended_projects:
            st.warning("No projects found. Please try different inputs.")
        else:
            st.write("Here are some projects you might be interested in:")
            # Display summaries
            for idx, project in enumerate(recommended_projects):
                st.subheader(f"{idx + 1}. {project['name']}")
                st.write(f"**Description:** {project['description']}")
                st.write(f"**URL:** [{project['url']}]({project['url']})")
                with st.spinner(f"Generating summary for {project['name']}..."):
                    summary = summarize_text(project['readme'], max_tokens=150)
                st.markdown("**Summary:**")
                st.write(summary)
                st.markdown("---")  # Separator between projects

            # Allow user to select projects to analyze
            st.header("3. Select Projects for Analysis")
            project_options = [f"{idx + 1}. {proj['name']}" for idx, proj in enumerate(recommended_projects)]
            selected_indices = st.multiselect(
                "Select projects to analyze:",
                options=range(len(recommended_projects)),
                format_func=lambda x: project_options[x]
            )

            if st.button("Analyze Selected Projects"):
                if not selected_indices:
                    st.warning("Please select at least one project to analyze.")
                else:
                    st.header("4. Project Analysis")
                    project_data = []
                    for idx in selected_indices:
                        project = recommended_projects[idx]
                        st.subheader(f"{project['name']}")
                        st.write(f"**Description:** {project['description']}")
                        st.write(f"**URL:** [{project['url']}]({project['url']})")

                        # Culture Analysis
                        with st.spinner(f"Analyzing culture for {project['name']}..."):
                            culture_analysis = analyze_project_culture(
                                project['name'], project['readme']
                            )
                        st.markdown("### Culture Analysis")
                        st.write(culture_analysis)

                        # Contribution Guidelines
                        with st.spinner(f"Generating guidelines for {project['name']}..."):
                            guidelines = generate_contribution_guidelines(project['name'])
                        st.markdown("### Contribution Guidelines")
                        st.write(guidelines)

                        st.markdown("---")  # Separator between projects

                        # Collect data for PDF
                        project_info = {
                            'name': project['name'],
                            'description': project['description'],
                            'url': project['url'],
                            'culture_analysis': culture_analysis,
                            'guidelines': guidelines
                        }
                        project_data.append(project_info)

                    # Button to generate PDF
                    if st.button("Download Project Details as PDF"):
                        with st.spinner("Generating PDF..."):
                            try:
                                # Generate HTML content using Jinja2 template
                                template = Template(open('templates/pdf_template.html', encoding='utf-8').read())
                                html_content = template.render(projects=project_data)

                                # Use a temporary directory
                                with tempfile.TemporaryDirectory() as tmpdirname:
                                    html_path = os.path.join(tmpdirname, 'temp.html')
                                    pdf_path = os.path.join(tmpdirname, 'output.pdf')

                                    # Save the HTML content to a temporary file
                                    with open(html_path, 'w', encoding='utf-8') as f:
                                        f.write(html_content)

                                    # Generate PDF using pdfkit
                                    pdfkit.from_file(html_path, pdf_path)

                                    # Provide the PDF file for download
                                    with open(pdf_path, 'rb') as f:
                                        pdf_data = f.read()

                                    st.download_button(
                                        label="Download PDF",
                                        data=pdf_data,
                                        file_name='project_details.pdf',
                                        mime='application/pdf'
                                    )
                            except Exception as e:
                                st.error(f"An error occurred while generating the PDF: {e}")
                                logging.exception("PDF Generation Error")
