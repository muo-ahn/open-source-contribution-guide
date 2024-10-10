import streamlit as st

def get_user_input():
    st.subheader("Enter Your Information")
    tech_stack = st.text_input("Technology Stack (comma-separated):")
    interests = st.text_input("Interest Areas (comma-separated):")
    available_time = st.number_input("Hours Available for Contribution:", min_value=1)

    if st.button("Submit"):
        return {
            "tech_stack": [tech.strip() for tech in tech_stack.split(",")],
            "interests": [interest.strip() for interest in interests.split(",")],
            "available_time": available_time
        }
    return None
