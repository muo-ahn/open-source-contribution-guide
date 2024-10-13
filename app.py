import streamlit as st
from models import UserInput, RecommendationOutput, CultureAnalysisOutput
from services import recommend_projects, analyze_culture
from feedback import collect_feedback

# Title of the app
st.title("Open Source Contribution Guide")

# User input section
st.header("User Input")

tech_stack = st.text_input("Enter your tech stack (comma-separated):")
interests = st.text_input("Enter your interests (comma-separated):")
available_time = st.number_input("Available time per week (in hours):", min_value=1)

if st.button("Get Recommendations"):
    user_input = UserInput(
        tech_stack=[tech.strip() for tech in tech_stack.split(",")],
        interests=[interest.strip() for interest in interests.split(",")],
        available_time=available_time
    )

    recommendations = recommend_projects(user_input)
    st.subheader("Project Recommendations")
    st.write(recommendations)

    # Analyze culture for recommended projects
    culture_analysis = analyze_culture(recommendations)
    st.subheader("Culture Analysis")
    st.write(culture_analysis)

# Feedback section
st.header("Feedback")
feedback_input = st.text_area("Share your feedback about the recommendations:")
if st.button("Submit Feedback"):
    collect_feedback(feedback_input)
    st.success("Feedback submitted successfully!")
