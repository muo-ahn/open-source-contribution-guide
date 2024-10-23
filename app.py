# app.py

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
    load_language,
    format_number,
)
import config
import boto3
import pdfkit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Initialize session state
if 'analyzed_projects' not in st.session_state:
    st.session_state['analyzed_projects'] = {}
if 'recommended_projects' not in st.session_state:
    st.session_state['recommended_projects'] = []
if 'search_performed' not in st.session_state:
    st.session_state['search_performed'] = False
if "language" not in st.session_state:
    st.session_state["language"] = "en"  # 기본 언어는 영어
if "confirm_reset" not in st.session_state:
    st.session_state["confirm_reset"] = False  # 팝업에서 예를 눌렀는지 여부
if "target_language" not in st.session_state:
    st.session_state["target_language"] = "English"

# AWS S3 Configuration
S3_BUCKET_NAME = config.S3_BUCKET_NAME
S3_REGION_NAME = config.AWS_REGION
s3_client = boto3.client('s3', region_name=S3_REGION_NAME)

# 세션 상태에 따라 언어팩 로드
language_pack = load_language(st.session_state["language"])

# Streamlit 페이지 구성 설정 (페이지 제목 및 레이아웃)
st.set_page_config(
    page_title=language_pack.get("page_title", "Open Source Contribution Guide"),
    layout="wide",
)

def analyze_project(idx, project, language_pack):
    """프로젝트를 분석하고 세션 상태를 업데이트하는 헬퍼 함수"""
    with st.spinner(f"{language_pack.get('analyzing_culture_message', 'Analyzing culture for')} {project['name']}..."):
        # 프로젝트 문화 분석
        culture_analysis = analyze_project_culture(project['name'], project['readme'])
        st.session_state['analyzed_projects'][idx]['culture_analysis'] = culture_analysis

    with st.spinner(f"{language_pack.get('generating_guidelines_message', 'Generating guidelines for')} {project['name']}..."):
        # 기여 가이드라인 생성
        guidelines = generate_contribution_guidelines(project['name'])
        st.session_state['analyzed_projects'][idx]['guidelines'] = guidelines

    target_language = st.session_state.get('target_language', '').strip()
    if target_language:
        with st.spinner(f"Translating culture analysis into {target_language}..."):
            translated_culture_analysis = translate_text_with_claude(culture_analysis, target_language)
            st.session_state['analyzed_projects'][idx]['translated_culture_analysis'] = translated_culture_analysis
        with st.spinner(f"Translating guidelines into {target_language}..."):
            translated_guidelines = translate_text_with_claude(guidelines, target_language)
            st.session_state['analyzed_projects'][idx]['translated_guidelines'] = translated_guidelines

    # 프로젝트 검색 여부 플래그를 업데이트하여 UI 즉시 반영
    st.experimental_rerun()

# 언어 전환 버튼
col1, col2 = st.columns([9, 1])  # 언어 버튼을 오른쪽에 위치시키기 위한 열 너비 조정
with col1:
    st.title(language_pack.get("page_title", "Open Source Contribution Guide"))
with col2:
    # 언어 전환 버튼 (영어 <-> 한국어)
    if st.button("🇰🇷" if st.session_state["language"] == "en" else "ENG"):
        # 현재 언어 상태를 변경하고 페이지를 새로고침
        st.session_state["language"] = "ko" if st.session_state["language"] == "en" else "en"
        st.experimental_rerun()  # 페이지를 다시 렌더링하여 언어 업데이트

