# Open Source Contribution Guide

This project provides a guide for students to contribute to open source projects by recommending suitable projects based on their skills and interests.

## Installation

```bash
pip install -r requirements.txt
```

## To run

```bash
source env/Scripts/activate
streamlit run app.py
```

## API
### POST /recommend
Request Body : 
{
    "tech_stack": ["Python", "JavaScript"],
    "interests": ["Open Source", "Machine Learning"],
    "available_time": 5
}

Response : 
{
    "message": "Recommendations retrieved successfully!",
    "data": [ ... ]
}
