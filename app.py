# app.py

import streamlit as st
import os
import pdfkit
from jinja2 import Template
from langchain.chat_models import ChatOpenAI
from utils import (
    get_recommended_projects,
    analyze_project_culture,
    generate_contribution_guidelines,
)
import config

# Initialize the OpenAI Chat LLM
llm = ChatOpenAI(
    openai_api_key=config.OPENAI_API_KEY,
    temperature=0.7,
    model_name="gpt-3.5-turbo-16k"  # Using the 16k model for larger context
)

# Streamlit App Configuration
st.set_page_config(page_title="Open Source Contribution Guide", layout="wide")

# Sidebar User Input
with st.sidebar:
    st.title("User Input")
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
    submit_button = st.button('Find Projects')

# Main content area
if submit_button:
    if not tech_stack.strip() or not interest_areas.strip():
        st.error("Please provide both your technology stack and areas of interest.")
    else:
        # Chatbot layout using a placeholder
        chat_placeholder = st.empty()

        # Initialize chat history
        if 'messages' not in st.session_state:
            st.session_state['messages'] = []

        # Add initial assistant message
        st.session_state['messages'].append({"role": "assistant", "content": "Fetching recommended projects..."})
        chat_placeholder.markdown(format_messages(st.session_state['messages']), unsafe_allow_html=True)

        # 1. Project Recommendations
        recommended_projects = get_recommended_projects(tech_stack, interest_areas)

        if not recommended_projects:
            st.session_state['messages'].append({"role": "assistant", "content": "No projects found. Please try different inputs."})
            chat_placeholder.markdown(format_messages(st.session_state['messages']), unsafe_allow_html=True)
        else:
            # List recommended projects
            project_options = [f"{proj['name']}: {proj['description']}" for proj in recommended_projects]
            project_list_message = "Here are some projects you might be interested in:\n"
            for idx, proj in enumerate(project_options):
                project_list_message += f"{idx + 1}. {proj}\n"
            st.session_state['messages'].append({"role": "assistant", "content": project_list_message})
            st.session_state['messages'].append({"role": "assistant", "content": "Please select the projects you'd like to analyze further."})
            chat_placeholder.markdown(format_messages(st.session_state['messages']), unsafe_allow_html=True)

            # Allow user to select projects
            selected_indices = st.multiselect(
                "Select projects to analyze (by number):",
                options=list(range(1, len(recommended_projects) + 1)),
                format_func=lambda x: f"{x}. {recommended_projects[x - 1]['name']}"
            )

            if st.button("Analyze Selected Projects"):
                if not selected_indices:
                    st.warning("Please select at least one project to analyze.")
                else:
                    for idx in selected_indices:
                        project = recommended_projects[idx - 1]
                        st.session_state['messages'].append({"role": "assistant", "content": f"Analyzing {project['name']}..."})
                        chat_placeholder.markdown(format_messages(st.session_state['messages']), unsafe_allow_html=True)

                        # Culture Analysis
                        culture_analysis = analyze_project_culture(
                            project['name'], project['readme']
                        )
                        st.session_state['messages'].append({"role": "assistant", "content": f"**Culture Analysis for {project['name']}**\n{culture_analysis}"})
                        chat_placeholder.markdown(format_messages(st.session_state['messages']), unsafe_allow_html=True)

                        # Contribution Guidelines
                        guidelines = generate_contribution_guidelines(project['name'])
                        st.session_state['messages'].append({"role": "assistant", "content": f"**Contribution Guidelines for {project['name']}**\n{guidelines}"})
                        chat_placeholder.markdown(format_messages(st.session_state['messages']), unsafe_allow_html=True)

                    # Option to download PDF
                    if st.button("Download Project Details as PDF"):
                        with st.spinner("Generating PDF..."):
                            # Collect data for PDF
                            project_data = []
                            for idx in selected_indices:
                                project = recommended_projects[idx - 1]
                                project_info = {
                                    'name': project['name'],
                                    'description': project['description'],
                                    'url': project['url'],
                                    'culture_analysis': analyze_project_culture(
                                        project['name'], project['readme']
                                    ),
                                    'guidelines': generate_contribution_guidelines(project['name'])
                                }
                                project_data.append(project_info)

                            # Generate HTML content using Jinja2 template
                            template = Template(open('templates/pdf_template.html', encoding='utf-8').read())
                            html_content = template.render(projects=project_data)

                            # Save the HTML content to a temporary file
                            with open('temp.html', 'w', encoding='utf-8') as f:
                                f.write(html_content)

                            # Generate PDF using pdfkit
                            pdfkit.from_file('temp.html', 'output.pdf')

                            # Remove the temporary HTML file
                            os.remove('temp.html')

                            # Provide the PDF file for download
                            with open('output.pdf', 'rb') as f:
                                pdf_data = f.read()

                            st.download_button(
                                label="Download PDF",
                                data=pdf_data,
                                file_name='project_details.pdf',
                                mime='application/pdf'
                            )

                            # Remove the PDF file
                            os.remove('output.pdf')
else:
    st.write("Please enter your details in the sidebar and click 'Find Projects'.")

# Function to format messages for chatbot layout
def format_messages(messages):
    formatted_messages = ""
    for message in messages:
        if message["role"] == "assistant":
            formatted_messages += f"<div style='text-align: left;'><b>Assistant:</b> {message['content']}</div><br>"
        else:
            formatted_messages += f"<div style='text-align: right;'><b>You:</b> {message['content']}</div><br>"
    return formatted_messages
