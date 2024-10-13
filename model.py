from pydantic import BaseModel
from typing import List

class UserInput(BaseModel):
    tech_stack: List[str]
    interests: List[str]
    available_time: int

class RecommendationOutput(BaseModel):
    message: str
    data: List[dict]

class CultureAnalysisOutput(BaseModel):
    message: str
    data: List[dict]
