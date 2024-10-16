# app.py

import streamlit as st
import os
import pdfkit
import tempfile
import logging
from jinja2 import Template
from utils import (
    get_recommended_projects,
    analyze_project_culture,
    generate_contribution_guidelines,
    summarize_text  # Import the summarize_text function
)
import config

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Initialize session state for analyzed projects
if 'analyzed_projects' not in st.session_state:
    st.session_state['analyzed_projects'] = {}

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
            # Display summaries and individual analyze buttons
            for idx, project in enumerate(recommended_projects):
                st.subheader(f"{idx + 1}. {project['name']}")
                st.write(f"**Description:** {project['description']}")
                st.write(f"**URL:** [{project['url']}]({project['url']})")
                with st.spinner(f"Generating summary for {project['name']}..."):
                    summary = summarize_text(project['readme'], max_tokens=150)
                st.markdown("**Summary:**")
                st.write(summary)

                # Individual Analyze Button
                analyze_button = st.button(f"Analyze {project['name']}", key=f"analyze_{idx}")

                if analyze_button or st.session_state['analyzed_projects'].get(idx):
                    if not st.session_state['analyzed_projects'].get(idx):
                        # Perform analysis and store results in session state
                        with st.spinner(f"Analyzing culture for {project['name']}..."):
                            culture_analysis = analyze_project_culture(
                                project['name'], project['readme']
                            )
                        with st.spinner(f"Generating guidelines for {project['name']}..."):
                            guidelines = generate_contribution_guidelines(project['name'])

                        st.session_state['analyzed_projects'][idx] = {
                            'culture_analysis': culture_analysis,
                            'guidelines': guidelines,
                            'project_info': project  # Store project info for PDF
                        }

                    # Display analysis results
                    st.markdown("### Culture Analysis")
                    st.write(st.session_state['analyzed_projects'][idx]['culture_analysis'])

                    st.markdown("### Contribution Guidelines")
                    st.write(st.session_state['analyzed_projects'][idx]['guidelines'])

                st.markdown("---")  # Separator between projects

            # Collect analyzed projects for PDF
            project_data = [
                {
                    'name': data['project_info']['name'],
                    'description': data['project_info']['description'],
                    'url': data['project_info']['url'],
                    'culture_analysis': data['culture_analysis'],
                    'guidelines': data['guidelines']
                }
                for idx, data in st.session_state['analyzed_projects'].items()
            ]

            # Button to generate PDF
            if project_data:
                if st.button("Download Project Details as PDF"):
                    with st.spinner("Generating PDF..."):
                        try:
                            logging.info("Starting PDF generation...")
                            # Generate HTML content using Jinja2 template
                            template_path = 'templates/pdf_template.html'
                            logging.debug(f"Loading template from {template_path}")
                            with open(template_path, encoding='utf-8') as f:
                                template = Template(f.read())

                            html_content = template.render(projects=project_data)
                            logging.debug("HTML content rendered for PDF.")

                            # Use a temporary directory
                            with tempfile.TemporaryDirectory() as tmpdirname:
                                html_path = os.path.join(tmpdirname, 'temp.html')
                                pdf_path = os.path.join(tmpdirname, 'output.pdf')

                                # Save the HTML content to a temporary file
                                with open(html_path, 'w', encoding='utf-8') as f:
                                    f.write(html_content)
                                logging.debug(f"HTML content saved to {html_path}")

                                # Generate PDF using pdfkit
                                logging.debug("Attempting to generate PDF with pdfkit...")
                                config_pdfkit = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')  # Update path if necessary
                                pdfkit.from_file(html_path, pdf_path, configuration=config_pdfkit)
                                logging.info(f"PDF generated at {pdf_path}")

                                # Provide the PDF file for download
                                with open(pdf_path, 'rb') as f:
                                    pdf_data = f.read()

                                st.download_button(
                                    label="Download PDF",
                                    data=pdf_data,
                                    file_name='project_details.pdf',
                                    mime='application/pdf'
                                )
                                logging.info("PDF provided for download.")
                        except Exception as e:
                            st.error(f"An error occurred while generating the PDF: {e}")
                            logging.exception("PDF Generation Error")
