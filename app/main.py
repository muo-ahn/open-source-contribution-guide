import streamlit as st
import requests
from user_input import get_user_input

def main():
    st.title("Open Source Contribution Guide")
    
    # User Input
    user_info = get_user_input()
    
    if user_info:
        # Project Recommendation
        response = requests.post("https://your-api-endpoint/recommend", json=user_info)
        recommended_projects = response.json()
        st.subheader("Recommended Projects:")
        st.write(recommended_projects)

        # Culture Analysis
        response = requests.post("https://your-api-endpoint/analyze-culture", json={"projects": recommended_projects})
        culture_analysis = response.json()
        st.subheader("Cultural Analysis:")
        st.write(culture_analysis)

        # Contribution Guidelines
        response = requests.post("https://your-api-endpoint/get-guidelines", json={"projects": recommended_projects})
        guidelines = response.json()
        st.subheader("Contribution Guidelines:")
        st.write(guidelines)

        # Feedback Collection
        feedback = collect_feedback()
        if feedback:
            # Send feedback to a backend service if needed
            st.success("Feedback submitted successfully!")

if __name__ == "__main__":
    main()
