import streamlit as st

def collect_feedback():
    st.subheader("Feedback")
    feedback = st.text_area("Your Feedback:")
    if st.button("Submit Feedback"):
        # Process the feedback (e.g., save to a database)
        st.success("Feedback submitted successfully!")
