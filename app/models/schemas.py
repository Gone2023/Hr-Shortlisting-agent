from pydantic import BaseModel, Field
from typing import List, Optional

class JobDescription(BaseModel):
    job_title: str
    company: str = Field(default="Unknown")
    required_skills: List[str]
    experience_years: Optional[int] = Field(default=None, description="Required years of experience")
    education: str = Field(default="Not specified")
    other_requirements: List[str] = Field(default_factory=list)

class CandidateProfile(BaseModel):
    name: str
    email: Optional[str] = None
    summary: str = Field(default="")
    skills: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    education: str = Field(default="Not specified")
    projects_portfolio: List[str] = Field(default_factory=list)

class DimensionScore(BaseModel):
    dimension_name: str = Field(description="Name of the dimension: 'Skills Match', 'Experience Relevance', 'Education & Certs', 'Project/Portfolio', 'Communication Quality'")
    score: int = Field(description="Score must be exactly 0, 5, or 10 based on rubric")
    justification: str = Field(description="One-line justification for the score")

class CandidateEvaluation(BaseModel):
    candidate_name: str
    scores: List[DimensionScore] = Field(description="Scores for exactly the 5 mandatory dimensions")
    total_weighted_score: float = Field(description="Total weighted score out of 100")
    recommendation: str = Field(description="Hire, No-Hire, or Interview")
    overall_summary: str = Field(description="Brief summary of the evaluation")