# 버튼 위치 조정 (CSS로 언어 버튼을 조정)
st.markdown(
    """
    <style>
        @media (min-width: 641px) {
            .css-ytkq5y.e1f1d6gn1 {
                top: 25px;
            }
        }
        .custom-divider {
            border-top: 3px solid red;
            margin: 25px 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# 1. User Input Stage
st.header(language_pack.get("header_1", "1. User Input"))

with st.form(key="user_input_form"):
    tech_stack = st.text_input(
        language_pack.get("tech_stack_label", "Enter your technology stack (e.g., Python, JavaScript):"),
        value="",
    )
    interest_areas = st.text_input(
        language_pack.get("interest_areas_label", "Enter your areas of interest (e.g., web development, data science):"),
        value="",
    )
    # available_hours = st.number_input(
    #     language_pack.get("available_hours_label", "Enter the number of hours you can contribute per week:"),
    #     min_value=1,
    #     max_value=40,
    #     value=5,
    # )
    target_language = st.text_input(
        language_pack.get("target_language_label", "Enter the target language (e.g., Korean, English):"),
        value="",
    )
    submit_button = st.form_submit_button(label=language_pack.get("find_projects_button", "Find Projects"))

# Update search_performed state when form is submitted
if submit_button:
    if not tech_stack.strip() or not interest_areas.strip():
        st.error(language_pack.get("error_message", "Please provide both your technology stack and areas of interest."))
    else:
        st.session_state['search_performed'] = True
        st.session_state['target_language'] = target_language
        with st.spinner(language_pack.get("fetching_projects_message", "Fetching recommended projects...")):
            recommended_projects = get_recommended_projects(tech_stack, interest_areas)
            st.session_state['recommended_projects'] = recommended_projects
            # Initialize analyzed_projects entries for new search
            st.session_state['analyzed_projects'] = {
                idx: {
                    'project_info': project,
                    'culture_analysis': None,
                    'guidelines': None
                }
                for idx, project in enumerate(recommended_projects)
            }

# Display projects if search has been performed
if st.session_state['search_performed']:
    st.header(language_pack.get("header_2", "2. Project Recommendations"))
    
    if not st.session_state['recommended_projects']:
        st.warning(language_pack.get("no_projects_warning", "No projects found. Please try different inputs."))
    else:
        for idx, project in enumerate(st.session_state['recommended_projects']):
            st.subheader(f"{idx + 1}. {project['name']}")
            
            # GitHub Readme Stats API를 사용하여 프로젝트 정보 표시
            repo_url = project['url']
            try:
                # GitHub URL에서 사용자명과 리포지토리명 추출
                repo_path = repo_url.replace("https://github.com/", "").strip("/")
                username, repo_name = repo_path.split("/")

                # GitHub Readme Stats API URL
                readme_stats_url = f"https://github-readme-stats.vercel.app/api/pin/?username={username}&repo={repo_name}"

                # 이미지 클릭 시 새 탭에서 GitHub 링크 열기 및 크기 조정
                st.markdown(
                    f"""
                    <a href="{repo_url}" target="_blank">
                        <img src="{readme_stats_url}" alt="{project['name']}" style="width:400px;">
                    </a>
                    """,
                    unsafe_allow_html=True
                )

            except Exception as e:
                st.error(f"Error loading GitHub stats: {e}")
                
            st.markdown('<br>', unsafe_allow_html=True)  # 줄바꿈 추가
            
            # Description과 GitHub Stats 사이에 구분선 추가
            st.write(f"**{language_pack.get('description_label', 'Description')}:** {project['description']}")

            st.markdown("---")  # 구분선 추가

            # 요약이 완료되지 않은 경우 요약 생성
            if f"summary_{idx}" not in st.session_state:
                with st.spinner(language_pack.get("generating_summary_message", f'Generating summary for {project["name"]}...')):
                    summary = summarize_text(project['readme'])
                    st.session_state[f"summary_{idx}"] = summary
            else:
                summary = st.session_state[f"summary_{idx}"]

            target_language = st.session_state.get('target_language', '').strip()
            if target_language:
                if f"translated_summary_{idx}" not in st.session_state:
                    with st.spinner(f"Translating summary into {target_language}..."):
                        translated_summary = translate_text_with_claude(summary, target_language)
                        st.session_state[f"translated_summary_{idx}"] = translated_summary
                else:
                    translated_summary = st.session_state[f"translated_summary_{idx}"]

                st.markdown(f"**{language_pack.get('summary_label', 'Summary')} ({target_language}):**")
                st.write(translated_summary)
            else:
                st.markdown(f"**{language_pack.get('summary_label', 'Summary')}:**")
                st.write(summary)

            # 프로젝트 분석 버튼에 고유 키 부여
            analyze_key = f"analyze_button_{idx}"
            
            # 프로젝트 분석 여부에 따라 버튼 출력
            project_data = st.session_state['analyzed_projects'].get(idx, {})
            if project_data.get('culture_analysis') is None:
                if st.button(f"{language_pack.get('analyze_button_label', 'Analyze')} {project['name']}", key=analyze_key):
                    analyze_project(idx, project, language_pack)  # 분석 후 페이지를 다시 렌더링하여 결과 즉시 표시
            else:
                target_language = st.session_state.get('target_language', '').strip()
                if target_language:
                    # Retrieve or translate the culture analysis
                    translated_culture_analysis = project_data.get('translated_culture_analysis')
                    if not translated_culture_analysis:
                        with st.spinner(f"Translating culture analysis into {target_language}..."):
                            translated_culture_analysis = translate_text_with_claude(project_data['culture_analysis'], target_language)
                            st.session_state['analyzed_projects'][idx]['translated_culture_analysis'] = translated_culture_analysis

                    # Retrieve or translate the guidelines
                    translated_guidelines = project_data.get('translated_guidelines')
                    if not translated_guidelines:
                        with st.spinner(f"Translating guidelines into {target_language}..."):
                            translated_guidelines = translate_text_with_claude(project_data['guidelines'], target_language)
                            st.session_state['analyzed_projects'][idx]['translated_guidelines'] = translated_guidelines

                    st.markdown(f"### {language_pack.get('culture_analysis_label', 'Culture Analysis')} ({target_language})")
                    st.write(translated_culture_analysis)
                    st.markdown(f"### {language_pack.get('guidelines_label', 'Contribution Guidelines')} ({target_language})")
                    st.write(translated_guidelines)
                else:
                    st.markdown(f"### {language_pack.get('culture_analysis_label', 'Culture Analysis')}")
                    st.write(project_data['culture_analysis'])
                    st.markdown(f"### {language_pack.get('guidelines_label', 'Contribution Guidelines')}")
                    st.write(project_data['guidelines'])

            st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)  # 구분선 추가

        # PDF Generation Section
        if any(data.get('culture_analysis') is not None for data in st.session_state['analyzed_projects'].values()):
            if st.button("Generate PDF and Upload to S3"):
                with st.spinner("Generating PDF and uploading to S3..."):
                    try:
                        # Collect only analyzed projects for PDF
                        project_data = [
                            {
                                'name': data['project_info']['name'],
                                'description': data['project_info']['description'],
                                'url': data['project_info']['url'],
                                'culture_analysis': data.get('translated_culture_analysis', data['culture_analysis']),
                                'guidelines': data.get('translated_guidelines', data['guidelines'])
                            }
                            for data in st.session_state['analyzed_projects'].values()
                            if data['culture_analysis'] is not None
                        ]

                        # Generate HTML content using Jinja2 template
                        template_path = 'templates/pdf_template.html'
                        with open(template_path, encoding='utf-8') as f:
                            template = Template(f.read())

                        html_content = template.render(projects=project_data)
                        
                        # Setup paths
                        output_dir = os.path.join(os.getcwd(), 'output_files')
                        os.makedirs(output_dir, exist_ok=True)
                        html_path = os.path.join(output_dir, 'temp.html')
                        pdf_path = os.path.join(output_dir, 'project_details.pdf')

                        # Generate PDF
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)

                        wkhtmltopdf_path = '/usr/bin/wkhtmltopdf'
                        config_pdfkit = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                        options = {
                            'encoding': 'UTF-8',
                            'enable-local-file-access': None,
                        }
                        pdfkit.from_file(html_path, pdf_path, configuration=config_pdfkit, options=options)

                        # Upload to S3
                        s3_key = f'project_details_{int(time.time())}.pdf'
                        s3_client.upload_file(pdf_path, S3_BUCKET_NAME, s3_key)
                        
                        # Generate download link
                        presigned_url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
                            ExpiresIn=3600
                        )

                        st.success("PDF generated and uploaded to S3.")
                        st.markdown(f"**Download your PDF here:** [Download PDF]({presigned_url})")

                        # Cleanup
                        os.remove(pdf_path)
                        os.remove(html_path)

                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        logging.error(f"PDF Generation or S3 Upload Error: {e}")