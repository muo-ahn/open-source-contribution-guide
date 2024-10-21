import streamlit as st
import os
import logging
import time
from jinja2 import Template
from utils import (
    get_recommended_projects,
    analyze_project_culture,
    generate_contribution_guidelines,
    summarize_text,
    translate_text_with_claude,
)
import config
import boto3
import pdfkit

from icons import fork_svg

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize session state for analyzed projects
if 'analyzed_projects' not in st.session_state:
    st.session_state['analyzed_projects'] = {}

# AWS S3 Configuration
S3_BUCKET_NAME = config.S3_BUCKET_NAME
S3_REGION_NAME = config.AWS_REGION  # Assuming same region

# Initialize S3 client
s3_client = boto3.client('s3', region_name=S3_REGION_NAME)

# Streamlit App Configuration
st.set_page_config(page_title="Open Source Contribution Guide", layout="wide")
st.title("Open Source Contribution Guide")

# Number formatting function for stars and forks only
def format_number(num):
    if num >= 1000000:
        return f"{num / 1000000:.1f}M"  # 100만 이상이면 M으로 표시
    elif num >= 1000:
        return f"{num / 1000:.1f}k"  # 1,000 이상이면 k로 표시
    else:
        return str(num)  # 1,000 이하이면 숫자 그대로 표시



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
    target_language = st.text_input("Enter the target language (e.g., Korean, Spanish):", value="")
    
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
                
                # Only apply formatting to stars and forks
                formatted_stars = format_number(project['stars'])
                formatted_forks = format_number(project['forks'])
                
                st.write(f"**Stars:** {formatted_stars} ⭐")  # 포맷된 스타 수 출력
                st.markdown(f"**Forks:** {formatted_forks} {fork_svg}", unsafe_allow_html=True)  # fork_svg를 icons.py에서 import
                st.write(f"**URL:** [{project['url']}]({project['url']})")
                
                with st.spinner(f"Generating summary for {project['name']}..."):
                    summary = summarize_text(project['readme'])
                    
                    # 번역 요청 추가
                    if target_language.strip():
                        translated_summary = translate_text_with_claude(summary, target_language)
                        st.markdown(f"**Summary ({target_language}):**")
                        st.write(translated_summary)
                    else:
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

            # Button to generate PDF and upload to S3
            if project_data:
                if st.button("Generate PDF and Upload to S3"):
                    with st.spinner("Generating PDF and uploading to S3..."):
                        try:
                            logging.info("Starting PDF generation...")
                            # Generate HTML content using Jinja2 template
                            template_path = 'templates/pdf_template.html'
                            with open(template_path, encoding='utf-8') as f:
                                template = Template(f.read())

                            html_content = template.render(projects=project_data)
                            logging.info("HTML content rendered for PDF.")

                            # Define the paths for saving the files
                            output_dir = os.path.join(os.getcwd(), 'output_files')
                            os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist
                            html_path = os.path.join(output_dir, 'temp.html')
                            pdf_path = os.path.join(output_dir, 'project_details.pdf')

                            # Save the HTML content to a file
                            with open(html_path, 'w', encoding='utf-8') as f:
                                f.write(html_content)
                            logging.info(f"HTML content saved to {html_path}")

                            # Generate PDF using pdfkit
                            logging.info("Attempting to generate PDF with pdfkit...")
                            wkhtmltopdf_path = '/usr/local/bin/wkhtmltopdf'  # Update this path if necessary
                            config_pdfkit = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                            pdfkit.from_file(html_path, pdf_path, configuration=config_pdfkit)
                            logging.info(f"PDF generated at {pdf_path}")

                            # Upload PDF to S3
                            s3_key = f'project_details_{int(time.time())}.pdf'
                            logging.info(f"Uploading PDF to S3 bucket {S3_BUCKET_NAME} with key {s3_key}...")
                            s3_client.upload_file(pdf_path, S3_BUCKET_NAME, s3_key)
                            logging.info("PDF uploaded to S3.")

                            # Generate a pre-signed URL
                            presigned_url = s3_client.generate_presigned_url(
                                'get_object',
                                Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
                                ExpiresIn=3600  # URL expires in 1 hour
                            )
                            logging.info("Generated pre-signed URL.")

                            st.success("PDF generated and uploaded to S3.")
                            st.markdown(f"**Download your PDF here:** [Download PDF]({presigned_url})")

                            # Cleanup temporary files
                            os.remove(pdf_path)
                            os.remove(html_path)

                        except Exception as e:
                            st.error(f"An error occurred: {e}")
                            logging.error(f"PDF Generation or S3 Upload Error: {e}")
